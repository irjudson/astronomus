"""Multi-day weather forecast service using Open-Meteo (free, no auth)."""

import logging
from typing import List

import requests

from app.models.models import DailyForecast, Location

logger = logging.getLogger(__name__)

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_DAILY_VARS = (
    "cloud_cover_mean,temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max,wind_speed_10m_max,precipitation_sum"
)


class MultiDayWeatherService:
    """Fetch 7-day daily forecast from Open-Meteo (no API key required)."""

    def get_forecast(self, location: Location, forecast_days: int = 7) -> List[DailyForecast]:
        """Return up to *forecast_days* DailyForecast objects for *location*.

        Returns an empty list on network/parse errors so callers degrade gracefully.
        """
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": _DAILY_VARS,
            "forecast_days": forecast_days,
            "timezone": "auto",
        }
        try:
            resp = requests.get(_OPEN_METEO_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("Open-Meteo request failed: %s", exc)
            return []

        try:
            daily = data["daily"]
            results: List[DailyForecast] = []
            for i, date in enumerate(daily["time"]):
                cloud_pct = float(daily["cloud_cover_mean"][i] or 0)
                score = max(0.0, min(100.0, 100.0 - cloud_pct))
                results.append(
                    DailyForecast(
                        date=date,
                        cloud_pct=min(100.0, max(0.0, cloud_pct)),
                        temp_min=float(daily["temperature_2m_min"][i] or 0),
                        temp_max=float(daily["temperature_2m_max"][i] or 0),
                        wind_mps=float(daily["wind_speed_10m_max"][i] or 0),
                        precip_mm=float(daily["precipitation_sum"][i] or 0),
                        astronomy_score=score,
                    )
                )
            return results
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Open-Meteo parse error: %s", exc)
            return []
