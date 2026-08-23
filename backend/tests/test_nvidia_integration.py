import io
import asyncio
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.core.nvidia_client import nvidia_client
from app.core.llm.nvidia_provider import nvidia_llm_provider
from app.core.llm.factory import get_llm_provider
from app.core.llm.base import BaseLLMProvider
from app.services.nvidia_service import nvidia_service
from app.schemas.nvidia import NvidiaChatRequest, NvidiaMessage

def test_llm_provider_abstraction():
    """
    Test LLM Provider abstraction interface and factory resolution.
    """
    provider = get_llm_provider("nvidia")
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "nvidia"

def test_nvidia_models_and_health_security():
    """
    Test NVIDIA models list and health check without exposing credentials.
    """
    models = nvidia_client.get_supported_models()
    assert len(models) >= 4
    model_ids = [m.id for m in models]
    assert "meta/llama-3.3-70b-instruct" in model_ids

    health = asyncio.run(nvidia_llm_provider.check_health())
    assert health.provider == "nvidia"
    assert "api_key" not in health.model_dump()
    assert health.has_credentials in [True, False]

def test_nvidia_service_four_core_responsibilities():
    """
    Test NVIDIA handles:
    1. Insight explanation
    2. Business reasoning
    3. Recommendations
    4. Natural-language data questions
    """
    # 1. Insight Explanation
    explanation = asyncio.run(nvidia_service.explain_insight(
        metric_name="monthly_churn",
        metric_value=0.045,
        context={"industry_benchmark": 0.02, "trend": "increasing"}
    ))
    assert isinstance(explanation, str)
    assert len(explanation) > 0

    # 2. Business Reasoning
    reasoning = asyncio.run(nvidia_service.generate_business_reasoning(
        dataset_summary={"total_records": 10000, "region": "Global"},
        key_metrics=[{"name": "revenue", "sum": 2500000}, {"name": "cagr", "value": 0.18}],
        segments=[{"category": "Enterprise", "share": "65%"}]
    ))
    assert isinstance(reasoning, str)
    assert len(reasoning) > 0

    # 3. Recommendations
    recommendations = asyncio.run(nvidia_service.generate_recommendations(
        audit_findings=[{"issue": "High missing email fields", "affected": 450}],
        performance_signals=[{"metric": "Conversion Drop", "severity": "high"}]
    ))
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

def test_nvidia_api_endpoints_complete_suite(client: TestClient):
    """
    Test complete NVIDIA API endpoints suite.
    """
    # 1. GET /api/v1/nvidia/health
    health_res = client.get("/api/v1/nvidia/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert "status" in health_data
    assert "default_model" in health_data
    # Assert API credentials are NOT returned
    assert "NVIDIA_API_KEY" not in health_data
    assert "api_key" not in health_data

    # 2. GET /api/v1/nvidia/models
    models_res = client.get("/api/v1/nvidia/models")
    assert models_res.status_code == 200
    assert len(models_res.json()) >= 4

    # 3. POST /api/v1/nvidia/chat
    chat_payload = {
        "messages": [{"role": "user", "content": "Explain customer lifetime value."}],
        "model": "meta/llama-3.3-70b-instruct"
    }
    chat_res = client.post("/api/v1/nvidia/chat", json=chat_payload)
    assert chat_res.status_code == 200
    assert "content" in chat_res.json()

    # 4. POST /api/v1/nvidia/explain-insight
    insight_payload = {
        "metric_name": "retention_rate",
        "metric_value": 0.88,
        "context": {"cohort": "Q1-2026"}
    }
    insight_res = client.post("/api/v1/nvidia/explain-insight", json=insight_payload)
    assert insight_res.status_code == 200
    assert "explanation" in insight_res.json()

    # 5. POST /api/v1/nvidia/business-reasoning
    reasoning_payload = {
        "dataset_summary": {"records": 500},
        "key_metrics": [{"name": "profit", "value": 85000}]
    }
    reasoning_res = client.post("/api/v1/nvidia/business-reasoning", json=reasoning_payload)
    assert reasoning_res.status_code == 200
    assert "business_reasoning" in reasoning_res.json()

    # 6. POST /api/v1/nvidia/recommendations
    rec_payload = {
        "audit_findings": [{"issue": "Duplicates detected", "count": 12}]
    }
    rec_res = client.post("/api/v1/nvidia/recommendations", json=rec_payload)
    assert rec_res.status_code == 200
    assert "recommendations" in rec_res.json()

    # 7. POST /api/v1/nvidia/ask-data with uploaded dataset
    csv_data = "dept,employees,budget\nEngineering,100,500000\nSales,50,250000\nHR,10,60000\n"
    files = {"file": ("org.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-org-01"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    ask_payload = {
        "dataset_id": dataset_id,
        "question": "What is the total budget for Engineering and Sales?"
    }
    ask_res = client.post("/api/v1/nvidia/ask-data", json=ask_payload)
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert ask_data["dataset_id"] == dataset_id
    assert "answer" in ask_data
    assert "verified_facts" in ask_data
