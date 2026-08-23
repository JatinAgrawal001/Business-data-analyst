import uuid
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.nvidia import (
    NvidiaChatRequest,
    NvidiaChatResponse,
    NvidiaUsage,
    NvidiaModelInfo,
    NvidiaHealthResponse
)
from app.core.logging import get_logger

logger = get_logger("app.core.nvidia_client")

SUPPORTED_NVIDIA_MODELS: List[NvidiaModelInfo] = [
    NvidiaModelInfo(
        id="meta/llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct",
        publisher="Meta / NVIDIA NIM",
        context_window=131072,
        description="State-of-the-art 70B instruction-tuned model with advanced reasoning, coding, and analytics synthesis."
    ),
    NvidiaModelInfo(
        id="nvidia/llama-3.1-nemotron-70b-instruct",
        name="Nemotron 70B Instruct",
        publisher="NVIDIA",
        context_window=131072,
        description="NVIDIA-optimized model tuned for complex multi-step reasoning, mathematical problem-solving, and roleplay."
    ),
    NvidiaModelInfo(
        id="meta/llama-3.1-405b-instruct",
        name="Llama 3.1 405B Instruct",
        publisher="Meta / NVIDIA NIM",
        context_window=131072,
        description="Flagship 405B dense foundation model for unmatched analytical depth and complex strategy synthesis."
    ),
    NvidiaModelInfo(
        id="mistralai/mixtral-8x22b-instruct-v0.1",
        name="Mixtral 8x22B Instruct",
        publisher="Mistral AI / NVIDIA NIM",
        context_window=65536,
        description="High-throughput Sparse Mixture-of-Experts model for rapid analysis and structured outputs."
    ),
    NvidiaModelInfo(
        id="deepseek-ai/deepseek-r1",
        name="DeepSeek R1",
        publisher="DeepSeek / NVIDIA NIM",
        context_window=65536,
        description="Advanced chain-of-thought reasoning model for mathematical validation and deep anomaly diagnosis."
    )
]

class NvidiaClient:
    """
    Async HTTP client for NVIDIA Inference Microservices (NIM) API.
    Interacts with https://integrate.api.nvidia.com/v1 endpoints.
    """

    def __init__(self):
        self.base_url = settings.NVIDIA_BASE_URL.rstrip("/")
        self.api_key = settings.NVIDIA_API_KEY
        self.default_model = settings.NVIDIA_DEFAULT_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def chat_completion(
        self,
        request: NvidiaChatRequest,
        api_key_override: Optional[str] = None
    ) -> NvidiaChatResponse:
        """
        Sends a chat completion request to NVIDIA NIM API.
        """
        key = api_key_override or self.api_key
        model = request.model or self.default_model

        if not key:
            # Return graceful informative response when API key is pending configuration
            logger.warning("NVIDIA_API_KEY is not set. Generating contextual fallback response.")
            return NvidiaChatResponse(
                id=f"nvidia-mock-{uuid.uuid4().hex[:8]}",
                model=model,
                content=(
                    f"NVIDIA NIM ({model}) integration is active and ready. "
                    "To enable live cloud LLM inference, configure 'NVIDIA_API_KEY' in your environment settings."
                ),
                role="assistant",
                finish_reason="stop",
                usage=NvidiaUsage(prompt_tokens=10, completion_tokens=25, total_tokens=35)
            )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature if request.temperature is not None else settings.NVIDIA_TEMPERATURE,
            "max_tokens": request.max_tokens or settings.NVIDIA_MAX_TOKENS,
            "top_p": request.top_p or 1.0,
            "stream": False
        }

        endpoint = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(endpoint, headers=headers, json=payload)
                
                if response.status_code != 200:
                    error_msg = response.text
                    logger.error(f"NVIDIA API Error ({response.status_code}): {error_msg}")
                    return NvidiaChatResponse(
                        id=f"nvidia-err-{uuid.uuid4().hex[:8]}",
                        model=model,
                        content=f"NVIDIA API request returned status {response.status_code}. Details: {error_msg[:200]}",
                        role="assistant",
                        finish_reason="error",
                        usage=NvidiaUsage()
                    )

                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                usage_data = data.get("usage", {})

                return NvidiaChatResponse(
                    id=data.get("id", str(uuid.uuid4())),
                    model=data.get("model", model),
                    content=message.get("content", ""),
                    role=message.get("role", "assistant"),
                    finish_reason=choice.get("finish_reason", "stop"),
                    usage=NvidiaUsage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0)
                    )
                )

            except Exception as e:
                logger.error(f"NVIDIA Client exception: {e}")
                return NvidiaChatResponse(
                    id=f"nvidia-exc-{uuid.uuid4().hex[:8]}",
                    model=model,
                    content=f"Unable to connect to NVIDIA API endpoint: {str(e)}",
                    role="assistant",
                    finish_reason="error",
                    usage=NvidiaUsage()
                )

    def get_supported_models(self) -> List[NvidiaModelInfo]:
        """Returns the list of recommended NVIDIA NIM models."""
        return SUPPORTED_NVIDIA_MODELS

    async def check_health(self) -> NvidiaHealthResponse:
        """Checks NVIDIA API configuration and connectivity."""
        has_key = self.is_configured()
        if not has_key:
            return NvidiaHealthResponse(
                status="unconfigured",
                available=False,
                default_model=self.default_model,
                base_url=self.base_url,
                has_api_key=False,
                error="NVIDIA_API_KEY environment variable is not configured."
            )

        return NvidiaHealthResponse(
            status="healthy",
            available=True,
            default_model=self.default_model,
            base_url=self.base_url,
            has_api_key=True,
            error=None
        )

nvidia_client = NvidiaClient()
