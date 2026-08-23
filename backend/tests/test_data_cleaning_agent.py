import io
import pandas as pd
from fastapi.testclient import TestClient
from app.analytics.profiler import profiler
from app.agents.data_cleaning_agent import data_cleaning_agent
from app.analytics.cleaning_engine import cleaning_engine

def test_cleaning_agent_detection_across_all_issue_types():
    """
    Test that DataCleaningAgent detects all 6 issue types from a dirty business dataset:
    1. missing values
    2. duplicate rows
    3. incorrect types
    4. inconsistent categorical values
    5. suspicious values
    6. possible outliers
    """
    dirty_df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-2", "ORD-4", "ORD-5", "ORD-6", "ORD-7", "ORD-8", "ORD-9", "ORD-10"],
        "sales_rep": ["Alice", "Bob", "Bob", "ALICE", "Charlie", "Alice", "Bob", "Charlie", "David", "David"],
        "raw_revenue": ["$1,000.00", "$2,500.50", "$2,500.50", "$3,200.00", "$500.00", "$4,100.00", "$1,800.00", "$900.00", "$2,200.00", "$3,000.00"],
        "units_sold": [10.0, 15.0, 15.0, None, 12.0, 14.0, 18.0, 11.0, 13.0, 100.0],
        "discount_amount": [50.0, 20.0, 20.0, 30.0, -100.0, 10.0, 0.0, 25.0, 15.0, 40.0]
    })

    # Add duplicate row
    dirty_df.loc[2] = dirty_df.loc[1]

    profile = profiler.generate_comprehensive_profile(
        df=dirty_df,
        dataset_id="test-dirty-01",
        project_id="proj-audit",
        name="Dirty Transactions",
        file_type="csv"
    )

    # 1. Agent Audits Dataset (Does NOT modify data)
    report = data_cleaning_agent.analyze_and_recommend(dirty_df, profile)

    assert report.total_issues_found >= 5
    issues = {r.issue for r in report.recommendations}

    # Verify detection of all requested categories
    assert "duplicate_rows" in issues
    assert "missing_values" in issues
    assert "incorrect_types" in issues
    assert "inconsistent_categories" in issues
    assert "suspicious_values" in issues
    assert "possible_outliers" in issues

    # Verify structured fields in each recommendation
    for rec in report.recommendations:
        assert rec.id is not None
        assert rec.suggested_action is not None
        assert rec.reason is not None
        assert rec.action_type is not None
        assert rec.status == "pending"  # Requires user approval

def test_deterministic_python_cleaning_execution():
    """
    Test applying approved cleaning transformations deterministically using Python/Pandas.
    """
    dirty_df = pd.DataFrame({
        "customer": ["Acme Corp", "acme corp", "Beta LLC", "Beta LLC", "Gamma Inc"],
        "revenue": ["$1,000", "$2,000", "$3,000", "$3,000", "$5,000"],
        "age": [25.0, None, 45.0, 45.0, 120.0]
    })

    profile = profiler.generate_comprehensive_profile(dirty_df, "ds-1", "p1", "Test", "csv")
    report = data_cleaning_agent.analyze_and_recommend(dirty_df, profile)

    # User approves all recommendations
    approved_recs = report.recommendations
    cleaned_df, applied_actions = cleaning_engine.execute_batch(dirty_df, approved_recs)

    # Verify data transformations
    assert len(applied_actions) > 0

    # 1. Missing value imputed (no NaN in age)
    assert cleaned_df["age"].isna().sum() == 0

    # 2. Text casing standardized
    assert "acme corp" not in cleaned_df["customer"].values

    # 3. Numeric string coerced
    if "revenue" in cleaned_df.columns:
        assert pd.api.types.is_numeric_dtype(cleaned_df["revenue"])

def test_cleaning_api_endpoints_workflow(client: TestClient):
    """
    Test complete API workflow: Upload -> Audit -> Get Recommendations -> Apply Approved Transformations
    """
    csv_content = (
        "id,category,amount,quantity\n"
        "1,Electronics,$100,5\n"
        "2,electronics,$200,10\n"
        "3,ELECTRONICS,$300,15\n"
        "4,Furniture,$400,\n"     # Missing quantity
        "4,Furniture,$400,20\n"
    )
    files = {"file": ("sales_dirty.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-clean-01"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 1. POST /api/v1/datasets/{id}/cleaning/audit
    audit_res = client.post(f"/api/v1/datasets/{dataset_id}/cleaning/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total_issues_found"] > 0
    assert len(audit_data["recommendations"]) > 0

    # 2. GET /api/v1/datasets/{id}/cleaning/recommendations
    recs_res = client.get(f"/api/v1/datasets/{dataset_id}/cleaning/recommendations")
    assert recs_res.status_code == 200
    recs_list = recs_res.json()
    assert len(recs_list) == len(audit_data["recommendations"])

    # 3. POST /api/v1/datasets/{id}/cleaning/apply (User approves selected transformations)
    approved_ids = [r["id"] for r in recs_list]
    apply_payload = {
        "approved_recommendation_ids": approved_ids,
        "save_as_new_dataset": False
    }

    apply_res = client.post(f"/api/v1/datasets/{dataset_id}/cleaning/apply", json=apply_payload)
    assert apply_res.status_code == 200
    apply_data = apply_res.json()

    assert apply_data["dataset_id"] == dataset_id
    assert apply_data["actions_applied_count"] > 0
    assert apply_data["health_score_after"] >= apply_data["health_score_before"]
    assert len(apply_data["preview_rows"]) > 0
