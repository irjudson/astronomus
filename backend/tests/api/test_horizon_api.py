"""Tests for horizon scan API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/horizon/scan  (start scan)
# ---------------------------------------------------------------------------


def test_start_horizon_scan_returns_scan_id():
    with patch("app.api.horizon.asyncio.create_task"):
        client = TestClient(app)
        response = client.post("/api/horizon/scan")
    assert response.status_code == 200
    data = response.json()
    assert "scan_id" in data
    assert len(data["scan_id"]) == 8
    assert data["message"] == "Horizon scan started"


def test_start_horizon_scan_with_custom_params():
    with patch("app.api.horizon.asyncio.create_task"):
        client = TestClient(app)
        response = client.post(
            "/api/horizon/scan?telescope_host=10.0.0.1&telescope_port=4800&az_step=10&scan_mode=full"
        )
    assert response.status_code == 200
    assert "scan_id" in response.json()


def test_start_horizon_scan_initializes_scan_state():
    """Scan entry should be added to _scans immediately (before task runs)."""
    import app.api.horizon as horizon_module

    initial_count = len(horizon_module._scans)

    with patch("app.api.horizon.asyncio.create_task"):
        client = TestClient(app)
        response = client.post("/api/horizon/scan")

    assert len(horizon_module._scans) == initial_count + 1
    scan_id = response.json()["scan_id"]
    assert horizon_module._scans[scan_id]["status"] == "scanning"
    assert horizon_module._scans[scan_id]["progress"] == 0

    # Cleanup
    del horizon_module._scans[scan_id]


# ---------------------------------------------------------------------------
# GET /api/horizon/scan/{scan_id}/status
# ---------------------------------------------------------------------------


def test_get_scan_status_found():
    import app.api.horizon as horizon_module

    scan_id = "abc12345"
    horizon_module._scans[scan_id] = {
        "status": "scanning",
        "progress": 50,
        "current_az": 180,
        "points": [{"az": 90, "alt": 10}],
    }

    client = TestClient(app)
    response = client.get(f"/api/horizon/scan/{scan_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scanning"
    assert data["progress"] == 50
    assert data["current_az"] == 180

    del horizon_module._scans[scan_id]


def test_get_scan_status_completed():
    import app.api.horizon as horizon_module

    scan_id = "done1234"
    horizon_module._scans[scan_id] = {
        "status": "complete",
        "progress": 100,
        "current_az": 360,
        "points": [{"az": 0, "alt": 5}, {"az": 90, "alt": 12}],
    }

    client = TestClient(app)
    response = client.get(f"/api/horizon/scan/{scan_id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert len(response.json()["points"]) == 2

    del horizon_module._scans[scan_id]


def test_get_scan_status_not_found():
    client = TestClient(app)
    response = client.get("/api/horizon/scan/nonexistent/status")
    assert response.status_code == 404
    assert "Scan not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /api/horizon/scan/{scan_id}
# ---------------------------------------------------------------------------


def test_clear_scan_existing():
    import app.api.horizon as horizon_module

    scan_id = "del12345"
    horizon_module._scans[scan_id] = {"status": "complete", "progress": 100, "points": [], "current_az": 0}

    client = TestClient(app)
    response = client.delete(f"/api/horizon/scan/{scan_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == scan_id
    assert scan_id not in horizon_module._scans


def test_clear_scan_nonexistent_is_idempotent():
    """DELETE on a nonexistent scan_id should still return 200 (pop with default)."""
    client = TestClient(app)
    response = client.delete("/api/horizon/scan/does_not_exist")
    assert response.status_code == 200
    assert response.json()["deleted"] == "does_not_exist"
