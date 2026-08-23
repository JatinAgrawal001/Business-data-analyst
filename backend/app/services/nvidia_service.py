from typing import List, Dict, Any, Optional
import pandas as pd
from app.core.llm.factory import get_llm_provider
from app.core.llm.types import LLMMessage, LLMResponse, LLMHealthStatus
from app.schemas.nvidia import (
    NvidiaChatRequest,
    NvidiaChatResponse,
    NvidiaUsage,
    NvidiaModelInfo,
    NvidiaHealthResponse
)
from app.schemas.profiler import DatasetProfile
from app.schemas.eda import EDAReport
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.core.nvidia_client import nvidia_client
from app.core.logging import get_logger

logger = get_logger("app.services.nvidia")

class NvidiaService:
    """
    Dedicated NVIDIA Service for:
    - Insight explanation
    - Business reasoning synthesis
    - Strategic recommendations
    - Natural language data questions strictly grounded in Python calculations
    """

    def __init__(self):
        self.provider = get_llm_provider("nvidia")

    async def chat(
        self,
        request: NvidiaChatRequest
    ) -> NvidiaChatResponse:
        """Processes a chat completion request via NVIDIA provider."""
        llm_messages = [LLMMessage(role=m.role, content=m.content) for m in request.messages]
        res: LLMResponse = await self.provider.chat_completion(
            messages=llm_messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return NvidiaChatResponse(
            id=res.id,
            model=res.model,
            content=res.content,
            role=res.role,
            finish_reason=res.finish_reason,
            usage=NvidiaUsage(
                prompt_tokens=res.usage.prompt_tokens,
                completion_tokens=res.usage.completion_tokens,
                total_tokens=res.usage.total_tokens
            )
        )

    async def explain_insight(
        self,
        metric_name: str,
        metric_value: Any,
        context: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> str:
        """Explains an analytical pattern or metric anomaly."""
        return await self.provider.explain_insight(
            metric_name=metric_name,
            metric_value=metric_value,
            context=context,
            user_prompt=prompt
        )

    async def generate_business_reasoning(
        self,
        dataset_summary: Dict[str, Any],
        key_metrics: List[Dict[str, Any]],
        segments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Synthesizes executive reasoning from deterministic dataset summaries."""
        return await self.provider.generate_business_reasoning(
            dataset_summary=dataset_summary,
            key_metrics=key_metrics,
            segments=segments
        )

    async def generate_recommendations(
        self,
        audit_findings: List[Dict[str, Any]],
        performance_signals: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Generates strategic actionable recommendations."""
        return await self.provider.generate_recommendations(
            audit_findings=audit_findings,
            performance_signals=performance_signals
        )

    async def answer_data_question(
        self,
        dataset_id: str,
        user_id: str,
        question: str,
        user_jwt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answers natural language question by:
        1. Executing deterministic Pandas / NumPy calculations on the dataset
        2. Passing verified factual numbers into NVIDIA NIM for clear language synthesis
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        # 1. Deterministic Python Fact Extraction
        q_lower = question.lower()
        aggregated_facts: Dict[str, Any] = {
            "dataset_name": profile.name,
            "total_rows": profile.row_count,
            "numeric_columns": profile.numeric_columns,
            "categorical_columns": profile.categorical_columns
        }

        # Check if question is asking about specific column
        for num_col in profile.numeric_columns:
            if num_col.lower() in q_lower or num_col.lower().replace("_", " ") in q_lower:
                s = df[num_col].dropna()
                aggregated_facts[f"{num_col}_stats"] = {
                    "sum": float(s.sum()),
                    "mean": round(float(s.mean()), 2),
                    "median": round(float(s.median()), 2),
                    "min": float(s.min()),
                    "max": float(s.max())
                }

        for cat_col in profile.categorical_columns:
            if cat_col.lower() in q_lower or cat_col.lower().replace("_", " ") in q_lower:
                top_counts = df[cat_col].value_counts().head(5).to_dict()
                aggregated_facts[f"{cat_col}_top_frequencies"] = top_counts

        # 2. NVIDIA LLM Natural Language Answer Synthesis
        schema_info = {
            "columns": [c.name for c in profile.columns],
            "numeric": profile.numeric_columns,
            "categorical": profile.categorical_columns
        }

        answer_text = await self.provider.answer_data_question(
            question=question,
            data_schema=schema_info,
            aggregated_facts=aggregated_facts
        )

        return {
            "dataset_id": dataset_id,
            "question": question,
            "answer": answer_text,
            "verified_facts": aggregated_facts
        }

    def list_models(self) -> List[NvidiaModelInfo]:
        """Returns the list of supported NVIDIA NIM foundation models."""
        return nvidia_client.get_supported_models()

    async def check_health(self) -> NvidiaHealthResponse:
        """Returns the operational health of the NVIDIA integration."""
        status_info: LLMHealthStatus = await self.provider.check_health()
        return NvidiaHealthResponse(
            status=status_info.status,
            available=status_info.available,
            default_model=status_info.model,
            base_url=status_info.base_url or "",
            has_api_key=status_info.has_credentials,
            error=status_info.error
        )

nvidia_service = NvidiaService()
