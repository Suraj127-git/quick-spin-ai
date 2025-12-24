"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient) -> None:
    """
    Test health check endpoint.

    Args:
        test_client: FastAPI test client
    """
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "quickspin-ai"


def test_root_endpoint(test_client: TestClient) -> None:
    """
    Test root endpoint.

    Args:
        test_client: FastAPI test client
    """
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "QuickSpin AI"
    assert "version" in data
    assert "docs" in data
