from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.visualization_agent import visualization_agent
from app.schemas.visualization import (
    VisualizationDashboardResponse,
    CustomChartRequest,
    CustomChartResponse,
    ColorTheme
)
from app.core.logging import get_logger

logger = get_logger("app.services.visualization")

class VisualizationService:
    """
    Coordinates auto-generated dashboard layouts and custom chart queries.
    """

    def __init__(self):
        self._dashboard_cache: Dict[str, VisualizationDashboardResponse] = {}

    async def generate_dashboard(
        self,
        dataset_id: str,
        user_id: str,
        theme: ColorTheme = "indigo_modern",
        user_jwt: Optional[str] = None
    ) -> VisualizationDashboardResponse:
        """
        Generates a curated multi-chart visual dashboard for the dataset.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        dashboard = visualization_agent.generate_dashboard(df, profile, theme=theme)
        self._dashboard_cache[dataset_id] = dashboard

        return dashboard

    async def get_dashboard(
        self,
        dataset_id: str,
        user_id: str,
        theme: ColorTheme = "indigo_modern",
        user_jwt: Optional[str] = None
    ) -> VisualizationDashboardResponse:
        """
        Retrieves cached dashboard or generates on demand.
        """
        if dataset_id not in self._dashboard_cache:
            return await self.generate_dashboard(dataset_id, user_id, theme, user_jwt)
        return self._dashboard_cache[dataset_id]

    async def query_custom_chart(
        self,
        dataset_id: str,
        user_id: str,
        request: CustomChartRequest,
        theme: ColorTheme = "indigo_modern",
        user_jwt: Optional[str] = None
    ) -> CustomChartResponse:
        """
        Generates a tailored chart based on user query or parameters.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        return visualization_agent.generate_custom_chart(df, profile, request, theme=theme)

visualization_service = VisualizationService()
