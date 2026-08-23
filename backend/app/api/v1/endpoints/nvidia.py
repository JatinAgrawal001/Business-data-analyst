from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.nvidia import (
    NvidiaChatRequest,
    NvidiaChatResponse,
    ExplainInsightRequest,
    BusinessReasoningRequest,
    RecommendationsRequest,
    AskDataRequest,
    AskDataResponse,
    NvidiaModelInfo,
    NvidiaHealthResponse
)
from app.services.nvidia_service import nvidia_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.nvidia")
router = APIRouter(prefix="/nvidia", tags=["NVIDIA AI Integration"])

@router.post("/chat", response_model=NvidiaChatResponse, summary="Chat Completion via NVIDIA NIM")
async def nvidia_chat_completion(
    request: NvidiaChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Direct chat completion endpoint with timeout, rate-limit, and retry protection.
    API keys remain safely isolated in backend environment variables.
    """
    return await nvidia_service.chat(request)

@router.post("/explain-insight", response_model=Dict[str, str], summary="Insight Explanation via NVIDIA")
async def explain_insight(
    request: ExplainInsightRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Uses NVIDIA LLM to explain an analytical finding or metric pattern.
    """
    explanation = await nvidia_service.explain_insight(
        metric_name=request.metric_name,
        metric_value=request.metric_value,
        context=request.context,
        prompt=request.prompt
    )
    return {"explanation": explanation}

@router.post("/business-reasoning", response_model=Dict[str, str], summary="Business Reasoning Synthesis via NVIDIA")
async def business_reasoning(
    request: BusinessReasoningRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Synthesizes strategic business reasoning from deterministic dataset facts.
    """
    reasoning = await nvidia_service.generate_business_reasoning(
        dataset_summary=request.dataset_summary,
        key_metrics=request.key_metrics,
        segments=request.segments
    )
    return {"business_reasoning": reasoning}

@router.post("/recommendations", response_model=Dict[str, List[str]], summary="Actionable Recommendations via NVIDIA")
async def get_recommendations(
    request: RecommendationsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generates prioritized strategic recommendations.
    """
    recommendations = await nvidia_service.generate_recommendations(
        audit_findings=request.audit_findings,
        performance_signals=request.performance_signals
    )
    return {"recommendations": recommendations}

@router.post("/ask-data", response_model=AskDataResponse, summary="Natural-Language Data Questions")
async def ask_data(
    request: AskDataRequest,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Answers natural language user questions strictly grounded in Python-computed calculations.
    """
    result = await nvidia_service.answer_data_question(
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        question=request.question,
        user_jwt=user_jwt
    )
    return AskDataResponse(**result)

@router.get("/models", response_model=List[NvidiaModelInfo], summary="List Supported NVIDIA NIM Models")
async def list_nvidia_models(
    current_user: User = Depends(get_current_user)
):
    """Returns the list of supported NVIDIA NIM foundation models."""
    return nvidia_service.list_models()

@router.get("/health", response_model=NvidiaHealthResponse, summary="NVIDIA API Connectivity & Health Check")
async def check_nvidia_health():
    """
    Checks the configuration and availability of the NVIDIA AI integration.
    Never exposes API keys or secrets in the response payload.
    """
    return await nvidia_service.check_health()
