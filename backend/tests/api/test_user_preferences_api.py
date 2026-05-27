"""Tests for user preferences API endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _make_mock_db(settings_map=None):
    """Return a mock DB session with configurable per-key AppSetting results."""
    mock_db = MagicMock()
    settings_map = settings_map or {}

    def _query_side_effect(model):
        q = MagicMock()

        def _filter_side_effect(*args, **kwargs):
            fq = MagicMock()

            def _first_side_effect():
                # Inspect the filter expression to figure out which key was requested.
                # args[0] is a SQLAlchemy BinaryExpression; we recover the key string
                # from the right-hand side of the comparison.
                try:
                    key_val = args[0].right.value
                except Exception:
                    key_val = None
                return settings_map.get(key_val)

            fq.first.side_effect = _first_side_effect
            return fq

        q.filter.side_effect = _filter_side_effect
        return q

    mock_db.query.side_effect = _query_side_effect
    return mock_db


def _setting(value):
    """Create a mock AppSetting with the given value."""
    s = MagicMock()
    s.value = value
    return s


# ---------------------------------------------------------------------------
# GET /api/user/preferences
# ---------------------------------------------------------------------------


def test_get_preferences_returns_defaults_when_no_settings():
    app.dependency_overrides[get_db] = lambda: _make_mock_db()
    client = TestClient(app)
    response = client.get("/api/user/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["units"] == "metric"
    assert data["auto_connect"] is True
    assert data["auto_reconnect"] is True
    assert data["volume"] == "backyard"
    assert data["min_altitude"] == 30.0
    assert data["max_moon_phase"] == 50
    assert data["avoid_moon"] is True
    assert data["prioritize_transits"] is False
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["elevation"] is None


def test_get_preferences_returns_stored_location():
    settings = {
        "user.latitude": _setting("45.9183"),
        "user.longitude": _setting("-111.5433"),
        "user.elevation": _setting("1234.0"),
    }
    app.dependency_overrides[get_db] = lambda: _make_mock_db(settings)
    client = TestClient(app)
    response = client.get("/api/user/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == pytest.approx(45.9183)
    assert data["longitude"] == pytest.approx(-111.5433)
    assert data["elevation"] == pytest.approx(1234.0)


def test_get_preferences_units_imperial():
    settings = {"user.units": _setting("imperial")}
    app.dependency_overrides[get_db] = lambda: _make_mock_db(settings)
    client = TestClient(app)
    response = client.get("/api/user/preferences")
    assert response.status_code == 200
    assert response.json()["units"] == "imperial"


def test_get_preferences_connection_flags_false():
    settings = {
        "user.auto_connect": _setting("false"),
        "user.auto_reconnect": _setting("False"),
    }
    app.dependency_overrides[get_db] = lambda: _make_mock_db(settings)
    client = TestClient(app)
    response = client.get("/api/user/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["auto_connect"] is False
    assert data["auto_reconnect"] is False


def test_get_preferences_observing_fields():
    settings = {
        "user.min_altitude": _setting("20.0"),
        "user.max_moon_phase": _setting("75"),
        "user.avoid_moon": _setting("false"),
        "user.prioritize_transits": _setting("true"),
        "user.volume": _setting("outdoor"),
        "user.default_device_id": _setting("3"),
    }
    app.dependency_overrides[get_db] = lambda: _make_mock_db(settings)
    client = TestClient(app)
    response = client.get("/api/user/preferences")
    assert response.status_code == 200
    data = response.json()
    assert data["min_altitude"] == pytest.approx(20.0)
    assert data["max_moon_phase"] == 75
    assert data["avoid_moon"] is False
    assert data["prioritize_transits"] is True
    assert data["volume"] == "outdoor"
    assert data["default_device_id"] == 3


# ---------------------------------------------------------------------------
# PUT /api/user/preferences
# ---------------------------------------------------------------------------


def _put_db():
    """Mock DB that always returns None (no existing settings) and records commits."""
    mock_db = MagicMock()
    q = MagicMock()
    fq = MagicMock()
    fq.first.return_value = None
    q.filter.return_value = fq
    mock_db.query.return_value = q
    return mock_db


def test_put_preferences_success():
    mock_db = _put_db()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    payload = {
        "latitude": 45.9,
        "longitude": -111.5,
        "elevation": 1200.0,
        "units": "metric",
        "auto_connect": True,
        "auto_reconnect": True,
        "volume": "backyard",
        "min_altitude": 30.0,
        "max_moon_phase": 50,
        "avoid_moon": True,
        "prioritize_transits": False,
    }
    response = client.put("/api/user/preferences", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    mock_db.commit.assert_called_once()


def test_put_preferences_creates_new_settings():
    mock_db = _put_db()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    payload = {
        "latitude": 51.5,
        "longitude": -0.1,
        "elevation": 50.0,
        "units": "imperial",
        "auto_connect": False,
        "auto_reconnect": False,
        "volume": "silent",
        "min_altitude": 25.0,
        "max_moon_phase": 30,
        "avoid_moon": False,
        "prioritize_transits": True,
    }
    response = client.put("/api/user/preferences", json=payload)
    assert response.status_code == 200
    # db.add should have been called for each new setting
    assert mock_db.add.call_count > 0


def test_put_preferences_updates_existing_settings():
    # Return existing setting objects so the update-branch is exercised
    existing = _setting("old_value")
    mock_db = MagicMock()
    q = MagicMock()
    fq = MagicMock()
    fq.first.return_value = existing
    q.filter.return_value = fq
    mock_db.query.return_value = q

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    payload = {
        "latitude": 48.8,
        "longitude": 2.3,
        "elevation": 35.0,
        "units": "metric",
        "auto_connect": True,
        "auto_reconnect": True,
        "volume": "backyard",
        "min_altitude": 30.0,
        "max_moon_phase": 50,
        "avoid_moon": True,
        "prioritize_transits": False,
    }
    response = client.put("/api/user/preferences", json=payload)
    assert response.status_code == 200
    mock_db.commit.assert_called_once()


def test_put_preferences_omits_null_location():
    """When lat/lon/elevation/default_device_id are null, no setting should be created for them."""
    mock_db = _put_db()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    payload = {
        "units": "metric",
        "auto_connect": True,
        "auto_reconnect": True,
        "volume": "backyard",
        "min_altitude": 30.0,
        "max_moon_phase": 50,
        "avoid_moon": True,
        "prioritize_transits": False,
    }
    response = client.put("/api/user/preferences", json=payload)
    assert response.status_code == 200
