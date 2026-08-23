import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler

def test_dynamic_numeric_profiling():
    """
    Test deep numeric statistics: moments, quantiles, and IQR outliers
    """
    # Create sample data with an intentional outlier (e.g. 500)
    data = pd.Series([10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 20.0, 22.0, 25.0, 500.0])
    stats = profiler.compute_numeric_stats(data)

    assert stats is not None
    assert stats.min == 10.0
    assert stats.max == 500.0
    assert stats.median == 17.0
    assert stats.mean > stats.median  # Positive skew due to 500.0
    assert stats.skewness > 1.0  # High positive skew

    # Quantiles check
    assert stats.quantiles.p25 < stats.quantiles.p50 < stats.quantiles.p75
    assert stats.quantiles.iqr > 0

    # Outliers check
    assert stats.outliers.outlier_count >= 1
    assert 500.0 in stats.outliers.outlier_samples
    assert stats.outliers.outlier_percentage > 0

def test_dynamic_categorical_profiling():
    """
    Test categorical cardinality, frequencies, mode, and Shannon entropy
    """
    data = pd.Series(["Enterprise", "Enterprise", "Enterprise", "SMB", "SMB", "Startup"])
    stats = profiler.compute_categorical_stats(data)

    assert stats.cardinality == 3
    assert stats.mode == "Enterprise"
    assert stats.entropy > 0
    assert len(stats.top_categories) == 3
    assert stats.top_categories[0].label == "Enterprise"
    assert stats.top_categories[0].count == 3
    assert stats.top_categories[-1].cumulative_percentage == 100.0

def test_data_quality_report():
    """
    Test health score and quality warnings for missing data and duplicate rows
    """
    df = pd.DataFrame({
        "id": [1, 2, 2, 4, 5],
        "val": [10.0, None, None, 40.0, 50.0],
        "const": ["A", "A", "A", "A", "A"]
    })
    report = profiler.compute_data_quality_report(df)

    assert report.total_cells == 15
    assert report.missing_cells == 2
    assert report.duplicate_rows_count == 1
    assert report.health_score < 100.0  # Penalties deducted

    warning_types = [w.warning_type for w in report.warnings]
    assert "constant_value" in warning_types or "high_missing" in warning_types

def test_multi_variable_correlation_matrix():
    """
    Test Pearson correlation and strong pairs detection
    """
    # Perfectly correlated variables
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]  # 2 * x (r = 1.0)
    z = [8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]      # -1 * x (r = -1.0)

    df = pd.DataFrame({"x": x, "y": y, "z": z})
    matrix, strong_pairs = profiler.compute_correlations(df)

    assert "x" in matrix
    assert matrix["x"]["y"] == 1.0
    assert matrix["x"]["z"] == -1.0

    assert len(strong_pairs) >= 2
    pair_types = [p.strength for p in strong_pairs]
    assert "very_strong" in pair_types

def test_get_dataset_deep_profile_endpoint(client: TestClient):
    """
    Test full API integration: POST upload -> GET /api/v1/datasets/{id}/profile
    """
    csv_data = (
        "transaction_id,sales_amount,discount,region,recorded_at\n"
        "tx_1,1000,50,North,2026-01-01T10:00:00Z\n"
        "tx_2,2500,100,South,2026-01-02T11:00:00Z\n"
        "tx_3,1800,75,North,2026-01-03T12:00:00Z\n"
        "tx_4,3200,120,East,2026-01-04T13:00:00Z\n"
        "tx_5,500,20,West,2026-01-05T14:00:00Z\n"
        "tx_6,4100,200,North,2026-01-06T15:00:00Z\n"
    )
    files = {"file": ("enterprise_sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-sales-01"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # Request deep dynamic profile
    profile_res = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_res.status_code == 200
    p_json = profile_res.json()

    assert p_json["dataset_id"] == dataset_id
    assert p_json["row_count"] == 6
    assert p_json["column_count"] == 5
    assert "quality_report" in p_json
    assert p_json["quality_report"]["health_score"] >= 90.0

    # Verify column statistics
    cols = {c["name"]: c for c in p_json["columns"]}
    assert cols["sales_amount"]["data_type"] == "numeric"
    assert cols["sales_amount"]["numeric_stats"]["mean"] > 0
    assert cols["sales_amount"]["numeric_stats"]["quantiles"]["p50"] > 0
    assert cols["region"]["categorical_stats"]["cardinality"] == 4
    assert cols["recorded_at"]["datetime_stats"]["timespan_days"] >= 4.0

    # Verify correlation matrix
    assert "sales_amount" in p_json["correlation_matrix"]
