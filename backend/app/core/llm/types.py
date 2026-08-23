from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

LLMProviderType = Literal['nvidia', 'gemini', 'mock']

class LLMMessage(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMResponse(BaseModel):
    id: str
    provider: LLMProviderType
    model: str
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = "stop"
    usage: LLMUsage = Field(default_factory=LLMUsage)
    latency_ms: float = 0.0
    created: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LLMHealthStatus(BaseModel):
    provider: LLMProviderType
    status: Literal['healthy', 'unconfigured', 'degraded']
    available: bool
    model: str
    base_url: Optional[str] = None
    has_credentials: bool
    error: Optional[str] = None
