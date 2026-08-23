import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.agents.insight_agent import insight_agent
from app.schemas.insight import StructuredInsightReport, QueryInsightRequest, QueryInsightResponse

def test_insight_agent_five_categories_and_python_facts():
    """
    Test InsightAgent generates all 5 required categories with Python-verified facts:
    - key_insights
    - trends
    - anomalies
    - risks
    - opportunities
    Zero fake numbers.
    """
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 25)],
        "order_date": pd.date_range(start="2026-01-01", periods=24, freq="D").strftime("%Y-%m-%d"),
        "tier": ["Enterprise", "Enterprise", "SMB", "Startup"] * 6,
        "revenue": [50000, 75000, 5000, 2000] * 5 + [52000, 78000, 5100, 300000],  # Outlier 300,000
        "units": [50, 75, 5, 2] * 5 + [52, 78, 5, 300]
    })

    profile = profiler.generate_comprehensive_profile(df, "ins-five-01", "p1", "SaaS Enterprise Subscriptions", "csv")
    eda_report = eda_agent.generate_eda_report(df, profile)

    report = insight_agent.generate_report(df, profile, eda_report=eda_report)

    assert isinstance(report, StructuredInsightReport)
    assert report.dataset_id == "ins-five-01"
    assert report.total_insights > 0

    # 1. Verify all 5 categories are structured
    assert len(report.key_insights) > 0
    assert len(report.trends) > 0
    assert len(report.anomalies) > 0
    assert len(report.opportunities) > 0

    # 2. Verify Key Insights - Python source of truth
    key_ins = report.key_insights[0]
    assert key_ins.category == "key_insight"
    assert "total_volume" in key_ins.python_verified_facts
    assert key_ins.python_verified_facts["total_volume"] == round(float(df["revenue"].sum()), 2)
    assert len(key_ins.natural_language_explanation) > 0

    # 3. Verify Trend - Python source of truth
    trend_ins = report.trends[0]
    assert trend_ins.category == "trend"
    assert "growth_rate_percentage" in trend_ins.python_verified_facts
    assert trend_ins.python_verified_facts["trajectory"] in ["upward", "downward", "stable"]

    # 4. Verify Anomaly - Tukey's IQR Fences
    anom_ins = report.anomalies[0]
    assert anom_ins.category == "anomaly"
    assert anom_ins.python_verified_facts["outlier_count"] >= 1
    assert 300000.0 in anom_ins.python_verified_facts["sample_outliers"]

    # 5. Verify Strategic Recommendations
    assert len(report.strategic_recommendations) >= 2
    for rec in report.strategic_recommendations:
        assert rec.impact in ["high", "medium", "low"]
        assert rec.timeframe in ["immediate", "short_term", "long_term"]

def test_query_targeted_insights_by_category():
    """
    Test querying insights filtered by specific category (e.g. 'trend' or 'anomaly').
    """
    df = pd.DataFrame({
        "recorded_at": ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"],
        "temp": [22.5, 23.0, 24.1, 25.0],
        "pressure": [101.3, 101.2, 101.5, 101.4]
    })
    profile = profiler.generate_comprehensive_profile(df, "telemetry-ins", "p1", "Sensors", "csv")

    req = QueryInsightRequest(category="trend")
    res = insight_agent.query_insights(df, profile, req)

    assert isinstance(res, QueryInsightResponse)
    assert len(res.insights) > 0
    assert res.insights[0].category == "trend"
    assert "growth_rate_percentage" in res.insights[0].python_verified_facts

def test_insight_api_endpoints_workflow(client: TestClient):
    """
    Test complete Insight API endpoints suite: POST /insights/generate, GET /insights/report, POST /insights/query
    """
    csv_data = (
        "segment,revenue,margin\n"
        "Retail,100000,0.25\n"
        "Wholesale,80000,0.15\n"
        "Online,120000,0.35\n"
        "Enterprise,200000,0.40\n"
    )
    files = {"file": ("insights_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-ins-suite"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. POST /api/v1/datasets/{id}/insights/generate
    gen_res = client.post(f"/api/v1/datasets/{dataset_id}/insights/generate")
    assert gen_res.status_code == 200
    report_data = gen_res.json()
    assert report_data["dataset_id"] == dataset_id
    assert "key_insights" in report_data
    assert "trends" in report_data
    assert "anomalies" in report_data
    assert "risks" in report_data
    assert "opportunities" in report_data
    assert "strategic_recommendations" in report_data

    # 2. GET /api/v1/datasets/{id}/insights/report
    get_res = client.get(f"/api/v1/datasets/{dataset_id}/insights/report")
    assert get_res.status_code == 200
    assert get_res.json()["dataset_id"] == dataset_id

    # 3. POST /api/v1/datasets/{id}/insights/query
    query_payload = {"category": "opportunity"}
    q_res = client.post(f"/api/v1/datasets/{dataset_id}/insights/query", json=query_payload)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "insights" in q_data
    assert "synthesis" in q_data
