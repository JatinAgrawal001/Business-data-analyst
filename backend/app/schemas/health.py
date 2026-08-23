from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status, e.g. 'healthy'")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Current running environment, e.g. 'development', 'production'")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of the health check"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional diagnostic sub-system details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "app": "InsightFlow Analytics API",
                "version": "1.0.0",
                "environment": "development",
                "timestamp": "2026-08-21T05:26:00Z",
                "details": {
                    "api_version": "v1"
                }
            }
        }
    }
