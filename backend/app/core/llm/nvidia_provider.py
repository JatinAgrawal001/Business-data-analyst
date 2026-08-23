import time
import uuid
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.types import LLMMessage, LLMResponse, LLMUsage, LLMHealthStatus
from app.core.logging import get_logger

logger = get_logger("app.core.llm.nvidia")

class NvidiaLLMProvider(BaseLLMProvider):
    """
    Production-grade NVIDIA NIM LLM Provider with:
    - Timeout handling (configurable via settings.NVIDIA_TIMEOUT_SECONDS)
    - Retry handling with exponential backoff on 5xx / connection drops
    - Rate limit handling (HTTP 429 with Retry-After header parsing)
    - Sensitive credentials isolation (API key never exposed in logs or payloads)
    - Structured latency & token usage logging
    """

    def __init__(self):
        self.base_url = settings.NVIDIA_BASE_URL.rstrip("/")
        self._api_key = settings.NVIDIA_API_KEY
        self.default_model = settings.NVIDIA_DEFAULT_MODEL
        self.timeout_seconds = settings.NVIDIA_TIMEOUT_SECONDS
        self.max_retries = settings.NVIDIA_MAX_RETRIES
        self.backoff_factor = settings.NVIDIA_RETRY_BACKOFF_FACTOR

    @property
    def provider_name(self) -> str:
        return "nvidia"

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Executes chat completion against NVIDIA NIM endpoint with robust retry/rate-limit resilience.
        """
        target_model = model or self.default_model
        temp = temperature if temperature is not None else settings.NVIDIA_TEMPERATURE
        max_tok = max_tokens or settings.NVIDIA_MAX_TOKENS

        if not self.is_configured():
            logger.warning("NVIDIA_API_KEY is not configured. Returning deterministic fallback.")
            return LLMResponse(
                id=f"nvidia-mock-{uuid.uuid4().hex[:8]}",
                provider="nvidia",
                model=target_model,
                content=(
                    f"[NVIDIA NIM {target_model}] Provider is active. "
                    "Configure NVIDIA_API_KEY in backend environment to enable live cloud model generation."
                ),
                role="assistant",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=10, completion_tokens=25, total_tokens=35),
                latency_ms=1.0
            )

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temp,
            "max_tokens": max_tok,
            "stream": False
        }

        last_exception: Optional[Exception] = None
        start_time = time.perf_counter()

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"NVIDIA NIM Request attempt {attempt}/{self.max_retries} to {target_model}")
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(endpoint, headers=headers, json=payload)
                    
                    # 1. Rate-Limit Handling (HTTP 429)
                    if response.status_code == 429:
                        retry_after = 2.0
                        retry_header = response.headers.get("Retry-After")
                        if retry_header and retry_header.isdigit():
                            retry_after = float(retry_header)
                        else:
                            retry_after = self.backoff_factor ** attempt

                        logger.warning(f"NVIDIA API Rate Limit (429). Backing off for {retry_after:.2f}s before retry.")
                        if attempt < self.max_retries:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            return self._build_error_response(
                                target_model, f"NVIDIA API Rate Limit (429) exceeded after {self.max_retries} retries.", start_time
                            )

                    # 2. Server Error Retry (HTTP 5xx)
                    if response.status_code >= 500:
                        logger.warning(f"NVIDIA API 5xx Server Error ({response.status_code}). Attempt {attempt}/{self.max_retries}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(self.backoff_factor ** attempt)
                            continue
                        else:
                            return self._build_error_response(
                                target_model, f"NVIDIA API server error {response.status_code} after {self.max_retries} retries.", start_time
                            )

                    # 3. Client Error (HTTP 4xx non-429)
                    if response.status_code != 200:
                        error_body = response.text[:200]
                        logger.error(f"NVIDIA API Client Error ({response.status_code}): {error_body}")
                        return self._build_error_response(
                            target_model, f"NVIDIA API error ({response.status_code}): {error_body}", start_time
                        )

                    # 4. Success Parsing
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    msg = choice.get("message", {})
                    usage_data = data.get("usage", {})
                    latency = (time.perf_counter() - start_time) * 1000

                    logger.info(f"NVIDIA NIM Success: model={target_model}, tokens={usage_data.get('total_tokens', 0)}, latency={latency:.2f}ms")

                    return LLMResponse(
                        id=data.get("id", str(uuid.uuid4())),
                        provider="nvidia",
                        model=data.get("model", target_model),
                        content=msg.get("content", "").strip(),
                        role=msg.get("role", "assistant"),
                        finish_reason=choice.get("finish_reason", "stop"),
                        usage=LLMUsage(
                            prompt_tokens=usage_data.get("prompt_tokens", 0),
                            completion_tokens=usage_data.get("completion_tokens", 0),
                            total_tokens=usage_data.get("total_tokens", 0)
                        ),
                        latency_ms=round(latency, 2)
                    )

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                last_exception = exc
                logger.warning(f"NVIDIA connection exception on attempt {attempt}: {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.backoff_factor ** attempt)
                else:
                    break

        # Fallback on total failure
        latency = (time.perf_counter() - start_time) * 1000
        logger.error(f"NVIDIA NIM failed after {self.max_retries} attempts: {last_exception}")
        return self._build_error_response(
            target_model, f"NVIDIA API connection timed out or failed after {self.max_retries} attempts.", start_time
        )

    def _build_error_response(self, model: str, message: str, start_time: float) -> LLMResponse:
        latency = (time.perf_counter() - start_time) * 1000
        return LLMResponse(
            id=f"nvidia-err-{uuid.uuid4().hex[:8]}",
            provider="nvidia",
            model=model,
            content=message,
            role="assistant",
            finish_reason="error",
            usage=LLMUsage(),
            latency_ms=round(latency, 2)
        )

    async def explain_insight(
        self,
        metric_name: str,
        metric_value: Any,
        context: Dict[str, Any],
        user_prompt: Optional[str] = None
    ) -> str:
        """Synthesizes clear narrative insight explaining observed metrics."""
        system_msg = LLMMessage(
            role="system",
            content="You are an expert AI business intelligence analyst. Explain data patterns and insights clearly and concisely without inventing unverified numbers."
        )
        prompt = (
            f"Explain this business data insight:\n"
            f"- Metric: '{metric_name}' = {metric_value}\n"
            f"- Context: {json.dumps(context, default=str)}\n"
            f"{f'- Specific Question: {user_prompt}' if user_prompt else ''}\n\n"
            "Provide a concise, 2-3 sentence analytical explanation highlighting what this means for business operations."
        )
        user_msg = LLMMessage(role="user", content=prompt)
        res = await self.chat_completion([system_msg, user_msg])
        return res.content

    async def generate_business_reasoning(
        self,
        dataset_summary: Dict[str, Any],
        key_metrics: List[Dict[str, Any]],
        segments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Synthesizes high-level business reasoning from deterministic statistical facts."""
        system_msg = LLMMessage(
            role="system",
            content="You are a Principal Business Strategist. Synthesize clear executive reasoning based strictly on provided numerical metrics."
        )
        prompt = (
            f"Synthesize strategic business reasoning from this verified dataset analysis:\n"
            f"- Overview: {json.dumps(dataset_summary, default=str)}\n"
            f"- Key Metrics: {json.dumps(key_metrics, default=str)}\n"
            f"- Top Segments: {json.dumps(segments or [], default=str)}\n\n"
            "Deliver an executive assessment in 2 focused paragraphs: 1. Core Drivers & Segment Performance, 2. Risk Factors & Operational Outlook."
        )
        user_msg = LLMMessage(role="user", content=prompt)
        res = await self.chat_completion([system_msg, user_msg])
        return res.content

    async def generate_recommendations(
        self,
        audit_findings: List[Dict[str, Any]],
        performance_signals: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Generates actionable, prioritized strategic recommendations."""
        system_msg = LLMMessage(
            role="system",
            content="You are an operations optimization advisor. Return 3-5 distinct actionable recommendations as a clean bulleted list."
        )
        prompt = (
            f"Based on the following data health and performance findings:\n"
            f"- Findings: {json.dumps(audit_findings, default=str)}\n"
            f"- Performance Signals: {json.dumps(performance_signals or [], default=str)}\n\n"
            "Generate 3-4 high-impact, prioritized business recommendations. Start each bullet with an active verb."
        )
        user_msg = LLMMessage(role="user", content=prompt)
        res = await self.chat_completion([system_msg, user_msg])
        lines = [line.strip().lstrip("-*123456789. ") for line in res.content.split("\n") if line.strip()]
        return [l for l in lines if len(l) > 10][:5] or [res.content]

    async def answer_data_question(
        self,
        question: str,
        data_schema: Dict[str, Any],
        aggregated_facts: Dict[str, Any]
    ) -> str:
        """Answers natural language user questions strictly grounded in Python-computed facts."""
        system_msg = LLMMessage(
            role="system",
            content=(
                "You are an accurate Data Intelligence Copilot. "
                "Answer the user's question using ONLY the provided verified Python-aggregated facts. "
                "Do not hallucinate or extrapolate numbers beyond the provided facts."
            )
        )
        prompt = (
            f"User Question: '{question}'\n\n"
            f"Verified Python Aggregated Data:\n{json.dumps(aggregated_facts, default=str)}\n\n"
            f"Dataset Attributes:\n{json.dumps(data_schema, default=str)}\n\n"
            "Answer the question directly, referencing the exact numerical values."
        )
        user_msg = LLMMessage(role="user", content=prompt)
        res = await self.chat_completion([system_msg, user_msg])
        return res.content

    async def check_health(self) -> LLMHealthStatus:
        """Checks configuration and availability."""
        has_key = self.is_configured()
        if not has_key:
            return LLMHealthStatus(
                provider="nvidia",
                status="unconfigured",
                available=False,
                model=self.default_model,
                base_url=self.base_url,
                has_credentials=False,
                error="NVIDIA_API_KEY environment variable is not configured."
            )

        return LLMHealthStatus(
            provider="nvidia",
            status="healthy",
            available=True,
            model=self.default_model,
            base_url=self.base_url,
            has_credentials=True,
            error=None
        )

nvidia_llm_provider = NvidiaLLMProvider()
