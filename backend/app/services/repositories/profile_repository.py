from typing import Optional, Dict, Any
from app.services.supabase_client import supabase_manager
from app.core.logging import get_logger

logger = get_logger("app.repositories.profile")

class ProfileRepository:
    """
    Data access repository for user profiles stored in PostgreSQL `public.profiles`.
    """

    async def get_by_user_id(self, user_id: str, user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return None

        try:
            res = client.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
            return res.data
        except Exception as e:
            logger.warning(f"Error fetching profile for user {user_id}: {e}")
            return None

    async def upsert_profile(self, profile_data: Dict[str, Any], user_jwt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return profile_data

        try:
            res = client.table("profiles").upsert(profile_data).execute()
            return res.data[0] if res.data else profile_data
        except Exception as e:
            logger.error(f"Error upserting profile: {e}")
            return profile_data

profile_repository = ProfileRepository()
