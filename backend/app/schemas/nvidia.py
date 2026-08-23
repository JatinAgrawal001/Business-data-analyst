from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class NvidiaMessage(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

class NvidiaChatRequest(BaseModel):
    messages: List[NvidiaMessage] = Field(..., min_length=1, description="Conversation history messages")
    model: Optional[str] = Field(default=None, description="NVIDIA NIM model identifier, e.g. meta/llama-3.3-70b-instruct")
    temperature: Optional[float] = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=8192)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False

class NvidiaUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class NvidiaChatResponse(BaseModel):
    id: str
    model: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = "stop"
    usage: NvidiaUsage = Field(default_factory=NvidiaUsage)
    created: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ExplainInsightRequest(BaseModel):
    metric_name: str
    metric_value: Any
    context: Dict[str, Any] = Field(default_factory=dict)
    prompt: Optional[str] = None

class BusinessReasoningRequest(BaseModel):
    dataset_summary: Dict[str, Any]
    key_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    segments: Optional[List[Dict[str, Any]]] = None

class RecommendationsRequest(BaseModel):
    audit_findings: List[Dict[str, Any]]
    performance_signals: Optional[List[Dict[str, Any]]] = None

class AskDataRequest(BaseModel):
    dataset_id: str
    question: str

class AskDataResponse(BaseModel):
    dataset_id: str
    question: str
    answer: str
    verified_facts: Dict[str, Any]

class NvidiaModelInfo(BaseModel):
    id: str
    name: str
    publisher: str
    context_window: int
    description: str

class NvidiaHealthResponse(BaseModel):
    status: Literal['healthy', 'unconfigured', 'degraded']
    available: bool
    default_model: str
    base_url: str
    has_api_key: bool
    error: Optional[str] = None
