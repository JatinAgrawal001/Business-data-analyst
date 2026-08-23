from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.prediction_agent import prediction_agent
from app.schemas.prediction import (
    PredictionReport,
    ValidatedTimeSeriesForecast,
    ForecastingSuitabilityReport,
    WhatIfScenarioRequest,
    WhatIfScenarioResponse,
    CustomForecastRequest
)
from app.core.logging import get_logger

logger = get_logger("app.services.prediction")

class PredictionService:
    """
    Coordinates AI predictive forecasting, driver attribution, and what-if scenario simulations.
    """

    def __init__(self):
        self._report_cache: Dict[str, PredictionReport] = {}

    async def generate_report(
        self,
        dataset_id: str,
        user_id: str,
        forecast_horizon: int = 6,
        user_jwt: Optional[str] = None
    ) -> PredictionReport:
        """
        Generates a comprehensive Prediction & Forecasting Report for the dataset.
        If dataset is unsuitable, returns analytical explanation without fake forecasts.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        report = prediction_agent.generate_report(df, profile, forecast_horizon=forecast_horizon)
        self._report_cache[dataset_id] = report

        return report

    async def get_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> PredictionReport:
        """Retrieves cached prediction report or generates on demand."""
        if dataset_id not in self._report_cache:
            return await self.generate_report(dataset_id, user_id, user_jwt=user_jwt)
        return self._report_cache[dataset_id]

    async def check_suitability(
        self,
        dataset_id: str,
        user_id: str,
        target_metric: Optional[str] = None,
        time_dimension: Optional[str] = None,
        user_jwt: Optional[str] = None
    ) -> ForecastingSuitabilityReport:
        """Checks forecasting suitability without fitting models."""
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        return prediction_agent.evaluate_forecasting_suitability(
            df, profile, target_metric=target_metric, time_dim=time_dimension
        )

    async def generate_custom_forecast(
        self,
        dataset_id: str,
        user_id: str,
        request: CustomForecastRequest,
        user_jwt: Optional[str] = None
    ) -> ValidatedTimeSeriesForecast:
        """Generates a custom forecast for a requested metric and horizon if suitable."""
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        suitability = prediction_agent.evaluate_forecasting_suitability(
            df, profile, target_metric=request.target_metric, time_dim=request.time_dimension
        )

        if not suitability.is_suitable:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Dataset is unsuitable for forecasting.",
                    "reasons": suitability.unsuitability_reasons,
                    "remediations": suitability.remediation_suggestions
                }
            )

        return prediction_agent.fit_validated_forecast(
            df, profile, target_metric=request.target_metric, time_dim=request.time_dimension, forecast_horizon=request.forecast_periods
        )

    async def simulate_what_if(
        self,
        dataset_id: str,
        user_id: str,
        request: WhatIfScenarioRequest,
        user_jwt: Optional[str] = None
    ) -> WhatIfScenarioResponse:
        """Runs what-if simulation on dataset metrics."""
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)

        return prediction_agent.simulate_what_if_scenario(df, request)

prediction_service = PredictionService()
