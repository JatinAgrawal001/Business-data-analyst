from typing import List, Optional, Dict, Any
from app.services.supabase_client import supabase_manager
from app.core.logging import get_logger

logger = get_logger("app.repositories.dataset")

class DatasetRepository:
    """
    Data access repository for dataset metadata stored in PostgreSQL `public.datasets`.
    """

    async def list_for_user(
        self, user_id: str, project_id: Optional[str] = None, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return []

        try:
            query = client.table("datasets").select("*").order("uploaded_at", desc=True)
            if project_id:
                query = query.eq("project_id", project_id)
            res = query.execute()
            return res.data or []
        except Exception as e:
            logger.warning(f"Error listing datasets: {e}")
            return []

    async def get_by_id(self, dataset_id: str, user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return None

        try:
            res = (
                client.table("datasets")
                .select("*")
                .eq("id", dataset_id)
                .maybe_single()
                .execute()
            )
            return res.data
        except Exception as e:
            logger.warning(f"Error fetching dataset {dataset_id}: {e}")
            return None

    async def save_metadata(self, dataset_payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return dataset_payload

        try:
            res = client.table("datasets").upsert(dataset_payload).execute()
            return res.data[0] if res.data else dataset_payload
        except Exception as e:
            logger.error(f"Error saving dataset metadata: {e}")
            return dataset_payload

    async def delete(self, dataset_id: str, user_jwt: Optional[str] = None) -> bool:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return True

        try:
            client.table("datasets").delete().eq("id", dataset_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_id}: {e}")
            return False

dataset_repository = DatasetRepository()
