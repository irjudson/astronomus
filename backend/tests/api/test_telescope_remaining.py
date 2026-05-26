"""Tests for uncovered telescope API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api import telescope as telescope_module
from app.clients.seestar_client import SeestarClient, SeestarState, SeestarStatus
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_seestar_client():
    client = AsyncMock(spec=SeestarClient)
    client.connected = True
    client.host = "192.168.2.47"
    client.port = 4700
    client._host = "192.168.2.47"
    client.status = SeestarStatus(
        connected=True,
        state=SeestarState.CONNECTED,
        firmware_version="5.50",
    )
    client.park = AsyncMock(return_value=True)
    client.stop_slew = AsyncMock(return_value=True)
    client.move_scope = AsyncMock(return_value=True)
    client.goto_target = AsyncMock(return_value=True)
    client.move_to_horizon = AsyncMock(return_value=True)
    client.start_imaging = AsyncMock(return_value=True)
    client.stop_imaging = AsyncMock(return_value=True)
    client.start_record_avi = AsyncMock(return_value=True)
    client.stop_record_avi = AsyncMock(return_value=True)
    client.start_polar_align = AsyncMock(return_value=True)
    client.stop_polar_align = AsyncMock(return_value=True)
    client.pause_polar_align = AsyncMock(return_value=True)
    client.start_preview = AsyncMock(return_value=True)
    client.get_live_preview = AsyncMock(return_value=b"\xff\xd8\xff" + b"\x00" * 100)
    client.get_current_coordinates = AsyncMock(return_value={"ra": 1.5, "dec": 30.0})
    client.get_app_state = AsyncMock(return_value={"stage": "Idle"})
    client.check_stacking_complete = AsyncMock(return_value=False)
    client.start_view_plan = AsyncMock(return_value=True)
    client.stop_view_plan = AsyncMock(return_value=True)
    client.get_view_plan_state = AsyncMock(return_value={"state": "idle"})
    client.get_plate_solve_result = AsyncMock(return_value={"ra": 1.5, "dec": 30.0})
    client.get_field_annotations = AsyncMock(return_value={"annotations": []})
    client.start_track_object = AsyncMock(return_value=True)
    client.stop_track_object = AsyncMock(return_value=True)
    client.start_annotate = AsyncMock(return_value=True)
    client.stop_annotate = AsyncMock(return_value=True)
    client._send_command = AsyncMock(return_value={"result": 0})
    return client


@pytest.fixture
def connected_client(mock_seestar_client):
    old = telescope_module.seestar_client
    telescope_module.seestar_client = mock_seestar_client
    yield mock_seestar_client
    telescope_module.seestar_client = old


@pytest.fixture
def disconnected_client():
    old = telescope_module.seestar_client
    telescope_module.seestar_client = None
    yield
    telescope_module.seestar_client = old


# ============================================================================
# POST /api/telescope/unpark
# ============================================================================

class TestUnparkTelescope:
    def test_unpark_success(self, client, connected_client):
        response = client.post("/api/telescope/unpark")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        connected_client.move_to_horizon.assert_called_once_with(azimuth=180.0, altitude=45.0)

    def test_unpark_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/unpark")
        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()

    def test_unpark_failure(self, client, connected_client):
        connected_client.move_to_horizon.return_value = False
        response = client.post("/api/telescope/unpark")
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ============================================================================
# POST /api/telescope/switch-mode
# ============================================================================

class TestSwitchMode:
    def test_switch_to_equatorial(self, client, connected_client):
        response = client.post("/api/telescope/switch-mode", json={"mode": "equatorial"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "equatorial" in data["message"].lower()

    def test_switch_to_altaz(self, client, connected_client):
        response = client.post("/api/telescope/switch-mode", json={"mode": "altaz"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_switch_invalid_mode(self, client, connected_client):
        response = client.post("/api/telescope/switch-mode", json={"mode": "invalid"})
        assert response.status_code == 400

    def test_switch_mode_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/switch-mode", json={"mode": "altaz"})
        assert response.status_code == 400


# ============================================================================
# POST /api/telescope/move
# ============================================================================

class TestMoveTelescope:
    def test_move_up(self, client, connected_client):
        response = client.post("/api/telescope/move", json={"action": "up"})
        assert response.status_code == 200
        assert response.json()["status"] == "moving"

    def test_move_stop(self, client, connected_client):
        connected_client.move_scope.return_value = True
        response = client.post("/api/telescope/move", json={"action": "stop"})
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

    def test_move_missing_action(self, client, connected_client):
        response = client.post("/api/telescope/move", json={})
        assert response.status_code == 400

    def test_move_invalid_action(self, client, connected_client):
        response = client.post("/api/telescope/move", json={"action": "diagonal"})
        assert response.status_code == 400

    def test_move_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/move", json={"action": "up"})
        assert response.status_code == 400

    def test_move_failure(self, client, connected_client):
        connected_client.move_scope.return_value = False
        response = client.post("/api/telescope/move", json={"action": "up"})
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ============================================================================
# POST /api/telescope/goto
# ============================================================================

class TestGotoCoordinates:
    def test_goto_success(self, client, connected_client):
        response = client.post("/api/telescope/goto", json={"ra": 1.5, "dec": 30.0, "target_name": "M31"})
        assert response.status_code == 200
        assert response.json()["status"] == "slewing"

    def test_goto_missing_coords(self, client, connected_client):
        response = client.post("/api/telescope/goto", json={"target_name": "M31"})
        assert response.status_code == 400

    def test_goto_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/goto", json={"ra": 1.5, "dec": 30.0})
        assert response.status_code == 400

    def test_goto_failure(self, client, connected_client):
        connected_client.goto_target.return_value = False
        response = client.post("/api/telescope/goto", json={"ra": 1.5, "dec": 30.0})
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ============================================================================
# POST /api/telescope/stop-slew
# ============================================================================

class TestStopSlew:
    def test_stop_slew_success(self, client, connected_client):
        response = client.post("/api/telescope/stop-slew")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

    def test_stop_slew_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/stop-slew")
        assert response.status_code == 400

    def test_stop_slew_failure(self, client, connected_client):
        connected_client.stop_slew.return_value = False
        response = client.post("/api/telescope/stop-slew")
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ============================================================================
# POST /api/telescope/polar-align/*
# ============================================================================

class TestPolarAlign:
    def test_start_polar_align_success(self, client, connected_client):
        response = client.post("/api/telescope/polar-align/start")
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_start_polar_align_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/polar-align/start")
        assert response.status_code == 400

    def test_stop_polar_align_success(self, client, connected_client):
        response = client.post("/api/telescope/polar-align/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

    def test_pause_polar_align_success(self, client, connected_client):
        response = client.post("/api/telescope/polar-align/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

    def test_pause_polar_align_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/polar-align/pause")
        assert response.status_code == 400


# ============================================================================
# POST /api/telescope/start-imaging / stop-imaging
# ============================================================================

class TestImaging:
    def test_start_imaging_success(self, client, connected_client):
        response = client.post("/api/telescope/start-imaging", json={"restart": True})
        assert response.status_code == 200
        assert response.json()["status"] == "imaging"

    def test_start_imaging_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/start-imaging", json={"restart": True})
        assert response.status_code == 400

    def test_start_imaging_failure(self, client, connected_client):
        connected_client.start_imaging.return_value = False
        response = client.post("/api/telescope/start-imaging", json={"restart": True})
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_stop_imaging_success(self, client, connected_client):
        response = client.post("/api/telescope/stop-imaging")
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"

    def test_stop_imaging_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/stop-imaging")
        assert response.status_code == 400


# ============================================================================
# POST /api/telescope/recording/*
# ============================================================================

class TestRecording:
    def test_start_recording_success(self, client, connected_client):
        response = client.post("/api/telescope/recording/start", json={"filename": "test.avi"})
        assert response.status_code == 200
        assert response.json()["status"] == "recording_started"

    def test_start_recording_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/recording/start", json={})
        assert response.status_code == 400

    def test_stop_recording_success(self, client, connected_client):
        response = client.post("/api/telescope/recording/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "recording_stopped"

    def test_stop_recording_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/recording/stop")
        assert response.status_code == 400


# ============================================================================
# GET /api/telescope/coordinates
# ============================================================================

class TestGetCoordinates:
    def test_get_coordinates_success(self, client, connected_client):
        response = client.get("/api/telescope/coordinates")
        assert response.status_code == 200
        data = response.json()
        assert "ra_hours" in data
        assert "dec_degrees" in data
        assert data["ra_hours"] == 1.5
        assert data["dec_degrees"] == 30.0

    def test_get_coordinates_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/coordinates")
        assert response.status_code == 400


# ============================================================================
# GET /api/telescope/app-state
# ============================================================================

class TestAppState:
    def test_get_app_state_success(self, client, connected_client):
        response = client.get("/api/telescope/app-state")
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "Idle"

    def test_get_app_state_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/app-state")
        assert response.status_code == 400


# ============================================================================
# GET /api/telescope/stacking-status
# ============================================================================

class TestStackingStatus:
    def test_stacking_status_not_complete(self, client, connected_client):
        response = client.get("/api/telescope/stacking-status")
        assert response.status_code == 200
        assert response.json()["is_stacked"] is False

    def test_stacking_status_complete(self, client, connected_client):
        connected_client.check_stacking_complete.return_value = True
        response = client.get("/api/telescope/stacking-status")
        assert response.status_code == 200
        assert response.json()["is_stacked"] is True

    def test_stacking_status_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/stacking-status")
        assert response.status_code == 400


# ============================================================================
# POST /api/telescope/plan/start, stop; GET /api/telescope/plan/state
# ============================================================================

class TestViewPlan:
    def test_start_view_plan_success(self, client, connected_client):
        response = client.post("/api/telescope/plan/start", json={"targets": []})
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_start_view_plan_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/plan/start", json={"targets": []})
        assert response.status_code == 400

    def test_stop_view_plan_success(self, client, connected_client):
        response = client.post("/api/telescope/plan/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_view_plan_state_success(self, client, connected_client):
        response = client.get("/api/telescope/plan/state")
        assert response.status_code == 200
        assert response.json()["state"] == "idle"

    def test_get_view_plan_state_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/plan/state")
        assert response.status_code == 400


# ============================================================================
# GET /api/telescope/solve-result; GET /api/telescope/field-annotations
# ============================================================================

class TestPlateSolveAndAnnotations:
    def test_get_solve_result_success(self, client, connected_client):
        response = client.get("/api/telescope/solve-result")
        assert response.status_code == 200

    def test_get_solve_result_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/solve-result")
        assert response.status_code == 400

    def test_get_field_annotations_success(self, client, connected_client):
        response = client.get("/api/telescope/field-annotations")
        assert response.status_code == 200

    def test_get_field_annotations_not_connected(self, client, disconnected_client):
        response = client.get("/api/telescope/field-annotations")
        assert response.status_code == 400


# ============================================================================
# POST /api/telescope/tracking/start, stop (use get_current_telescope dep)
# ============================================================================

class TestTracking:
    def test_start_tracking_success(self, client, connected_client):
        old = telescope_module.seestar_client
        telescope_module.seestar_client = connected_client
        try:
            response = client.post(
                "/api/telescope/tracking/start",
                json={"object_type": "satellite", "object_id": "ISS"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "tracking_started"
            assert data["object_type"] == "satellite"
        finally:
            telescope_module.seestar_client = old

    def test_stop_tracking_success(self, client, connected_client):
        old = telescope_module.seestar_client
        telescope_module.seestar_client = connected_client
        try:
            response = client.post("/api/telescope/tracking/stop")
            assert response.status_code == 200
            assert response.json()["status"] == "tracking_stopped"
        finally:
            telescope_module.seestar_client = old

    def test_stop_tracking_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/tracking/stop")
        assert response.status_code == 503


# ============================================================================
# POST /api/telescope/start-preview
# ============================================================================

class TestStartPreview:
    def test_start_preview_default_mode(self, client, connected_client):
        response = client.post("/api/telescope/start-preview", json={"mode": "scenery"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "preview_started"
        assert data["mode"] == "scenery"

    def test_start_preview_moon_mode(self, client, connected_client):
        response = client.post("/api/telescope/start-preview", json={"mode": "moon"})
        assert response.status_code == 200
        assert response.json()["mode"] == "moon"

    def test_start_preview_invalid_mode(self, client, connected_client):
        response = client.post("/api/telescope/start-preview", json={"mode": "invalid"})
        assert response.status_code == 400

    def test_start_preview_not_connected(self, client, disconnected_client):
        response = client.post("/api/telescope/start-preview", json={"mode": "scenery"})
        assert response.status_code == 400

    def test_start_preview_failure(self, client, connected_client):
        connected_client.start_preview.return_value = False
        response = client.post("/api/telescope/start-preview", json={"mode": "scenery"})
        assert response.status_code == 200
        assert response.json()["status"] == "error"


# ============================================================================
# GET /api/telescope/preview (no connection required - just checks /fits)
# ============================================================================

class TestTelescopePreview:
    def test_preview_no_fits_dir(self, client):
        with patch("app.api.telescope.Path") as MockPath:
            mock_fits = MagicMock()
            mock_fits.exists.return_value = False
            MockPath.return_value = mock_fits
            with patch("os.getenv", return_value="/nonexistent"):
                response = client.get("/api/telescope/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


# ============================================================================
# POST /api/telescope/connect (device_id path)
# ============================================================================

class TestConnectWithDeviceId:
    def test_connect_no_host_no_device_id(self, client):
        response = client.post("/api/telescope/connect", json={})
        assert response.status_code == 400
        assert "Must provide" in response.json()["detail"]

    def test_connect_device_id_not_found(self, client):
        from app.database import get_db
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db
        response = client.post("/api/telescope/connect", json={"device_id": 999})
        app.dependency_overrides.clear()
        assert response.status_code in (404, 500)
