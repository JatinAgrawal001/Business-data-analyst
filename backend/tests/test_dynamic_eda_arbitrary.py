import pandas as pd
import numpy as np
from app.analytics.profiler import profiler
from app.agents.eda_agent import eda_agent
from app.schemas.eda import EDAReport

def test_dynamic_eda_on_arbitrary_sensor_telemetry_dataset():
    """
    Test EDA Agent dynamically analyzes an arbitrary IoT/telemetry dataset
    with non-standard column names (no sales, revenue, profit, or customer columns).
    """
    df = pd.DataFrame({
        "device_guid": [f"DEV-{i:04d}" for i in range(1, 26)],
        "telemetry_timestamp": pd.date_range("2026-03-01", periods=25, freq="D").strftime("%Y-%m-%d"),
        "sensor_zone": ["Zone-Alpha", "Zone-Beta", "Zone-Gamma", "Zone-Delta", "Zone-Epsilon"] * 5,
        "operating_mode": ["High-Performance", "Eco-Mode", "Standby", "High-Performance", "Eco-Mode"] * 5,
        "packet_volume": [1200, 450, 100, 1500, 480, 1300, 500, 120, 1600, 520, 1400, 490, 110, 1700, 540, 1350, 470, 95, 1550, 510, 1250, 460, 105, 1650, 530],
        "latency_ms": [15.2, 45.8, 120.4, 12.1, 48.0, 14.5, 42.0, 115.0, 11.8, 46.2, 13.9, 44.1, 125.0, 10.5, 49.3, 14.1, 43.5, 118.0, 12.0, 45.0, 15.0, 47.1, 122.0, 11.2, 48.5],
        "thermal_load": [65.0, 42.0, 30.0, 72.0, 44.0, 68.0, 41.0, 32.0, 75.0, 45.0, 66.0, 43.0, 31.0, 78.0, 46.0, 67.0, 42.5, 29.5, 74.0, 44.5, 65.5, 43.2, 30.5, 76.5, 45.8]
    })

    # Add an outlier in latency
    df.loc[24, "latency_ms"] = 550.0

    profile = profiler.generate_comprehensive_profile(
        df=df,
        dataset_id="sensor-telemetry-01",
        project_id="proj-iot",
        name="Industrial Sensor Telemetry",
        file_type="csv"
    )

    # Execute dynamic EDA Agent
    report = eda_agent.generate_eda_report(df, profile)

    assert isinstance(report, EDAReport)
    assert report.dataset_id == "sensor-telemetry-01"

    # 1. Descriptive Statistics generated for all numeric columns
    assert "packet_volume" in report.descriptive_statistics
    assert "latency_ms" in report.descriptive_statistics
    assert "thermal_load" in report.descriptive_statistics
    assert report.descriptive_statistics["packet_volume"].mean > 0
    assert report.descriptive_statistics["latency_ms"].median > 0

    # 2. Distributions (5-bucket histograms)
    assert "packet_volume" in report.distributions
    assert len(report.distributions["packet_volume"]) == 5

    # 3. Category Analysis (cardinality, entropy, frequencies)
    assert len(report.category_analysis) >= 2
    cat_names = [c.column for c in report.category_analysis]
    assert "sensor_zone" in cat_names
    assert "operating_mode" in cat_names
    for cat in report.category_analysis:
        assert cat.cardinality > 0
        assert cat.entropy >= 0
        assert len(cat.top_categories) > 0

    # 4. Outlier Analysis (Tukey's IQR reports)
    assert len(report.outlier_analysis) > 0
    latency_outlier = next((o for o in report.outlier_analysis if o.column == "latency_ms"), None)
    assert latency_outlier is not None
    assert latency_outlier.outlier_count > 0
    assert latency_outlier.severity in ["severe", "moderate"]

    # 5. Group-by Multi-dimensional Analysis
    assert len(report.group_by_analysis) > 0
    grp = report.group_by_analysis[0]
    assert grp.dimension_column in ["sensor_zone", "operating_mode"]
    assert len(grp.top_segments) > 0
    assert grp.top_segments[0].metric_sum > 0
    assert grp.top_segments[0].percentage > 0

    # 6. Time Trends (Chronological progression)
    assert report.time_trends is not None
    assert report.time_trends.time_column == "telemetry_timestamp"
    assert len(report.time_trends.data_points) == 25
    assert report.time_trends.trend_direction in ["upward", "downward", "stable", "volatile"]

    # 7. Relevant KPIs dynamically derived
    assert len(report.kpis) > 0
    kpi_keys = [k.key for k in report.kpis]
    assert any(k in ["packet_volume", "latency_ms", "thermal_load"] for k in kpi_keys)
    for kpi in report.kpis:
        assert kpi.formatted_value is not None
        assert kpi.value != 0

    # 8. Correlations Summary
    assert report.correlations is not None
    assert len(report.correlations.matrix) > 0

    # 9. Chart Recommendations
    assert len(report.chart_recommendations) > 0
    chart_types = {c.chart_type for c in report.chart_recommendations}
    assert "bar" in chart_types
    assert "donut" in chart_types

def test_dynamic_eda_on_academic_research_dataset():
    """
    Test EDA Agent on an academic research dataset with zero standard business keywords.
    """
    df = pd.DataFrame({
        "specimen_id": [f"SPEC-{i}" for i in range(1, 16)],
        "experiment_batch": ["Batch-A", "Batch-B", "Batch-C"] * 5,
        "ph_level": [6.8, 7.1, 7.4, 6.9, 7.0, 7.3, 6.7, 7.2, 7.5, 6.9, 7.1, 7.3, 6.8, 7.0, 7.4],
        "absorbance_nm": [0.45, 0.62, 0.88, 0.48, 0.65, 0.91, 0.42, 0.60, 0.85, 0.47, 0.63, 0.89, 0.44, 0.61, 0.87],
        "yield_grams": [12.4, 18.2, 25.6, 13.1, 19.0, 26.2, 11.9, 17.5, 24.8, 12.8, 18.5, 25.9, 12.2, 17.9, 25.1]
    })

    profile = profiler.generate_comprehensive_profile(df, "specimen-01", "p-lab", "Lab Experiments", "csv")
    report = eda_agent.generate_eda_report(df, profile)

    assert report.summary.total_rows == 15
    assert report.summary.total_columns == 5
    assert len(report.kpis) > 0
    assert len(report.group_by_analysis) > 0
    assert report.group_by_analysis[0].dimension_column == "experiment_batch"
