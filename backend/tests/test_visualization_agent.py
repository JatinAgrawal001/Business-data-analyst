import io
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.agents.visualization_agent import visualization_agent
from app.schemas.visualization import CustomChartRequest, VisualizationDashboardResponse, CustomChartResponse

def test_visualization_agent_generates_all_supported_chart_types():
    """
    Test VisualizationAgent generates all required chart types dynamically:
    - line
    - bar
    - scatter
    - histogram
    - box plot (box_plot)
    - heatmap
    - KPI (kpi_card)
    """
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:03d}" for i in range(1, 25)],
        "order_date": pd.date_range(start="2026-01-01", periods=24, freq="D").strftime("%Y-%m-%d"),
        "region": ["North America", "EMEA", "APAC", "LATAM"] * 6,
        "revenue": [1000, 2500, 800, 3200, 1500, 4100, 900, 2200, 1800, 3000, 1100, 2700, 950, 3400, 1600, 4300, 850, 2100, 1900, 3100, 1050, 2600, 880, 5500], # Outlier 5500
        "units_sold": [10, 25, 8, 32, 15, 41, 9, 22, 18, 30, 11, 27, 9, 34, 16, 43, 8, 21, 19, 31, 10, 26, 9, 50]
    })

    profile = profiler.generate_comprehensive_profile(df, "viz-all-01", "p1", "Multi-Chart Sales", "csv")
    eda_report = eda_agent.generate_eda_report(df, profile)

    dashboard = visualization_agent.generate_dashboard(df, profile, eda_report=eda_report, theme="indigo_modern")

    assert isinstance(dashboard, VisualizationDashboardResponse)
    assert len(dashboard.kpi_cards) > 0
    assert len(dashboard.charts) >= 5

    chart_types = {c.config.chart_type for c in dashboard.charts}

    # Verify all core chart types are present
    assert "bar" in chart_types
    assert "line" in chart_types
    assert "scatter" in chart_types
    assert "histogram" in chart_types
    assert "box_plot" in chart_types
    assert "heatmap" in chart_types

    # 1. Verify Box Plot mathematical accuracy (No fake values)
    box_chart = next(c for c in dashboard.charts if c.config.chart_type == "box_plot")
    box_row = box_chart.data[0]
    assert box_row["median"] == float(df["revenue"].median())
    assert box_row["q1"] == float(df["revenue"].quantile(0.25))
    assert box_row["q3"] == float(df["revenue"].quantile(0.75))

    # 2. Verify Heatmap correlation grid
    heatmap_chart = next(c for c in dashboard.charts if c.config.chart_type == "heatmap")
    assert len(heatmap_chart.data) >= 4
    for cell in heatmap_chart.data:
        assert "x" in cell
        assert "y" in cell
        assert -1.0 <= cell["value"] <= 1.0

def test_high_cardinality_guardrails_prevention():
    """
    Test that high-cardinality categorical columns (e.g. 50 distinct cities)
    are aggregated to Top 10 + Other to keep charts clean and readable.
    """
    cities = [f"City-{i:02d}" for i in range(1, 51)]
    df = pd.DataFrame({
        "city": cities,
        "sales": [float(i * 100) for i in range(1, 51)]
    })

    profile = profiler.generate_comprehensive_profile(df, "high-card-01", "p1", "High Cardinality", "csv")
    dashboard = visualization_agent.generate_dashboard(df, profile)

    bar_chart = next((c for c in dashboard.charts if c.config.chart_type == "bar"), None)
    if bar_chart:
        # Must be capped at <= 11 items (Top 10 + 'Other')
        assert len(bar_chart.data) <= 11
        cat_labels = [item["category"] for item in bar_chart.data]
        assert "Other" in cat_labels

def test_custom_chart_box_plot_and_histogram_queries():
    """
    Test custom text2chart queries for box plot and histogram.
    """
    df = pd.DataFrame({
        "salary": [45000, 52000, 61000, 58000, 95000, 53000, 62000, 48000, 150000],
        "department": ["Sales", "Engineering", "Marketing", "HR", "Exec", "Sales", "Engineering", "HR", "Exec"]
    })
    profile = profiler.generate_comprehensive_profile(df, "hr-viz", "p1", "HR", "csv")

    # 1. Custom Box Plot Query
    req_box = CustomChartRequest(query="Show box plot of salary")
    res_box = visualization_agent.generate_custom_chart(df, profile, req_box)
    assert res_box.chart.config.chart_type == "box_plot"
    assert len(res_box.chart.data) == 1
    assert res_box.chart.data[0]["median"] == float(df["salary"].median())

    # 2. Custom Histogram Query
    req_hist = CustomChartRequest(query="Show distribution of salary", preferred_chart_type="histogram")
    res_hist = visualization_agent.generate_custom_chart(df, profile, req_hist)
    assert res_hist.chart.config.chart_type == "histogram"
    assert len(res_hist.chart.data) == 5

def test_visualization_api_endpoints_workflow(client: TestClient):
    """
    Test API endpoints: GET /visualizations/dashboard and POST /visualizations/query
    """
    csv_data = (
        "region,product,sales,quantity\n"
        "North,Laptops,5000,10\n"
        "South,Phones,3000,20\n"
        "East,Laptops,4000,8\n"
        "West,Tablets,2500,15\n"
    )
    files = {"file": ("sales_viz.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-viz-01"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. GET /api/v1/datasets/{id}/visualizations/dashboard
    dash_res = client.get(f"/api/v1/datasets/{dataset_id}/visualizations/dashboard?theme=slate_executive")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["dataset_id"] == dataset_id
    assert dash_data["theme"] == "slate_executive"
    assert len(dash_data["kpi_cards"]) > 0
    assert len(dash_data["charts"]) > 0

    # 2. POST /api/v1/datasets/{id}/visualizations/query
    query_payload = {"query": "Show sales by region"}
    query_res = client.post(f"/api/v1/datasets/{dataset_id}/visualizations/query", json=query_payload)
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert "chart" in query_data
    assert len(query_data["chart"]["data"]) > 0
