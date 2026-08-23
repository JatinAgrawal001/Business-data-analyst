import io
import pandas as pd
from fastapi.testclient import TestClient

def test_upload_and_profile_csv_dynamic_schema(client: TestClient):
    """
    Test uploading a CSV with arbitrary dynamic schema: numeric, categorical, datetime, and id columns.
    """
    csv_data = (
        "patient_id,heart_rate,blood_pressure,department,admitted_at\n"
        "pt_001,72,120,Cardiology,2026-01-01T08:00:00Z\n"
        "pt_002,85,135,Neurology,2026-01-02T10:15:00Z\n"
        "pt_003,64,110,Cardiology,2026-01-03T14:30:00Z\n"
        "pt_004,110,145,Emergency,2026-01-04T18:00:00Z\n"
        "pt_005,78,125,Orthopedics,2026-01-05T09:45:00Z\n"
    )

    files = {
        "file": ("patients_telemetry.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")
    }
    data = {
        "projectId": "proj-clinical-01",
        "name": "Clinical Patient Telemetry"
    }

    response = client.post("/api/v1/datasets/upload", files=files, data=data)
    assert response.status_code == 201

    res = response.json()
    assert res["name"] == "Clinical Patient Telemetry"
    assert res["status"] == "completed"
    assert res["rowCount"] == 5
    assert res["columnCount"] == 5
    assert res["fileType"] == "csv"
    assert "storagePath" in res
    assert res["storageBucket"] == "datasets"
    assert "patients_telemetry" in res["fileName"].lower()

    # Column type verification
    cols = {c["name"]: c for c in res["columns"]}
    assert cols["patient_id"]["dataType"] == "id"
    assert cols["heart_rate"]["dataType"] == "numeric"
    assert cols["blood_pressure"]["dataType"] == "numeric"
    assert cols["department"]["dataType"] == "categorical"
    assert cols["admitted_at"]["dataType"] == "datetime"

    # Numeric summary verification
    hr_summary = cols["heart_rate"]["summary"]
    assert hr_summary["min"] == 64.0
    assert hr_summary["max"] == 110.0
    assert hr_summary["uniqueCount"] == 5
    assert len(hr_summary["distribution"]) == 5

    # Categorical summary verification
    dept_summary = cols["department"]["summary"]
    assert dept_summary["uniqueCount"] == 4
    assert len(dept_summary["topCategories"]) > 0

    dataset_id = res["id"]

    # Test GET /api/v1/datasets/{dataset_id}
    get_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == dataset_id
    assert get_res.json()["status"] == "completed"

    # Test GET /api/v1/datasets/{dataset_id}/preview
    preview_res = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=10")
    assert preview_res.status_code == 200
    p_data = preview_res.json()
    assert p_data["id"] == dataset_id
    assert p_data["status"] == "completed"
    assert len(p_data["sampleRows"]) == 5
    assert len(p_data["columns"]) == 5

    # Test DELETE /api/v1/datasets/{dataset_id}
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 204

def test_upload_excel_xlsx_format(client: TestClient):
    """
    Test uploading XLSX Excel workbook without predefined schema
    """
    df = pd.DataFrame({
        "sku": ["SKU-01", "SKU-02", "SKU-03", "SKU-04"],
        "units_sold": [150, 420, 85, 310],
        "unit_cost": [12.50, 45.00, 8.20, 22.00]
    })
    excel_buf = io.BytesIO()
    df.to_excel(excel_buf, index=False)
    excel_bytes = excel_buf.getvalue()

    files = {
        "file": ("q2_inventory.xlsx", io.BytesIO(excel_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    data = {
        "projectId": "proj-supply-01",
        "name": "Q2 Inventory"
    }

    response = client.post("/api/v1/datasets/upload", files=files, data=data)
    assert response.status_code == 201
    res = response.json()
    assert res["name"] == "Q2 Inventory"
    assert res["status"] == "completed"
    assert res["rowCount"] == 4
    assert res["columnCount"] == 3
    assert res["fileType"] == "xlsx"

def test_reject_unsupported_file_format(client: TestClient):
    """
    Test that unsupported formats (e.g. JSON, PDF, TXT) are rejected with 400 Bad Request
    """
    files = {
        "file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")
    }
    response = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-1"})
    assert response.status_code == 400
    err_msg = response.json()["error"]["message"]
    assert "Only CSV, XLS, and XLSX are supported" in err_msg

def test_reject_empty_file(client: TestClient):
    """
    Test that empty file is rejected with 400 Bad Request
    """
    files = {
        "file": ("empty.csv", io.BytesIO(b""), "text/csv")
    }
    response = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "proj-1"})
    assert response.status_code == 400
    assert "empty" in response.json()["error"]["message"].lower()

def test_download_dataset_stream(client: TestClient):
    """
    Test downloading raw dataset binary stream
    """
    csv_bytes = b"id,val\n1,100\n2,200\n"
    files = {
        "file": ("raw_data.csv", io.BytesIO(csv_bytes), "text/csv")
    }
    upload_res = client.post("/api/v1/datasets/upload", files=files, data={"projectId": "p1"})
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    download_res = client.get(f"/api/v1/datasets/{dataset_id}/download")
    assert download_res.status_code == 200
    assert download_res.content == csv_bytes
    assert "attachment" in download_res.headers.get("content-disposition", "")
