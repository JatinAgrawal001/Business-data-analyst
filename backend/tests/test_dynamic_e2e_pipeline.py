import io
import json
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.agents.data_cleaning_agent import data_cleaning_agent
from app.analytics.cleaning_engine import cleaning_engine
from app.agents.visualization_agent import visualization_agent
from app.agents.insight_agent import insight_agent
from app.agents.recommendation_agent import recommendation_agent
from app.agents.prediction_agent import prediction_agent
from app.agents.ask_data_agent import ask_data_agent
from app.schemas.ask_data import AskDataQueryRequest
from app.schemas.prediction import WhatIfScenarioRequest

def test_dynamic_saas_telemetry_complete_pipeline():
    """
    End-to-End dynamic-data test on an arbitrary SaaS Cloud Telemetry dataset.
    Validates Profiling -> EDA -> Cleaning -> Visualization -> Insights -> Recommendations -> Forecasting -> Ask Your Data.
    """
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=24, freq="ME").strftime("%Y-%m-%d").tolist()
    tiers = ["Enterprise", "Mid-Market", "SMB", "Startup"] * 6
    arr = [50000 + i * 4000 + int(np.random.randint(-1500, 1500)) for i in range(24)]
    compute_hours = [1200 + i * 110 + int(np.random.randint(-50, 50)) for i in range(24)]
    api_latency_ms = [45 + (15 if i % 7 == 0 else 0) + float(np.random.randn() * 3) for i in range(24)] # Has intentional outlier spikes
    active_users = [2500 + i * 180 for i in range(24)]

    df = pd.DataFrame({
        "timestamp": dates,
        "subscription_tier": tiers,
        "arr_usd": arr,
        "compute_hours": compute_hours,
        "api_latency_ms": api_latency_ms,
        "active_users": active_users
    })

    # Step 1: Dynamic Profiling
    profile = profiler.generate_comprehensive_profile(
        df,
        dataset_id="dyn-saas-01",
        project_id="proj-saas",
        name="SaaS Cloud Telemetry",
        file_type="csv"
    )

    assert profile.row_count == 24
    assert profile.column_count == 6
    assert "timestamp" in profile.datetime_columns
    assert "subscription_tier" in profile.categorical_columns
    assert "arr_usd" in profile.numeric_columns
    assert "compute_hours" in profile.numeric_columns
    assert "api_latency_ms" in profile.numeric_columns
    assert profile.quality_report.health_score >= 90.0

    # Step 2: Dynamic EDA Agent
    eda_report = eda_agent.generate_eda_report(df, profile)
    assert len(eda_report.kpis) >= 3
    assert eda_report.summary.total_rows == 24
    assert len(eda_report.correlations.ranked_pairs) > 0

    # Verify strong correlation between compute_hours and arr_usd
    corr_found = any(
        (c.feature_x == "arr_usd" and c.feature_y == "compute_hours") or
        (c.feature_x == "compute_hours" and c.feature_y == "arr_usd")
        for c in eda_report.correlations.ranked_pairs
    )
    assert corr_found

    # Step 3: Dynamic Data Cleaning Agent (Detect & Apply)
    audit_report = data_cleaning_agent.analyze_and_recommend(df, profile)
    assert audit_report.dataset_id == "dyn-saas-01"
    assert len(audit_report.recommendations) > 0

    # Apply transformation via deterministic Python cleaning engine
    first_rec = audit_report.recommendations[0]
    cleaned_df, detail = cleaning_engine.apply_transformation(df.copy(), first_rec)
    assert detail.action_type == first_rec.action_type
    assert len(cleaned_df) <= len(df)

    # Step 4: Dynamic Visualization Agent
    viz_dashboard = visualization_agent.generate_dashboard(df, profile)
    assert len(viz_dashboard.charts) >= 3
    chart_types = [c.config.chart_type for c in viz_dashboard.charts]
    assert "line" in chart_types or "bar" in chart_types

    # Step 5: Dynamic Insight Agent (5-Category Grounded Insights)
    insight_report = insight_agent.generate_report(df, profile, eda_report)
    assert insight_report.total_insights >= 5
    assert len(insight_report.insights) >= 5
    for ins in insight_report.insights:
        assert len(ins.python_verified_facts) > 0
        assert ins.confidence_score >= 0.70

    # Step 6: Dynamic Recommendation Agent (6-Pillar Framework)
    rec_report = recommendation_agent.generate_report(df, profile, eda_report, insight_report)
    assert len(rec_report.recommendations) >= 2
    for r in rec_report.recommendations:
        assert len(r.problem) > 0
        assert len(r.evidence) > 0
        assert len(r.action) > 0
        assert len(r.reasoning) > 0
        assert len(r.limitations) > 0
        assert r.priority in ["P0_critical", "P1_high", "P2_medium", "P3_low", "critical", "high", "medium", "low"]
        assert "guaranteed" not in r.action.lower()

    # Step 7: Dynamic Prediction Agent (6-Point Suitability & Baseline Model Comparison)
    pred_res = prediction_agent.generate_report(df, profile, forecast_horizon=6)
    assert pred_res.is_suitable is True
    assert pred_res.suitability_report.is_suitable is True
    assert pred_res.suitability_report.train_test_split_viable is True
    assert pred_res.primary_forecast is not None
    assert pred_res.primary_forecast.forecast_horizon_periods == 6
    assert len(pred_res.primary_forecast.predicted_values) > 0
    assert pred_res.primary_forecast.model_used in ["Exponential Smoothing (ETS)", "Linear Trend (Ordinary Least Squares)", "Linear Trend (OLS)"]
    assert pred_res.primary_forecast.projected_net_change_pct > 0
    assert len(pred_res.primary_forecast.baseline_comparison.candidate_models_evaluated) >= 2

    # Step 8: Dynamic What-If Simulation
    whatif_res = prediction_agent.simulate_what_if_scenario(
        df,
        WhatIfScenarioRequest(
            target_metric="arr_usd",
            feature_adjustments={"compute_hours": 1.25} # +25% compute
        )
    )
    assert whatif_res.simulated_predicted_value > whatif_res.baseline_predicted_value
    assert whatif_res.percentage_change > 0

    # Step 9: Dynamic "Ask Your Data" Queries
    # Q1: Extremum / Ranking query
    q1_req = AskDataQueryRequest(query="What is the highest performing subscription tier?")
    q1_res = ask_data_agent.answer_query(df, profile, q1_req)
    assert "subscription_tier" in q1_res.relevant_columns
    assert "arr_usd" in q1_res.relevant_columns
    assert q1_res.supporting_metrics["top_entity"] in ["Enterprise", "Mid-Market", "SMB", "Startup"]
    assert q1_res.chart is not None

    # Q2: Diagnostic / Variance query
    q2_req = AskDataQueryRequest(query="Show trend and variance of arr over time")
    q2_res = ask_data_agent.answer_query(df, profile, q2_req)
    assert "arr_usd" in q2_res.relevant_columns
    assert q2_res.supporting_metrics["net_delta"] > 0
    assert q2_res.chart.chart_type == "line"

    # Q3: Correlation query
    q3_req = AskDataQueryRequest(query="What is the correlation between compute hours and arr?")
    q3_res = ask_data_agent.answer_query(df, profile, q3_req)
    assert q3_res.supporting_metrics["pearson_r"] > 0.8
    assert q3_res.chart.chart_type == "scatter"

def test_dynamic_clinical_healthcare_dataset():
    """
    End-to-End dynamic-data test on a Clinical Healthcare Inpatient dataset.
    Validates handling of medical parameters, patient outcomes, and length-of-stay distributions.
    """
    df = pd.DataFrame({
        "admission_date": [f"2026-01-{i:02d}" for i in range(1, 21)],
        "department": ["Cardiology", "Neurology", "Orthopedics", "Oncology", "Cardiology"] * 4,
        "patient_age": [62, 54, 48, 71, 65, 59, 43, 75, 68, 51, 46, 73, 61, 57, 49, 78, 64, 53, 47, 72],
        "oxygen_saturation": [96.5, 98.0, 97.2, 94.1, 95.8, 97.5, 98.2, 93.9, 96.1, 98.4, 97.0, 94.5, 96.8, 97.9, 97.4, 93.5, 96.2, 98.1, 97.3, 94.8],
        "treatment_cost_usd": [12500, 8900, 7400, 19200, 13100, 9200, 6800, 21500, 12800, 8400, 7100, 20100, 13400, 9000, 7600, 22400, 12900, 8700, 7300, 19800],
        "length_of_stay_days": [5, 3, 2, 8, 5, 4, 2, 9, 5, 3, 2, 8, 6, 3, 3, 10, 5, 3, 2, 8]
    })

    profile = profiler.generate_comprehensive_profile(df, "dyn-health-01", "proj-health", "Inpatient Care", "csv")
    assert profile.row_count == 20
    assert "treatment_cost_usd" in profile.numeric_columns
    assert "department" in profile.categorical_columns

    eda_report = eda_agent.generate_eda_report(df, profile)
    assert len(eda_report.kpis) >= 3

    # Ask Data query for Department cost
    q_req = AskDataQueryRequest(query="Which department has the highest treatment cost?")
    q_res = ask_data_agent.answer_query(df, profile, q_req)
    assert q_res.supporting_metrics["top_entity"] in ["Cardiology", "Oncology"]
    assert "department" in q_res.relevant_columns
    assert "treatment_cost_usd" in q_res.relevant_columns

def test_dynamic_unsuitable_time_series_dataset_rejection():
    """
    Tests Prediction Agent pre-flight suitability audit on an unsuitable non-temporal dataset (3 rows, no dates).
    Verifies that the agent gracefully explains why forecasting is not appropriate instead of fabricating numbers.
    """
    df = pd.DataFrame({
        "category": ["A", "B", "C"],
        "revenue": [100, 200, 300]
    })
    profile = profiler.generate_comprehensive_profile(df, "dyn-unsuitable-01", "p1", "Tiny Data", "csv")

    pred_res = prediction_agent.generate_report(df, profile, forecast_horizon=3)
    assert pred_res.is_suitable is False
    assert pred_res.primary_forecast is None
    assert "inappropriate" in pred_res.executive_summary.lower() or "suitability" in pred_res.executive_summary.lower()

def test_dynamic_api_endpoints_full_lifecycle(client: TestClient):
    """
    Complete end-to-end API test exercising the entire FastAPI endpoint suite with dynamic data.
    """
    csv_payload = (
        "date,region,units_sold,unit_price,revenue,net_margin\n"
        "2026-01-01,North,120,50,6000,1800\n"
        "2026-01-02,South,90,50,4500,1125\n"
        "2026-01-03,East,150,55,8250,2475\n"
        "2026-01-04,West,110,50,5500,1375\n"
        "2026-01-05,North,130,52,6760,2028\n"
        "2026-01-06,South,95,50,4750,1187\n"
        "2026-01-07,East,160,55,8800,2640\n"
        "2026-01-08,West,115,50,5750,1437\n"
    )

    # 1. POST /api/v1/datasets/upload
    files = {"file": ("dynamic_sales_flow.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-dyn-test", "customName": "Dynamic Sales Flow"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. GET /api/v1/datasets/{id}/preview
    prev_res = client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert prev_res.status_code == 200
    assert prev_res.json()["rowCount"] == 8

    # 3. GET /api/v1/datasets/{id}/eda/report
    eda_res = client.get(f"/api/v1/datasets/{dataset_id}/eda/report")
    assert eda_res.status_code == 200
    assert len(eda_res.json()["kpis"]) > 0

    # 4. GET /api/v1/datasets/{id}/insights/report
    ins_res = client.get(f"/api/v1/datasets/{dataset_id}/insights/report")
    assert ins_res.status_code == 200
    assert ins_res.json()["total_insights"] >= 3

    # 5. GET /api/v1/datasets/{id}/recommendations/report
    rec_res = client.get(f"/api/v1/datasets/{dataset_id}/recommendations/report")
    assert rec_res.status_code == 200
    assert len(rec_res.json()["recommendations"]) >= 2

    # 6. GET /api/v1/datasets/{id}/predictions/report
    pred_res = client.get(f"/api/v1/datasets/{dataset_id}/predictions/report")
    assert pred_res.status_code == 200

    # 7. POST /api/v1/datasets/{id}/ask
    ask_res = client.post(f"/api/v1/datasets/{dataset_id}/ask", json={"query": "Which region has the highest revenue?"})
    assert ask_res.status_code == 200
    assert "East" in ask_res.json()["answer"]
    assert "region" in ask_res.json()["relevant_columns"]

    # 8. GET /api/v1/datasets/{id}/chat-history
    hist_res = client.get(f"/api/v1/datasets/{dataset_id}/chat-history")
    assert hist_res.status_code == 200
    assert hist_res.json()["total_messages"] >= 2
