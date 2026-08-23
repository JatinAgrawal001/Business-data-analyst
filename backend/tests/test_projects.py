from fastapi.testclient import TestClient

def test_list_projects(client: TestClient):
    """
    Test GET /api/v1/projects returns a list
    """
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_project(client: TestClient):
    """
    Test POST /api/v1/projects creates a project
    """
    payload = {
        "name": "Q3 Revenue Analytics",
        "description": "Cross-channel revenue performance tracking",
        "tags": ["Revenue", "Q3"],
        "status": "active"
    }
    response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Q3 Revenue Analytics"
    assert data["status"] == "active"
    assert "id" in data
    assert "createdAt" in data
