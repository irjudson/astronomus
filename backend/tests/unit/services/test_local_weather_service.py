"""Unit tests for LocalWeatherService and LocalWeatherReading."""

from unittest.mock import MagicMock, patch


_SAMPLE_DATA = {
    "timestamp": "2026-05-26T22:00:00Z",
    "outdoor_temp_f": 59.0,
    "feels_like_f": 57.0,
    "dew_point_f": 45.0,
    "humidity_pct": 60,
    "wind_speed_mph": 8.0,
    "wind_gust_mph": 12.0,
    "wind_direction_deg": 270,
    "rain_rate_in_hr": 0.0,
    "daily_rain_in": 0.0,
    "relative_pressure_inhg": 30.1,
    "uv_index": 0.0,
    "solar_radiation_wm2": 0.0,
    "indoor_temp_f": 68.0,
    "indoor_humidity_pct": 45,
}


def test_reading_parses_all_fields():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading(_SAMPLE_DATA)
    assert r.outdoor_temp_f == 59.0
    assert r.humidity_pct == 60
    assert r.wind_speed_mph == 8.0
    assert r.wind_direction_deg == 270
    assert r.dew_point_f == 45.0
    assert r.indoor_temp_f == 68.0
    assert r.indoor_humidity_pct == 45


def test_reading_converts_temp_to_celsius():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading(_SAMPLE_DATA)
    expected_c = (59.0 - 32) * 5 / 9
    assert abs(r.outdoor_temp_c - expected_c) < 0.001


def test_is_raining_false_when_zero_rate():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "rain_rate_in_hr": 0.0})
    assert r.is_raining is False


def test_is_raining_true_when_rate_positive():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "rain_rate_in_hr": 0.12})
    assert r.is_raining is True


def test_is_raining_false_when_rate_none():
    from app.services.local_weather_service import LocalWeatherReading

    data = {k: v for k, v in _SAMPLE_DATA.items() if k != "rain_rate_in_hr"}
    r = LocalWeatherReading(data)
    assert r.is_raining is False


def test_dew_point_spread_correct():
    from app.services.local_weather_service import LocalWeatherReading

    # temp=59F, dew=45F → spread=14F
    r = LocalWeatherReading({**_SAMPLE_DATA, "outdoor_temp_f": 59.0, "dew_point_f": 45.0})
    spread = r.outdoor_temp_f - r.dew_point_f
    assert abs(spread - 14.0) < 0.001


def test_astronomy_suitability_score_clear_conditions():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading(_SAMPLE_DATA)
    result = r.astronomy_suitability()
    assert 0.0 <= result["score"] <= 1.0
    assert isinstance(result["issues"], list)
    assert isinstance(result["ok"], bool)


def test_astronomy_suitability_score_flags_rain():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "rain_rate_in_hr": 0.5})
    result = r.astronomy_suitability()
    assert not result["ok"]
    assert any("Rain" in issue for issue in result["issues"])


def test_astronomy_suitability_score_flags_high_humidity():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "humidity_pct": 95})
    result = r.astronomy_suitability()
    assert not result["ok"]
    assert any("humidity" in issue.lower() for issue in result["issues"])


def test_astronomy_suitability_score_flags_high_wind():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "wind_speed_mph": 30.0})
    result = r.astronomy_suitability()
    assert not result["ok"]
    assert any("wind" in issue.lower() for issue in result["issues"])


def test_astronomy_suitability_score_near_dew_point():
    from app.services.local_weather_service import LocalWeatherReading

    # spread < 3F → dew risk
    r = LocalWeatherReading({**_SAMPLE_DATA, "outdoor_temp_f": 50.0, "dew_point_f": 48.5})
    result = r.astronomy_suitability()
    assert any("dew" in issue.lower() for issue in result["issues"])


def test_get_current_returns_reading_on_success():
    from app.services.local_weather_service import LocalWeatherService, LocalWeatherReading

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _SAMPLE_DATA

    with patch("app.services.local_weather_service.requests.get", return_value=mock_resp):
        svc = LocalWeatherService()
        result = svc.get_current()

    assert isinstance(result, LocalWeatherReading)
    assert result.outdoor_temp_f == 59.0


def test_get_current_returns_none_on_http_error():
    from app.services.local_weather_service import LocalWeatherService
    import requests as req_lib

    with patch(
        "app.services.local_weather_service.requests.get",
        side_effect=req_lib.exceptions.ConnectionError("wx-service down"),
    ):
        svc = LocalWeatherService()
        result = svc.get_current()

    assert result is None


def test_get_current_returns_none_on_timeout():
    from app.services.local_weather_service import LocalWeatherService
    import requests as req_lib

    with patch(
        "app.services.local_weather_service.requests.get",
        side_effect=req_lib.exceptions.Timeout("timed out"),
    ):
        svc = LocalWeatherService()
        result = svc.get_current()

    assert result is None


def test_reading_handles_missing_optional_fields():
    from app.services.local_weather_service import LocalWeatherReading

    minimal = {"timestamp": "2026-05-26T22:00:00Z"}
    r = LocalWeatherReading(minimal)
    assert r.outdoor_temp_f == 0
    assert r.humidity_pct == 0
    assert r.wind_speed_mph == 0
    assert r.dew_point_f is None
    assert r.dew_point_c is None
    assert r.rain_rate_in_hr is None
    assert r.is_raining is False


def test_wind_direction_compass():
    from app.services.local_weather_service import LocalWeatherReading

    r = LocalWeatherReading({**_SAMPLE_DATA, "wind_direction_deg": 270})
    assert r.wind_direction_compass == "W"


def test_wind_direction_compass_none_when_missing():
    from app.services.local_weather_service import LocalWeatherReading

    data = {k: v for k, v in _SAMPLE_DATA.items() if k != "wind_direction_deg"}
    r = LocalWeatherReading(data)
    assert r.wind_direction_compass is None
