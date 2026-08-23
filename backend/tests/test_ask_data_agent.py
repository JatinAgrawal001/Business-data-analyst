import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.ask_data_agent import ask_data_agent
from app.schemas.ask_data import (
    AskDataQueryRequest,
    AskDataQueryResponse,
    SuggestedQuestionsResponse,
    ChatHistoryResponse
)

def test_ask_data_highest_performing_category_query():
    """
    Test example query: "What is the highest performing category?"
    Verifies deterministic calculation, supporting metrics, relevant columns, and bar chart.
    """
    df = pd.DataFrame({
        "category": ["Electronics", "Apparel", "Home & Kitchen", "Electronics", "Apparel", "Electronics"],
        "revenue": [50000, 20000, 15000, 45000, 12000, 60000]
    })
    profile = profiler.generate_comprehensive_profile(df, "ask-cat-01", "p1", "E-commerce", "csv")

    req = AskDataQueryRequest(query="What is the highest performing category?")
    res = ask_data_agent.answer_query(df, profile, req)

    assert isinstance(res, AskDataQueryResponse)
    assert res.supporting_metrics["top_entity"] == "Electronics"
    assert res.supporting_metrics["top_value"] == 155000.0
    assert "category" in res.relevant_columns
    assert "revenue" in res.relevant_columns
    assert res.chart is not None
    assert res.chart.chart_type == "bar"
    assert "Electronics" in res.answer
    assert "$155.00K" in res.answer or "155,000" in res.answer

def test_ask_data_highest_profit_region_query():
    """
    Test example query: "Which region has the highest profit?"
    Verifies deterministic profit calculation, top region identification, and relevant columns.
    """
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "profit": [50000, 32000, 41000, 28000],
        "sales": [150000, 120000, 130000, 100000]
    })
    profile = profiler.generate_comprehensive_profile(df, "ask-reg-01", "p1", "Regional Profit", "csv")

    req = AskDataQueryRequest(query="Which region has the highest profit?")
    res = ask_data_agent.answer_query(df, profile, req)

    assert isinstance(res, AskDataQueryResponse)
    assert res.supporting_metrics["top_entity"] == "North"
    assert res.supporting_metrics["top_value"] == 50000.0
    assert "region" in res.relevant_columns
    assert "profit" in res.relevant_columns
    assert "North" in res.answer
    assert res.direct_kpi_value == 50000.0

def test_ask_data_why_performance_declined_diagnostic_query():
    """
    Test example query: "Why did performance decline?"
    Verifies diagnostic root cause delta calculation and relevant columns.
    """
    df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "revenue": [10000, 12000, 9000, 6000, 4000],
        "ad_spend": [1000, 1200, 800, 500, 300]
    })
    profile = profiler.generate_comprehensive_profile(df, "ask-diag-01", "p1", "Revenue Drop", "csv")

    req = AskDataQueryRequest(query="Why did performance decline?")
    res = ask_data_agent.answer_query(df, profile, req)

    assert isinstance(res, AskDataQueryResponse)
    assert res.supporting_metrics["net_delta"] < 0  # 4000 - 10000 = -6000
    assert res.supporting_metrics["net_delta_pct"] < 0  # -60.0%
    assert "date" in res.relevant_columns or "revenue" in res.relevant_columns
    assert "Diagnostic" in res.answer or "Trajectory" in res.answer
    assert res.chart is not None
    assert res.chart.chart_type == "line"

def test_ask_data_single_kpi_aggregate_query():
    """
    Test deterministic single KPI calculation (e.g. Total Revenue).
    """
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 6)],
        "revenue": [1000, 2000, 3000, 4000, 5000]
    })
    profile = profiler.generate_comprehensive_profile(df, "ask-kpi-02", "p1", "KPIs", "csv")

    req = AskDataQueryRequest(query="What is the total revenue?")
    res = ask_data_agent.answer_query(df, profile, req)

    assert isinstance(res, AskDataQueryResponse)
    assert res.direct_kpi_value == 15000.0
    assert res.supporting_metrics["sum"] == 15000.0
    assert "revenue" in res.relevant_columns
    assert res.chart.chart_type == "kpi_card"

def test_ask_data_starter_questions_generation():
    """
    Test generation of dataset-tailored starter questions.
    """
    df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "region": ["North", "South"],
        "sales": [1000, 2000],
        "units": [10, 20]
    })
    profile = profiler.generate_comprehensive_profile(df, "starter-02", "p1", "Sales", "csv")

    res = ask_data_agent.generate_starter_questions(profile)
    assert isinstance(res, SuggestedQuestionsResponse)
    assert len(res.starter_questions) >= 3
    for q in res.starter_questions:
        assert len(q.question) > 0
        assert q.category in ["metric_summary", "breakdown", "trend", "outlier", "correlation"]

def test_ask_data_api_endpoints_workflow_and_chat_history(client: TestClient):
    """
    Test complete Ask Data API endpoints workflow:
    - POST /ask
    - GET /chat-history (verifying Supabase / in-memory history persistence)
    - GET /suggested-questions
    """
    csv_data = (
        "region,category,sales,profit\n"
        "North,Electronics,80000,24000\n"
        "South,Furniture,30000,6000\n"
        "East,Electronics,50000,15000\n"
        "West,Apparel,60000,18000\n"
    )
    files = {"file": ("ask_suite_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-ask-flow"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. GET /api/v1/datasets/{id}/suggested-questions
    sq_res = client.get(f"/api/v1/datasets/{dataset_id}/suggested-questions")
    assert sq_res.status_code == 200
    assert len(sq_res.json()["starter_questions"]) > 0

    # 2. POST /api/v1/datasets/{id}/ask (Highest performing category)
    ask_payload = {"query": "What is the highest performing category?"}
    ask_res = client.post(f"/api/v1/datasets/{dataset_id}/ask", json=ask_payload)
    assert ask_res.status_code == 200
    ans_data = ask_res.json()
    assert ans_data["dataset_id"] == dataset_id
    assert "Electronics" in ans_data["answer"]
    assert "supporting_metrics" in ans_data
    assert ans_data["supporting_metrics"]["top_entity"] == "Electronics"
    assert "relevant_columns" in ans_data
    assert "category" in ans_data["relevant_columns"]
    assert ans_data["chart"] is not None

    # 3. GET /api/v1/datasets/{id}/chat-history (Verifying persistence)
    hist_res = client.get(f"/api/v1/datasets/{dataset_id}/chat-history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["dataset_id"] == dataset_id
    assert hist_data["total_messages"] >= 2
    assert hist_data["messages"][0]["role"] == "user"
    assert hist_data["messages"][0]["content"] == "What is the highest performing category?"
    assert hist_data["messages"][1]["role"] == "assistant"
    assert "Electronics" in hist_data["messages"][1]["content"]
