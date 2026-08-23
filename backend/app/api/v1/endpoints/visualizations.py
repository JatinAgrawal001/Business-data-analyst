from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.visualization import (
    VisualizationDashboardResponse,
    CustomChartRequest,
    CustomChartResponse,
    ColorTheme
)
from app.services.visualization_service import visualization_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.visualizations")
router = APIRouter(prefix="/datasets", tags=["Visualization Agent"])

@router.get("/{dataset_id}/visualizations/dashboard", response_model=VisualizationDashboardResponse, summary="Get Interactive Visual Dashboard")
async def get_visual_dashboard(
    dataset_id: str,
    theme: ColorTheme = Query("indigo_modern", description="Color theme: indigo_modern, emerald_growth, sunset_amber, cyber_neon, slate_executive"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Generates a full interactive visual dashboard containing:
    - Executive KPI Cards
    - Multi-dimensional Bar Charts
    - Proportional Donut Charts
    - Temporal Area/Line Trends
    - Multi-Variable Scatter Correlations
    - Frequency Distribution Histograms
    """
    return await visualization_service.get_dashboard(
        dataset_id=dataset_id, user_id=current_user.id, theme=theme, user_jwt=user_jwt
    )

@router.post("/{dataset_id}/visualizations/query", response_model=CustomChartResponse, summary="Query Custom Chart (Text2Chart / Parametric)")
async def query_custom_chart(
    dataset_id: str,
    request: CustomChartRequest,
    theme: ColorTheme = Query("indigo_modern", description="Color theme for chart"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Generates a custom chart based on a natural language query (e.g. 'Show latency by sensor zone')
    or explicit dimension/metric parameters.
    """
    return await visualization_service.query_custom_chart(
        dataset_id=dataset_id, user_id=current_user.id, request=request, theme=theme, user_jwt=user_jwt
    )
