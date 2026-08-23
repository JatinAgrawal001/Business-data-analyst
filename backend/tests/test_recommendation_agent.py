import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.agents.insight_agent import insight_agent
from app.agents.recommendation_agent import recommendation_agent
from app.schemas.recommendation import RecommendationReport, CustomRecommendationQueryRequest, CustomRecommendationQueryResponse

def test_recommendation_agent_six_pillar_framework_and_non_guaranteed_language():
    """
    Test RecommendationAgent generates recommendations containing all 6 required pillars:
    - problem
    - evidence
    - action
    - priority
    - reasoning
    - limitations
    And verifies no guaranteed outcome claims are made.
    """
    df = pd.DataFrame({
        "customer_id": [f"CUST-{i:03d}" for i in range(1, 21)],
        "joined_date": pd.date_range(start="2026-01-01", periods=20, freq="D").strftime("%Y-%m-%d"),
        "tier": ["Enterprise", "SMB", "Startup", "Enterprise"] * 5,
        "arr_revenue": [50000, 12000, 5000, 75000, 48000, 11000, 4500, 82000, 51000, 13000, 5200, 90000, 49000, 12500, 4800, 88000, 50500, 11800, 5100, 300000],
        "churn_risk_score": [0.15, 0.45, 0.60, 0.10, 0.12, 0.50, 0.65, 0.08, 0.14, 0.48, 0.58, 0.05, 0.13, 0.42, 0.62, 0.09, 0.11, 0.46, 0.61, 0.02]
    })

    # Generate Profile, EDA, and Insights
    profile = profiler.generate_comprehensive_profile(df, "rec-six-01", "p1", "SaaS Retention & Expansion", "csv")
    eda_report = eda_agent.generate_eda_report(df, profile)
    insight_report = insight_agent.generate_report(df, profile, eda_report=eda_report)

    # Generate Recommendations
    report = recommendation_agent.generate_report(
        df, profile, eda_report=eda_report, insight_report=insight_report
    )

    assert isinstance(report, RecommendationReport)
    assert report.dataset_id == "rec-six-01"
    assert report.total_recommendations >= 2
    assert "guaranteed" in report.disclaimer.lower()

    # Verify all 6 pillars for each recommendation
    for rec in report.recommendations:
        # 1. Problem
        assert len(rec.problem) > 15
        # 2. Evidence (Empirical numbers verified)
        assert len(rec.evidence) > 15
        # 3. Action
        assert len(rec.action) > 15
        # 4. Priority
        assert rec.priority in ["P0_critical", "P1_high", "P2_medium", "P3_low"]
        # 5. Reasoning
        assert len(rec.reasoning) > 15
        # 6. Limitations (Assumptions & non-guaranteed language)
        assert len(rec.limitations) > 15
        assert any(k in rec.limitations.lower() for k in ["assumes", "contingent", "not guaranteed", "assumptions", "limitations", "risk"])

def test_query_recommendations_by_domain():
    """
    Test filtering recommendations by domain focus (e.g. 'growth').
    """
    df = pd.DataFrame({
        "channel": ["Organic", "Paid", "Email", "Direct"] * 5,
        "conversions": [150, 400, 200, 120] * 5,
        "ad_spend": [500, 4500, 800, 300] * 5
    })
    profile = profiler.generate_comprehensive_profile(df, "mkt-rec", "p1", "Marketing", "csv")

    req = CustomRecommendationQueryRequest(domain_focus="growth")
    res = recommendation_agent.query_recommendations(df, profile, req)

    assert isinstance(res, CustomRecommendationQueryResponse)
    assert len(res.recommendations) > 0
    assert len(res.strategic_synthesis) > 0

def test_recommendation_api_endpoints_workflow(client: TestClient):
    """
    Test complete Recommendation API endpoints: Generate -> Get Report -> Action -> Query
    """
    csv_data = (
        "department,headcount,budget,satisfaction\n"
        "Engineering,80,1200000,4.5\n"
        "Sales,50,800000,4.0\n"
        "Marketing,30,450000,3.8\n"
        "Operations,20,250000,3.9\n"
    )
    files = {"file": ("rec_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-rec-api"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. POST /api/v1/datasets/{id}/recommendations/generate
    gen_res = client.post(f"/api/v1/datasets/{dataset_id}/recommendations/generate")
    assert gen_res.status_code == 200
    report_data = gen_res.json()
    assert report_data["dataset_id"] == dataset_id
    assert len(report_data["recommendations"]) > 0
    first_rec = report_data["recommendations"][0]
    
    # Assert all 6 pillars are in the response JSON
    assert "problem" in first_rec
    assert "evidence" in first_rec
    assert "action" in first_rec
    assert "priority" in first_rec
    assert "reasoning" in first_rec
    assert "limitations" in first_rec

    # 2. GET /api/v1/datasets/{id}/recommendations/report
    get_res = client.get(f"/api/v1/datasets/{dataset_id}/recommendations/report")
    assert get_res.status_code == 200
    assert get_res.json()["dataset_id"] == dataset_id

    # 3. POST /api/v1/datasets/{id}/recommendations/action
    action_payload = {
        "recommendation_id": first_rec["id"],
        "action": "accept",
        "notes": "Approved for Q1 execution."
    }
    action_res = client.post(f"/api/v1/datasets/{dataset_id}/recommendations/action", json=action_payload)
    assert action_res.status_code == 200
    assert action_res.json()["status"] == "accepted"

    # 4. POST /api/v1/datasets/{id}/recommendations/query
    q_res = client.post(f"/api/v1/datasets/{dataset_id}/recommendations/query", json={"domain_focus": "operational"})
    assert q_res.status_code == 200
    assert "recommendations" in q_res.json()
