from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.prediction import (
    PredictionReport,
    ValidatedTimeSeriesForecast,
    ForecastingSuitabilityReport,
    WhatIfScenarioRequest,
    WhatIfScenarioResponse,
    CustomForecastRequest
)
from app.services.prediction_service import prediction_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.predictions")
router = APIRouter(prefix="/datasets", tags=["Prediction Agent"])

@router.get("/{dataset_id}/predictions/suitability", response_model=ForecastingSuitabilityReport, summary="Audit Time-Series Forecasting Suitability")
async def audit_forecasting_suitability(
    dataset_id: str,
    target_metric: Optional[str] = Query(default=None, description="Optional metric to evaluate"),
    time_dimension: Optional[str] = Query(default=None, description="Optional datetime column to evaluate"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Performs a pre-flight suitability audit checking:
    - datetime column presence & parseability
    - continuous numeric metric presence & variance
    - historical series length (>= 5 periods)
    - frequency regularity
    - missing periods / gaps ratio
    - train/test holdout viability
    """
    return await prediction_service.check_suitability(
        dataset_id=dataset_id,
        user_id=current_user.id,
        target_metric=target_metric,
        time_dimension=time_dimension,
        user_jwt=user_jwt
    )

@router.post("/{dataset_id}/predictions/forecast", response_model=PredictionReport, summary="Generate Time-Series Forecasts & Attribution Report")
async def generate_prediction_report(
    dataset_id: str,
    horizon: int = Query(default=6, ge=1, le=36, description="Forecast horizon periods"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Audits suitability and compiles forecast report.
    If unsuitable, provides structured explanation of unsuitability reasons rather than fake numbers.
    """
    return await prediction_service.generate_report(
        dataset_id=dataset_id, user_id=current_user.id, forecast_horizon=horizon, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/predictions/report", response_model=PredictionReport, summary="Get Cached Prediction Report")
async def get_prediction_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Retrieves the latest prediction and forecast deck for the dataset."""
    return await prediction_service.get_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/predictions/custom-forecast", response_model=ValidatedTimeSeriesForecast, summary="Generate Custom Metric Forecast")
async def generate_custom_metric_forecast(
    dataset_id: str,
    request: CustomForecastRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Generates a parametric time-series forecast for a specific user-selected target metric with baseline comparison."""
    return await prediction_service.generate_custom_forecast(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/predictions/what-if", response_model=WhatIfScenarioResponse, summary="Simulate What-If Scenario")
async def simulate_what_if_scenario(
    dataset_id: str,
    request: WhatIfScenarioRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Executes a deterministic what-if scenario simulation by adjusting feature multiplier inputs
    and calculating predicted metric deltas based on empirical sensitivity beta weights.
    """
    return await prediction_service.simulate_what_if(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )
