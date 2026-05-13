from unittest.mock import MagicMock, patch

import pytest
from app.models.models import DailyForecast, Location
from app.services.multi_day_weather_service import MultiDayWeatherService


@pytest.fixture
def location():
    return Location(
        name="Test",
        latitude=45.92,
        longitude=-111.54,
        elevation=1234.0,
        timezone="America/Denver",
    )


OPEN_METEO_RESPONSE = {
    "daily": {
        "time": ["2026-05-14", "2026-05-15"],
        "cloud_cover_mean": [20.0, 80.0],
        "temperature_2m_max": [18.0, 15.0],
        "temperature_2m_min": [8.0, 6.0],
        "wind_speed_10m_max": [3.5, 12.0],
        "precipitation_sum": [0.0, 5.0],
        "precipitation_probability_max": [5, 70],
    }
}


class TestMultiDayWeatherService:
    def test_returns_list_of_daily_forecasts(self, location):
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert len(forecasts) == 2
        assert all(isinstance(f, DailyForecast) for f in forecasts)

    def test_astronomy_score_is_100_minus_cloud(self, location):
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = OPEN_METEO_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert forecasts[0].astronomy_score == pytest.approx(80.0)
        assert forecasts[1].astronomy_score == pytest.approx(20.0)

    def test_astronomy_score_clamped_0_to_100(self, location):
        resp = {
            "daily": {
                "time": ["2026-05-14"],
                "cloud_cover_mean": [110.0],
                "temperature_2m_max": [20.0],
                "temperature_2m_min": [5.0],
                "wind_speed_10m_max": [1.0],
                "precipitation_sum": [0.0],
                "precipitation_probability_max": [0],
            }
        }
        svc = MultiDayWeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = resp
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            forecasts = svc.get_forecast(location)
        assert forecasts[0].astronomy_score == 0.0

    def test_returns_empty_on_network_error(self, location):
        import requests

        svc = MultiDayWeatherService()
        with patch("requests.get", side_effect=requests.RequestException("timeout")):
            forecasts = svc.get_forecast(location)
        assert forecasts == []
