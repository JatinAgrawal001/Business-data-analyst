from fastapi.testclient import TestClient

def test_health_check_endpoint(client: TestClient):
    """
    Test GET /api/v1/health returns 200 and valid schema
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert data["details"]["api_version"] == "v1"
    
    # Check headers
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers

def test_root_endpoint(client: TestClient):
    """
    Test root endpoint / returns 200 and links
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["health"] == "/api/v1/health"
    assert data["docs"] == "/docs"

def test_not_found_error_format(client: TestClient):
    """
    Test 404 response uses standardized error format
    """
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"

def test_cors_headers(client: TestClient):
    """
    Test CORS headers are present on preflight / requests
    """
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    # 200 OK or appropriate CORS preflight response
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
