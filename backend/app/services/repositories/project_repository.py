from typing import List, Optional, Dict, Any
from app.services.supabase_client import supabase_manager
from app.core.logging import get_logger

logger = get_logger("app.repositories.project")

class ProjectRepository:
    """
    Data access repository for projects stored in PostgreSQL `public.projects`.
    """

    async def list_for_user(self, user_id: str, user_jwt: Optional[str] = None) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return []

        try:
            res = (
                client.table("projects")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning(f"Error listing projects: {e}")
            return []

    async def get_by_id(self, project_id: str, user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return None

        try:
            res = (
                client.table("projects")
                .select("*")
                .eq("id", project_id)
                .maybe_single()
                .execute()
            )
            return res.data
        except Exception as e:
            logger.warning(f"Error fetching project {project_id}: {e}")
            return None

    async def create(self, project_payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return project_payload

        try:
            res = client.table("projects").insert(project_payload).execute()
            return res.data[0] if res.data else project_payload
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return project_payload

    async def update(self, project_id: str, updates: Dict[str, Any], user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return None

        try:
            res = client.table("projects").update(updates).eq("id", project_id).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return None

    async def delete(self, project_id: str, user_jwt: Optional[str] = None) -> bool:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return True

        try:
            client.table("projects").delete().eq("id", project_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False

project_repository = ProjectRepository()
