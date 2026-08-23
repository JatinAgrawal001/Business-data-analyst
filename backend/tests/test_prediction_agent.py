import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.prediction_agent import prediction_agent
from app.schemas.prediction import (
    PredictionReport,
    ValidatedTimeSeriesForecast,
    ForecastingSuitabilityReport,
    WhatIfScenarioRequest,
    WhatIfScenarioResponse,
    CustomForecastRequest
)

def test_prediction_agent_suitability_audit_and_baseline_comparison():
    """
    Test PredictionAgent performs mandatory suitability checks,
    evaluates candidate models against Naive Baseline, and returns verified analytical bounds.
    """
    # 1. Suitable Time-Series Dataset (12 monthly periods)
    df = pd.DataFrame({
        "order_date": pd.date_range(start="2025-01-01", periods=12, freq="ME").strftime("%Y-%m-%d"),
        "revenue": [10000, 12000, 15000, 18000, 22000, 26000, 31000, 37000, 44000, 52000, 61000, 71000],
        "marketing_spend": [1000, 1200, 1500, 1800, 2100, 2500, 3000, 3600, 4200, 5000, 5800, 6800],
        "active_users": [500, 600, 750, 900, 1100, 1300, 1550, 1850, 2200, 2600, 3050, 3550]
    })

    profile = profiler.generate_comprehensive_profile(df, "pred-suit-01", "p1", "SaaS Growth", "csv")
    suitability = prediction_agent.evaluate_forecasting_suitability(df, profile)

    # Verify Suitability Passed
    assert isinstance(suitability, ForecastingSuitabilityReport)
    assert suitability.is_suitable is True
    assert suitability.datetime_column_found is True
    assert suitability.numeric_metric_found is True
    assert suitability.historical_periods_count == 12
    assert suitability.train_test_split_viable is True

    # Fit Validated Forecast
    forecast = prediction_agent.fit_validated_forecast(df, profile, forecast_horizon=6)
    assert isinstance(forecast, ValidatedTimeSeriesForecast)
    assert forecast.is_suitable is True
    assert forecast.target_metric == "revenue"
    assert forecast.forecast_horizon_periods == 6

    # Verify Baseline Comparison
    base_comp = forecast.baseline_comparison
    assert base_comp.baseline_model_name == "Naive (Last Observed Value) Baseline"
    assert base_comp.baseline_test_rmse > 0
    assert base_comp.champion_test_rmse > 0
    assert len(base_comp.candidate_models_evaluated) >= 2

    # Verify Analytical 95% Confidence Bounds (No Fabricated Confidence)
    assert len(forecast.predicted_values) == 18  # 12 historical + 6 forecast
    for pt in forecast.predicted_values:
        assert pt.lower_bound_95 <= pt.forecast_value <= pt.upper_bound_95

    # Verify Model Used and Limitations
    assert len(forecast.model_used) > 0
    assert len(forecast.limitations) > 20
    assert "assumes" in forecast.limitations.lower() or "projections" in forecast.limitations.lower()

def test_prediction_agent_rejects_unsuitable_dataset():
    """
    Test PredictionAgent detects when a dataset is unsuitable (e.g. no date column, small data)
    and explains why instead of generating a fake forecast.
    """
    df_unsuitable = pd.DataFrame({
        "category": ["A", "B", "C"],
        "metric": [100, 200, 300]
    })
    profile_unsuitable = profiler.generate_comprehensive_profile(df_unsuitable, "unsuit-01", "p1", "Categorical Data", "csv")

    suitability = prediction_agent.evaluate_forecasting_suitability(df_unsuitable, profile_unsuitable)
    assert suitability.is_suitable is False
    assert len(suitability.unsuitability_reasons) >= 1
    assert any("datetime" in r.lower() for r in suitability.unsuitability_reasons)

    report = prediction_agent.generate_report(df_unsuitable, profile_unsuitable)
    assert isinstance(report, PredictionReport)
    assert report.is_suitable is False
    assert report.primary_forecast is None
    assert "inappropriate" in report.executive_summary.lower()

def test_prediction_agent_what_if_simulation():
    """
    Test deterministic what-if scenario simulations with feature adjustments.
    """
    df = pd.DataFrame({
        "revenue": [10000, 15000, 20000, 25000, 30000],
        "marketing_spend": [1000, 1500, 2000, 2500, 3000],
        "discount_rate": [0.05, 0.08, 0.10, 0.12, 0.15]
    })

    req = WhatIfScenarioRequest(
        target_metric="revenue",
        feature_adjustments={"marketing_spend": 1.20}  # +20% marketing spend
    )
    res = prediction_agent.simulate_what_if_scenario(df, req)

    assert isinstance(res, WhatIfScenarioResponse)
    assert res.target_metric == "revenue"
    assert res.baseline_predicted_value == 20000.0  # Mean revenue
    assert res.simulated_predicted_value > res.baseline_predicted_value
    assert res.percentage_change > 0
    assert len(res.strategic_interpretation) > 0

def test_prediction_api_endpoints_workflow(client: TestClient):
    """
    Test complete Prediction API endpoints:
    - GET /predictions/suitability
    - POST /predictions/forecast
    - GET /predictions/report
    - POST /predictions/custom-forecast
    - POST /predictions/what-if
    """
    csv_data = (
        "date,sales,ad_spend,leads\n"
        "2026-01-01,100,50,20\n"
        "2026-01-02,120,60,25\n"
        "2026-01-03,140,70,30\n"
        "2026-01-04,160,80,35\n"
        "2026-01-05,180,90,40\n"
        "2026-01-06,200,100,45\n"
        "2026-01-07,220,110,50\n"
    )
    files = {"file": ("forecast_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-pred-suite"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. GET /api/v1/datasets/{id}/predictions/suitability
    suit_res = client.get(f"/api/v1/datasets/{dataset_id}/predictions/suitability")
    assert suit_res.status_code == 200
    assert suit_res.json()["is_suitable"] is True

    # 2. POST /api/v1/datasets/{id}/predictions/forecast
    gen_res = client.post(f"/api/v1/datasets/{dataset_id}/predictions/forecast?horizon=4")
    assert gen_res.status_code == 200
    report_data = gen_res.json()
    assert report_data["dataset_id"] == dataset_id
    assert report_data["is_suitable"] is True
    assert "primary_forecast" in report_data
    assert "baseline_comparison" in report_data["primary_forecast"]

    # 3. GET /api/v1/datasets/{id}/predictions/report
    get_res = client.get(f"/api/v1/datasets/{dataset_id}/predictions/report")
    assert get_res.status_code == 200
    assert get_res.json()["dataset_id"] == dataset_id

    # 4. POST /api/v1/datasets/{id}/predictions/custom-forecast
    custom_req = {"target_metric": "ad_spend", "forecast_periods": 3}
    custom_res = client.post(f"/api/v1/datasets/{dataset_id}/predictions/custom-forecast", json=custom_req)
    assert custom_res.status_code == 200
    assert custom_res.json()["target_metric"] == "ad_spend"
    assert "baseline_comparison" in custom_res.json()

    # 5. POST /api/v1/datasets/{id}/predictions/what-if
    what_if_req = {"target_metric": "sales", "feature_adjustments": {"ad_spend": 1.10}}
    what_if_res = client.post(f"/api/v1/datasets/{dataset_id}/predictions/what-if", json=what_if_req)
    assert what_if_res.status_code == 200
    assert what_if_res.json()["target_metric"] == "sales"
    assert "simulated_predicted_value" in what_if_res.json()
