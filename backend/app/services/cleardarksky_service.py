"""Astronomy weather forecast service using Open-Meteo (free, no API key required).

Replaces the former ClearDarkSky stub whose chart-image parser always returned [].
Open-Meteo provides cloud cover, visibility, wind speed, and temperature at hourly
resolution for any lat/lon on Earth.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List

import requests
from pydantic import BaseModel


class CloudCover(Enum):
    CLEAR = (0, 10)
    MOSTLY_CLEAR = (10, 30)
    PARTLY_CLOUDY = (30, 70)
    MOSTLY_CLOUDY = (70, 90)
    OVERCAST = (90, 100)


class Transparency(Enum):
    EXCELLENT = 5
    ABOVE_AVERAGE = 4
    AVERAGE = 3
    BELOW_AVERAGE = 2
    POOR = 1


class Seeing(Enum):
    EXCELLENT = 5
    GOOD = 4
    AVERAGE = 3
    BELOW_AVERAGE = 2
    POOR = 1


class ClearDarkSkyForecast(BaseModel):
    time: datetime
    cloud_cover: CloudCover
    transparency: Transparency
    seeing: Seeing
    temperature_c: float
    wind_speed_kmh: float

    def astronomy_score(self) -> float:
        cloud_min, cloud_max = self.cloud_cover.value
        cloud_avg = (cloud_min + cloud_max) / 2
        cloud_score = 1.0 - (cloud_avg / 100.0)
        transp_score = self.transparency.value / 5.0
        seeing_score = self.seeing.value / 5.0
        return cloud_score * 0.4 + transp_score * 0.35 + seeing_score * 0.25


def _cloud_cover_enum(pct: float) -> CloudCover:
    if pct <= 10:
        return CloudCover.CLEAR
    elif pct <= 30:
        return CloudCover.MOSTLY_CLEAR
    elif pct <= 70:
        return CloudCover.PARTLY_CLOUDY
    elif pct <= 90:
        return CloudCover.MOSTLY_CLOUDY
    return CloudCover.OVERCAST


def _transparency_from_visibility(vis_m: float) -> Transparency:
    """Map visibility in metres to atmospheric transparency."""
    if vis_m >= 24000:
        return Transparency.EXCELLENT
    elif vis_m >= 16000:
        return Transparency.ABOVE_AVERAGE
    elif vis_m >= 8000:
        return Transparency.AVERAGE
    elif vis_m >= 4000:
        return Transparency.BELOW_AVERAGE
    return Transparency.POOR


def _seeing_from_wind(wind_kmh: float) -> Seeing:
    """Estimate astronomical seeing from surface wind speed."""
    if wind_kmh < 5:
        return Seeing.EXCELLENT
    elif wind_kmh < 15:
        return Seeing.GOOD
    elif wind_kmh < 25:
        return Seeing.AVERAGE
    elif wind_kmh < 40:
        return Seeing.BELOW_AVERAGE
    return Seeing.POOR


class ClearDarkSkyService:
    """Astronomy weather forecast using Open-Meteo API."""

    _API = "https://api.open-meteo.com/v1/forecast"
    _TIMEOUT = 10

    def get_forecast(self, latitude: float, longitude: float, hours: int = 48) -> List[ClearDarkSkyForecast]:
        """Return hourly astronomy forecast for the given coordinates.

        Uses Open-Meteo (https://open-meteo.com) — free, no API key.
        Returns up to `hours` entries starting from the current hour.
        Returns [] on network error rather than raising.
        """
        try:
            resp = requests.get(
                self._API,
                params={
                    "latitude": round(latitude, 4),
                    "longitude": round(longitude, 4),
                    "hourly": "cloud_cover,visibility,wind_speed_10m,temperature_2m",
                    "wind_speed_unit": "kmh",
                    "forecast_days": min(7, max(1, (hours // 24) + 1)),
                    "timezone": "UTC",
                },
                timeout=self._TIMEOUT,
            )
            resp.raise_for_status()
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(f"Open-Meteo request failed: {exc}")
            return []

        data = resp.json().get("hourly", {})
        times = data.get("time", [])
        clouds = data.get("cloud_cover", [])
        vis = data.get("visibility", [])
        wind = data.get("wind_speed_10m", [])
        temp = data.get("temperature_2m", [])

        now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        results: List[ClearDarkSkyForecast] = []

        for i, t_str in enumerate(times):
            if len(results) >= hours:
                break
            try:
                t = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if t < now_utc:
                continue

            results.append(
                ClearDarkSkyForecast(
                    time=t,
                    cloud_cover=_cloud_cover_enum(float(clouds[i] or 0)),
                    transparency=_transparency_from_visibility(float(vis[i] or 0)),
                    seeing=_seeing_from_wind(float(wind[i] or 0)),
                    temperature_c=float(temp[i] or 0),
                    wind_speed_kmh=float(wind[i] or 0),
                )
            )

        return results

    # Keep old method names for any callers that used them
    def find_nearest_chart(self, latitude: float, longitude: float):
        return f"{latitude:.2f},{longitude:.2f}"

    def fetch_forecast(self, chart_id: str) -> List[ClearDarkSkyForecast]:
        try:
            lat, lon = (float(x) for x in chart_id.split(","))
        except ValueError:
            return []
        return self.get_forecast(lat, lon)
