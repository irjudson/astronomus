"""Integration tests for telescope API endpoints."""

import pytest

pytestmark = pytest.mark.integration


def test_progress_includes_active_plan_id(client):
    """GET /api/telescope/progress response includes active_plan_id field."""
    resp = client.get("/api/telescope/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_plan_id" in data
