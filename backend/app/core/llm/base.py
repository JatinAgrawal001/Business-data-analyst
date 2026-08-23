from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.core.llm.types import LLMMessage, LLMResponse, LLMHealthStatus

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM providers (NVIDIA NIM, Google Gemini, etc.).
    Decouples core business reasoning, insight explanation, and natural language
    data queries from specific cloud vendor SDKs.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'nvidia', 'gemini')."""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Low-level multi-turn chat completion with retry and timeout resilience."""
        pass

    @abstractmethod
    async def explain_insight(
        self,
        metric_name: str,
        metric_value: Any,
        context: Dict[str, Any],
        user_prompt: Optional[str] = None
    ) -> str:
        """Explains an analytical insight, anomaly, or statistical pattern."""
        pass

    @abstractmethod
    async def generate_business_reasoning(
        self,
        dataset_summary: Dict[str, Any],
        key_metrics: List[Dict[str, Any]],
        segments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Synthesizes executive business reasoning from deterministic statistical summaries."""
        pass

    @abstractmethod
    async def generate_recommendations(
        self,
        audit_findings: List[Dict[str, Any]],
        performance_signals: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Generates actionable, prioritized strategic recommendations."""
        pass

    @abstractmethod
    async def answer_data_question(
        self,
        question: str,
        data_schema: Dict[str, Any],
        aggregated_facts: Dict[str, Any]
    ) -> str:
        """Answers natural language user questions strictly grounded in Python-computed facts."""
        pass

    @abstractmethod
    async def check_health(self) -> LLMHealthStatus:
        """Checks provider credentials and endpoint connectivity."""
        pass
