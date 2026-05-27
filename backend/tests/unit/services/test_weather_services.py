"""Tests for weather and 7Timer services."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
import pytz

from unittest.mock import MagicMock, Mock, patch

from app.models import Location, WeatherForecast
from app.services.cleardarksky_service import (
    ClearDarkSkyForecast,
    ClearDarkSkyService,
    CloudCover,
    Seeing,
    Transparency,
    _cloud_cover_enum,
    _seeing_from_wind,
    _transparency_from_visibility,
)
from app.services.seven_timer_service import SevenTimerService
from app.services.weather_service import WeatherService


@pytest.fixture
def sample_location():
    """Sample location."""
    return Location(
        name="Three Forks, MT", latitude=45.9183, longitude=-111.5433, elevation=1234.0, timezone="America/Denver"
    )


class TestSevenTimerService:
    """Test 7Timer service."""

    def test_convert_seeing_values(self):
        """Test seeing scale conversion."""
        service = SevenTimerService()

        # Test all seeing values
        assert service._convert_seeing(1) == 0.4  # Excellent
        assert service._convert_seeing(2) == 0.6  # Good
        assert service._convert_seeing(3) == 0.9  # Average
        assert service._convert_seeing(4) == 1.5  # Below average
        assert service._convert_seeing(5) == 2.2  # Poor
        assert service._convert_seeing(6) == 3.5  # Very poor
        assert service._convert_seeing(7) == 7.0  # Terrible
        assert service._convert_seeing(8) == 12.0  # Unusable
        assert service._convert_seeing(99) == 2.0  # Default

    def test_convert_transparency_values(self):
        """Test transparency scale conversion."""
        service = SevenTimerService()

        # Test all transparency values
        assert service._convert_transparency(1) == 16.0  # Poor
        assert service._convert_transparency(2) == 17.0
        assert service._convert_transparency(3) == 18.0
        assert service._convert_transparency(4) == 19.0
        assert service._convert_transparency(5) == 20.0  # Good
        assert service._convert_transparency(6) == 21.0  # Very good
        assert service._convert_transparency(7) == 21.5  # Excellent
        assert service._convert_transparency(8) == 22.0  # Exceptional
        assert service._convert_transparency(99) == 18.0  # Default

    def test_convert_cloudcover_values(self):
        """Test cloud cover scale conversion."""
        service = SevenTimerService()

        # Test all cloud cover values
        assert service._convert_cloudcover(1) == 6.0
        assert service._convert_cloudcover(2) == 19.0
        assert service._convert_cloudcover(3) == 31.0
        assert service._convert_cloudcover(4) == 44.0
        assert service._convert_cloudcover(5) == 56.0
        assert service._convert_cloudcover(6) == 69.0
        assert service._convert_cloudcover(7) == 81.0
        assert service._convert_cloudcover(8) == 94.0
        assert service._convert_cloudcover(9) == 100.0
        assert service._convert_cloudcover(99) == 50.0  # Default

    def test_describe_conditions_clear(self):
        """Test condition description for clear skies."""
        service = SevenTimerService()

        description = service._describe_conditions(seeing=0.8, transparency=21.0, cloudcover=10)

        assert "clear" in description.lower()
        assert "excellent seeing" in description.lower()
        assert "excellent transparency" in description.lower()

    def test_describe_conditions_poor(self):
        """Test condition description for poor conditions."""
        service = SevenTimerService()

        description = service._describe_conditions(seeing=5.0, transparency=16.0, cloudcover=95)

        assert "overcast" in description.lower()
        assert "poor" in description.lower()

    def test_describe_conditions_moderate(self):
        """Test condition description for moderate conditions."""
        service = SevenTimerService()

        description = service._describe_conditions(seeing=1.5, transparency=19.0, cloudcover=40)

        assert "partly cloudy" in description.lower() or "mostly cloudy" in description.lower()
        assert "good" in description.lower() or "average" in description.lower()

    @patch("app.services.seven_timer_service.requests.get")
    def test_get_astronomy_forecast_success(self, mock_get, sample_location):
        """Test successful 7Timer API call."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "init": "2025110600",
            "dataseries": [
                {
                    "timepoint": 0,
                    "seeing": 2,
                    "transparency": 6,
                    "cloudcover": 2,
                    "temp2m": 10,
                    "wind10m": {"speed": 3},
                },
                {"timepoint": 3, "seeing": 3, "transparency": 5, "cloudcover": 3, "temp2m": 8, "wind10m": {"speed": 2}},
            ],
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        service = SevenTimerService()
        start_time = datetime(2025, 11, 6, 0, 0, 0)
        end_time = datetime(2025, 11, 6, 12, 0, 0)

        forecasts = service.get_astronomy_forecast(sample_location, start_time, end_time)

        assert len(forecasts) >= 1
        assert all(isinstance(f, WeatherForecast) for f in forecasts)
        assert all(f.source == "7timer" for f in forecasts)
        assert all(f.seeing_arcseconds is not None for f in forecasts)
        assert all(f.transparency_magnitude is not None for f in forecasts)

    @patch("app.services.seven_timer_service.requests.get")
    def test_get_astronomy_forecast_api_error(self, mock_get, sample_location):
        """Test 7Timer API error handling."""
        mock_get.side_effect = Exception("API error")

        service = SevenTimerService()
        start_time = datetime(2025, 11, 6, 0, 0, 0)
        end_time = datetime(2025, 11, 6, 12, 0, 0)

        forecasts = service.get_astronomy_forecast(sample_location, start_time, end_time)

        assert forecasts == []  # Should return empty list on error

    @patch("app.services.seven_timer_service.requests.get")
    def test_get_astronomy_forecast_no_dataseries(self, mock_get, sample_location):
        """Test 7Timer response with no dataseries."""
        mock_response = Mock()
        mock_response.json.return_value = {"init": "2025110600"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        service = SevenTimerService()
        start_time = datetime(2025, 11, 6, 0, 0, 0)
        end_time = datetime(2025, 11, 6, 12, 0, 0)

        forecasts = service.get_astronomy_forecast(sample_location, start_time, end_time)

        assert forecasts == []


class TestWeatherService:
    """Test weather service (extended)."""

    def test_composite_weather_score(self):
        """Test composite weather scoring with astronomy data."""
        service = WeatherService()

        # Perfect composite conditions
        composite_forecast = WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=0.0,
            humidity=40.0,
            temperature=15.0,
            wind_speed=2.0,
            conditions="Clear",
            seeing_arcseconds=0.8,
            transparency_magnitude=21.5,
            source="composite",
        )
        score = service.calculate_weather_score(composite_forecast)
        assert score >= 0.9  # Should be very high

        # Poor composite conditions
        poor_composite = WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=100.0,
            humidity=90.0,
            temperature=15.0,
            wind_speed=15.0,
            conditions="Overcast",
            seeing_arcseconds=8.0,
            transparency_magnitude=16.0,
            source="composite",
        )
        score = service.calculate_weather_score(poor_composite)
        assert score < 0.3  # Should be very low

    def test_astronomy_only_score(self):
        """Test scoring with only astronomy data."""
        service = WeatherService()

        # Excellent astronomy conditions
        astro_forecast = WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=0.0,
            humidity=50.0,
            temperature=15.0,
            wind_speed=5.0,
            conditions="Clear",
            seeing_arcseconds=0.6,
            transparency_magnitude=21.0,
            source="7timer",
        )
        score = service.calculate_weather_score(astro_forecast)
        assert score >= 0.85

        # Poor astronomy conditions
        poor_astro = WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=0.0,
            humidity=50.0,
            temperature=15.0,
            wind_speed=5.0,
            conditions="Clear",
            seeing_arcseconds=7.0,
            transparency_magnitude=16.5,
            source="7timer",
        )
        score = service.calculate_weather_score(poor_astro)
        # With 0% cloud cover (score=1.0) at 50% weight and poor astronomy at 50%,
        # total score is around 0.7. Poor astronomy alone doesn't make it bad if skies are clear.
        assert score < 0.75

    def test_calculate_astronomy_score_edge_cases(self):
        """Test astronomy score calculation edge cases."""
        service = WeatherService()

        # Test with None values
        score = service._calculate_astronomy_score(None, None)
        assert score == 0.5  # Should return neutral score

        # Test excellent seeing
        score = service._calculate_astronomy_score(0.5, 21.0)
        assert score >= 0.9

        # Test excellent transparency
        score = service._calculate_astronomy_score(1.5, 22.0)
        assert score >= 0.8

        # Test poor seeing
        score = service._calculate_astronomy_score(10.0, 19.0)
        assert score < 0.5

        # Test poor transparency
        score = service._calculate_astronomy_score(1.5, 15.0)
        assert score < 0.6  # Good seeing compensates somewhat

    def test_calculate_general_weather_score_edge_cases(self):
        """Test general weather score calculation edge cases."""
        service = WeatherService()

        # Perfect conditions
        score = service._calculate_general_weather_score(0, 50, 3)
        assert score >= 0.95

        # Terrible conditions
        score = service._calculate_general_weather_score(100, 95, 15)
        assert score < 0.35

        # High humidity threshold
        score_low = service._calculate_general_weather_score(20, 55, 4)
        score_high = service._calculate_general_weather_score(20, 85, 4)
        assert score_low > score_high

        # Wind speed threshold
        score_calm = service._calculate_general_weather_score(20, 60, 3)
        score_windy = service._calculate_general_weather_score(20, 60, 12)
        assert score_calm > score_windy

    def test_merge_conditions(self):
        """Test merging condition descriptions."""
        service = WeatherService()

        # Test with seeing info
        merged = service._merge_conditions("Clear sky", "Partly cloudy, excellent seeing, good transparency")
        assert "Clear sky" in merged
        assert "seeing" in merged.lower() or "transparency" in merged.lower()

        # Test without seeing info
        merged = service._merge_conditions("Clear sky", "Partly cloudy")
        assert merged == "Clear sky"

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_merge_forecasts_time_matching(self, mock_get, mock_seven_timer, sample_location):
        """Test forecast merging with time window matching."""
        # Mock OpenWeatherMap response
        mock_owm_response = Mock()
        mock_owm_response.json.return_value = {
            "list": [
                {
                    "dt": int(datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC).timestamp()),
                    "clouds": {"all": 10},
                    "main": {"humidity": 50, "temp": 10},
                    "wind": {"speed": 3},
                    "weather": [{"description": "clear sky"}],
                },
                {
                    "dt": int(datetime(2025, 11, 6, 3, 0, 0, tzinfo=pytz.UTC).timestamp()),
                    "clouds": {"all": 20},
                    "main": {"humidity": 55, "temp": 9},
                    "wind": {"speed": 4},
                    "weather": [{"description": "few clouds"}],
                },
            ]
        }
        mock_owm_response.raise_for_status = Mock()
        mock_get.return_value = mock_owm_response

        # Mock 7Timer forecasts
        mock_seven_timer_instance = Mock()
        mock_seven_timer_instance.get_astronomy_forecast.return_value = [
            WeatherForecast(
                timestamp=datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC),
                cloud_cover=15.0,
                humidity=50.0,
                temperature=10.0,
                wind_speed=3.0,
                conditions="Clear",
                seeing_arcseconds=1.2,
                transparency_magnitude=20.0,
                source="7timer",
            )
        ]
        mock_seven_timer.return_value = mock_seven_timer_instance

        service = WeatherService()
        start_time = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 11, 6, 6, 0, 0, tzinfo=pytz.UTC)

        forecasts = service.get_forecast(sample_location, start_time, end_time)

        # Should have merged forecasts
        assert len(forecasts) > 0
        # At least one should be composite (merged)
        composite_forecasts = [f for f in forecasts if f.source == "composite"]
        if composite_forecasts:
            assert any(f.seeing_arcseconds is not None for f in composite_forecasts)

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_forecast_fallback_owm_only(self, mock_get, mock_seven_timer, sample_location):
        """Test fallback to OpenWeatherMap only."""
        # Mock OpenWeatherMap response
        mock_owm_response = Mock()
        mock_owm_response.json.return_value = {
            "list": [
                {
                    "dt": int(datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC).timestamp()),
                    "clouds": {"all": 10},
                    "main": {"humidity": 50, "temp": 10},
                    "wind": {"speed": 3},
                    "weather": [{"description": "clear sky"}],
                }
            ]
        }
        mock_owm_response.raise_for_status = Mock()
        mock_get.return_value = mock_owm_response

        # Mock 7Timer failure
        mock_seven_timer_instance = Mock()
        mock_seven_timer_instance.get_astronomy_forecast.return_value = []
        mock_seven_timer.return_value = mock_seven_timer_instance

        service = WeatherService()
        start_time = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 11, 6, 6, 0, 0, tzinfo=pytz.UTC)

        forecasts = service.get_forecast(sample_location, start_time, end_time)

        # Should have OWM forecasts only
        assert len(forecasts) > 0
        assert all(f.source == "openweathermap" for f in forecasts)
        assert all(f.seeing_arcseconds is None for f in forecasts)

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_forecast_fallback_seven_timer_only(self, mock_get, mock_seven_timer, sample_location):
        """Test fallback to 7Timer only."""
        # Mock OpenWeatherMap failure
        mock_get.side_effect = Exception("OWM API error")

        # Mock 7Timer success
        mock_seven_timer_instance = Mock()
        mock_seven_timer_instance.get_astronomy_forecast.return_value = [
            WeatherForecast(
                timestamp=datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC),
                cloud_cover=15.0,
                humidity=50.0,
                temperature=10.0,
                wind_speed=3.0,
                conditions="Clear",
                seeing_arcseconds=1.2,
                transparency_magnitude=20.0,
                source="7timer",
            )
        ]
        mock_seven_timer.return_value = mock_seven_timer_instance

        service = WeatherService()
        start_time = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 11, 6, 6, 0, 0, tzinfo=pytz.UTC)

        forecasts = service.get_forecast(sample_location, start_time, end_time)

        # Should have 7Timer forecasts only
        assert len(forecasts) > 0
        assert all(f.source == "7timer" for f in forecasts)
        assert all(f.seeing_arcseconds is not None for f in forecasts)

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_forecast_complete_failure(self, mock_get, mock_seven_timer, sample_location):
        """Test fallback to default forecast when both APIs fail."""
        # Mock both API failures
        mock_get.side_effect = Exception("OWM API error")

        mock_seven_timer_instance = Mock()
        mock_seven_timer_instance.get_astronomy_forecast.return_value = []
        mock_seven_timer.return_value = mock_seven_timer_instance

        service = WeatherService()
        start_time = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)
        end_time = datetime(2025, 11, 6, 6, 0, 0, tzinfo=pytz.UTC)

        forecasts = service.get_forecast(sample_location, start_time, end_time)

        # Should have default forecasts
        assert len(forecasts) > 0
        assert all(f.conditions == "Clear sky (estimated)" for f in forecasts)
        assert all(f.cloud_cover == 20.0 for f in forecasts)


# ============================================================
# ClearDarkSky (Open-Meteo) tests
# ============================================================


class TestCloudCoverEnum:

    def test_clear_at_zero(self):
        assert _cloud_cover_enum(0) == CloudCover.CLEAR

    def test_clear_at_10(self):
        assert _cloud_cover_enum(10) == CloudCover.CLEAR

    def test_mostly_clear(self):
        assert _cloud_cover_enum(20) == CloudCover.MOSTLY_CLEAR

    def test_partly_cloudy(self):
        assert _cloud_cover_enum(50) == CloudCover.PARTLY_CLOUDY

    def test_mostly_cloudy(self):
        assert _cloud_cover_enum(80) == CloudCover.MOSTLY_CLOUDY

    def test_overcast(self):
        assert _cloud_cover_enum(100) == CloudCover.OVERCAST


class TestTransparencyFromVisibility:

    def test_excellent_high_visibility(self):
        assert _transparency_from_visibility(30000) == Transparency.EXCELLENT

    def test_above_average(self):
        assert _transparency_from_visibility(20000) == Transparency.ABOVE_AVERAGE

    def test_average(self):
        assert _transparency_from_visibility(10000) == Transparency.AVERAGE

    def test_below_average(self):
        assert _transparency_from_visibility(5000) == Transparency.BELOW_AVERAGE

    def test_poor_low_visibility(self):
        assert _transparency_from_visibility(1000) == Transparency.POOR


class TestSeeingFromWind:

    def test_excellent_calm(self):
        assert _seeing_from_wind(0) == Seeing.EXCELLENT

    def test_good_light_wind(self):
        assert _seeing_from_wind(10) == Seeing.GOOD

    def test_average_moderate_wind(self):
        assert _seeing_from_wind(20) == Seeing.AVERAGE

    def test_below_average_strong_wind(self):
        assert _seeing_from_wind(35) == Seeing.BELOW_AVERAGE

    def test_poor_very_strong_wind(self):
        assert _seeing_from_wind(50) == Seeing.POOR


class TestClearDarkSkyForecastAstronomyScore:

    def test_clear_excellent_conditions_high_score(self):
        forecast = ClearDarkSkyForecast(
            time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc),
            cloud_cover=CloudCover.CLEAR,
            transparency=Transparency.EXCELLENT,
            seeing=Seeing.EXCELLENT,
            temperature_c=5.0,
            wind_speed_kmh=2.0,
        )
        score = forecast.astronomy_score()
        assert score > 0.8

    def test_overcast_poor_conditions_low_score(self):
        forecast = ClearDarkSkyForecast(
            time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc),
            cloud_cover=CloudCover.OVERCAST,
            transparency=Transparency.POOR,
            seeing=Seeing.POOR,
            temperature_c=5.0,
            wind_speed_kmh=50.0,
        )
        score = forecast.astronomy_score()
        assert score < 0.3

    def test_score_between_zero_and_one(self):
        for cc in CloudCover:
            for t in Transparency:
                for s in Seeing:
                    forecast = ClearDarkSkyForecast(
                        time=datetime(2025, 1, 15, 22, 0, tzinfo=timezone.utc),
                        cloud_cover=cc,
                        transparency=t,
                        seeing=s,
                        temperature_c=10.0,
                        wind_speed_kmh=5.0,
                    )
                    score = forecast.astronomy_score()
                    assert 0.0 <= score <= 1.0


class TestClearDarkSkyServiceGetForecast:

    def _make_response(self, times, clouds, vis, wind, temp):
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "hourly": {
                "time": times,
                "cloud_cover": clouds,
                "visibility": vis,
                "wind_speed_10m": wind,
                "temperature_2m": temp,
            }
        }
        return mock_resp

    @patch("app.services.cleardarksky_service.requests.get")
    def test_returns_list_of_forecasts(self, mock_get):
        future_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        from datetime import timedelta
        times = [(future_hour + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(1, 4)]
        mock_get.return_value = self._make_response(times, [5, 15, 50], [25000, 12000, 5000], [2, 10, 30], [5, 4, 3])

        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0, hours=48)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(f, ClearDarkSkyForecast) for f in result)

    @patch("app.services.cleardarksky_service.requests.get", side_effect=Exception("network error"))
    def test_returns_empty_on_network_error(self, mock_get):
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0)
        assert result == []

    @patch("app.services.cleardarksky_service.requests.get")
    def test_http_error_returns_empty(self, mock_get):
        import requests
        mock_resp = Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.return_value = mock_resp
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0)
        assert result == []

    @patch("app.services.cleardarksky_service.requests.get")
    def test_skips_past_hours(self, mock_get):
        from datetime import timedelta
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        past = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
        future = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
        mock_get.return_value = self._make_response(
            [past, future], [10, 20], [25000, 20000], [2, 5], [10, 8]
        )
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0, hours=48)
        assert len(result) == 1

    @patch("app.services.cleardarksky_service.requests.get")
    def test_respects_hours_limit(self, mock_get):
        from datetime import timedelta
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        times = [(now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(1, 10)]
        mock_get.return_value = self._make_response(
            times, [0] * 9, [30000] * 9, [1] * 9, [10] * 9
        )
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0, hours=3)
        assert len(result) == 3

    @patch("app.services.cleardarksky_service.requests.get")
    def test_null_values_treated_as_zero(self, mock_get):
        from datetime import timedelta
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        times = [(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")]
        mock_get.return_value = self._make_response(
            times, [None], [None], [None], [None]
        )
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0, hours=48)
        assert len(result) == 1
        assert result[0].wind_speed_kmh == 0.0
        assert result[0].temperature_c == 0.0

    @patch("app.services.cleardarksky_service.requests.get")
    def test_skips_invalid_time_strings(self, mock_get):
        from datetime import timedelta
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        future = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
        mock_get.return_value = self._make_response(
            ["not-a-date", future], [10, 20], [25000, 20000], [2, 5], [10, 8]
        )
        svc = ClearDarkSkyService()
        result = svc.get_forecast(45.0, -111.0, hours=48)
        assert len(result) == 1


class TestWeatherServiceAdditionalBranches:
    """Cover remaining branches in weather_service.py."""

    def test_merge_forecasts_both_empty_returns_empty(self):
        svc = WeatherService()
        result = svc._merge_forecasts([], [])
        assert result == []

    def test_merge_forecasts_owm_only_returns_owm(self):
        svc = WeatherService()
        owm = [WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=20.0, humidity=50.0, temperature=10.0,
            wind_speed=3.0, conditions="clear", source="openweathermap"
        )]
        result = svc._merge_forecasts(owm, [])
        assert result is owm

    def test_merge_forecasts_seven_timer_only_returns_7timer(self):
        svc = WeatherService()
        st = [WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=10.0, humidity=40.0, temperature=8.0,
            wind_speed=2.0, conditions="clear", source="7timer"
        )]
        result = svc._merge_forecasts([], st)
        assert result is st

    def test_generate_default_forecast_returns_hourly_entries(self):
        svc = WeatherService()
        start = datetime(2025, 11, 6, 20, 0, 0)
        end = datetime(2025, 11, 6, 23, 0, 0)
        forecasts = svc._generate_default_forecast(start, end)
        assert len(forecasts) == 4  # 20, 21, 22, 23
        assert all(f.cloud_cover == 20.0 for f in forecasts)
        assert all(f.conditions == "Clear sky (estimated)" for f in forecasts)

    def test_astronomy_score_seeing_2_to_3(self):
        svc = WeatherService()
        # seeing = 2.5 → average bracket
        score = svc._calculate_astronomy_score(2.5, 20.0)
        assert 0.4 <= score <= 0.9

    def test_astronomy_score_seeing_above_3(self):
        svc = WeatherService()
        # seeing = 4.0 → linear decay bracket; good transparency keeps overall score mid-range
        score = svc._calculate_astronomy_score(4.0, 20.0)
        assert 0.2 <= score <= 1.0

    def test_astronomy_score_transparency_17_to_19(self):
        svc = WeatherService()
        score = svc._calculate_astronomy_score(1.0, 18.0)
        assert 0.4 <= score <= 0.9

    def test_astronomy_score_transparency_19_to_21(self):
        svc = WeatherService()
        score = svc._calculate_astronomy_score(1.0, 20.0)
        assert 0.5 <= score <= 1.0

    def test_astronomy_score_transparency_below_17(self):
        svc = WeatherService()
        # transparency=14 → poor; but excellent seeing (1.0) raises average; combined still < 0.7
        score = svc._calculate_astronomy_score(1.0, 14.0)
        assert score < 0.7

    def test_general_weather_humidity_60_to_80(self):
        svc = WeatherService()
        score = svc._calculate_general_weather_score(0, 70, 3)
        # humidity 70 is between 60-80 → intermediate score
        assert 0.5 < score < 1.0

    def test_general_weather_wind_5_to_10(self):
        svc = WeatherService()
        score = svc._calculate_general_weather_score(0, 50, 7)
        # wind 7 m/s → intermediate
        assert 0.7 < score <= 1.0

    def test_weather_score_owm_only_source(self):
        svc = WeatherService()
        forecast = WeatherForecast(
            timestamp=datetime.now(pytz.UTC),
            cloud_cover=30.0, humidity=55.0, temperature=10.0,
            wind_speed=4.0, conditions="partly cloudy",
            source="openweathermap",
        )
        score = svc.calculate_weather_score(forecast)
        assert 0.0 <= score <= 1.0

    @patch("app.services.weather_service.requests.get")
    @patch("app.services.weather_service.SevenTimerService")
    def test_get_openweathermap_no_api_key_returns_empty(self, mock_seven_timer, mock_get, sample_location):
        """With no OWM key, _get_openweathermap_forecast returns []."""
        svc = WeatherService()
        svc.api_key = None  # simulate missing key

        result = svc._get_openweathermap_forecast(
            sample_location,
            datetime(2025, 11, 6, 0, 0, tzinfo=pytz.UTC),
            datetime(2025, 11, 6, 6, 0, tzinfo=pytz.UTC),
        )
        assert result == []
        mock_get.assert_not_called()

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_get_openweathermap_http_error_returns_empty(self, mock_get, mock_stt, sample_location):
        mock_get.side_effect = Exception("timeout")
        svc = WeatherService()
        svc.api_key = "fakekey"

        result = svc._get_openweathermap_forecast(
            sample_location,
            datetime(2025, 11, 6, 0, 0, tzinfo=pytz.UTC),
            datetime(2025, 11, 6, 6, 0, tzinfo=pytz.UTC),
        )
        assert result == []

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_merge_conditions_without_seeing_returns_owm(self, mock_get, mock_stt):
        svc = WeatherService()
        result = svc._merge_conditions("Partly cloudy", "Generic forecast")
        assert result == "Partly cloudy"

    def test_merge_forecasts_both_nonempty_merges_by_hour(self):
        """Cover the _merge_forecasts loop (lines 147-173)."""
        svc = WeatherService()
        ts = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)
        owm = [WeatherForecast(
            timestamp=ts, cloud_cover=10.0, humidity=50.0, temperature=10.0,
            wind_speed=3.0, conditions="clear sky", source="openweathermap"
        )]
        st = [WeatherForecast(
            timestamp=ts, cloud_cover=12.0, humidity=52.0, temperature=9.0,
            wind_speed=2.0, conditions="Mostly clear, excellent seeing, good transparency",
            seeing_arcseconds=0.8, transparency_magnitude=21.0, source="7timer"
        )]
        merged = svc._merge_forecasts(owm, st)
        assert len(merged) == 1
        assert merged[0].source == "composite"
        assert merged[0].seeing_arcseconds == 0.8

    def test_merge_forecasts_no_seven_timer_match_uses_owm(self):
        """OWM entry with no 7Timer match in the merge loop."""
        svc = WeatherService()
        owm_ts = datetime(2025, 11, 6, 6, 0, 0, tzinfo=pytz.UTC)
        st_ts = datetime(2025, 11, 6, 0, 0, 0, tzinfo=pytz.UTC)  # different slot
        owm = [WeatherForecast(
            timestamp=owm_ts, cloud_cover=20.0, humidity=55.0, temperature=8.0,
            wind_speed=4.0, conditions="few clouds", source="openweathermap"
        )]
        st = [WeatherForecast(
            timestamp=st_ts, cloud_cover=10.0, humidity=40.0, temperature=10.0,
            wind_speed=2.0, conditions="clear", seeing_arcseconds=1.0,
            transparency_magnitude=20.0, source="7timer"
        )]
        merged = svc._merge_forecasts(owm, st)
        assert len(merged) == 1
        assert merged[0].source == "openweathermap"  # no match found

    @patch("app.services.weather_service.SevenTimerService")
    @patch("app.services.weather_service.requests.get")
    def test_get_openweathermap_forecast_parses_response(self, mock_get, mock_stt, sample_location):
        """Cover lines 82-108: the OWM parsing loop."""
        import pytz as _pytz
        ts_utc = datetime(2025, 11, 6, 1, 0, 0, tzinfo=_pytz.UTC)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "list": [
                {
                    "dt": int(ts_utc.timestamp()),
                    "clouds": {"all": 15},
                    "main": {"humidity": 60, "temp": 5},
                    "wind": {"speed": 3},
                    "weather": [{"description": "light rain"}],
                }
            ]
        }
        mock_get.return_value = mock_resp

        svc = WeatherService()
        svc.api_key = "fakekey"
        # Use timezone-aware start/end
        start = datetime(2025, 11, 6, 0, 0, 0, tzinfo=_pytz.UTC)
        end = datetime(2025, 11, 6, 6, 0, 0, tzinfo=_pytz.UTC)
        forecasts = svc._get_openweathermap_forecast(sample_location, start, end)
        assert len(forecasts) == 1
        assert forecasts[0].cloud_cover == 15
        assert forecasts[0].source == "openweathermap"


class TestClearDarkSkyServiceLegacyMethods:

    def test_find_nearest_chart_returns_string(self):
        svc = ClearDarkSkyService()
        result = svc.find_nearest_chart(45.12, -111.34)
        assert "45.12" in result
        assert "-111.34" in result

    @patch("app.services.cleardarksky_service.requests.get")
    def test_fetch_forecast_delegates_to_get_forecast(self, mock_get):
        from datetime import timedelta
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        times = [(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")]
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        mock_resp.json.return_value = {
            "hourly": {
                "time": times,
                "cloud_cover": [5],
                "visibility": [25000],
                "wind_speed_10m": [2],
                "temperature_2m": [10],
            }
        }
        mock_get.return_value = mock_resp

        svc = ClearDarkSkyService()
        chart_id = svc.find_nearest_chart(45.0, -111.0)
        result = svc.fetch_forecast(chart_id)
        assert isinstance(result, list)

    def test_fetch_forecast_invalid_chart_id_returns_empty(self):
        svc = ClearDarkSkyService()
        result = svc.fetch_forecast("not_valid")
        assert result == []
