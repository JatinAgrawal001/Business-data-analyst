import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.schemas.eda import EDAReport

def test_eda_agent_report_generation():
    """
    Test EDA Agent generates comprehensive exploratory reports with segments, trends, and charts.
    """
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 21)],
        "order_date": pd.date_range(start="2026-01-01", periods=20, freq="D").strftime("%Y-%m-%d"),
        "region": ["North America", "EMEA", "APAC", "LATAM"] * 5,
        "product_category": ["Software", "Hardware", "Services", "Cloud"] * 5,
        "revenue": [1000, 2500, 800, 3200, 1500, 4100, 900, 2200, 1800, 3000, 1100, 2700, 950, 3400, 1600, 4300, 850, 2100, 1900, 3100],
        "units": [10, 25, 8, 32, 15, 41, 9, 22, 18, 30, 11, 27, 9, 34, 16, 43, 8, 21, 19, 31]
    })

    profile = profiler.generate_comprehensive_profile(df, "sales-eda-01", "p1", "Sales Dataset", "csv")
    report = eda_agent.generate_eda_report(df, profile)

    assert isinstance(report, EDAReport)
    assert report.dataset_id == "sales-eda-01"
    assert report.summary.total_rows == 20
    assert report.summary.total_columns == 6
    assert len(report.summary.key_takeaways) > 0

    # 1. Group-by / Segment Breakdown Verification
    assert len(report.group_by_analysis) > 0
    seg = report.group_by_analysis[0]
    assert seg.metric_column == "revenue"
    assert len(seg.top_segments) > 0
    assert seg.top_segments[0].metric_sum > 0
    assert seg.top_segments[0].percentage > 0

    # 2. Time-Series Trend Verification
    assert report.time_trends is not None
    assert report.time_trends.time_column == "order_date"
    assert len(report.time_trends.data_points) == 20
    assert report.time_trends.trend_direction in ["upward", "downward", "stable", "volatile"]

    # 3. Chart Recommendations Verification
    chart_types = {c.chart_type for c in report.chart_recommendations}
    assert "bar" in chart_types
    assert "line" in chart_types
    assert "donut" in chart_types

    # 4. Insights Verification
    assert len(report.insights) > 0

def test_eda_api_endpoints_workflow(client: TestClient):
    """
    Test complete EDA API endpoints workflow: Upload -> Analyze -> Get Report -> Get Charts
    """
    csv_data = (
        "date,channel,spend,conversions\n"
        "2026-01-01,Google,500,20\n"
        "2026-01-02,Meta,800,35\n"
        "2026-01-03,Google,600,25\n"
        "2026-01-04,LinkedIn,1200,15\n"
        "2026-01-05,Meta,900,40\n"
        "2026-01-06,TikTok,400,30\n"
    )
    files = {"file": ("campaigns.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-mkt-eda"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. POST /api/v1/datasets/{id}/eda/analyze
    analyze_res = client.post(f"/api/v1/datasets/{dataset_id}/eda/analyze")
    assert analyze_res.status_code == 200
    report_data = analyze_res.json()
    assert report_data["dataset_id"] == dataset_id
    assert "summary" in report_data
    assert len(report_data["chart_recommendations"]) > 0

    # 2. GET /api/v1/datasets/{id}/eda/report
    report_res = client.get(f"/api/v1/datasets/{dataset_id}/eda/report")
    assert report_res.status_code == 200
    assert report_res.json()["dataset_id"] == dataset_id

    # 3. GET /api/v1/datasets/{id}/eda/charts
    charts_res = client.get(f"/api/v1/datasets/{dataset_id}/eda/charts")
    assert charts_res.status_code == 200
    charts_list = charts_res.json()
    assert len(charts_list) > 0
    assert "chart_type" in charts_list[0]
    assert "data" in charts_list[0]
