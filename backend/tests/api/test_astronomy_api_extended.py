"""Extended tests for astronomy API endpoints — covering uncovered paths."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.services.satellite_service import PassVisibility, SatellitePass
from app.services.viewing_months_service import MonthRating, ViewingMonth

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pass(name="ISS (ZARYA)"):
    t = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc)
    return SatellitePass(
        satellite_name=name,
        start_time=t,
        end_time=t,
        max_altitude_deg=55.0,
        max_altitude_time=t,
        start_azimuth_deg=270.0,
        end_azimuth_deg=90.0,
        visibility=PassVisibility.EXCELLENT,
        magnitude=-3.5,
    )


def _make_month(n=1, rating=MonthRating.EXCELLENT):
    return ViewingMonth(
        month=n,
        month_name=f"Month{n}",
        rating=rating,
        visibility_hours=8.0,
        best_time="22:00",
        notes="Clear",
    )


# ---------------------------------------------------------------------------
# get_local_weather
# ---------------------------------------------------------------------------


class TestGetLocalWeather:
    @patch("app.api.astronomy.LocalWeatherService")
    def test_local_weather_returns_data(self, MockLW):
        reading = MagicMock()
        reading.to_dict.return_value = {"temp_f": 65.0, "humidity_pct": 50}
        MockLW.return_value.get_current.return_value = reading

        resp = client.get("/api/weather/local")
        assert resp.status_code == 200
        assert resp.json()["temp_f"] == 65.0

    @patch("app.api.astronomy.LocalWeatherService")
    def test_local_weather_503_when_unreachable(self, MockLW):
        MockLW.return_value.get_current.return_value = None

        resp = client.get("/api/weather/local")
        assert resp.status_code == 503
        assert "unreachable" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# get_multiday_weather — unit (no DB required)
# ---------------------------------------------------------------------------


class TestGetMultiDayWeatherUnit:
    @pytest.fixture(autouse=True)
    def clear_overrides(self):
        yield
        app.dependency_overrides.clear()

    def test_multiday_no_location_returns_empty_list(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch("app.api.astronomy.SettingsService") as MockSS:
            MockSS.return_value.get_location.return_value = None
            resp = client.get("/api/weather/multiday")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_multiday_with_location_returns_forecasts(self):
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        from app.models.models import DailyForecast, Location as Loc

        mock_loc = Loc(name="Test", latitude=45.0, longitude=-111.0, elevation=0.0, timezone="UTC")
        mock_fc = DailyForecast(
            date="2026-05-26",
            cloud_pct=10.0,
            temp_min=5.0,
            temp_max=20.0,
            wind_mps=2.0,
            precip_mm=0.0,
            astronomy_score=90.0,
        )

        with (
            patch("app.api.astronomy.SettingsService") as MockSS,
            patch("app.api.astronomy.MultiDayWeatherService") as MockMD,
        ):
            MockSS.return_value.get_location.return_value = mock_loc
            MockMD.return_value.get_forecast.return_value = [mock_fc]
            resp = client.get("/api/weather/multiday")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["date"] == "2026-05-26"


# ---------------------------------------------------------------------------
# get_astronomy_weather error path
# ---------------------------------------------------------------------------


class TestAstronomyWeatherErrors:
    @patch("app.api.astronomy.SevenTimerService")
    def test_astronomy_weather_service_exception_returns_500(self, MockST):
        MockST.return_value.get_astronomy_forecast.side_effect = RuntimeError("network failure")

        resp = client.get("/api/weather/astronomy?lat=40.0&lon=-74.0&hours=24")
        assert resp.status_code == 500
        assert "Error fetching astronomy weather" in resp.json()["detail"]

    @patch("app.services.seven_timer_service.SevenTimerService.get_astronomy_forecast")
    def test_astronomy_weather_with_valid_forecast(self, mock_forecast):
        from app.models import WeatherForecast

        forecast = WeatherForecast(
            timestamp=datetime(2026, 1, 1, 20, 0),
            cloud_cover=5,
            transparency_magnitude=1,
            seeing_arcseconds=1.0,
            temperature=10.0,
            wind_speed=2.0,
            humidity=40,
            conditions="Excellent",
        )
        mock_forecast.return_value = [forecast]

        resp = client.get("/api/weather/astronomy?lat=40.0&lon=-74.0&hours=12")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "7timer"
        assert data["count"] == 1


# ---------------------------------------------------------------------------
# ISS passes — error paths
# ---------------------------------------------------------------------------


class TestISSPassesErrors:
    @patch("app.api.astronomy.SatelliteService")
    def test_iss_passes_service_exception_returns_500(self, MockSS):
        MockSS.return_value.get_iss_passes.side_effect = RuntimeError("TLE fetch failed")

        resp = client.get("/api/satellites/iss?lat=40.0&lon=-74.0&days=3")
        assert resp.status_code == 500
        assert "Error fetching ISS passes" in resp.json()["detail"]

    @patch("app.api.astronomy.SatelliteService")
    def test_iss_passes_empty_list(self, MockSS):
        MockSS.return_value.get_iss_passes.return_value = []

        resp = client.get("/api/satellites/iss?lat=40.0&lon=-74.0&days=3")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


# ---------------------------------------------------------------------------
# Generic satellite passes — error paths
# ---------------------------------------------------------------------------


class TestSatellitePassesErrors:
    @patch("app.api.astronomy.SatelliteService")
    def test_satellite_passes_service_exception_returns_500(self, MockSS):
        MockSS.return_value.get_satellite_passes.side_effect = RuntimeError("orbit error")

        resp = client.get("/api/satellites/passes?norad_id=25544&lat=40.0&lon=-74.0")
        assert resp.status_code == 500
        assert "Error fetching satellite passes" in resp.json()["detail"]

    @patch("app.api.astronomy.SatelliteService")
    def test_satellite_passes_returns_name(self, MockSS):
        MockSS.return_value.get_satellite_passes.return_value = [_make_pass("Hubble")]

        resp = client.get(
            "/api/satellites/passes?norad_id=20580&lat=40.0&lon=-74.0&satellite_name=Hubble"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["satellite_name"] == "Hubble"
        assert data["norad_id"] == 20580


# ---------------------------------------------------------------------------
# Viewing months — error paths
# ---------------------------------------------------------------------------


class TestViewingMonthsErrors:
    @patch("app.api.astronomy.ViewingMonthsService")
    def test_viewing_months_service_exception_returns_500(self, MockVM):
        MockVM.return_value.calculate_viewing_months.side_effect = RuntimeError("calc error")

        resp = client.get("/api/viewing-months?ra_hours=5.0&dec_degrees=-5.0&latitude=40.0")
        assert resp.status_code == 500
        assert "Error calculating viewing months" in resp.json()["detail"]

    @patch("app.api.astronomy.ViewingMonthsService")
    def test_viewing_months_returns_coordinates(self, MockVM):
        MockVM.return_value.calculate_viewing_months.return_value = [_make_month(1), _make_month(2)]

        resp = client.get(
            "/api/viewing-months?ra_hours=5.0&dec_degrees=-5.0&latitude=40.0&object_name=M42"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["coordinates"]["ra_hours"] == 5.0
        assert data["observer_latitude"] == 40.0


# ---------------------------------------------------------------------------
# Viewing months summary — error paths
# ---------------------------------------------------------------------------


class TestViewingMonthsSummaryErrors:
    @patch("app.api.astronomy.ViewingMonthsService")
    def test_summary_service_exception_returns_500(self, MockVM):
        MockVM.return_value.calculate_viewing_months.side_effect = RuntimeError("fail")

        resp = client.get("/api/viewing-months/summary?ra_hours=5.0&dec_degrees=-5.0&latitude=40.0")
        assert resp.status_code == 500
        assert "Error generating viewing summary" in resp.json()["detail"]

    @patch("app.api.astronomy.ViewingMonthsService")
    def test_summary_includes_coordinates(self, MockVM):
        MockVM.return_value.calculate_viewing_months.return_value = [_make_month()]
        MockVM.return_value.get_viewing_summary.return_value = {
            "best_months": ["January"],
            "good_months_count": 1,
            "peak_month": "January",
        }

        resp = client.get("/api/viewing-months/summary?ra_hours=5.0&dec_degrees=-5.0&latitude=40.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["coordinates"]["ra_hours"] == 5.0


# ---------------------------------------------------------------------------
# Altitude curve
# ---------------------------------------------------------------------------


class TestAltitudeCurve:
    def test_altitude_curve_with_ra_dec(self):
        with patch("app.api.astronomy.EphemerisService") as MockEph:
            MockEph.return_value.calculate_position.return_value = (45.0, 180.0)
            resp = client.get(
                "/api/altitude-curve"
                "?lat=40.0&lon=-105.0"
                "&imaging_start=2026-01-01T22:00:00"
                "&imaging_end=2026-01-01T23:00:00"
                "&ra_hours=5.0&dec_degrees=-5.0"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data
        assert len(data["points"]) > 0

    def test_altitude_curve_missing_params_returns_400(self):
        resp = client.get(
            "/api/altitude-curve"
            "?lat=40.0&lon=-105.0"
            "&imaging_start=2026-01-01T22:00:00"
            "&imaging_end=2026-01-01T23:00:00"
        )
        assert resp.status_code == 400
        assert "Provide either" in resp.json()["detail"]

    def test_altitude_curve_end_before_start_returns_400(self):
        resp = client.get(
            "/api/altitude-curve"
            "?lat=40.0&lon=-105.0"
            "&imaging_start=2026-01-01T23:00:00"
            "&imaging_end=2026-01-01T22:00:00"
            "&ra_hours=5.0&dec_degrees=-5.0"
        )
        assert resp.status_code == 400
        assert "imaging_end must be after" in resp.json()["detail"]

    def test_altitude_curve_with_body_name_sun(self):
        # Use naive UTC times to avoid URL-encoding issues with the '+' in '+00:00'
        resp = client.get(
            "/api/altitude-curve"
            "?lat=40.0&lon=-105.0"
            "&imaging_start=2026-06-15T18:00:00"
            "&imaging_end=2026-06-15T19:00:00"
            "&body_name=Sun"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data

    def test_altitude_curve_with_body_name_moon(self):
        resp = client.get(
            "/api/altitude-curve"
            "?lat=40.0&lon=-105.0"
            "&imaging_start=2026-06-15T04:00:00"
            "&imaging_end=2026-06-15T05:00:00"
            "&body_name=Moon"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data

    def test_altitude_curve_service_exception_returns_500(self):
        with patch("app.api.astronomy.EphemerisService") as MockEph:
            MockEph.return_value.calculate_position.side_effect = RuntimeError("astropy fail")
            resp = client.get(
                "/api/altitude-curve"
                "?lat=40.0&lon=-105.0"
                "&imaging_start=2026-01-01T22:00:00"
                "&imaging_end=2026-01-01T23:00:00"
                "&ra_hours=5.0&dec_degrees=-5.0"
            )
        assert resp.status_code == 500
        assert "Error computing altitude curve" in resp.json()["detail"]
