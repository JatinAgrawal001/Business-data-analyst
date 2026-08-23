import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.core.security import verify_resource_ownership
from app.core.logging import get_logger

logger = get_logger("app.services.report")

class ReportService:
    """
    Reusable service for managing executive intelligence reports in Supabase,
    with automatic in-memory fallback for detached or test execution environments.
    """

    def __init__(self):
        self._local_reports: Dict[str, Dict[str, Any]] = {}

    async def list_reports(
        self, user_id: str, project_id: Optional[str] = None, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        combined: Dict[str, Dict[str, Any]] = {}
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                query = client.table("reports").select("*").order("created_at", desc=True)
                if project_id:
                    query = query.eq("project_id", project_id)
                res = query.execute()
                if res.data:
                    for r in res.data:
                        combined[r["id"]] = r
            except Exception as e:
                logger.warning(f"Error listing reports in Supabase: {e}")

        # Merge local store
        for r_id, r in self._local_reports.items():
            if r_id not in combined:
                if not project_id or r.get("project_id") == project_id:
                    combined[r_id] = r

        return list(combined.values())

    async def get_report(self, report_id: str, user_id: str, user_jwt: Optional[str] = None) -> Dict[str, Any]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("reports").select("*").eq("id", report_id).maybe_single().execute()
                if res and res.data:
                    verify_resource_ownership(res.data.get("user_id"), user_id, "Report")
                    return res.data
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting report {report_id} from Supabase: {e}")

        # Local fallback
        if report_id in self._local_reports:
            rep = self._local_reports[report_id]
            verify_resource_ownership(rep.get("user_id"), user_id, "Report")
            return rep

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    async def create_report(self, user_id: str, payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        report_id = payload.get("id") or str(uuid.uuid4())
        record = {
            "id": report_id,
            "user_id": user_id,
            "project_id": payload.get("project_id") or payload.get("projectId") or "proj-general",
            "dataset_id": payload.get("dataset_id") or payload.get("datasetId") or "",
            "title": payload.get("title", "Executive Report"),
            "subtitle": payload.get("subtitle", ""),
            "executive_summary": payload.get("executive_summary") or payload.get("executiveSummary") or "",
            "sections": payload.get("sections", []),
            "key_takeaways": payload.get("key_takeaways") or payload.get("keyTakeaways") or [],
            "author": payload.get("author", "Lead Data Analyst"),
            "status": payload.get("status", "published"),
            "format": payload.get("format", "pdf"),
            "cadence": payload.get("cadence", "on_demand"),
            "disclaimer": payload.get("disclaimer", ""),
            "generated_at": payload.get("generated_at") or payload.get("generatedAt") or datetime.now(timezone.utc).isoformat()
        }

        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                # Strip fields not in minimal table if any
                res = client.table("reports").insert(record).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Supabase report insert fallback: {e}")

        self._local_reports[report_id] = record
        return record

    async def delete_report(self, report_id: str, user_id: str, user_jwt: Optional[str] = None) -> bool:
        await self.get_report(report_id, user_id, user_jwt)
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("reports").delete().eq("id", report_id).execute()
            except Exception as e:
                logger.error(f"Error deleting report {report_id}: {e}")

        if report_id in self._local_reports:
            del self._local_reports[report_id]
        return True

report_service = ReportService()
