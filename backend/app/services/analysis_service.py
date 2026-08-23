import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.core.security import verify_resource_ownership
from app.core.logging import get_logger

logger = get_logger("app.services.analysis")

class AnalysisService:
    """
    Reusable service for saving, retrieving, and scoping multi-variable dataset analyses.
    """

    async def list_analyses(
        self, user_id: str, project_id: Optional[str] = None, dataset_id: Optional[str] = None, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return []
        try:
            query = client.table("analyses").select("*").order("created_at", desc=True)
            if project_id:
                query = query.eq("project_id", project_id)
            if dataset_id:
                query = query.eq("dataset_id", dataset_id)
            res = query.execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Error listing analyses: {e}")
            return []

    async def get_analysis(self, analysis_id: str, user_id: str, user_jwt: Optional[str] = None) -> Dict[str, Any]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
        try:
            res = client.table("analyses").select("*").eq("id", analysis_id).maybe_single().execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
            
            verify_resource_ownership(res.data.get("user_id"), user_id, "Analysis")
            return res.data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting analysis {analysis_id}: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    async def save_analysis(self, user_id: str, analysis_payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        analysis_id = analysis_payload.get("id") or str(uuid.uuid4())
        record = {
            "id": analysis_id,
            "user_id": user_id,
            "project_id": analysis_payload.get("projectId"),
            "dataset_id": analysis_payload.get("datasetId"),
            "status": analysis_payload.get("status", "completed"),
            "progress_percentage": analysis_payload.get("progressPercentage", 100),
            "kpis": analysis_payload.get("kpis", []),
            "charts": analysis_payload.get("charts", []),
            "statistical_summary": analysis_payload.get("statisticalSummary", {})
        }
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return record
        try:
            res = client.table("analyses").upsert(record).execute()
            return res.data[0] if res.data else record
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return record

    async def delete_analysis(self, analysis_id: str, user_id: str, user_jwt: Optional[str] = None) -> bool:
        await self.get_analysis(analysis_id, user_id, user_jwt)
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("analyses").delete().eq("id", analysis_id).execute()
                return True
            except Exception as e:
                logger.error(f"Error deleting analysis {analysis_id}: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete analysis")
        return True

analysis_service = AnalysisService()
