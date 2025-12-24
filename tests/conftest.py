"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def test_client() -> TestClient:
    """
    Get FastAPI test client.

    Returns:
        TestClient instance
    """
    return TestClient(app)


@pytest.fixture
def mock_user_token() -> str:
    """
    Get mock user JWT token.

    Returns:
        Mock JWT token string
    """
    return "mock_jwt_token_for_testing"


@pytest.fixture
def mock_user_context() -> dict:
    """
    Get mock user context.

    Returns:
        Dictionary with user context
    """
    return {
        "user_id": "user_test_123",
        "email": "test@example.com",
        "organization_id": "org_test_456",
        "tier": "pro",
        "roles": ["member"],
    }
