from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.recommendation_agent import recommendation_agent
from app.schemas.recommendation import (
    RecommendationReport,
    BusinessRecommendation,
    RecommendationActionRequest,
    CustomRecommendationQueryRequest,
    CustomRecommendationQueryResponse,
    RecommendationStatus
)
from app.core.logging import get_logger

logger = get_logger("app.services.recommendation")

class RecommendationService:
    """
    Coordinates AI recommendation generation, prioritization, and user decision flows.
    """

    def __init__(self):
        self._report_cache: Dict[str, RecommendationReport] = {}

    async def generate_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> RecommendationReport:
        """
        Generates a comprehensive prioritized Recommendation Report for the dataset.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        report = recommendation_agent.generate_report(df, profile)
        self._report_cache[dataset_id] = report

        return report

    async def get_report(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> RecommendationReport:
        """Retrieves cached recommendation report or generates on demand."""
        if dataset_id not in self._report_cache:
            return await self.generate_report(dataset_id, user_id, user_jwt)
        return self._report_cache[dataset_id]

    async def update_recommendation_status(
        self,
        dataset_id: str,
        user_id: str,
        request: RecommendationActionRequest,
        user_jwt: Optional[str] = None
    ) -> BusinessRecommendation:
        """
        Updates the status of a specific recommendation (accept, reject, in_progress, completed).
        """
        status_map: Dict[str, RecommendationStatus] = {
            "accept": "accepted",
            "accepted": "accepted",
            "reject": "rejected",
            "rejected": "rejected",
            "in_progress": "in_progress",
            "completed": "completed"
        }
        new_status = status_map.get(request.action, "pending")

        report = await self.get_report(dataset_id, user_id, user_jwt)
        for rec in report.recommendations:
            if rec.id == request.recommendation_id:
                rec.status = new_status
                logger.info(f"Recommendation {rec.id} status updated to {new_status}")
                return rec

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID '{request.recommendation_id}' not found in dataset '{dataset_id}'."
        )

    async def query_recommendations(
        self,
        dataset_id: str,
        user_id: str,
        request: CustomRecommendationQueryRequest,
        user_jwt: Optional[str] = None
    ) -> CustomRecommendationQueryResponse:
        """Filters recommendations based on domain focus or target goals."""
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        return recommendation_agent.query_recommendations(df, profile, request)

recommendation_service = RecommendationService()
