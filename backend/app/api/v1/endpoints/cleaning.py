from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.cleaning import (
    CleaningRecommendation,
    CleaningAuditReport,
    ApplyTransformationsRequest,
    TransformationResult
)
from app.services.cleaning_service import cleaning_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.cleaning")
router = APIRouter(prefix="/datasets", tags=["Data Cleaning Agent"])

@router.post("/{dataset_id}/cleaning/audit", response_model=CleaningAuditReport, summary="Run Data Cleaning Agent Audit")
async def audit_dataset_cleaning(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Runs the Google ADK Data Cleaning Agent to analyze the DatasetProfile and generate
    actionable cleaning recommendations (missing values, duplicates, outliers, inconsistent casing,
    incorrect types, suspicious values).
    Does NOT modify user data automatically.
    """
    return await cleaning_service.audit_dataset(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/cleaning/recommendations", response_model=List[CleaningRecommendation], summary="Get Cleaning Recommendations")
async def get_cleaning_recommendations(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Returns the list of pending, approved, or rejected data cleaning recommendations.
    """
    return await cleaning_service.get_recommendations(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/cleaning/apply", response_model=TransformationResult, summary="Apply Approved Transformations")
async def apply_cleaning_transformations(
    dataset_id: str,
    request: ApplyTransformationsRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Applies user-approved cleaning recommendations deterministically using pure Python/Pandas.
    Returns the before/after health score delta, rows modified, and transformed preview rows.
    """
    return await cleaning_service.apply_transformations(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )
