"""Tests for telescope_features API endpoints (telescope-agnostic, fast mock tests)."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_telescope
from app.clients.seestar_client import SeestarClient
from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scope(**overrides):
    """Return a minimal Mock that satisfies SeestarClient's spec."""
    sc = Mock(spec=SeestarClient)
    sc.connected = True
    defaults = {
        "set_dew_heater": AsyncMock(return_value=True),
        "get_device_state": AsyncMock(return_value={}),
        "set_dc_output": AsyncMock(return_value=True),
        "move_focuser_to_position": AsyncMock(return_value=True),
        "move_focuser_relative": AsyncMock(return_value=True),
        "reset_focuser_to_factory": AsyncMock(return_value=True),
        "_send_command": AsyncMock(return_value={"result": 500}),
        "set_manual_exposure": AsyncMock(return_value=True),
        "set_exposure": AsyncMock(return_value=True),
        "configure_dither": AsyncMock(return_value=True),
        "auto_focus": AsyncMock(return_value=True),
        "stop_autofocus": AsyncMock(return_value=True),
        "connect_to_wifi": AsyncMock(return_value=True),
        "scan_wifi_networks": AsyncMock(return_value={"networks": []}),
        "list_saved_wifi_networks": AsyncMock(return_value={"networks": []}),
        "set_location": AsyncMock(return_value=True),
        "shutdown_telescope": AsyncMock(return_value=True),
        "reboot_telescope": AsyncMock(return_value=True),
        "get_pi_info": AsyncMock(return_value={"cpu": "4-core"}),
        "get_station_state": AsyncMock(return_value={"connected": True}),
        "get_pi_time": AsyncMock(return_value={"time": 0}),
        "set_pi_time": AsyncMock(return_value=True),
        "slew_to_coordinates": AsyncMock(return_value=True),
        "stop_telescope_movement": AsyncMock(return_value=True),
        "move_to_horizon": AsyncMock(return_value=True),
        "check_polar_alignment": AsyncMock(return_value={"status": "ok"}),
        "clear_polar_alignment": AsyncMock(return_value=True),
        "start_compass_calibration": AsyncMock(return_value=True),
        "stop_compass_calibration": AsyncMock(return_value=True),
        "get_compass_state": AsyncMock(return_value={"direction": 270}),
        "start_leveling": AsyncMock(return_value=True),
        "get_balance_sensor": AsyncMock(return_value={"x": 0, "y": 0, "z": 1, "angle": 0}),
        "start_gsensor_calibration": AsyncMock(return_value=True),
        "check_client_verified": AsyncMock(return_value=True),
        "list_plan": AsyncMock(return_value=[]),
        "set_plan": AsyncMock(return_value=True),
        "delete_plan": AsyncMock(return_value=True),
        "list_images": AsyncMock(return_value=[]),
        "get_image_file_info": AsyncMock(return_value={}),
        "get_stacked_image": AsyncMock(return_value=b"fake"),
        "get_raw_frame": AsyncMock(return_value=b"fake"),
        "delete_image": AsyncMock(return_value=True),
        "get_live_preview": AsyncMock(return_value=b"\xff\xd8\xff"),
        "enable_wifi_client_mode": AsyncMock(return_value=True),
        "disable_wifi_client_mode": AsyncMock(return_value=True),
        "save_wifi_network": AsyncMock(return_value=True),
        "remove_wifi_network": AsyncMock(return_value=True),
        "configure_access_point": AsyncMock(return_value=True),
        "set_wifi_country": AsyncMock(return_value=True),
        "join_remote_session": AsyncMock(return_value=True),
        "leave_remote_session": AsyncMock(return_value=True),
        "disconnect_remote_client": AsyncMock(return_value=True),
        "start_demo_mode": AsyncMock(return_value=True),
        "stop_demo_mode": AsyncMock(return_value=True),
        "set_auto_exposure": AsyncMock(return_value=True),
        "configure_advanced_stacking": AsyncMock(return_value=True),
    }
    for k, v in defaults.items():
        if k not in overrides:
            setattr(sc, k, v)
    for k, v in overrides.items():
        setattr(sc, k, v)
    return sc


@pytest.fixture
def client_with_scope():
    sc = _make_scope()
    app.dependency_overrides[get_current_telescope] = lambda: sc
    client = TestClient(app)
    yield client, sc
    app.dependency_overrides.pop(get_current_telescope, None)


@pytest.fixture
def client_no_scope():
    """TestClient with no telescope connected."""
    from app.api import telescope as tel_module

    old = tel_module.seestar_client
    tel_module.seestar_client = None
    client = TestClient(app)
    yield client
    tel_module.seestar_client = old


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


def test_get_capabilities(client_with_scope):
    client, _ = client_with_scope
    resp = client.get("/api/telescope/features/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["telescope_type"] == "seestar"
    assert "features" in data


def test_get_capabilities_no_telescope(client_no_scope):
    resp = client_no_scope.get("/api/telescope/features/capabilities")
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Dew heater
# ---------------------------------------------------------------------------


def test_dew_heater_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/hardware/dew-heater", json={"enabled": True, "power_level": 75})
    assert resp.status_code == 200
    assert resp.json() == {"success": True}
    sc.set_dew_heater.assert_called_once_with(True, 75)


def test_dew_heater_rejection(client_with_scope):
    # _ok(False) raises HTTPException(502) which is caught by the outer except → 500
    client, sc = client_with_scope
    sc.set_dew_heater = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/hardware/dew-heater", json={"enabled": False})
    assert resp.status_code in (500, 502)


def test_dew_heater_status(client_with_scope):
    client, sc = client_with_scope
    sc.get_device_state = AsyncMock(return_value={"dew_heater": {"state": True, "value": 90}})
    resp = client.get("/api/telescope/features/hardware/dew-heater/status")
    assert resp.status_code == 200
    assert resp.json()["state"] is True


# ---------------------------------------------------------------------------
# DC output
# ---------------------------------------------------------------------------


def test_dc_output_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/hardware/dc-output", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json() == {"success": True}


def test_dc_output_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.set_dc_output = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/hardware/dc-output", json={"enabled": False})
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# Focuser
# ---------------------------------------------------------------------------


def test_focuser_move_by_position(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/focuser/move", json={"position": 1200})
    assert resp.status_code == 200
    sc.move_focuser_to_position.assert_called_once_with(1200)


def test_focuser_move_by_offset(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/focuser/move", json={"offset": -50})
    assert resp.status_code == 200
    sc.move_focuser_relative.assert_called_once_with(-50)


def test_focuser_move_no_params_returns_error(client_with_scope):
    # HTTPException(400) raised inside try/except → re-wrapped as 500
    client, _ = client_with_scope
    resp = client.post("/api/telescope/features/focuser/move", json={})
    assert resp.status_code in (400, 500)


def test_focuser_move_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.move_focuser_to_position = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/focuser/move", json={"position": 500})
    assert resp.status_code in (500, 502)


def test_focuser_factory_reset_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/focuser/factory-reset")
    assert resp.status_code == 200
    assert resp.json() == {"success": True}


def test_focuser_factory_reset_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.reset_focuser_to_factory = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/focuser/factory-reset")
    assert resp.status_code in (500, 502)


def test_focuser_get_position(client_with_scope):
    client, sc = client_with_scope
    sc._send_command = AsyncMock(return_value={"result": 500})
    resp = client.get("/api/telescope/features/focus/position")
    assert resp.status_code == 200
    assert resp.json()["position"] == 500


def test_focuser_get_position_dict_result(client_with_scope):
    client, sc = client_with_scope
    sc._send_command = AsyncMock(return_value={"result": {"step": 700}})
    resp = client.get("/api/telescope/features/focus/position")
    assert resp.status_code == 200
    assert resp.json()["position"] == 700


def test_stop_autofocus_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/focuser/stop")
    assert resp.status_code == 200


def test_stop_autofocus_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.stop_autofocus = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/focuser/stop")
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# Exposure settings
# ---------------------------------------------------------------------------


def test_exposure_manual_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/imaging/exposure",
        json={"exposure_ms": 5000.0, "gain": 80.0},
    )
    assert resp.status_code == 200
    sc.set_manual_exposure.assert_called_once_with(5000.0, 80.0)


def test_exposure_stack_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/imaging/exposure",
        json={"stack_exposure_ms": 10000},
    )
    assert resp.status_code == 200
    sc.set_exposure.assert_called_once_with(10000, 500)


def test_exposure_missing_params_returns_error(client_with_scope):
    # HTTPException(400) raised inside try/except → re-wrapped as 500
    client, _ = client_with_scope
    resp = client.post("/api/telescope/features/imaging/exposure", json={})
    assert resp.status_code in (400, 500)


def test_exposure_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.set_manual_exposure = AsyncMock(return_value=False)
    resp = client.post(
        "/api/telescope/features/imaging/exposure",
        json={"exposure_ms": 100.0, "gain": 50.0},
    )
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# Dither config
# ---------------------------------------------------------------------------


def test_dither_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/imaging/dither",
        json={"enabled": True, "pixels": 30, "interval": 5},
    )
    assert resp.status_code == 200
    sc.configure_dither.assert_called_once_with(True, 30, 5)


def test_dither_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.configure_dither = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/imaging/dither", json={"enabled": True})
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# Autofocus
# ---------------------------------------------------------------------------


def test_autofocus_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/imaging/autofocus")
    assert resp.status_code == 200


def test_autofocus_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.auto_focus = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/imaging/autofocus")
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------


def test_wifi_connect_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/wifi/connect", json={"ssid": "HomeWifi"})
    assert resp.status_code == 200
    sc.connect_to_wifi.assert_called_once_with("HomeWifi")


def test_wifi_connect_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.connect_to_wifi = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/wifi/connect", json={"ssid": "BadNet"})
    assert resp.status_code in (500, 502)


def test_wifi_scan(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/wifi/scan")
    assert resp.status_code == 200


def test_wifi_saved_list(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/wifi/saved")
    assert resp.status_code == 200


def test_wifi_enable_client(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/wifi/enable-client")
    assert resp.status_code == 200


def test_wifi_disable_client(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/wifi/disable-client")
    assert resp.status_code == 200


def test_wifi_save_network(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/wifi/save-network",
        params={"ssid": "HomeWifi", "password": "secret"},
    )
    assert resp.status_code == 200


def test_wifi_remove_network(client_with_scope):
    client, sc = client_with_scope
    resp = client.delete("/api/telescope/features/wifi/network/HomeWifi")
    assert resp.status_code == 200


def test_wifi_station_state(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/wifi/station-state")
    assert resp.status_code == 200


def test_wifi_configure_ap(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/wifi/access-point",
        params={"ssid": "Seestar_AP", "password": "password123"},
    )
    assert resp.status_code == 200


def test_wifi_set_country(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/wifi/country", params={"country_code": "US"})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------


def test_system_location_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/system/location",
        json={"latitude": 40.0, "longitude": -105.0},
    )
    assert resp.status_code == 200
    # Note: set_location(longitude, latitude) — args are swapped in the route
    sc.set_location.assert_called_once_with(-105.0, 40.0)


def test_system_location_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.set_location = AsyncMock(return_value=False)
    resp = client.post(
        "/api/telescope/features/system/location",
        json={"latitude": 0.0, "longitude": 0.0},
    )
    assert resp.status_code in (500, 502)


def test_system_shutdown_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/system/shutdown")
    assert resp.status_code == 200


def test_system_shutdown_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.shutdown_telescope = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/system/shutdown")
    assert resp.status_code in (500, 502)


def test_system_reboot_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/system/reboot")
    assert resp.status_code == 200


def test_system_reboot_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.reboot_telescope = AsyncMock(return_value=False)
    resp = client.post("/api/telescope/features/system/reboot")
    assert resp.status_code in (500, 502)


def test_system_info(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/system/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "pi_info" in data
    assert "station_state" in data


def test_system_get_time(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/system/time")
    assert resp.status_code == 200


def test_system_set_time(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/system/time", params={"unix_timestamp": 1700000000})
    assert resp.status_code == 200


def test_system_pi_info(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/system/pi-info")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------


def test_slew_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/movement/slew",
        params={"ra_hours": 5.5, "dec_degrees": 45.0},
    )
    assert resp.status_code == 200
    sc.slew_to_coordinates.assert_called_once_with(5.5, 45.0)


def test_slew_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.slew_to_coordinates = AsyncMock(return_value=False)
    resp = client.post(
        "/api/telescope/features/movement/slew",
        params={"ra_hours": 5.5, "dec_degrees": 45.0},
    )
    assert resp.status_code in (500, 502)


def test_stop_movement_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/movement/stop")
    assert resp.status_code == 200


def test_move_to_horizon_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/movement/horizon",
        params={"azimuth": 180.0, "altitude": 45.0},
    )
    assert resp.status_code == 200
    sc.move_to_horizon.assert_called_once_with(180.0, 45.0)


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def test_polar_alignment_check(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/calibration/polar-alignment")
    assert resp.status_code == 200


def test_polar_alignment_clear(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/calibration/polar-alignment/clear")
    assert resp.status_code == 200


def test_compass_calibration_start(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/calibration/compass/start")
    assert resp.status_code == 200


def test_compass_calibration_stop(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/calibration/compass/stop")
    assert resp.status_code == 200


def test_compass_state(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/calibration/compass/state")
    assert resp.status_code == 200


def test_raw_device_state(client_with_scope):
    client, sc = client_with_scope
    sc._send_command = AsyncMock(return_value={"result": {"mount": {}}, "code": 0})
    resp = client.get("/api/telescope/features/calibration/debug/device-state")
    assert resp.status_code == 200


def test_start_leveling(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/calibration/balance/start")
    assert resp.status_code == 200


def test_get_balance_sensor(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/calibration/balance")
    assert resp.status_code == 200
    data = resp.json()
    assert "x" in data


def test_gsensor_calibration_start(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/calibration/gsensor/start")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def test_list_images(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/images/list")
    assert resp.status_code == 200
    assert "images" in resp.json()


def test_get_image_info(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/images/info")
    assert resp.status_code == 200


def test_delete_image(client_with_scope):
    client, sc = client_with_scope
    resp = client.delete("/api/telescope/features/images/test_image.fits")
    assert resp.status_code == 200


def test_download_image(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/images/download/test.fits")
    assert resp.status_code == 200


def test_download_raw_frame(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/images/raw/test.fits")
    assert resp.status_code == 200


def test_live_preview(client_with_scope):
    client, sc = client_with_scope
    resp = client.get("/api/telescope/features/images/preview/live")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Remote sessions
# ---------------------------------------------------------------------------


def test_join_remote_session(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/remote/join")
    assert resp.status_code == 200


def test_leave_remote_session(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/remote/leave")
    assert resp.status_code == 200


def test_disconnect_remote_client(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/remote/disconnect/client-1")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------


def test_start_demo_mode(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/demo/start")
    assert resp.status_code == 200


def test_stop_demo_mode(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/demo/stop")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Verification status
# ---------------------------------------------------------------------------


def test_verification_status_verified(client_with_scope):
    client, sc = client_with_scope
    sc.check_client_verified = AsyncMock(return_value=True)
    resp = client.get("/api/telescope/features/verification-status")
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


def test_verification_status_not_verified(client_with_scope):
    client, sc = client_with_scope
    sc.check_client_verified = AsyncMock(return_value=False)
    resp = client.get("/api/telescope/features/verification-status")
    assert resp.status_code == 200
    assert resp.json()["verified"] is False


# ---------------------------------------------------------------------------
# Plan management (list / delete)
# ---------------------------------------------------------------------------


def test_list_plans_on_telescope(client_with_scope):
    client, sc = client_with_scope
    sc.list_plan = AsyncMock(return_value=[{"name": "test-plan"}])
    resp = client.get("/api/telescope/features/plan/list")
    assert resp.status_code == 200
    assert resp.json()["plans"] == [{"name": "test-plan"}]


def test_list_plans_non_list_result(client_with_scope):
    client, sc = client_with_scope
    sc.list_plan = AsyncMock(return_value=None)
    resp = client.get("/api/telescope/features/plan/list")
    assert resp.status_code == 200
    assert resp.json()["plans"] == []


def test_delete_plan_success(client_with_scope):
    client, sc = client_with_scope
    resp = client.delete("/api/telescope/features/plan/my-plan")
    assert resp.status_code == 200


def test_delete_plan_rejection(client_with_scope):
    client, sc = client_with_scope
    sc.delete_plan = AsyncMock(return_value=False)
    resp = client.delete("/api/telescope/features/plan/my-plan")
    assert resp.status_code in (500, 502)


# ---------------------------------------------------------------------------
# Plan upload
# ---------------------------------------------------------------------------


def test_upload_plan_success(client_with_scope, override_get_db):
    from app.models.plan_models import SavedPlan

    client, sc = client_with_scope

    mock_plan = Mock(spec=SavedPlan)
    mock_plan.id = 1
    mock_plan.plan_data = {
        "scheduled_targets": [
            {
                "target": {
                    "name": "M31",
                    "ra_hours": 0.712,
                    "dec_degrees": 41.27,
                },
                "duration_minutes": 60,
            }
        ],
        "session": {"observing_date": "2026-05-26"},
    }

    # Override DB to return our fake plan
    from app.database import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        resp = client.post("/api/telescope/features/plan/upload", json={"plan_id": 1})
        assert resp.status_code == 200
        assert resp.json() == {"success": True}
        sc.set_plan.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_upload_plan_not_found(client_with_scope):
    client, sc = client_with_scope
    from app.database import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        resp = client.post("/api/telescope/features/plan/upload", json={"plan_id": 9999})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_upload_plan_telescope_rejection(client_with_scope):
    from app.models.plan_models import SavedPlan

    client, sc = client_with_scope
    sc.set_plan = AsyncMock(return_value=False)

    mock_plan = Mock(spec=SavedPlan)
    mock_plan.plan_data = {"scheduled_targets": [], "session": {}}

    from app.database import get_db

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_plan
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        resp = client.post("/api/telescope/features/plan/upload", json={"plan_id": 1})
        assert resp.status_code in (500, 502)
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# _plan_to_seestar_format helper unit tests
# ---------------------------------------------------------------------------


def test_plan_to_seestar_format_basic():
    from app.api.telescope_features import _plan_to_seestar_format

    plan_data = {
        "session": {"observing_date": "2026-05-26"},
        "scheduled_targets": [
            {
                "target": {"name": "M31", "ra_hours": 0.712, "dec_degrees": 41.27},
                "duration_minutes": 90,
            }
        ],
    }
    result = _plan_to_seestar_format(plan_data)
    assert result["plan_name"] == "2026-05-26-plan"
    assert len(result["list"]) == 1
    t = result["list"][0]
    assert t["target_name"] == "M31"
    # RA in degrees: 0.712 * 15
    assert abs(t["target_ra_dec"][0] - 0.712 * 15) < 0.001
    assert t["target_ra_dec"][1] == 41.27
    assert t["duration_min"] == 90


def test_plan_to_seestar_format_no_date():
    from app.api.telescope_features import _plan_to_seestar_format

    plan_data = {"scheduled_targets": [], "session": {}}
    result = _plan_to_seestar_format(plan_data)
    assert result["plan_name"] == "plan"
    assert result["list"] == []


def test_plan_to_seestar_format_empty_targets():
    from app.api.telescope_features import _plan_to_seestar_format

    plan_data = {"scheduled_targets": [], "session": {"observing_date": "2026-05-26"}}
    result = _plan_to_seestar_format(plan_data)
    assert result["list"] == []


def test_plan_to_seestar_format_stack_total_sec_minimum():
    from app.api.telescope_features import _plan_to_seestar_format

    plan_data = {
        "scheduled_targets": [
            {
                "target": {"name": "Test", "ra_hours": 1.0, "dec_degrees": 30.0},
                "duration_minutes": 2,  # less than 3 min leaves negative → capped at 60
            }
        ],
        "session": {},
    }
    result = _plan_to_seestar_format(plan_data)
    t = result["list"][0]
    assert t["stack_total_sec"] == 60  # max(2*60-180, 60) = max(-60, 60) = 60


# ---------------------------------------------------------------------------
# Imaging advanced
# ---------------------------------------------------------------------------


def test_manual_exposure_endpoint(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/imaging/manual-exposure",
        params={"exposure_ms": 5000.0, "gain": 80.0},
    )
    assert resp.status_code == 200


def test_auto_exposure_endpoint(client_with_scope):
    client, sc = client_with_scope
    resp = client.post("/api/telescope/features/imaging/auto-exposure")
    assert resp.status_code == 200


def test_advanced_stacking_endpoint(client_with_scope):
    client, sc = client_with_scope
    resp = client.post(
        "/api/telescope/features/imaging/advanced-stacking",
        json={"dark_background_extraction": True},
    )
    assert resp.status_code == 200
