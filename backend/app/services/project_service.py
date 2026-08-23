import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.core.security import verify_resource_ownership
from app.core.logging import get_logger

logger = get_logger("app.services.project")

def ensure_valid_uuid(id_str: Optional[str]) -> str:
    """Ensures a string is a valid UUID, or converts via deterministic namespace."""
    if not id_str:
        return str(uuid.uuid4())
    try:
        uuid.UUID(id_str)
        return id_str
    except (ValueError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, id_str))

class ProjectService:
    """
    Reusable service for project access control and Supabase persistence.
    """

    def __init__(self):
        self._local_projects: Dict[str, Dict[str, Any]] = {}

    async def list_projects(self, user_id: str, user_jwt: Optional[str] = None) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("projects").select("*").order("created_at", desc=True).execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Error listing projects from Supabase: {e}")

        # Fallback to local store for development
        return [p for p in self._local_projects.values() if p.get("user_id") == user_id]

    async def get_project(self, project_id: str, user_id: str, user_jwt: Optional[str] = None) -> Dict[str, Any]:
        clean_proj_id = ensure_valid_uuid(project_id)
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("projects").select("*").eq("id", clean_proj_id).maybe_single().execute()
                if res and res.data:
                    verify_resource_ownership(res.data.get("user_id"), user_id, "Project")
                    return res.data
            except HTTPException:
                raise
            except Exception as e:
                logger.debug(f"Project lookup in Supabase: {e}")

        # Check local store
        record = self._local_projects.get(clean_proj_id) or self._local_projects.get(project_id)
        if record:
            verify_resource_ownership(record.get("user_id"), user_id, "Project")
            return record

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    async def create_project(self, user_id: str, payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        raw_id = payload.get("id")
        proj_id = ensure_valid_uuid(raw_id)
        record = {
            "id": proj_id,
            "user_id": user_id,
            "name": payload.get("name", "New Project"),
            "description": payload.get("description", ""),
            "tags": payload.get("tags", []),
            "status": payload.get("status", "active"),
            "member_count": payload.get("member_count", 1)
        }

        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("projects").insert(record).execute()
                if res and res.data:
                    self._local_projects[proj_id] = res.data[0]
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Project insert note: {e}")

        self._local_projects[proj_id] = record
        return record

    async def update_project(self, project_id: str, user_id: str, updates: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        existing = await self.get_project(project_id, user_id, user_jwt)
        clean_proj_id = existing["id"]
        
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("projects").update(updates).eq("id", clean_proj_id).execute()
                if res and res.data:
                    self._local_projects[clean_proj_id] = res.data[0]
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Project update note: {e}")

        existing.update(updates)
        self._local_projects[clean_proj_id] = existing
        return existing

    async def delete_project(self, project_id: str, user_id: str, user_jwt: Optional[str] = None) -> bool:
        existing = await self.get_project(project_id, user_id, user_jwt)
        clean_proj_id = existing["id"]
        
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("projects").delete().eq("id", clean_proj_id).execute()
            except Exception as e:
                logger.debug(f"Project delete note: {e}")

        self._local_projects.pop(clean_proj_id, None)
        return True

project_service = ProjectService()
