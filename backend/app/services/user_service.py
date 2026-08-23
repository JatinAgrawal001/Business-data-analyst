from typing import Optional, Dict, Any
from app.services.supabase_client import supabase_manager
from app.core.logging import get_logger

logger = get_logger("app.services.user")

class UserService:
    """
    Reusable service for managing user profiles and metadata in Supabase PostgreSQL.
    """

    async def get_profile(self, user_id: str, user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return None
        try:
            res = client.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
            return res.data
        except Exception as e:
            logger.warning(f"Error retrieving user profile {user_id}: {e}")
            return None

    async def update_profile(self, user_id: str, payload: Dict[str, Any], user_jwt: Optional[str] = None) -> Dict[str, Any]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        payload["id"] = user_id
        if not client:
            return payload
        try:
            res = client.table("profiles").upsert(payload).execute()
            return res.data[0] if res.data else payload
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return payload

user_service = UserService()
