"""Test Vue.js app serving."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def simple_client():
    """Test client without database dependency."""
    from app.main import app

    return TestClient(app)


def test_vue_app_index_served(simple_client: TestClient):
    """Test that Vue app index.html is served at /app route."""
    response = simple_client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_vue_app_catches_all_routes(simple_client: TestClient):
    """Test that Vue app handles SPA routing."""
    # These should all return the Vue app index.html
    for path in ["/app/catalog", "/app/plan", "/app/execute"]:
        response = simple_client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


def test_legacy_frontend_still_works(simple_client: TestClient):
    """Test that legacy frontend is still accessible."""
    response = simple_client.get("/")
    assert response.status_code == 200
