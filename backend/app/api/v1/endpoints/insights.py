from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.insight import (
    InsightReport,
    QueryInsightRequest,
    QueryInsightResponse
)
from app.services.insight_service import insight_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.insights")
router = APIRouter(prefix="/datasets", tags=["Insight Agent"])

@router.post("/{dataset_id}/insights/generate", response_model=InsightReport, summary="Generate Executive Insight & Strategic Report")
async def generate_insight_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Synthesizes a 360-degree executive insight report containing:
    - Multi-dimensional patterns & statistical anomalies
    - Segment dominance & Pareto distribution insights
    - Strong correlation & dependency signals
    - Temporal trajectories and growth velocity
    - Prioritized high-ROI strategic recommendations
    """
    return await insight_service.generate_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/insights/report", response_model=InsightReport, summary="Get Cached Insight Report")
async def get_insight_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Retrieves the latest insight report for the dataset."""
    return await insight_service.get_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/insights/query", response_model=QueryInsightResponse, summary="Query Targeted Insights")
async def query_insights(
    dataset_id: str,
    request: QueryInsightRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Queries targeted insights for specific metric, dimension, or natural language prompt."""
    return await insight_service.query_insights(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )
