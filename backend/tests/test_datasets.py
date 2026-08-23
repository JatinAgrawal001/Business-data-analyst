import io
import uuid
from fastapi.testclient import TestClient

def test_list_datasets(client: TestClient):
    """
    Test GET /api/v1/datasets returns a list
    """
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_upload_dataset(client: TestClient):
    """
    Test POST /api/v1/datasets/upload with CSV content
    """
    proj_id = str(uuid.uuid4())
    csv_content = b"date,revenue,users\n2026-01-01,1000,50\n2026-01-02,1200,65\n"
    files = {
        "file": ("metrics.csv", io.BytesIO(csv_content), "text/csv")
    }
    data = {
        "projectId": proj_id,
        "name": "Q1 Metrics"
    }
    response = client.post("/api/v1/datasets/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "Q1 Metrics"
    assert res_data["status"] == "completed"
    assert res_data["rowCount"] == 2
    assert len(res_data["columns"]) == 3
    assert res_data["storageBucket"] == "datasets"
    assert "storagePath" in res_data
    assert proj_id in res_data["storagePath"]

def test_options_datasets_preflight(client: TestClient):
    """
    Test OPTIONS /api/v1/datasets CORS preflight returns 200 OK with proper headers
    """
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization, content-type"
    }
    response = client.options("/api/v1/datasets", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "GET" in response.headers.get("access-control-allow-methods", "")
