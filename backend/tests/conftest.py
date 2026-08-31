import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    TestClient fixture for executing synchronous API requests against the FastAPI app.
    """
    with TestClient(app) as test_client:
        yield test_client
