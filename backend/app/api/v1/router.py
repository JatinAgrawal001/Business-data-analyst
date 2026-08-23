from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    projects,
    datasets,
    cleaning,
    eda,
    visualizations,
    nvidia,
    insights,
    recommendations,
    predictions,
    ask_data,
    reports
)

api_v1_router = APIRouter()

# Include version 1 endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(datasets.router)
api_v1_router.include_router(cleaning.router)
api_v1_router.include_router(eda.router)
api_v1_router.include_router(visualizations.router)
api_v1_router.include_router(nvidia.router)
api_v1_router.include_router(insights.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(predictions.router)
api_v1_router.include_router(ask_data.router)
api_v1_router.include_router(reports.router)
