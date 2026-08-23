import io
import pandas as pd
from app.analytics.profiler import profiler
from app.schemas.profiler import DatasetProfile

def test_sales_dataset_profiling():
    """
    Test profiling an arbitrary multi-variable Sales dataset.
    """
    sales_df = pd.DataFrame({
        "order_id": [f"ORD-{i:04d}" for i in range(1, 21)],
        "order_date": pd.date_range(start="2026-01-01", periods=20, freq="D").strftime("%Y-%m-%d"),
        "customer_segment": ["Enterprise", "Mid-Market", "SMB", "Consumer"] * 5,
        "region": ["North America", "EMEA", "APAC", "LATAM"] * 5,
        "product_category": ["Software", "Hardware", "Services", "Cloud"] * 5,
        "units_sold": [5, 12, 3, 25, 8, 14, 2, 30, 7, 10, 4, 18, 9, 15, 6, 22, 11, 13, 1, 40],
        "unit_price": [199.99, 499.50, 150.00, 75.00] * 5,
        "total_revenue": [999.95, 5994.00, 450.00, 1875.00, 1599.92, 6993.00, 300.00, 2250.00, 1399.93, 4995.00, 600.00, 1350.00, 1799.91, 7492.50, 900.00, 1650.00, 2199.89, 6493.50, 150.00, 3000.00],
        "discount_rate": [0.05, 0.10, 0.0, 0.15, 0.05, 0.10, 0.0, 0.20, 0.05, 0.10, 0.0, 0.15, 0.05, 0.10, 0.0, 0.15, 0.05, 0.10, 0.0, 0.25],
        "is_expedited_shipping": [True, False, False, True] * 5
    })

    profile = profiler.generate_comprehensive_profile(
        df=sales_df,
        dataset_id="sales-01",
        project_id="proj-sales",
        name="Global Sales Q1",
        file_type="csv"
    )

    assert isinstance(profile, DatasetProfile)
    assert profile.row_count == 20
    assert profile.column_count == 10

    # 1. Detection of column types
    assert "order_id" in profile.identifier_columns
    assert "order_date" in profile.datetime_columns
    assert "customer_segment" in profile.categorical_columns
    assert "region" in profile.categorical_columns
    assert "product_category" in profile.categorical_columns
    assert "units_sold" in profile.numeric_columns
    assert "total_revenue" in profile.numeric_columns
    assert "discount_rate" in profile.numeric_columns

    # 2. Descriptive statistics check
    rev_stats = profile.descriptive_stats["total_revenue"]
    assert rev_stats.min == 150.0
    assert rev_stats.max == 7492.50
    assert rev_stats.mean > 0
    assert rev_stats.median > 0
    assert rev_stats.quantiles.p25 < rev_stats.quantiles.p50 < rev_stats.quantiles.p75
    assert len(rev_stats.distribution) == 5

    # 3. Potential metrics check
    potential_metric_keys = [m.name for m in profile.potential_metrics]
    assert "total_revenue" in potential_metric_keys
    assert "units_sold" in potential_metric_keys
    assert "order_id" not in potential_metric_keys  # Identifier excluded

    # 4. Data Quality & Duplicates
    assert profile.missing_values_summary.missing_cells == 0
    assert profile.duplicate_summary.duplicate_rows == 0
    assert profile.quality_report.health_score == 100.0

def test_hr_dataset_profiling():
    """
    Test profiling an arbitrary HR & Employee Analytics dataset.
    """
    hr_df = pd.DataFrame({
        "emp_uuid": [f"EMP-{i:03d}" for i in range(1, 16)],
        "hire_date": pd.date_range(start="2020-03-01", periods=15, freq="200D").strftime("%Y-%m-%d"),
        "department": ["Engineering", "Product", "Sales", "HR", "Finance"] * 3,
        "job_level": ["Junior", "Mid", "Senior", "Lead", "Director"] * 3,
        "monthly_salary": [4500, 6800, 9200, 12500, 18000, 4800, 7100, 9500, 13000, 19500, 5000, 7500, 9800, 13500, 21000],
        "satisfaction_rating": [4.2, 3.8, 4.5, 4.0, 4.9, 3.2, 4.1, 4.7, 3.9, 4.8, 3.5, 4.0, 4.6, 4.3, 5.0],
        "performance_score": [85, 78, 92, 88, 95, 72, 84, 94, 80, 96, 75, 82, 93, 89, 99],
        "is_active": [True, True, True, True, False, True, True, True, True, False, True, True, True, True, True]
    })

    profile = profiler.generate_comprehensive_profile(
        df=hr_df,
        dataset_id="hr-01",
        project_id="proj-hr",
        name="HR Workforce Analytics",
        file_type="csv"
    )

    assert profile.row_count == 15
    assert profile.column_count == 8

    # Types & Identifiers
    assert "emp_uuid" in profile.identifier_columns
    assert "hire_date" in profile.datetime_columns
    assert "department" in profile.categorical_columns
    assert "monthly_salary" in profile.numeric_columns
    assert "performance_score" in profile.numeric_columns

    # Descriptive Stats
    salary_stats = profile.descriptive_stats["monthly_salary"]
    assert salary_stats.min == 4500
    assert salary_stats.max == 21000
    assert salary_stats.sum > 0
    assert salary_stats.std_dev > 0

    # Potential KPIs
    metric_names = [m.name for m in profile.potential_metrics]
    assert "monthly_salary" in metric_names
    assert "performance_score" in metric_names
    assert "satisfaction_rating" in metric_names

def test_marketing_dataset_profiling():
    """
    Test profiling an arbitrary Marketing & Campaign Performance dataset with missing values.
    """
    mkt_df = pd.DataFrame({
        "campaign_id": [f"CMP_{i:02d}" for i in range(1, 11)],
        "channel": ["Google Ads", "Meta Ads", "LinkedIn", "TikTok", "YouTube"] * 2,
        "launch_timestamp": ["2026-02-01T00:00:00Z", "2026-02-02T00:00:00Z", "2026-02-03T00:00:00Z", "2026-02-04T00:00:00Z", "2026-02-05T00:00:00Z"] * 2,
        "impressions": [50000, 120000, 25000, 180000, 85000, 60000, 140000, 30000, 210000, 95000],
        "clicks": [1500, 4200, 450, 7200, 2100, 1800, 5100, 520, 8900, 2400],
        "ad_spend": [1200.0, 3500.0, 850.0, 4200.0, 1900.0, 1450.0, 4100.0, 920.0, 5100.0, 2150.0],
        "conversions": [45, 110, 12, 185, 52, 58, 135, 15, 240, 65],
        "cpc": [0.80, 0.83, 1.89, 0.58, 0.90, 0.81, 0.80, 1.77, 0.57, 0.90],
        "notes": ["Target Q1", None, "B2B Only", None, "Video Ad", None, "Retargeting", None, "Viral push", None]
    })

    profile = profiler.generate_comprehensive_profile(
        df=mkt_df,
        dataset_id="mkt-01",
        project_id="proj-mkt",
        name="Q1 Marketing Campaigns",
        file_type="csv"
    )

    assert profile.row_count == 10
    assert profile.column_count == 9

    # Identifiers, Datetimes, Categoricals
    assert "campaign_id" in profile.identifier_columns
    assert "launch_timestamp" in profile.datetime_columns
    assert "channel" in profile.categorical_columns

    # Missing values detection
    assert profile.missing_values_summary.missing_cells == 5
    assert "notes" in profile.missing_values_summary.columns_with_missing
    assert profile.quality_report.health_score < 100.0

    # Correlation checks
    assert "ad_spend" in profile.descriptive_stats
    assert len(profile.strong_correlations) > 0  # ad_spend and impressions/clicks/conversions are highly correlated

def test_ecommerce_dataset_profiling():
    """
    Test profiling an arbitrary E-Commerce transactions dataset.
    """
    ecom_df = pd.DataFrame({
        "txn_hash": [f"TXN_{hex(i*999)[2:]}" for i in range(1, 13)],
        "created_at": pd.date_range(start="2026-03-01 08:00:00", periods=12, freq="h").strftime("%Y-%m-%d %H:%M:%S"),
        "customer_uuid": [f"CUST-{i%4}" for i in range(1, 13)],
        "device": ["Mobile iOS", "Mobile Android", "Desktop Chrome", "Desktop Safari"] * 3,
        "payment_provider": ["Stripe", "PayPal", "Apple Pay", "Klarna"] * 3,
        "cart_subtotal": [49.99, 129.50, 24.00, 310.00, 85.00, 199.90, 42.50, 450.00, 68.00, 145.00, 35.00, 520.00],
        "shipping_cost": [4.99, 0.00, 4.99, 0.00, 4.99, 0.00, 4.99, 0.00, 4.99, 0.00, 4.99, 0.00],
        "is_successful": [True, True, True, True, True, True, False, True, True, True, True, True]
    })

    profile = profiler.generate_comprehensive_profile(
        df=ecom_df,
        dataset_id="ecom-01",
        project_id="proj-ecom",
        name="Live E-commerce Telemetry",
        file_type="csv"
    )

    assert profile.row_count == 12
    assert profile.column_count == 8

    # Identifiers
    assert "txn_hash" in profile.identifier_columns
    assert "created_at" in profile.datetime_columns
    assert "device" in profile.categorical_columns
    assert "payment_provider" in profile.categorical_columns
    assert "cart_subtotal" in profile.numeric_columns

    # Potential KPIs
    metric_keys = [m.name for m in profile.potential_metrics]
    assert "cart_subtotal" in metric_keys
    assert "shipping_cost" in metric_keys

    # Datetime timespan
    date_col = next(c for c in profile.columns if c.name == "created_at")
    assert date_col.datetime_stats is not None
    assert date_col.datetime_stats.timespan_days >= 0.0
