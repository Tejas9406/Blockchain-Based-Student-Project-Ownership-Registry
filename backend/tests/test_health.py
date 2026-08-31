from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    """
    Test that GET /health returns HTTP 200 and standard health payload.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"
    assert "environment" in data
    assert "version" in data
    assert "database" in data
    assert isinstance(data["database"]["connected"], bool)


def test_versioned_health_endpoint(client: TestClient):
    """
    Test that GET /api/v1/health returns HTTP 200 and identical health payload.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"


def test_openapi_docs_endpoint(client: TestClient):
    """
    Test that OpenAPI schema is properly generated and accessible.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Student Project Ownership Registry API"
    assert "/health" in data["paths"]
