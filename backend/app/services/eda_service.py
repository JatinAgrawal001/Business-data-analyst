from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.schemas.eda import EDAReport, ChartRecommendation
from app.core.logging import get_logger

logger = get_logger("app.services.eda")

class EDAService:
    """
    Coordinates Exploratory Data Analysis (EDA) runs and artifact caching.
    """

    def __init__(self):
        self._eda_cache: Dict[str, EDAReport] = {}

    async def run_eda_analysis(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> EDAReport:
        """
        Executes full EDA Agent analysis on the dataset.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        report = eda_agent.generate_eda_report(df, profile)
        self._eda_cache[dataset_id] = report

        return report

    async def get_eda_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> EDAReport:
        """
        Retrieves cached EDA report or generates on demand.
        """
        if dataset_id not in self._eda_cache:
            return await self.run_eda_analysis(dataset_id, user_id, user_jwt)
        return self._eda_cache[dataset_id]

    async def get_recommended_charts(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> List[ChartRecommendation]:
        """
        Retrieves the list of recommended visualization blueprints.
        """
        report = await self.get_eda_report(dataset_id, user_id, user_jwt)
        return report.chart_recommendations

eda_service = EDAService()
