import uuid
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from app.services.supabase_client import supabase_manager
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.agents.ask_data_agent import ask_data_agent
from app.schemas.ask_data import (
    AskDataQueryRequest,
    AskDataQueryResponse,
    SuggestedQuestionsResponse,
    ChatHistoryMessage,
    ChatHistoryResponse
)
from app.core.logging import get_logger

logger = get_logger("app.services.ask_data")

class AskDataService:
    """
    Coordinates natural language data querying, visualization generation,
    and chat history persistence in Supabase.
    """

    def __init__(self):
        # In-memory fallback and test cache: dataset_id -> List[ChatHistoryMessage]
        self._history_cache: Dict[str, List[ChatHistoryMessage]] = {}

    async def ask_question(
        self,
        dataset_id: str,
        user_id: str,
        request: AskDataQueryRequest,
        user_jwt: Optional[str] = None
    ) -> AskDataQueryResponse:
        """
        Executes a natural language question against the dataset and persists conversation in Supabase.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        response = ask_data_agent.answer_query(df, profile, request)

        # 1. Record User Message in history
        user_msg = ChatHistoryMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            dataset_id=dataset_id,
            role="user",
            content=request.query
        )

        # 2. Record Assistant Message in history
        assistant_msg = ChatHistoryMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            dataset_id=dataset_id,
            role="assistant",
            content=response.answer,
            supporting_metrics=response.supporting_metrics,
            relevant_columns=response.relevant_columns,
            chart=response.chart
        )

        # Persist locally in cache
        if dataset_id not in self._history_cache:
            self._history_cache[dataset_id] = []
        self._history_cache[dataset_id].extend([user_msg, assistant_msg])

        # Persist in Supabase
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("chat_messages").insert([
                    {
                        "id": user_msg.id,
                        "user_id": user_id,
                        "dataset_id": dataset_id,
                        "role": "user",
                        "content": user_msg.content,
                        "created_at": user_msg.timestamp
                    },
                    {
                        "id": assistant_msg.id,
                        "user_id": user_id,
                        "dataset_id": dataset_id,
                        "role": "assistant",
                        "content": assistant_msg.content,
                        "supporting_metrics": assistant_msg.supporting_metrics,
                        "relevant_columns": assistant_msg.relevant_columns,
                        "created_at": assistant_msg.timestamp
                    }
                ]).execute()
            except Exception as e:
                logger.debug(f"Supabase chat_messages insert note: {e}")

        return response

    async def get_chat_history(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> ChatHistoryResponse:
        """
        Retrieves full chat history for the dataset from Supabase or memory cache.
        """
        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                res = client.table("chat_messages").select("*").eq("dataset_id", dataset_id).order("created_at", desc=False).execute()
                if res and res.data:
                    messages = [
                        ChatHistoryMessage(
                            id=m["id"],
                            user_id=m.get("user_id"),
                            dataset_id=m["dataset_id"],
                            role=m["role"],
                            content=m["content"],
                            supporting_metrics=m.get("supporting_metrics"),
                            relevant_columns=m.get("relevant_columns"),
                            timestamp=m.get("created_at", "")
                        )
                        for m in res.data
                    ]
                    return ChatHistoryResponse(
                        dataset_id=dataset_id,
                        messages=messages,
                        total_messages=len(messages)
                    )
            except Exception as e:
                logger.debug(f"Supabase chat_messages query note: {e}")

        cached_msgs = self._history_cache.get(dataset_id, [])
        return ChatHistoryResponse(
            dataset_id=dataset_id,
            messages=cached_msgs,
            total_messages=len(cached_msgs)
        )

    async def get_suggested_questions(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> SuggestedQuestionsResponse:
        """
        Generates dynamic starter questions tailored to the dataset's unique schema.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        return ask_data_agent.generate_starter_questions(profile)

ask_data_service = AskDataService()
