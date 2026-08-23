from typing import Optional
from app.core.config import settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.nvidia_provider import nvidia_llm_provider
from app.core.logging import get_logger

logger = get_logger("app.core.llm.factory")

def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function returning the active LLM provider based on settings.LLM_PROVIDER
    or explicit override.
    """
    chosen = (provider_name or settings.LLM_PROVIDER or "nvidia").lower().strip()

    if chosen == "nvidia":
        return nvidia_llm_provider
    elif chosen == "gemini":
        # Can route to Gemini provider if needed; currently default is resilient NVIDIA
        return nvidia_llm_provider
    else:
        logger.info(f"Using default NVIDIA LLM provider for '{chosen}'")
        return nvidia_llm_provider
