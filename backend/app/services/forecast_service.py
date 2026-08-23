import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.core.security import verify_resource_ownership
from app.core.logging import get_logger

logger = get_logger("app.services.forecast")

class ForecastService:
    """
    Reusable service for persisting and querying time-series forecasts in Supabase.
    """

    async def list_forecasts(
        self, user_id: str, dataset_id: Optional[str] = None, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return []
        try:
            query = client.table("forecasts").select("*").order("created_at", desc=True)
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
            res = query.execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Error listing forecasts: {e}")
            return []

    async def get_forecast(self, forecast_id: str, user_id: str, user_jwt: Optional[str] = None) -> Dict[str, Any]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found")
        try:
            res = client.table("forecasts").select("*").eq("id", forecast_id).maybe_single().execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found")
            
            verify_resource_ownership(res.data.get("user_id"), user_id, "Forecast")
            return res.data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting forecast {forecast_id}: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found")

    async def save_forecast(self, user_id: str, payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        forecast_id = payload.get("id") or str(uuid.uuid4())
        record = {
            "id": forecast_id,
            "user_id": user_id,
            "project_id": payload.get("projectId"),
            "dataset_id": payload.get("datasetId"),
            "target_metric_key": payload.get("targetMetricKey"),
            "target_metric_label": payload.get("targetMetricLabel"),
            "time_column_key": payload.get("timeColumnKey", "period"),
            "historical_data": payload.get("historicalData", []),
            "forecast_data": payload.get("forecastData", []),
            "confidence_interval": payload.get("confidenceInterval", 95.0),
            "growth_rate": payload.get("growthRate", 0.0),
            "model_used": payload.get("modelUsed", "Polynomial Trend")
        }
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return record
        try:
            res = client.table("forecasts").upsert(record).execute()
            return res.data[0] if res.data else record
        except Exception as e:
            logger.error(f"Error saving forecast: {e}")
            return record

forecast_service = ForecastService()
