"""Integration tests for comets API endpoints."""

import pytest

pytestmark = pytest.mark.integration


def test_visible_tonight_comets_endpoint(client):
    """GET /api/comets/visible-tonight returns a list."""
    resp = client.get("/api/comets/visible-tonight")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_visible_tonight_with_params(client):
    """GET /api/comets/visible-tonight accepts query params."""
    resp = client.get("/api/comets/visible-tonight", params={"min_altitude": 15, "max_magnitude": 10})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
