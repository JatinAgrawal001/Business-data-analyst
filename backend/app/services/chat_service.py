import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.core.logging import get_logger

logger = get_logger("app.services.chat")

class ChatService:
    """
    Reusable service for managing conversational analysis sessions and message history in Supabase.
    """

    async def get_history(
        self, user_id: str, dataset_id: str, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return []
        try:
            res = (
                client.table("chat_messages")
                .select("*")
                .eq("user_id", user_id)
                .eq("dataset_id", dataset_id)
                .order("created_at", desc=False)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning(f"Error getting chat history: {e}")
            return []

    async def save_message(
        self, user_id: str, dataset_id: str, role: str, content: str, user_jwt: Optional[str] = None
    ) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        record = {
            "id": msg_id,
            "user_id": user_id,
            "dataset_id": dataset_id,
            "role": role,
            "content": content
        }
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return record
        try:
            res = client.table("chat_messages").insert(record).execute()
            return res.data[0] if res.data else record
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return record

    async def clear_history(self, user_id: str, dataset_id: str, user_jwt: Optional[str] = None) -> bool:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if not client:
            return True
        try:
            client.table("chat_messages").delete().eq("user_id", user_id).eq("dataset_id", dataset_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            return False

chat_service = ChatService()
