"""Tests for asteroids API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import AsteroidEphemeris, AsteroidTarget, AsteroidVisibility
from app.models.models import AsteroidOrbitalElements


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _orbital_elements():
    return AsteroidOrbitalElements(
        epoch_jd=2451545.0,
        semi_major_axis_au=1.5,
        eccentricity=0.2,
        inclination_deg=5.0,
        arg_perihelion_deg=100.0,
        ascending_node_deg=200.0,
        mean_anomaly_deg=50.0,
    )


def _make_asteroid(designation="433", name="Eros"):
    return AsteroidTarget(
        designation=designation,
        name=name,
        orbital_elements=_orbital_elements(),
        current_magnitude=8.5,
    )


def _make_ephemeris(designation="433"):
    return AsteroidEphemeris(
        designation=designation,
        date_utc=datetime(2026, 1, 1, 0, 0, 0),
        date_jd=2461041.5,
        ra_hours=5.0,
        dec_degrees=20.0,
        geo_distance_au=1.2,
        helio_distance_au=1.5,
        magnitude=8.5,
    )


def _make_visibility(asteroid=None, ephemeris=None):
    asteroid = asteroid or _make_asteroid()
    ephemeris = ephemeris or _make_ephemeris()
    return AsteroidVisibility(
        asteroid=asteroid,
        ephemeris=ephemeris,
        altitude_deg=45.0,
        azimuth_deg=180.0,
        is_visible=True,
        is_dark_enough=True,
        elongation_ok=True,
        recommended=True,
    )


# ---------------------------------------------------------------------------
# GET /api/asteroids/
# ---------------------------------------------------------------------------

def test_list_asteroids_returns_list():
    mock_svc = MagicMock()
    mock_svc.get_all_asteroids.return_value = [_make_asteroid("433"), _make_asteroid("1", "Ceres")]
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["designation"] == "433"


def test_list_asteroids_empty():
    mock_svc = MagicMock()
    mock_svc.get_all_asteroids.return_value = []
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_asteroids_magnitude_filter():
    bright = _make_asteroid("433", "Eros")
    bright.current_magnitude = 8.0
    faint = _make_asteroid("1", "Ceres")
    faint.current_magnitude = 15.0
    mock_svc = MagicMock()
    mock_svc.get_all_asteroids.return_value = [bright, faint]
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/?max_magnitude=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["designation"] == "433"


def test_list_asteroids_service_error():
    mock_svc = MagicMock()
    mock_svc.get_all_asteroids.side_effect = RuntimeError("DB failure")
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/")
    assert response.status_code == 500
    assert "Error listing asteroids" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/asteroids/{designation}
# ---------------------------------------------------------------------------

def test_get_asteroid_found():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = _make_asteroid("433", "Eros")
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/433")
    assert response.status_code == 200
    assert response.json()["designation"] == "433"
    assert response.json()["name"] == "Eros"


def test_get_asteroid_not_found():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = None
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/UNKNOWN")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_asteroid_service_error():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.side_effect = RuntimeError("oops")
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.get("/api/asteroids/433")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/asteroids/  (add asteroid)
# ---------------------------------------------------------------------------

def test_add_asteroid_success():
    mock_svc = MagicMock()
    mock_svc.add_asteroid.return_value = 42
    payload = {
        "designation": "2000 SG344",
        "orbital_elements": {
            "epoch_jd": 2451545.0,
            "semi_major_axis_au": 1.0,
            "eccentricity": 0.1,
            "inclination_deg": 2.0,
            "arg_perihelion_deg": 10.0,
            "ascending_node_deg": 20.0,
            "mean_anomaly_deg": 5.0,
        },
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["asteroid_id"] == 42
    assert data["designation"] == "2000 SG344"


def test_add_asteroid_service_error():
    mock_svc = MagicMock()
    mock_svc.add_asteroid.side_effect = RuntimeError("insert failed")
    payload = {
        "designation": "X",
        "orbital_elements": {
            "epoch_jd": 2451545.0,
            "semi_major_axis_au": 1.0,
            "eccentricity": 0.1,
            "inclination_deg": 2.0,
            "arg_perihelion_deg": 10.0,
            "ascending_node_deg": 20.0,
            "mean_anomaly_deg": 5.0,
        },
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/", json=payload)
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/asteroids/{designation}/ephemeris
# ---------------------------------------------------------------------------

def test_compute_ephemeris_success():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = _make_asteroid()
    mock_svc.compute_ephemeris.return_value = _make_ephemeris()
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/433/ephemeris")
    assert response.status_code == 200
    data = response.json()
    assert data["designation"] == "433"
    assert data["ra_hours"] == 5.0


def test_compute_ephemeris_not_found():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = None
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/MISSING/ephemeris")
    assert response.status_code == 404


def test_compute_ephemeris_with_time_param():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = _make_asteroid()
    mock_svc.compute_ephemeris.return_value = _make_ephemeris()
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/433/ephemeris?time_utc=2026-01-01T00:00:00")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/asteroids/{designation}/visibility
# ---------------------------------------------------------------------------

def test_check_visibility_success():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = _make_asteroid()
    mock_svc.compute_visibility.return_value = _make_visibility()
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "America/Denver",
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/433/visibility", json=location_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["altitude_deg"] == 45.0
    assert data["is_visible"] is True


def test_check_visibility_not_found():
    mock_svc = MagicMock()
    mock_svc.get_asteroid_by_designation.return_value = None
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/GONE/visibility", json=location_payload)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/asteroids/visible
# ---------------------------------------------------------------------------

def test_list_visible_asteroids_success():
    mock_svc = MagicMock()
    mock_svc.get_visible_asteroids.return_value = [_make_visibility()]
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/visible", json=location_payload)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_visible_asteroids_empty():
    mock_svc = MagicMock()
    mock_svc.get_visible_asteroids.return_value = []
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/visible", json=location_payload)
    assert response.status_code == 200
    assert response.json() == []


def test_list_visible_asteroids_service_error():
    mock_svc = MagicMock()
    mock_svc.get_visible_asteroids.side_effect = RuntimeError("calc error")
    location_payload = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    with patch("app.api.asteroids.AsteroidService", return_value=mock_svc):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        response = client.post("/api/asteroids/visible", json=location_payload)
    assert response.status_code == 500
