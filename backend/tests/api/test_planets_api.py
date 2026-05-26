"""Tests for planets API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import PlanetEphemeris, PlanetTarget, PlanetVisibility


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _make_planet(name="Mars"):
    return PlanetTarget(
        name=name,
        planet_type="terrestrial",
        diameter_km=6779.0,
        orbital_period_days=687.0,
        has_rings=False,
        num_moons=2,
        notes="Red planet",
    )


def _make_ephemeris(name="Mars"):
    return PlanetEphemeris(
        name=name,
        date_utc=datetime(2026, 1, 1, 0, 0, 0),
        date_jd=2461041.5,
        ra_hours=6.0,
        dec_degrees=23.0,
        distance_au=0.8,
        magnitude=-1.2,
        angular_diameter_arcsec=14.0,
        phase_percent=90.0,
        elongation_deg=130.0,
        constellation="Gemini",
    )


def _make_visibility(planet=None, ephemeris=None):
    planet = planet or _make_planet()
    ephemeris = ephemeris or _make_ephemeris()
    return PlanetVisibility(
        planet=planet,
        ephemeris=ephemeris,
        altitude_deg=50.0,
        azimuth_deg=180.0,
        is_visible=True,
        is_daytime=False,
        elongation_ok=True,
        recommended=True,
    )


# ---------------------------------------------------------------------------
# GET /api/planets/
# ---------------------------------------------------------------------------

def test_list_planets_returns_all():
    planets = [_make_planet("Mars"), _make_planet("Jupiter"), _make_planet("Saturn")]
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_all_planets.return_value = planets
        client = TestClient(app)
        response = client.get("/api/planets/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Mars"


def test_list_planets_empty():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_all_planets.return_value = []
        client = TestClient(app)
        response = client.get("/api/planets/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_planets_service_error():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_all_planets.side_effect = RuntimeError("ephem error")
        client = TestClient(app)
        response = client.get("/api/planets/")
    assert response.status_code == 500
    assert "Error listing planets" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/planets/{planet_name}
# ---------------------------------------------------------------------------

def test_get_planet_found():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_planet_by_name.return_value = _make_planet("Mars")
        client = TestClient(app)
        response = client.get("/api/planets/mars")
    assert response.status_code == 200
    assert response.json()["name"] == "Mars"


def test_get_planet_not_found():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_planet_by_name.return_value = None
        client = TestClient(app)
        response = client.get("/api/planets/Pluto")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_planet_service_error():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_planet_by_name.side_effect = RuntimeError("boom")
        client = TestClient(app)
        response = client.get("/api/planets/mars")
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/planets/{planet_name}/ephemeris
# ---------------------------------------------------------------------------

def test_compute_planet_ephemeris_success():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.compute_ephemeris.return_value = _make_ephemeris("Mars")
        client = TestClient(app)
        response = client.post("/api/planets/mars/ephemeris?time_utc=2026-01-01T00:00:00")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Mars"
    assert data["ra_hours"] == 6.0


def test_compute_planet_ephemeris_invalid_planet():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.compute_ephemeris.side_effect = ValueError("Unknown planet: Vulcan")
        client = TestClient(app)
        response = client.post("/api/planets/Vulcan/ephemeris?time_utc=2026-01-01T00:00:00")
    assert response.status_code == 400
    assert "Vulcan" in response.json()["detail"]


def test_compute_planet_ephemeris_service_error():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.compute_ephemeris.side_effect = RuntimeError("computation failed")
        client = TestClient(app)
        response = client.post("/api/planets/mars/ephemeris?time_utc=2026-01-01T00:00:00")
    assert response.status_code == 500


def test_compute_planet_ephemeris_missing_time():
    client = TestClient(app)
    response = client.post("/api/planets/mars/ephemeris")
    # time_utc is required
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/planets/{planet_name}/visibility
# ---------------------------------------------------------------------------

def test_compute_planet_visibility_success():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.compute_visibility.return_value = _make_visibility()
        client = TestClient(app)
        location = {
            "name": "Test",
            "latitude": 45.9,
            "longitude": -111.5,
            "elevation": 1234.0,
            "timezone": "UTC",
        }
        response = client.post(
            "/api/planets/mars/visibility?time_utc=2026-01-01T00:00:00",
            json=location,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["altitude_deg"] == 50.0
    assert data["is_visible"] is True


def test_compute_planet_visibility_invalid_planet():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.compute_visibility.side_effect = ValueError("Unknown planet")
        client = TestClient(app)
        location = {
            "name": "Test",
            "latitude": 45.9,
            "longitude": -111.5,
            "elevation": 1234.0,
            "timezone": "UTC",
        }
        response = client.post(
            "/api/planets/Vulcan/visibility?time_utc=2026-01-01T00:00:00",
            json=location,
        )
    assert response.status_code == 400


def test_compute_planet_visibility_missing_time():
    client = TestClient(app)
    location = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    response = client.post("/api/planets/mars/visibility", json=location)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/planets/visible
# ---------------------------------------------------------------------------

def test_get_visible_planets_success():
    visible = [_make_visibility(_make_planet("Mars")), _make_visibility(_make_planet("Jupiter"))]
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_visible_planets.return_value = visible
        client = TestClient(app)
        location = {
            "name": "Test",
            "latitude": 45.9,
            "longitude": -111.5,
            "elevation": 1234.0,
            "timezone": "UTC",
        }
        response = client.post(
            "/api/planets/visible?time_utc=2026-01-01T00:00:00",
            json=location,
        )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_visible_planets_empty():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_visible_planets.return_value = []
        client = TestClient(app)
        location = {
            "name": "Test",
            "latitude": 45.9,
            "longitude": -111.5,
            "elevation": 1234.0,
            "timezone": "UTC",
        }
        response = client.post(
            "/api/planets/visible?time_utc=2026-01-01T00:00:00",
            json=location,
        )
    assert response.status_code == 200
    assert response.json() == []


def test_get_visible_planets_service_error():
    with patch("app.api.planets.planet_service") as mock_svc:
        mock_svc.get_visible_planets.side_effect = RuntimeError("error")
        client = TestClient(app)
        location = {
            "name": "Test",
            "latitude": 45.9,
            "longitude": -111.5,
            "elevation": 1234.0,
            "timezone": "UTC",
        }
        response = client.post(
            "/api/planets/visible?time_utc=2026-01-01T00:00:00",
            json=location,
        )
    assert response.status_code == 500


def test_get_visible_planets_missing_time():
    client = TestClient(app)
    location = {
        "name": "Test",
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1234.0,
        "timezone": "UTC",
    }
    response = client.post("/api/planets/visible", json=location)
    assert response.status_code == 422
