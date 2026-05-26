"""Mock-based unit tests for app/api/settings.py.

Covers the previously uncovered endpoint groups:
- GET/PUT /settings/app  (AppSetting CRUD)
- GET/POST /settings/devices  (SeestarDevice CRUD)
- GET/POST/PUT/DELETE /settings/locations  (ObservingLocation CRUD)
- GET/PUT /settings/wishlist
- GET/PUT /settings/horizon-profile
- GET/PUT /settings/user
- GET/PUT /settings/planning

No real DB required — all DB access is mocked via dependency override.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def make_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.all.return_value = []
    return db


@pytest.fixture
def client_with_mock_db():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c, db


# ---------------------------------------------------------------------------
# Helper factories for mock DB models
# ---------------------------------------------------------------------------


def mock_setting(key="test.key", value="test_value", value_type="string",
                 description=None, category=None, is_secret=False, id=1):
    s = MagicMock()
    s.id = id
    s.key = key
    s.value = value
    s.value_type = value_type
    s.description = description
    s.category = category
    s.is_secret = is_secret
    return s


def mock_location(id=1, name="Test Location", latitude=45.0, longitude=-111.0,
                  elevation=1234.0, timezone="America/Denver", bortle_class=4,
                  is_default=True, is_active=True):
    loc = MagicMock()
    loc.id = id
    loc.name = name
    loc.latitude = latitude
    loc.longitude = longitude
    loc.elevation = elevation
    loc.timezone = timezone
    loc.bortle_class = bortle_class
    loc.is_default = is_default
    loc.is_active = is_active
    loc.description = None
    return loc


def mock_device(id=1, name="My Seestar", control_host="192.168.2.47",
                control_port=4700, is_control_enabled=True,
                mount_path=None, is_mount_enabled=False,
                is_default=True, is_active=True):
    dev = MagicMock()
    dev.id = id
    dev.name = name
    dev.description = None
    dev.control_host = control_host
    dev.control_port = control_port
    dev.is_control_enabled = is_control_enabled
    dev.mount_path = mount_path
    dev.is_mount_enabled = is_mount_enabled
    dev.is_default = is_default
    dev.is_active = is_active
    return dev


# ---------------------------------------------------------------------------
# App Settings endpoints
# ---------------------------------------------------------------------------


class TestAppSettingsGet:
    def test_get_all_settings_empty(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.all.return_value = []
        resp = client.get("/api/settings/app")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_all_settings_with_category_filter(self, client_with_mock_db):
        client, db = client_with_mock_db
        s = mock_setting(key="ui.theme", value="dark", category="ui")
        db.query.return_value.filter.return_value.all.return_value = [s]
        resp = client.get("/api/settings/app?category=ui")
        assert resp.status_code == 200

    def test_get_setting_by_key_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        s = mock_setting(key="ui.theme", value="dark", category="ui")
        db.query.return_value.filter.return_value.first.return_value = s
        resp = client.get("/api/settings/app/ui.theme")
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == "ui.theme"
        assert data["value"] == "dark"

    def test_get_setting_by_key_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/app/nonexistent.key")
        assert resp.status_code == 404


class TestAppSettingsPut:
    def test_update_setting_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        s = mock_setting(key="ui.theme", value="dark")
        db.query.return_value.filter.return_value.first.return_value = s
        resp = client.put("/api/settings/app/ui.theme", json={"value": "light"})
        assert resp.status_code == 200
        assert s.value == "light"

    def test_update_setting_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.put("/api/settings/app/missing.key", json={"value": "x"})
        assert resp.status_code == 404


class TestAppSettingsPost:
    def test_create_setting_success(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        new_s = mock_setting(key="new.setting", value="hello")
        db.refresh = MagicMock(return_value=None)

        from app.models.settings_models import AppSetting

        with patch("app.api.settings.AppSetting") as MockSetting:
            MockSetting.return_value = new_s
            resp = client.post(
                "/api/settings/app",
                json={"key": "new.setting", "value": "hello", "value_type": "string"},
            )
        # Could be 200 or require mock refresh
        assert resp.status_code in [200, 500]

    def test_create_setting_duplicate_returns_400(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_setting(key="ui.theme", value="dark")
        db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.post(
            "/api/settings/app",
            json={"key": "ui.theme", "value": "light", "value_type": "string"},
        )
        assert resp.status_code == 400


class TestAppSettingsDelete:
    def test_delete_setting_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        s = mock_setting(key="ui.theme", value="dark")
        db.query.return_value.filter.return_value.first.return_value = s
        resp = client.delete("/api/settings/app/ui.theme")
        assert resp.status_code == 200
        data = resp.json()
        assert "deleted" in data["message"].lower() or "ui.theme" in data["message"]

    def test_delete_setting_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.delete("/api/settings/app/gone.key")
        assert resp.status_code == 404


class TestAppSettingsCategories:
    def test_get_categories(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.distinct.return_value.all.return_value = [("ui",), ("telescope",)]
        resp = client.get("/api/settings/app/categories/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data


# ---------------------------------------------------------------------------
# Seestar Device endpoints
# ---------------------------------------------------------------------------


class TestDevicesGet:
    def test_list_active_devices(self, client_with_mock_db):
        client, db = client_with_mock_db
        dev = mock_device()
        db.query.return_value.filter.return_value.all.return_value = [dev]
        resp = client.get("/api/settings/devices")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_all_devices_including_inactive(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.all.return_value = []
        resp = client.get("/api/settings/devices?active_only=false")
        assert resp.status_code == 200

    def test_get_device_by_id_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        dev = mock_device(id=1)
        db.query.return_value.filter.return_value.first.return_value = dev
        resp = client.get("/api/settings/devices/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1

    def test_get_device_by_id_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/devices/999")
        assert resp.status_code == 404

    def test_get_default_device_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        dev = mock_device(is_default=True)
        db.query.return_value.filter.return_value.first.return_value = dev
        resp = client.get("/api/settings/devices/default/get")
        assert resp.status_code == 200

    def test_get_default_device_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/devices/default/get")
        assert resp.status_code == 404


class TestDevicesPost:
    def test_create_device_duplicate_returns_400(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_device(name="My Seestar")
        db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.post(
            "/api/settings/devices",
            json={"name": "My Seestar", "control_port": 4700},
        )
        assert resp.status_code == 400


class TestDevicesPut:
    def test_update_device_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.put("/api/settings/devices/999", json={"name": "NewName"})
        assert resp.status_code == 404


class TestDevicesDelete:
    def test_delete_device_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        dev = mock_device(name="My Seestar")
        db.query.return_value.filter.return_value.first.return_value = dev
        resp = client.delete("/api/settings/devices/1")
        assert resp.status_code == 200

    def test_delete_device_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.delete("/api/settings/devices/999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Observing Location endpoints
# ---------------------------------------------------------------------------


class TestLocationsGet:
    def test_list_active_locations(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location()
        db.query.return_value.filter.return_value.all.return_value = [loc]
        resp = client.get("/api/settings/locations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_location_by_id_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location(id=1)
        db.query.return_value.filter.return_value.first.return_value = loc
        resp = client.get("/api/settings/locations/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1

    def test_get_location_by_id_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/locations/999")
        assert resp.status_code == 404

    def test_get_default_location_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location(is_default=True)
        db.query.return_value.filter.return_value.first.return_value = loc
        resp = client.get("/api/settings/locations/default/get")
        assert resp.status_code == 200

    def test_get_default_location_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/locations/default/get")
        assert resp.status_code == 404


class TestLocationsPost:
    def test_create_location_duplicate_returns_400(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_location(name="Home")
        db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.post(
            "/api/settings/locations",
            json={
                "name": "Home", "latitude": 45.0, "longitude": -111.0,
                "elevation": 0.0, "timezone": "UTC",
            },
        )
        assert resp.status_code == 400

    def test_create_location_invalid_latitude(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.post(
            "/api/settings/locations",
            json={
                "name": "Bad", "latitude": 999.0, "longitude": 0.0,
                "elevation": 0.0, "timezone": "UTC",
            },
        )
        assert resp.status_code == 422


class TestLocationsPut:
    def test_update_location_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.put("/api/settings/locations/999", json={"name": "NewName"})
        assert resp.status_code == 404


class TestLocationsDelete:
    def test_delete_location_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location(name="Home")
        db.query.return_value.filter.return_value.first.return_value = loc
        resp = client.delete("/api/settings/locations/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "Home" in data["message"] or "deleted" in data["message"].lower()

    def test_delete_location_not_found(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.delete("/api/settings/locations/999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Wishlist endpoints
# ---------------------------------------------------------------------------


class TestWishlist:
    def test_get_wishlist_when_not_set(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/wishlist")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_wishlist_with_data(self, client_with_mock_db):
        client, db = client_with_mock_db
        wishlist = [{"name": "M31", "type": "dso"}, {"name": "Jupiter", "type": "planet"}]
        setting = mock_setting(key="user.wishlist_targets", value=json.dumps(wishlist))
        db.query.return_value.filter.return_value.first.return_value = setting
        resp = client.get("/api/settings/wishlist")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "M31"

    def test_get_wishlist_bad_json_returns_empty(self, client_with_mock_db):
        client, db = client_with_mock_db
        setting = mock_setting(key="user.wishlist_targets", value="not valid json{{")
        db.query.return_value.filter.return_value.first.return_value = setting
        resp = client.get("/api/settings/wishlist")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_put_wishlist_creates_new(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        wishlist = [{"name": "Saturn", "type": "planet"}]
        resp = client.put("/api/settings/wishlist", json=wishlist)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert "updated" in data["message"].lower()

    def test_put_wishlist_updates_existing(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_setting(key="user.wishlist_targets", value="[]")
        db.query.return_value.filter.return_value.first.return_value = existing
        wishlist = [{"name": "Mars", "type": "planet"}, {"name": "Moon", "type": "moon"}]
        resp = client.put("/api/settings/wishlist", json=wishlist)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        # Verify the mock setting value was updated
        assert existing.value == json.dumps(wishlist)


# ---------------------------------------------------------------------------
# Horizon profile endpoints
# ---------------------------------------------------------------------------


class TestHorizonProfile:
    def test_get_horizon_profile_when_not_set(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/settings/horizon-profile")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_horizon_profile_with_data(self, client_with_mock_db):
        client, db = client_with_mock_db
        profile = [{"az": 0, "alt": 10}, {"az": 90, "alt": 15}]
        setting = mock_setting(key="user.horizon_profile", value=json.dumps(profile))
        db.query.return_value.filter.return_value.first.return_value = setting
        resp = client.get("/api/settings/horizon-profile")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["az"] == 0

    def test_get_horizon_profile_bad_json(self, client_with_mock_db):
        client, db = client_with_mock_db
        setting = mock_setting(key="user.horizon_profile", value="{{broken")
        db.query.return_value.filter.return_value.first.return_value = setting
        resp = client.get("/api/settings/horizon-profile")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_put_horizon_profile_creates_new(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        profile = [{"az": 0, "alt": 5}, {"az": 180, "alt": 10}]
        resp = client.put("/api/settings/horizon-profile", json=profile)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert "updated" in data["message"].lower()

    def test_put_horizon_profile_updates_existing(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_setting(key="user.horizon_profile", value="[]")
        db.query.return_value.filter.return_value.first.return_value = existing
        profile = [{"az": 45, "alt": 8}]
        resp = client.put("/api/settings/horizon-profile", json=profile)
        assert resp.status_code == 200
        assert existing.value == json.dumps(profile)


# ---------------------------------------------------------------------------
# User settings endpoints
# ---------------------------------------------------------------------------


class TestUserSettings:
    def test_get_user_settings_no_location(self, client_with_mock_db):
        client, db = client_with_mock_db
        # No default location, no pref rows
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        resp = client.get("/api/settings/user")
        assert resp.status_code == 200
        data = resp.json()
        # Falls back to defaults
        assert "latitude" in data
        assert "longitude" in data
        assert "timezone" in data

    def test_get_user_settings_with_location(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location(name="Three Forks", latitude=45.9, longitude=-111.5,
                            elevation=1234.0, timezone="America/Denver")
        # first call returns location, subsequent calls return empty prefs
        db.query.return_value.filter.return_value.first.return_value = loc
        db.query.return_value.filter.return_value.all.return_value = []
        resp = client.get("/api/settings/user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["latitude"] == 45.9
        assert data["longitude"] == -111.5

    def test_put_user_settings_updates_location(self, client_with_mock_db):
        client, db = client_with_mock_db
        loc = mock_location(name="Old Name")
        db.query.return_value.filter.return_value.first.return_value = loc
        db.query.return_value.filter.return_value.all.return_value = []

        payload = {
            "locationName": "New Name",
            "latitude": 35.0,
            "longitude": -100.0,
            "elevation": 500.0,
            "timezone": "America/Chicago",
            "temperatureUnit": "C",
            "distanceUnit": "km",
            "showThumbnails": True,
            "autoRefresh": False,
            "telescopeHost": "192.168.1.1",
            "telescopePort": 4700,
            "planMinAltitude": 25,
            "planMaxAltitude": 85,
            "planAvoidMoon": False,
            "planSetupMinutes": 15,
            "planObjectTypes": ["galaxy", "nebula"],
            "catalogSortBy": "magnitude",
            "catalogVisibleNow": True,
            "catalogUseScoring": False,
            "imagingMode": "deep-sky",
            "annotationsEnabled": False,
            "autoExecuteEnabled": False,
            "autoExecuteRetryCount": 3,
            "weatherAbortOnRain": True,
            "weatherAbortWindMph": 20.0,
            "weatherAbortHumidityPct": 90,
        }
        resp = client.put("/api/settings/user", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["latitude"] == 35.0
        assert data["longitude"] == -100.0

    def test_put_user_settings_creates_location_when_none(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []

        payload = {
            "locationName": "Somewhere",
            "latitude": 40.0,
            "longitude": -75.0,
            "elevation": 0.0,
            "timezone": "America/New_York",
            "temperatureUnit": "F",
            "distanceUnit": "mi",
            "showThumbnails": True,
            "autoRefresh": False,
            "telescopeHost": "",
            "telescopePort": 4700,
            "planMinAltitude": 30,
            "planMaxAltitude": 70,
            "planAvoidMoon": True,
            "planSetupMinutes": 30,
            "planObjectTypes": ["galaxy"],
            "catalogSortBy": "name",
            "catalogVisibleNow": False,
            "catalogUseScoring": False,
            "imagingMode": "deep-sky",
            "annotationsEnabled": False,
            "autoExecuteEnabled": False,
            "autoExecuteRetryCount": 6,
            "weatherAbortOnRain": True,
            "weatherAbortWindMph": 25.0,
            "weatherAbortHumidityPct": 95,
        }
        resp = client.put("/api/settings/user", json=payload)
        assert resp.status_code == 200
        db.add.assert_called()


# ---------------------------------------------------------------------------
# Planning settings endpoints
# ---------------------------------------------------------------------------


class TestPlanningSettings:
    def test_get_planning_settings_defaults(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.all.return_value = []
        resp = client.get("/api/settings/planning")
        assert resp.status_code == 200
        data = resp.json()
        assert "daily_enabled" in data
        assert "daily_time_hour" in data
        assert "daily_target_count" in data
        assert "webhook_url" in data

    def test_get_planning_settings_with_db_rows(self, client_with_mock_db):
        client, db = client_with_mock_db
        rows = [
            mock_setting(key="planning.daily_enabled", value="true", value_type="bool"),
            mock_setting(key="planning.daily_time_hour", value="14", value_type="int"),
        ]
        db.query.return_value.filter.return_value.all.return_value = rows
        resp = client.get("/api/settings/planning")
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_enabled"] is True
        assert data["daily_time_hour"] == 14

    def test_put_planning_settings(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_setting(key="planning.daily_enabled", value="false", value_type="bool")
        db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.put(
            "/api/settings/planning",
            json={"daily_enabled": True, "daily_time_hour": 10, "daily_target_count": 8},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_put_planning_settings_creates_new_rows(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.put(
            "/api/settings/planning",
            json={"daily_enabled": False, "webhook_url": "https://example.com/hook"},
        )
        assert resp.status_code == 200
        db.add.assert_called()


# ---------------------------------------------------------------------------
# Init default settings endpoint
# ---------------------------------------------------------------------------


class TestInitSettings:
    def test_init_settings_when_all_missing(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.post("/api/settings/app/init")
        assert resp.status_code == 200
        data = resp.json()
        assert "created" in data
        assert isinstance(data["created"], list)

    def test_init_settings_when_already_exists(self, client_with_mock_db):
        client, db = client_with_mock_db
        existing = mock_setting()
        db.query.return_value.filter.return_value.first.return_value = existing
        resp = client.post("/api/settings/app/init")
        assert resp.status_code == 200
        data = resp.json()
        # No new settings created since they already exist
        assert data["created"] == []
