from fastapi import APIRouter, status
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Status",
    description="Returns current operational status, application version, environment, and timestamp."
)
async def check_health() -> HealthResponse:
    """
    Health check endpoint for container orchestrators, load balancers, and monitoring tools.
    """
    return HealthResponse(
        status="healthy",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        details={
            "api_version": "v1",
            "debug_mode": settings.DEBUG
        }
    )
