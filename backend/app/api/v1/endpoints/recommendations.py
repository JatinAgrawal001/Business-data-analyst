from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationReport,
    BusinessRecommendation,
    RecommendationActionRequest,
    CustomRecommendationQueryRequest,
    CustomRecommendationQueryResponse
)
from app.services.recommendation_service import recommendation_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.recommendations")
router = APIRouter(prefix="/datasets", tags=["Recommendation Agent"])

@router.post("/{dataset_id}/recommendations/generate", response_model=RecommendationReport, summary="Generate Prioritized Business Recommendations")
async def generate_recommendation_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Synthesizes a prioritized strategic recommendation report containing:
    - Composite priority ranking (Impact vs Effort vs Confidence)
    - Value Matrix classification (Quick Wins, Strategic Bets, Tactical Fixes)
    - Quantitative ROI uplift projections grounded in Python facts
    - Concrete 3-phase execution roadmaps with milestones
    """
    return await recommendation_service.generate_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/recommendations/report", response_model=RecommendationReport, summary="Get Cached Recommendation Report")
async def get_recommendation_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Retrieves the latest recommendation deck for the dataset."""
    return await recommendation_service.get_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/recommendations/action", response_model=BusinessRecommendation, summary="Update Recommendation Status")
async def update_recommendation_action(
    dataset_id: str,
    request: RecommendationActionRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Updates recommendation status: accept, reject, in_progress, completed."""
    return await recommendation_service.update_recommendation_status(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/recommendations/query", response_model=CustomRecommendationQueryResponse, summary="Query Recommendations by Domain/Goal")
async def query_recommendations(
    dataset_id: str,
    request: CustomRecommendationQueryRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Filters recommendations based on domain focus or specific target goals."""
    return await recommendation_service.query_recommendations(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )
