from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.ask_data import (
    AskDataQueryRequest,
    AskDataQueryResponse,
    SuggestedQuestionsResponse,
    ChatHistoryResponse
)
from app.services.ask_data_service import ask_data_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.ask_data")
router = APIRouter(prefix="/datasets", tags=["Ask Your Data"])

@router.post("/{dataset_id}/ask", response_model=AskDataQueryResponse, summary="Ask Natural Language Question to Dataset")
async def ask_dataset_question(
    dataset_id: str,
    request: AskDataQueryRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Flow:
    1. Authenticated user question
    2. Dataset context resolution
    3. Intent understanding (Ranking, Extremums, Diagnostics, Root Cause, Trends, Aggregates)
    4. Deterministic Python/Pandas calculation (Zero Hallucinated Numbers)
    5. Actual numerical results & supporting metrics
    6. NVIDIA NIM natural language explanation
    7. Structured response (answer, supporting metrics, relevant columns, chart config)
    8. Persists chat conversation in Supabase
    """
    return await ask_data_service.ask_question(
        dataset_id=dataset_id, user_id=current_user.id, request=request, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/chat-history", response_model=ChatHistoryResponse, summary="Get Dataset Chat History")
async def get_dataset_chat_history(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Retrieves the full conversation history for the dataset from Supabase."""
    return await ask_data_service.get_chat_history(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/suggested-questions", response_model=SuggestedQuestionsResponse, summary="Get Dynamic Starter Questions for Dataset")
async def get_suggested_questions(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """Generates schema-tailored starter questions covering metrics, breakdowns, trends, and outliers."""
    return await ask_data_service.get_suggested_questions(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )
