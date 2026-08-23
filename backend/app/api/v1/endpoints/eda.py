from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.eda import EDAReport, ChartRecommendation
from app.services.eda_service import eda_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.eda")
router = APIRouter(prefix="/datasets", tags=["EDA Agent"])

@router.post("/{dataset_id}/eda/analyze", response_model=EDAReport, summary="Run Automated EDA Analysis")
async def analyze_dataset_eda(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Executes automated Exploratory Data Analysis (EDA) using the Google ADK EDA Agent:
    - Subgroup segmentations & group-by aggregations
    - Chronological time-series trend analysis
    - Multi-variable correlation signals
    - Dynamic front-end chart visualization blueprints
    - Executive business takeaways and insights
    """
    return await eda_service.run_eda_analysis(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/eda/report", response_model=EDAReport, summary="Get EDA Analysis Report")
async def get_dataset_eda_report(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Retrieves the complete Exploratory Data Analysis (EDA) report for the dataset.
    """
    return await eda_service.get_eda_report(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/eda/charts", response_model=List[ChartRecommendation], summary="Get Recommended Charts")
async def get_eda_charts(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Retrieves recommended visualization blueprints (bar, line, donut, scatter charts) tailored to the dataset.
    """
    return await eda_service.get_recommended_charts(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )
