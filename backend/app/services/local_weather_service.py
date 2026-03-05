"""Local weather station integration (Ambient Weather WS-2902 via wx-service)."""

import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_WX_URL = "http://wx-service:8000/api/weather/latest"
_TIMEOUT = 3


class LocalWeatherReading:
    """Current conditions from the local weather station."""

    def __init__(self, data: dict):
        self.timestamp: datetime = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        self.outdoor_temp_f: float = data.get("outdoor_temp_f", 0)
        self.outdoor_temp_c: float = (self.outdoor_temp_f - 32) * 5 / 9
        self.feels_like_f: Optional[float] = data.get("feels_like_f")
        self.dew_point_f: Optional[float] = data.get("dew_point_f")
        self.dew_point_c: Optional[float] = ((self.dew_point_f - 32) * 5 / 9) if self.dew_point_f is not None else None
        self.humidity_pct: int = data.get("humidity_pct", 0)
        self.wind_speed_mph: float = data.get("wind_speed_mph", 0)
        self.wind_speed_ms: float = self.wind_speed_mph * 0.44704
        self.wind_gust_mph: Optional[float] = data.get("wind_gust_mph")
        self.wind_direction_deg: Optional[int] = data.get("wind_direction_deg")
        self.rain_rate_in_hr: Optional[float] = data.get("rain_rate_in_hr")
        self.daily_rain_in: float = data.get("daily_rain_in", 0)
        self.relative_pressure_inhg: Optional[float] = data.get("relative_pressure_inhg")
        self.uv_index: float = data.get("uv_index", 0)
        self.solar_radiation_wm2: float = data.get("solar_radiation_wm2", 0)
        self.indoor_temp_f: Optional[float] = data.get("indoor_temp_f")
        self.indoor_humidity_pct: Optional[int] = data.get("indoor_humidity_pct")

    @property
    def is_raining(self) -> bool:
        return bool(self.rain_rate_in_hr and self.rain_rate_in_hr > 0)

    @property
    def wind_direction_compass(self) -> Optional[str]:
        if self.wind_direction_deg is None:
            return None
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = round(self.wind_direction_deg / 22.5) % 16
        return dirs[idx]

    def astronomy_suitability(self) -> dict:
        """Return quick astronomy go/no-go assessment from local conditions."""
        issues = []

        if self.is_raining:
            issues.append("Rain in progress")
        if self.humidity_pct > 90:
            issues.append(f"Very high humidity ({self.humidity_pct}%)")
        elif self.humidity_pct > 80:
            issues.append(f"High humidity ({self.humidity_pct}%)")

        if self.wind_speed_mph > 25:
            issues.append(f"High wind ({self.wind_speed_mph:.0f} mph)")
        elif self.wind_speed_mph > 15:
            issues.append(f"Moderate wind ({self.wind_speed_mph:.0f} mph)")

        # Dew point spread — risk of dew on optics
        if self.dew_point_f is not None:
            spread_f = self.outdoor_temp_f - self.dew_point_f
            if spread_f < 3:
                issues.append(f"Near dew point (spread {spread_f:.1f}°F) — dew risk")

        score = max(0.0, 1.0 - len(issues) * 0.25)
        return {"score": round(score, 2), "issues": issues, "ok": len(issues) == 0}

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "outdoor_temp_c": round(self.outdoor_temp_c, 1),
            "outdoor_temp_f": self.outdoor_temp_f,
            "feels_like_f": self.feels_like_f,
            "dew_point_c": round(self.dew_point_c, 1) if self.dew_point_c is not None else None,
            "dew_point_f": self.dew_point_f,
            "humidity_pct": self.humidity_pct,
            "wind_speed_mph": self.wind_speed_mph,
            "wind_speed_ms": round(self.wind_speed_ms, 2),
            "wind_gust_mph": self.wind_gust_mph,
            "wind_direction_deg": self.wind_direction_deg,
            "wind_direction_compass": self.wind_direction_compass,
            "rain_rate_in_hr": self.rain_rate_in_hr,
            "daily_rain_in": self.daily_rain_in,
            "is_raining": self.is_raining,
            "relative_pressure_inhg": self.relative_pressure_inhg,
            "uv_index": self.uv_index,
            "solar_radiation_wm2": self.solar_radiation_wm2,
            "indoor_temp_f": self.indoor_temp_f,
            "indoor_humidity_pct": self.indoor_humidity_pct,
            "astronomy": self.astronomy_suitability(),
        }


class LocalWeatherService:
    """Fetches real-time data from the local Ambient Weather WS-2902 station."""

    def get_current(self) -> Optional[LocalWeatherReading]:
        """Return the latest reading, or None if the station is unreachable."""
        try:
            resp = requests.get(_WX_URL, timeout=_TIMEOUT)
            resp.raise_for_status()
            return LocalWeatherReading(resp.json())
        except Exception as exc:
            logger.warning(f"Local weather station unavailable: {exc}")
            return None
