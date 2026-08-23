from typing import Dict, Any, Optional
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.insight_agent import insight_agent
from app.schemas.insight import (
    InsightReport,
    QueryInsightRequest,
    QueryInsightResponse
)
from app.core.logging import get_logger

logger = get_logger("app.services.insight")

class InsightService:
    """
    Coordinates AI Insight extraction, strategic recommendations, and query resolution.
    """

    def __init__(self):
        self._report_cache: Dict[str, InsightReport] = {}

    async def generate_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> InsightReport:
        """
        Generates a comprehensive 360-degree Insight Report for the dataset.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        report = insight_agent.generate_report(df, profile)
        self._report_cache[dataset_id] = report

        return report

    async def get_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> InsightReport:
        """Retrieves cached insight report or generates on demand."""
        if dataset_id not in self._report_cache:
            return await self.generate_report(dataset_id, user_id, user_jwt)
        return self._report_cache[dataset_id]

    async def query_insights(
        self,
        dataset_id: str,
        user_id: str,
        request: QueryInsightRequest,
        user_jwt: Optional[str] = None
    ) -> QueryInsightResponse:
        """Queries targeted insights for specific metric or dimension."""
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        return insight_agent.query_insights(df, profile, request)

insight_service = InsightService()
