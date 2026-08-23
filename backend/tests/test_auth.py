from fastapi.testclient import TestClient

def test_get_current_user_profile(client: TestClient):
    """
    Test GET /api/v1/auth/me returns valid UserProfileResponse
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "email" in data
    assert "plan" in data
    assert "preferences" in data
    assert data["preferences"]["theme"] in ["dark", "light", "system"]
