"""Tests for comets API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import CometEphemeris, CometTarget, CometVisibility
from app.models.models import OrbitalElements


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _orbital_elements():
    return OrbitalElements(
        epoch_jd=2451545.0,
        perihelion_distance_au=0.5,
        eccentricity=0.9,
        inclination_deg=45.0,
        arg_perihelion_deg=100.0,
        ascending_node_deg=200.0,
        perihelion_time_jd=2451600.0,
    )


def _make_comet(designation="C/2020 F3", name="NEOWISE"):
    return CometTarget(
        designation=designation,
        name=name,
        orbital_elements=_orbital_elements(),
        current_magnitude=5.0,
        comet_type="long-period",
    )


def _make_ephemeris(designation="C/2020 F3"):
    return CometEphemeris(
        designation=designation,
        date_utc=datetime(2026, 1, 1, 0, 0, 0),
        date_jd=2461041.5,
        ra_hours=3.5,
        dec_degrees=15.0,
        geo_distance_au=0.8,
        helio_distance_au=1.2,
        magnitude=5.0,
    )


def _make_visibility(comet=None, ephemeris=None):
    comet = comet or _make_comet()
    ephemeris = ephemeris or _make_ephemeris()
    return CometVisibility(
        comet=comet,
        ephemeris=ephemeris,
        altitude_deg=40.0,
        azimuth_deg=220.0,
        is_visible=True,
        is_dark_enough=True,
        elongation_ok=True,
        recommended=True,
    )


# ---------------------------------------------------------------------------
# GET /api/comets/
# ---------------------------------------------------------------------------


def test_list_comets_returns_list():
    mock_svc = MagicMock()
    mock_svc.get_all_comets.return_value = [_make_comet("C/2020 F3"), _make_comet("1P", "Halley")]
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_comets_empty():
    mock_svc = MagicMock()
    mock_svc.get_all_comets.return_value = []
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_comets_magnitude_filter():
    bright = _make_comet("C/2020 F3")
    bright.current_magnitude = 5.0
    faint = _make_comet("1P", "Halley")
    faint.current_magnitude = 14.0
    mock_svc = MagicMock()
    mock_svc.get_all_comets.return_value = [bright, faint]
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/?max_magnitude=8")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["designation"] == "C/2020 F3"


def test_list_comets_service_error():
    mock_svc = MagicMock()
    mock_svc.get_all_comets.side_effect = RuntimeError("db error")
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/")
    assert response.status_code == 500
    assert "Error listing comets" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/comets/{designation}
# ---------------------------------------------------------------------------


def test_get_comet_found():
    mock_svc = MagicMock()
    # Use a designation without slashes to avoid URL path splitting issues
    mock_svc.get_comet_by_designation.return_value = _make_comet("1P", "Halley")
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/1P")
    assert response.status_code == 200
    assert response.json()["designation"] == "1P"


def test_get_comet_not_found():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = None
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/UNKNOWN")
    assert response.status_code == 404


def test_get_comet_service_error():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.side_effect = RuntimeError("oops")
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/C1")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/comets/  (add comet)
# ---------------------------------------------------------------------------


def test_add_comet_success():
    mock_svc = MagicMock()
    mock_svc.add_comet.return_value = 99
    payload = {
        "designation": "C/2099 X1",
        "orbital_elements": {
            "epoch_jd": 2451545.0,
            "perihelion_distance_au": 0.5,
            "eccentricity": 0.95,
            "inclination_deg": 30.0,
            "arg_perihelion_deg": 60.0,
            "ascending_node_deg": 90.0,
            "perihelion_time_jd": 2460000.0,
        },
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["comet_id"] == 99
    assert data["designation"] == "C/2099 X1"


def test_add_comet_service_error():
    mock_svc = MagicMock()
    mock_svc.add_comet.side_effect = RuntimeError("db insert failed")
    payload = {
        "designation": "C/BAD",
        "orbital_elements": {
            "epoch_jd": 2451545.0,
            "perihelion_distance_au": 0.5,
            "eccentricity": 0.95,
            "inclination_deg": 30.0,
            "arg_perihelion_deg": 60.0,
            "ascending_node_deg": 90.0,
            "perihelion_time_jd": 2460000.0,
        },
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/", json=payload)
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/comets/{designation}/ephemeris
# ---------------------------------------------------------------------------


def test_compute_comet_ephemeris_success():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = _make_comet()
    mock_svc.compute_ephemeris.return_value = _make_ephemeris()
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/C1/ephemeris")
    assert response.status_code == 200
    data = response.json()
    assert data["designation"] == "C/2020 F3"
    assert data["ra_hours"] == 3.5


def test_compute_comet_ephemeris_not_found():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = None
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/MISSING/ephemeris")
    assert response.status_code == 404


def test_compute_comet_ephemeris_with_time_param():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = _make_comet()
    mock_svc.compute_ephemeris.return_value = _make_ephemeris()
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/C1/ephemeris?time_utc=2026-03-01T00:00:00")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/comets/{designation}/visibility
# ---------------------------------------------------------------------------


def test_check_comet_visibility_success():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = _make_comet()
    mock_svc.compute_visibility.return_value = _make_visibility()
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/C1/visibility", json=location_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["altitude_deg"] == 40.0
    assert data["is_visible"] is True


def test_check_comet_visibility_not_found():
    mock_svc = MagicMock()
    mock_svc.get_comet_by_designation.return_value = None
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/GONE/visibility", json=location_payload)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/comets/visible
# ---------------------------------------------------------------------------


def test_list_visible_comets_success():
    mock_svc = MagicMock()
    mock_svc.get_visible_comets.return_value = [_make_visibility()]
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/visible", json=location_payload)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_visible_comets_empty():
    mock_svc = MagicMock()
    mock_svc.get_visible_comets.return_value = []
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/visible", json=location_payload)
    assert response.status_code == 200
    assert response.json() == []


def test_list_visible_comets_service_error():
    mock_svc = MagicMock()
    mock_svc.get_visible_comets.side_effect = RuntimeError("fail")
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.comets.CometService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/visible", json=location_payload)
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/comets/import  (import from Horizons)
# ---------------------------------------------------------------------------


def test_import_comet_success():
    mock_comet_svc = MagicMock()
    mock_comet_svc.get_comet_by_designation.return_value = None  # not yet in catalog
    mock_comet_svc.add_comet.return_value = 7
    mock_horizons = MagicMock()
    mock_horizons.fetch_comet_by_designation.return_value = _make_comet("C/2024 A1", "TestComet")

    with (
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
        patch("app.api.comets.horizons_service", mock_horizons),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/import?designation=C%2F2024%20A1")
    assert response.status_code == 201
    data = response.json()
    assert data["comet_id"] == 7
    assert "Successfully imported" in data["message"]


def test_import_comet_already_exists():
    mock_comet_svc = MagicMock()
    mock_comet_svc.get_comet_by_designation.return_value = _make_comet("C/2020 F3")

    with patch("app.api.comets.CometService", return_value=mock_comet_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/import?designation=C%2F2020%20F3")
    assert response.status_code == 409


def test_import_comet_not_found_in_horizons():
    mock_comet_svc = MagicMock()
    mock_comet_svc.get_comet_by_designation.return_value = None
    mock_horizons = MagicMock()
    mock_horizons.fetch_comet_by_designation.return_value = None

    with (
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
        patch("app.api.comets.horizons_service", mock_horizons),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/import?designation=UNKNOWN")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/comets/search/bright
# ---------------------------------------------------------------------------


def test_search_bright_comets_success():
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.return_value = [_make_comet("C/2020 F3"), _make_comet("1P", "Halley")]

    with patch("app.api.comets.horizons_service", mock_horizons):
        client = TestClient(app)
        response = client.get("/api/comets/search/bright?max_magnitude=12")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_search_bright_comets_empty():
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.return_value = []

    with patch("app.api.comets.horizons_service", mock_horizons):
        client = TestClient(app)
        response = client.get("/api/comets/search/bright")
    assert response.status_code == 200
    assert response.json() == []


def test_search_bright_comets_service_error():
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.side_effect = RuntimeError("network error")

    with patch("app.api.comets.horizons_service", mock_horizons):
        client = TestClient(app)
        response = client.get("/api/comets/search/bright")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/comets/refresh
# ---------------------------------------------------------------------------


def test_refresh_comet_catalog_success():
    mock_comet_svc = MagicMock()
    mock_comet_svc.upsert_comet.side_effect = [
        (None, True),  # first comet: created
        (None, False),  # second comet: updated
    ]
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.return_value = [_make_comet("C/2020 F3"), _make_comet("1P")]

    with (
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
        patch("app.api.comets.horizons_service", mock_horizons),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["added"] == 1
    assert data["updated"] == 1
    assert data["failed"] == 0
    assert data["total_fetched"] == 2


def test_refresh_comet_catalog_with_failures():
    mock_comet_svc = MagicMock()
    mock_comet_svc.upsert_comet.side_effect = RuntimeError("upsert failed")
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.return_value = [_make_comet("C/BAD")]

    with (
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
        patch("app.api.comets.horizons_service", mock_horizons),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 1
    assert data["added"] == 0


def test_refresh_comet_catalog_horizons_error():
    mock_comet_svc = MagicMock()
    mock_horizons = MagicMock()
    mock_horizons.fetch_bright_comets.side_effect = RuntimeError("horizons down")

    with (
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
        patch("app.api.comets.horizons_service", mock_horizons),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/comets/refresh")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/comets/visible-tonight
# ---------------------------------------------------------------------------


def test_get_visible_comets_tonight_no_location():
    mock_settings_svc = MagicMock()
    mock_settings_svc.get_location.return_value = None

    with patch("app.api.comets.SettingsService", return_value=mock_settings_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/visible-tonight")
    assert response.status_code == 200
    assert response.json() == []


def test_get_visible_comets_tonight_with_location():
    from app.models import Location

    mock_location = Location(
        name="Test",
        latitude=45.9,
        longitude=-111.5,
        elevation=1234.0,
        timezone="UTC",
    )

    mock_settings_svc = MagicMock()
    mock_settings_svc.get_location.return_value = mock_location

    visibility = _make_visibility()
    mock_comet_svc = MagicMock()
    mock_comet_svc.get_visible_comets.return_value = [visibility]

    with (
        patch("app.api.comets.SettingsService", return_value=mock_settings_svc),
        patch("app.api.comets.CometService", return_value=mock_comet_svc),
    ):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/comets/visible-tonight")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["designation"] == "C/2020 F3"
    assert "altitude" in data[0]
    assert "azimuth" in data[0]
