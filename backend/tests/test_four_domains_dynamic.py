import io
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

# =============================================================================
# 1. SALES DATASET TEST
# =============================================================================
def test_sales_dataset_complete_dynamic_lifecycle(client: TestClient):
    """
    Validates complete dynamic lifecycle for a Sales & Commercial Revenue dataset.
    """
    np.random.seed(101)
    n = 30
    dates = pd.date_range(start="2025-01-01", periods=n, freq="W").strftime("%Y-%m-%d").tolist()
    reps = ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince"] * 8
    territories = ["North America", "EMEA", "APAC", "LATAM"] * 8
    products = ["SaaS Enterprise", "SaaS Professional", "API Cloud", "Managed Services"] * 8

    units = [50 + i * 5 + int(np.random.randint(-10, 10)) for i in range(n)]
    prices = [150.0 for _ in range(n)]
    revenue = [u * p for u, p in zip(units, prices)]
    margin = [r * 0.35 + float(np.random.randint(-200, 200)) for r in revenue]

    sales_df = pd.DataFrame({
        "transaction_date": dates,
        "sales_rep": reps[:n],
        "territory": territories[:n],
        "product_line": products[:n],
        "units_sold": units,
        "unit_price": prices,
        "gross_revenue": revenue,
        "net_profit": margin
    })

    # 1. Upload & Ingestion via API
    csv_bytes = sales_df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("commercial_sales.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"projectId": "proj-sales", "customName": "Commercial Sales Q1"}
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Profiling & Data Quality
    profile = profiler.generate_comprehensive_profile(sales_df, dataset_id, "proj-sales", "Commercial Sales Q1", "csv")
    assert profile.row_count == 30
    assert "gross_revenue" in profile.numeric_columns
    assert "territory" in profile.categorical_columns
    assert "transaction_date" in profile.datetime_columns
    assert profile.quality_report.health_score >= 90.0

    # 3. Dynamic EDA & KPIs
    eda_report = eda_agent.generate_eda_report(sales_df, profile)
    assert len(eda_report.kpis) >= 3
    assert eda_report.summary.total_rows == 30
    assert len(eda_report.correlations.ranked_pairs) > 0

    # 4. Dynamic Visualization Dashboard
    viz_dashboard = visualization_agent.generate_dashboard(sales_df, profile)
    assert len(viz_dashboard.charts) >= 3
    chart_types = [c.config.chart_type for c in viz_dashboard.charts]
    assert any(t in ["line", "bar", "area"] for t in chart_types)

    # 5. Grounded Insights (5 Categories)
    insights = insight_agent.generate_report(sales_df, profile, eda_report)
    assert insights.total_insights >= 3
    assert len(insights.insights) >= 3

    # 6. Actionable Recommendations (6 Pillars)
    recs = recommendation_agent.generate_report(sales_df, profile, eda_report, insights)
    assert len(recs.recommendations) >= 2
    for r in recs.recommendations:
        assert len(r.problem) > 0
        assert len(r.action) > 0
        assert len(r.limitations) > 0
        assert "guaranteed" not in r.action.lower()

    # 7. Time-Series Forecasting
    pred_res = prediction_agent.generate_report(sales_df, profile, forecast_horizon=6)
    assert pred_res.is_suitable is True
    assert pred_res.primary_forecast.forecast_horizon_periods == 6
    assert len([p for p in pred_res.primary_forecast.predicted_values if not p.is_historical]) == 6

    # 8. Ask Your Data
    q_req = AskDataQueryRequest(query="Which territory has the highest gross revenue?")
    q_res = ask_data_agent.answer_query(sales_df, profile, q_req)
    assert "territory" in q_res.relevant_columns
    assert "gross_revenue" in q_res.relevant_columns
    assert q_res.chart is not None

# =============================================================================
# 2. HR & TALENT DATASET TEST
# =============================================================================
def test_hr_dataset_complete_dynamic_lifecycle(client: TestClient):
    """
    Validates complete dynamic lifecycle for an HR & Workforce Analytics dataset.
    """
    np.random.seed(202)
    n = 25
    departments = ["Engineering", "Product", "Sales", "People Ops", "Finance"] * 5
    job_levels = ["L3 Junior", "L4 Mid", "L5 Senior", "L6 Staff", "L7 Principal"] * 5
    salaries = [75000 + i * 4500 + int(np.random.randint(-2000, 2000)) for i in range(n)]
    tenure = [1.5 + (i * 0.4) for i in range(n)]
    overtime_hrs = [10 + (i % 6) * 4 for i in range(n)]
    satisfaction = [7.5 + (0.5 if i % 2 == 0 else -0.8) for i in range(n)]

    hr_df = pd.DataFrame({
        "department": departments,
        "job_level": job_levels,
        "monthly_salary": salaries,
        "tenure_years": tenure,
        "overtime_hours": overtime_hrs,
        "satisfaction_score": satisfaction
    })

    # 1. Upload & Ingestion via API
    csv_bytes = hr_df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("hr_workforce.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"projectId": "proj-hr", "customName": "Global Workforce Compensation"}
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Profiling & Data Quality
    profile = profiler.generate_comprehensive_profile(hr_df, dataset_id, "proj-hr", "HR Workforce", "csv")
    assert profile.row_count == 25
    assert "monthly_salary" in profile.numeric_columns
    assert "department" in profile.categorical_columns
    assert profile.quality_report.health_score >= 90.0

    # 3. Dynamic EDA & KPIs
    eda_report = eda_agent.generate_eda_report(hr_df, profile)
    assert len(eda_report.kpis) >= 3
    assert eda_report.summary.total_rows == 25

    # 4. Grounded Insights
    insights = insight_agent.generate_report(hr_df, profile, eda_report)
    assert insights.total_insights >= 3

    # 5. Prescriptive Recommendations
    recs = recommendation_agent.generate_report(hr_df, profile, eda_report, insights)
    assert len(recs.recommendations) >= 2

    # 6. Forecasting Suitability (Non-temporal table should gracefully explain lack of timestamp)
    pred_res = prediction_agent.generate_report(hr_df, profile, forecast_horizon=4)
    assert pred_res.is_suitable is False
    assert pred_res.primary_forecast is None
    assert "datetime" in pred_res.executive_summary.lower() or "suitability" in pred_res.executive_summary.lower()

    # 7. Ask Your Data
    q_req = AskDataQueryRequest(query="Which department has the highest monthly salary?")
    q_res = ask_data_agent.answer_query(hr_df, profile, q_req)
    assert "department" in q_res.relevant_columns
    assert "monthly_salary" in q_res.relevant_columns
    assert q_res.supporting_metrics["top_entity"] in ["Engineering", "Product", "Sales", "People Ops", "Finance"]

# =============================================================================
# 3. MARKETING CAMPAIGNS DATASET TEST
# =============================================================================
def test_marketing_dataset_complete_dynamic_lifecycle(client: TestClient):
    """
    Validates complete dynamic lifecycle for a Multi-Channel Marketing dataset.
    """
    np.random.seed(303)
    n = 24
    dates = pd.date_range(start="2025-06-01", periods=n, freq="W").strftime("%Y-%m-%d").tolist()
    channels = ["Google Search", "Meta Ads", "LinkedIn B2B", "TikTok Growth"] * 6
    ad_spend = [5000 + i * 400 + int(np.random.randint(-300, 300)) for i in range(n)]
    impressions = [s * 45 + int(np.random.randint(-1000, 1000)) for s in ad_spend]
    clicks = [int(imp * 0.035) for imp in impressions]
    conversions = [int(c * 0.12) for c in clicks]
    cpa = [round(s / max(1, conv), 2) for s, conv in zip(ad_spend, conversions)]

    mkt_df = pd.DataFrame({
        "campaign_date": dates,
        "channel": channels,
        "ad_spend_usd": ad_spend,
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "cost_per_acquisition": cpa
    })

    # 1. Ingestion via API
    csv_bytes = mkt_df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("marketing_campaigns.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"projectId": "proj-mkt", "customName": "Paid Acquisition Channels"}
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Profiling
    profile = profiler.generate_comprehensive_profile(mkt_df, dataset_id, "proj-mkt", "Marketing Campaigns", "csv")
    assert profile.row_count == 24
    assert "ad_spend_usd" in profile.numeric_columns
    assert "channel" in profile.categorical_columns
    assert "campaign_date" in profile.datetime_columns

    # 3. Dynamic EDA
    eda_report = eda_agent.generate_eda_report(mkt_df, profile)
    assert len(eda_report.kpis) >= 3

    # Check strong correlation between ad_spend_usd and conversions
    corr_found = any(
        (c.feature_x == "ad_spend_usd" and c.feature_y == "conversions") or
        (c.feature_x == "conversions" and c.feature_y == "ad_spend_usd")
        for c in eda_report.correlations.ranked_pairs
    )
    assert corr_found

    # 4. Insights & Recommendations
    insights = insight_agent.generate_report(mkt_df, profile, eda_report)
    assert insights.total_insights >= 3
    recs = recommendation_agent.generate_report(mkt_df, profile, eda_report, insights)
    assert len(recs.recommendations) >= 2

    # 5. Prediction
    pred_res = prediction_agent.generate_report(mkt_df, profile, forecast_horizon=6)
    assert pred_res.is_suitable is True
    assert pred_res.primary_forecast is not None

    # 6. Ask Your Data
    q_req = AskDataQueryRequest(query="Which channel has the highest ad spend?")
    q_res = ask_data_agent.answer_query(mkt_df, profile, q_req)
    assert "channel" in q_res.relevant_columns
    assert "ad_spend_usd" in q_res.relevant_columns

# =============================================================================
# 4. E-COMMERCE DATASET TEST
# =============================================================================
def test_ecommerce_dataset_complete_dynamic_lifecycle(client: TestClient):
    """
    Validates complete dynamic lifecycle for an E-commerce Cart & Conversion dataset.
    """
    np.random.seed(404)
    n = 28
    dates = pd.date_range(start="2025-09-01", periods=n, freq="D").strftime("%Y-%m-%d").tolist()
    devices = ["Mobile iOS", "Mobile Android", "Desktop Web", "Tablet"] * 7
    user_tiers = ["VIP Gold", "Standard Member", "First-Time Guest", "Returning User"] * 7
    cart_values = [45.0 + i * 3.5 + float(np.random.randint(-10, 10)) for i in range(n)]
    items_count = [2 + (i % 5) for i in range(n)]
    shipping = [5.99 if val < 75.0 else 0.0 for val in cart_values]
    ratings = [4.2 + (0.4 if i % 3 == 0 else -0.3) for i in range(n)]

    ecom_df = pd.DataFrame({
        "order_timestamp": dates,
        "device_type": devices,
        "user_tier": user_tiers,
        "cart_value_usd": cart_values,
        "items_count": items_count,
        "shipping_fee": shipping,
        "customer_rating": ratings
    })

    # 1. Ingestion via API
    csv_bytes = ecom_df.to_csv(index=False).encode("utf-8")
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("ecommerce_orders.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"projectId": "proj-ecom", "customName": "E-Commerce Daily Checkouts"}
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. Profiling & EDA
    profile = profiler.generate_comprehensive_profile(ecom_df, dataset_id, "proj-ecom", "E-Commerce Checkouts", "csv")
    assert profile.row_count == 28
    assert "cart_value_usd" in profile.numeric_columns
    assert "device_type" in profile.categorical_columns
    assert "order_timestamp" in profile.datetime_columns

    eda_report = eda_agent.generate_eda_report(ecom_df, profile)
    assert len(eda_report.kpis) >= 3

    # 3. Insights, Recommendations, Prediction & Ask Data
    insights = insight_agent.generate_report(ecom_df, profile, eda_report)
    assert insights.total_insights >= 3

    recs = recommendation_agent.generate_report(ecom_df, profile, eda_report, insights)
    assert len(recs.recommendations) >= 2

    pred_res = prediction_agent.generate_report(ecom_df, profile, forecast_horizon=7)
    assert pred_res.is_suitable is True
    assert pred_res.primary_forecast is not None

    q_req = AskDataQueryRequest(query="Which device type has the highest cart value?")
    q_res = ask_data_agent.answer_query(ecom_df, profile, q_req)
    assert "device_type" in q_res.relevant_columns
    assert "cart_value_usd" in q_res.relevant_columns
    assert q_res.chart is not None
