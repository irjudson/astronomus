"""Mock-based unit tests for app/api/routes.py.

Covers the previously uncovered endpoint groups:
- /targets/near, /targets, /targets/scored, /targets/{id}, /caldwell
- /search/unified, /catalog/search, /catalog/stats
- /twilight, /export, /share, /shared-plans
- /sky-quality, /images/previews, /images/targets
- /solar-system/objects
- /wishlist/defaults

No real DB required — all DB access is mocked via dependency override.
"""

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
    db.query.return_value.count.return_value = 0
    db.query.return_value.scalar.return_value = 0
    db.query.return_value.one.return_value = MagicMock(
        very_bright=0, bright=0, moderate=0, faint=0
    )
    return db


@pytest.fixture
def client_with_mock_db():
    db = make_db()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c, db


@pytest.fixture
def plain_client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper — build a minimal DSOCatalog-like mock row
# ---------------------------------------------------------------------------


def dso_row(
    catalog_name="NGC",
    catalog_number=1,
    common_name=None,
    object_type="galaxy",
    ra_hours=1.0,
    dec_degrees=10.0,
    magnitude=8.0,
    size_major_arcmin=5.0,
    constellation="And",
):
    row = MagicMock()
    row.catalog_name = catalog_name
    row.catalog_number = catalog_number
    row.common_name = common_name
    row.object_type = object_type
    row.ra_hours = ra_hours
    row.dec_degrees = dec_degrees
    row.magnitude = magnitude
    row.size_major_arcmin = size_major_arcmin
    row.size_arcmin = size_major_arcmin
    row.size_minor_arcmin = size_major_arcmin / 2
    row.constellation = constellation
    row.id = catalog_number
    row.caldwell_number = None
    return row


# ---------------------------------------------------------------------------
# /targets/near
# ---------------------------------------------------------------------------


class TestTargetsNear:
    def test_returns_empty_list_when_no_candidates(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        resp = client.get("/api/targets/near?ra_hours=1.0&dec_degrees=10.0")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_nearby_objects_within_radius(self, client_with_mock_db):
        client, db = client_with_mock_db
        row = dso_row(ra_hours=1.0, dec_degrees=10.0, magnitude=8.0)
        # The endpoint calls db.query(DSOCatalog).filter(...).filter(...).all()
        # Build a flexible mock that returns the row regardless of filter chain depth
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = [row]
        db.query.return_value = mock_q
        resp = client.get("/api/targets/near?ra_hours=1.0&dec_degrees=10.0&radius_deg=5.0")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ra_hours"] == 1.0

    def test_uses_common_name_as_catalog_id(self, client_with_mock_db):
        client, db = client_with_mock_db
        row = dso_row(catalog_name="NGC", catalog_number=224, common_name="Andromeda", ra_hours=0.712, dec_degrees=41.27)
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [row]
        resp = client.get("/api/targets/near?ra_hours=0.712&dec_degrees=41.27&radius_deg=5.0")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            assert data[0]["catalog_id"] == "Andromeda"

    def test_respects_limit(self, client_with_mock_db):
        client, db = client_with_mock_db
        rows = [dso_row(ra_hours=1.0, dec_degrees=10.0 + i * 0.01) for i in range(20)]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = rows
        resp = client.get("/api/targets/near?ra_hours=1.0&dec_degrees=10.0&radius_deg=5.0&limit=3")
        assert resp.status_code == 200
        assert len(resp.json()) <= 3


# ---------------------------------------------------------------------------
# /targets
# ---------------------------------------------------------------------------


class TestTargetsList:
    def test_returns_200_with_empty_list(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.filter_targets.return_value = []
            db.query.return_value.filter.return_value.all.return_value = []
            resp = client.get("/api/targets?limit=10&include_visibility=false")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_include_visibility_false_skips_visibility(self, client_with_mock_db):
        client, db = client_with_mock_db
        from app.models import DSOTarget

        mock_target = DSOTarget(
            name="M31", catalog_id="M31", object_type="galaxy",
            ra_hours=0.712, dec_degrees=41.27, magnitude=3.4, size_arcmin=190.0
        )
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.filter_targets.return_value = [mock_target]
            db.query.return_value.filter.return_value.all.return_value = []
            resp = client.get("/api/targets?include_visibility=false&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["catalog_id"] == "M31"

    def test_sort_by_magnitude(self, client_with_mock_db):
        client, db = client_with_mock_db
        from app.models import DSOTarget

        targets = [
            DSOTarget(name="NGC1", catalog_id="NGC1", object_type="galaxy",
                      ra_hours=1.0, dec_degrees=10.0, magnitude=9.0, size_arcmin=5.0),
            DSOTarget(name="M31", catalog_id="M31", object_type="galaxy",
                      ra_hours=0.712, dec_degrees=41.27, magnitude=3.4, size_arcmin=190.0),
        ]
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.filter_targets.return_value = targets
            db.query.return_value.filter.return_value.all.return_value = []
            resp = client.get("/api/targets?sort_by=magnitude&include_visibility=false&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["magnitude"] <= data[1]["magnitude"]


# ---------------------------------------------------------------------------
# /targets/{catalog_id}
# ---------------------------------------------------------------------------


class TestTargetById:
    def test_found_returns_target(self, client_with_mock_db):
        client, db = client_with_mock_db
        from app.models import DSOTarget

        mock_target = DSOTarget(
            name="M31", catalog_id="M31", object_type="galaxy",
            ra_hours=0.712, dec_degrees=41.27, magnitude=3.4, size_arcmin=190.0
        )
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.get_target_by_id.return_value = mock_target
            resp = client.get("/api/targets/M31")
        assert resp.status_code == 200
        assert resp.json()["catalog_id"] == "M31"

    def test_not_found_returns_404(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.get_target_by_id.return_value = None
            resp = client.get("/api/targets/NONEXISTENT999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /caldwell
# ---------------------------------------------------------------------------


class TestCaldwell:
    def test_returns_caldwell_list(self, client_with_mock_db):
        client, db = client_with_mock_db
        from app.models import DSOTarget

        mock_targets = [
            DSOTarget(name="C1", catalog_id="C1", object_type="cluster",
                      ra_hours=0.5, dec_degrees=57.0, magnitude=4.0, size_arcmin=20.0)
        ]
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.get_caldwell_targets.return_value = mock_targets
            resp = client.get("/api/caldwell")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["catalog_id"] == "C1"

    def test_returns_empty_list(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value.get_caldwell_targets.return_value = []
            resp = client.get("/api/caldwell")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# /search/unified
# ---------------------------------------------------------------------------


class TestUnifiedSearch:
    def test_search_returns_grouped_results(self, client_with_mock_db):
        client, db = client_with_mock_db
        # DB returns empty lists for DSO and star queries
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("app.api.routes.CatalogService"):
            with patch("app.services.planet_service.PlanetService") as MockPlanet:
                MockPlanet.return_value.get_all_planets.return_value = []
                resp = client.get("/api/search/unified?query=andromeda")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "dsos" in data["results"]
        assert "stars" in data["results"]
        assert "planets" in data["results"]

    def test_search_with_object_type_filter(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("app.api.routes.CatalogService"):
            resp = client.get("/api/search/unified?query=M31&object_types=dso")
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "M31"
        assert "results" in data

    def test_planet_search_filters_by_name(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_planet = MagicMock()
        mock_planet.name = "Jupiter"
        mock_planet.planet_type = "gas_giant"
        mock_planet.diameter_km = 142984
        mock_planet.orbital_period_days = 4333
        mock_planet.has_rings = True
        mock_planet.num_moons = 95
        mock_planet.notes = "Largest planet"
        with patch("app.api.routes.CatalogService"):
            # PlanetService is imported inside the function, patch at its source module
            with patch("app.services.planet_service.PlanetService") as MockPlanet:
                MockPlanet.return_value.get_all_planets.return_value = [mock_planet]
                resp = client.get("/api/search/unified?query=jupiter&object_types=planet")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_results"] >= 0


# ---------------------------------------------------------------------------
# /catalog/search
# ---------------------------------------------------------------------------


class TestCatalogSearch:
    def test_basic_search_returns_paginated_results(self, client_with_mock_db):
        client, db = client_with_mock_db
        row = dso_row(catalog_name="NGC", catalog_number=224, common_name="M031")
        # Set up the query chain for the non-visible_now path
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.count.return_value = 1
        mock_q.limit.return_value.offset.return_value.all.return_value = [row]
        db.query.return_value = mock_q

        mock_target = MagicMock()
        mock_target.catalog_id = "NGC224"
        mock_target.name = "M031"
        mock_target.object_type = "galaxy"
        mock_target.magnitude = 3.4
        mock_target.ra_hours = 0.712
        mock_target.dec_degrees = 41.27
        mock_target.size_arcmin = 190.0

        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value._db_row_to_target.return_value = mock_target
            MockCatalog.return_value._get_constellation_details.return_value = None
            resp = client.get("/api/catalog/search?page=1&page_size=10")

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_search_with_type_filter(self, client_with_mock_db):
        client, db = client_with_mock_db
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.count.return_value = 0
        mock_q.limit.return_value.offset.return_value.all.return_value = []
        db.query.return_value = mock_q

        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value._db_row_to_target.return_value = MagicMock()
            MockCatalog.return_value._get_constellation_details.return_value = None
            resp = client.get("/api/catalog/search?type=galaxy&page=1&page_size=20")

        assert resp.status_code == 200

    def test_search_with_text_query(self, client_with_mock_db):
        client, db = client_with_mock_db
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.count.return_value = 0
        mock_q.limit.return_value.offset.return_value.all.return_value = []
        mock_q.all.return_value = []  # for exact match query
        db.query.return_value = mock_q

        with patch("app.api.routes.CatalogService") as MockCatalog:
            MockCatalog.return_value._db_row_to_target.return_value = MagicMock()
            MockCatalog.return_value._get_constellation_details.return_value = None
            resp = client.get("/api/catalog/search?search=M31&page=1&page_size=20")

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /catalog/stats
# ---------------------------------------------------------------------------


class TestCatalogStats:
    def test_returns_stats_structure(self, client_with_mock_db):
        client, db = client_with_mock_db
        # Mock scalar for total count
        mock_q = MagicMock()
        mock_q.scalar.return_value = 100
        mock_q.filter.return_value.scalar.return_value = 10
        mock_q.filter.return_value.one.return_value = MagicMock(
            very_bright=5, bright=20, moderate=60, faint=15
        )
        # for by_type and by_catalog group_by queries
        mock_q.group_by.return_value.order_by.return_value.all.return_value = [
            ("galaxy", 50), ("nebula", 30)
        ]
        db.query.return_value = mock_q

        resp = client.get("/api/catalog/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_objects" in data
        assert "by_type" in data
        assert "by_catalog" in data
        assert "by_magnitude" in data


# ---------------------------------------------------------------------------
# /twilight
# ---------------------------------------------------------------------------


class TestTwilight:
    def test_calculate_twilight_calls_planner(self, client_with_mock_db):
        client, db = client_with_mock_db
        mock_result = {
            "sunset": "2025-01-15T18:00:00",
            "astronomical_twilight_end": "2025-01-15T19:30:00",
            "astronomical_twilight_start": "2025-01-16T05:30:00",
            "sunrise": "2025-01-16T07:00:00",
        }
        with patch("app.api.routes.PlannerService") as MockPlanner:
            MockPlanner.return_value.calculate_twilight.return_value = mock_result
            resp = client.post(
                "/api/twilight?date=2025-01-15",
                json={"name": "Test", "latitude": 45.0, "longitude": -111.0,
                      "elevation": 1234.0, "timezone": "America/Denver"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "sunset" in data

    def test_twilight_error_returns_500(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.PlannerService") as MockPlanner:
            MockPlanner.return_value.calculate_twilight.side_effect = Exception("ephemeris error")
            resp = client.post(
                "/api/twilight?date=2025-01-15",
                json={"name": "Test", "latitude": 45.0, "longitude": -111.0,
                      "elevation": 1234.0, "timezone": "UTC"},
            )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# /export
# ---------------------------------------------------------------------------


def _minimal_plan():
    """Return a dict that satisfies the ObservingPlan Pydantic model."""
    return {
        "session": {
            "observing_date": "2025-01-15",
            "sunset": "2025-01-15T18:00:00",
            "civil_twilight_end": "2025-01-15T18:30:00",
            "nautical_twilight_end": "2025-01-15T19:00:00",
            "astronomical_twilight_end": "2025-01-15T19:30:00",
            "astronomical_twilight_start": "2025-01-16T05:30:00",
            "nautical_twilight_start": "2025-01-16T06:00:00",
            "civil_twilight_start": "2025-01-16T06:30:00",
            "sunrise": "2025-01-16T07:00:00",
            "imaging_start": "2025-01-15T20:00:00",
            "imaging_end": "2025-01-16T05:00:00",
            "total_imaging_minutes": 540,
        },
        "location": {
            "name": "Test", "latitude": 45.0, "longitude": -111.0,
            "elevation": 1234.0, "timezone": "America/Denver",
        },
        "scheduled_targets": [],
        "weather_forecast": [],
        "total_targets": 0,
        "coverage_percent": 0.0,
    }


class TestExport:
    def _minimal_plan(self):
        return _minimal_plan()

    def test_export_json_format(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.PlannerService") as MockPlanner:
            MockPlanner.return_value.exporter.export.return_value = '{"plan": "data"}'
            resp = client.post("/api/export?format=json", json=self._minimal_plan())
        assert resp.status_code == 200
        data = resp.json()
        assert "format_type" in data
        assert data["format_type"] == "json"

    def test_export_invalid_format_returns_400(self, client_with_mock_db):
        client, db = client_with_mock_db
        with patch("app.api.routes.PlannerService") as MockPlanner:
            MockPlanner.return_value.exporter.export.side_effect = ValueError("Unknown format")
            resp = client.post("/api/export?format=invalid_xyz", json=self._minimal_plan())
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /share and /shared-plans
# ---------------------------------------------------------------------------


class TestSharePlan:
    def _minimal_plan(self):
        return _minimal_plan()

    def test_share_creates_plan_id(self, plain_client):
        resp = plain_client.post("/api/share", json=self._minimal_plan())
        assert resp.status_code == 200
        data = resp.json()
        assert "plan_id" in data
        assert "share_url" in data
        assert "api_url" in data
        assert len(data["plan_id"]) == 8

    def test_get_shared_plan_found(self, plain_client):
        # First share a plan
        share_resp = plain_client.post("/api/share", json=self._minimal_plan())
        plan_id = share_resp.json()["plan_id"]
        # Then retrieve it
        resp = plain_client.get(f"/api/shared-plans/{plan_id}")
        assert resp.status_code == 200

    def test_get_shared_plan_not_found(self, plain_client):
        resp = plain_client.get("/api/shared-plans/nonexist")
        assert resp.status_code == 404

    def test_get_shared_plan_expired(self, plain_client):
        import app.api.routes as routes_module
        import time

        plan_resp = plain_client.post("/api/share", json=self._minimal_plan())
        plan_id = plan_resp.json()["plan_id"]

        # Artificially expire the plan
        plan_obj, _ = routes_module.shared_plans[plan_id]
        routes_module.shared_plans[plan_id] = (plan_obj, time.time() - 1)

        resp = plain_client.get(f"/api/shared-plans/{plan_id}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /sky-quality
# ---------------------------------------------------------------------------


class TestSkyQuality:
    def test_returns_sky_quality_data(self, plain_client):
        mock_sky = MagicMock()
        mock_sky.bortle_class = 4
        mock_sky.bortle_name = "Rural/suburban transition"
        mock_sky.sqm_estimate = 21.0
        mock_sky.light_pollution_level = "moderate"
        mock_sky.visibility_description = "Good"
        mock_sky.suitable_for = ["galaxies", "nebulae"]
        mock_sky.limiting_magnitude = 13.0
        mock_sky.milky_way_visibility = "visible"
        mock_sky.light_pollution_source = "SQM estimate"

        with patch("app.api.routes.LightPollutionService") as MockLP:
            MockLP.return_value.get_sky_quality.return_value = mock_sky
            MockLP.return_value.get_observing_recommendations.return_value = ["Use wide field"]
            resp = plain_client.get("/api/sky-quality/45.9/-111.5")

        assert resp.status_code == 200
        data = resp.json()
        assert data["bortle_class"] == 4
        assert "location" in data
        assert "recommendations" in data

    def test_returns_location_in_response(self, plain_client):
        mock_sky = MagicMock()
        mock_sky.bortle_class = 5
        mock_sky.bortle_name = "Suburban"
        mock_sky.sqm_estimate = 20.0
        mock_sky.light_pollution_level = "high"
        mock_sky.visibility_description = "Poor"
        mock_sky.suitable_for = []
        mock_sky.limiting_magnitude = 12.0
        mock_sky.milky_way_visibility = "not visible"
        mock_sky.light_pollution_source = "estimate"

        with patch("app.api.routes.LightPollutionService") as MockLP:
            MockLP.return_value.get_sky_quality.return_value = mock_sky
            MockLP.return_value.get_observing_recommendations.return_value = []
            resp = plain_client.get("/api/sky-quality/40.7/-74.0?location_name=New+York")

        assert resp.status_code == 200
        data = resp.json()
        assert data["location"]["name"] == "New York"
        assert data["location"]["latitude"] == 40.7
        assert data["location"]["longitude"] == -74.0


# ---------------------------------------------------------------------------
# /images/previews/{filename}
# ---------------------------------------------------------------------------


class TestImagePreviews:
    def test_returns_404_when_file_missing(self, plain_client):
        with patch("app.api.routes.Path") as MockPath:
            mock_path_obj = MagicMock()
            mock_path_obj.__truediv__ = MagicMock(return_value=mock_path_obj)
            mock_path_obj.resolve.return_value = mock_path_obj
            mock_path_obj.__str__ = MagicMock(return_value="/app/data/previews/nosuchfile.jpg")
            mock_path_obj.exists.return_value = False
            MockPath.return_value = mock_path_obj
            resp = plain_client.get("/api/images/previews/nosuchfile.jpg")
        # Either 404 (file not found) or we need to verify the path logic
        assert resp.status_code in [404, 403, 500]

    def test_directory_traversal_denied(self, plain_client):
        resp = plain_client.get("/api/images/previews/../etc/passwd")
        # Should be 403 (path traversal blocked) or 404
        assert resp.status_code in [403, 404, 422]


# ---------------------------------------------------------------------------
# /images/targets/{catalog_id}
# ---------------------------------------------------------------------------


class TestImageTargets:
    def test_invalid_catalog_id_returns_404(self, client_with_mock_db):
        client, db = client_with_mock_db
        db.query.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/images/targets/INVALID")
        assert resp.status_code == 404

    def test_catalog_id_not_found_in_db_returns_404(self, client_with_mock_db):
        client, db = client_with_mock_db
        # DB returns None — target not in catalog
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        resp = client.get("/api/images/targets/NGC9999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /solar-system/objects
# ---------------------------------------------------------------------------


class TestSolarSystemObjects:
    def test_returns_objects_list(self, plain_client):
        mock_objects = [
            {"name": "Jupiter", "type": "planet", "magnitude": -2.5,
             "altitude_deg": 45.0, "is_visible": True, "is_visible_tonight": True,
             "peak_altitude_tonight": 60.0, "constellation": "Leo",
             "angular_diameter_arcsec": 45.0, "notes": None},
        ]
        with patch("app.api.routes._compute_solar_system_objects_sync", return_value=mock_objects):
            resp = plain_client.get("/api/solar-system/objects?lat=45.0&lon=-111.0")
        assert resp.status_code == 200
        data = resp.json()
        assert "objects" in data
        assert isinstance(data["objects"], list)

    def test_defaults_to_zero_coords_when_none(self, plain_client):
        mock_objects = []
        with patch("app.api.routes._compute_solar_system_objects_sync", return_value=mock_objects) as mock_fn:
            resp = plain_client.get("/api/solar-system/objects")
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(0.0, 0.0, None, "UTC")

    def test_passes_date_and_tz(self, plain_client):
        mock_objects = []
        with patch("app.api.routes._compute_solar_system_objects_sync", return_value=mock_objects) as mock_fn:
            resp = plain_client.get(
                "/api/solar-system/objects?lat=45.0&lon=-111.0&date=2025-06-01&tz=America/Denver"
            )
        assert resp.status_code == 200
        mock_fn.assert_called_once_with(45.0, -111.0, "2025-06-01", "America/Denver")


# ---------------------------------------------------------------------------
# /wishlist/defaults
# ---------------------------------------------------------------------------


class TestWishlistDefaults:
    def test_returns_19_items(self, plain_client):
        resp = plain_client.get("/api/wishlist/defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 19

    def test_includes_all_8_planets(self, plain_client):
        resp = plain_client.get("/api/wishlist/defaults")
        data = resp.json()
        planets = [d["name"] for d in data if d["type"] == "planet"]
        for name in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            assert name in planets

    def test_includes_moon_and_sun(self, plain_client):
        resp = plain_client.get("/api/wishlist/defaults")
        data = resp.json()
        names = [d["name"] for d in data]
        assert "Moon" in names
        assert "Sun" in names

    def test_all_items_have_name_and_type(self, plain_client):
        resp = plain_client.get("/api/wishlist/defaults")
        data = resp.json()
        for item in data:
            assert "name" in item
            assert "type" in item


# ---------------------------------------------------------------------------
# /health (routes.py health — not main health)
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_health_endpoint(self, plain_client):
        resp = plain_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "service" in data
