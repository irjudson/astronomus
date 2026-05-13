"""Satellite pass avoidance service for astrophotography planning."""

import logging
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytz
import requests
from pydantic import BaseModel
from skyfield.api import EarthSatellite, load, wgs84

logger = logging.getLogger(__name__)

TLE_URL = "https://celestrak.org/TLE/catalog.csv?GROUP=visual&FORMAT=tle"
TLE_CACHE_HOURS = 24
TLE_CACHE_PATH = Path(tempfile.gettempdir()) / "astronomus_visual_tle.txt"
MIN_ELEVATION_DEG = 10.0


class BlockedInterval(BaseModel):
    """A time window to avoid scheduling imaging in."""

    start_time: datetime
    end_time: datetime
    satellite_name: str

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)


class SatelliteAvoidanceService:
    """Compute satellite pass windows that should be avoided during imaging."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._ts = load.timescale()

    def get_blocked_intervals(
        self,
        location,
        session_start: datetime,
        session_end: datetime,
        min_elevation: float = MIN_ELEVATION_DEG,
    ) -> List[BlockedInterval]:
        """Return time intervals when a bright satellite passes over the observer."""
        satellites = self._load_tle_data()
        if not satellites:
            return []

        observer = wgs84.latlon(
            location.latitude,
            location.longitude,
            elevation_m=getattr(location, "elevation", 0.0),
        )

        t0 = self._ts.from_datetime(session_start.astimezone(pytz.UTC))
        t1 = self._ts.from_datetime(session_end.astimezone(pytz.UTC))

        intervals: List[BlockedInterval] = []

        for sat in satellites:
            try:
                times, events = sat.find_events(observer, t0, t1, altitude_degrees=min_elevation)
                i = 0
                while i < len(events):
                    if events[i] == 0:  # rise
                        rise_t = times[i].utc_datetime().replace(tzinfo=pytz.UTC)
                        for j in range(i + 1, len(events)):
                            if events[j] == 2:  # set
                                set_t = times[j].utc_datetime().replace(tzinfo=pytz.UTC)
                                intervals.append(
                                    BlockedInterval(
                                        start_time=rise_t - timedelta(seconds=30),
                                        end_time=set_t + timedelta(seconds=30),
                                        satellite_name=sat.name,
                                    )
                                )
                                break
                    i += 1
            except Exception as e:
                logger.debug("Error computing passes for %s: %s", sat.name, e)

        logger.info("Found %d satellite pass intervals during session", len(intervals))
        return intervals

    def overlaps_blocked(self, start: datetime, end: datetime, blocked: List[BlockedInterval]) -> bool:
        """Return True if [start, end) overlaps any blocked interval."""
        for interval in blocked:
            if start < interval.end_time and end > interval.start_time:
                return True
        return False

    def _load_tle_data(self) -> List[EarthSatellite]:
        """Load TLE data from cache or download from Celestrak."""
        if self._cache_is_fresh():
            raw = TLE_CACHE_PATH.read_text()
        else:
            raw = self._download_tles()
            if raw:
                TLE_CACHE_PATH.write_text(raw)
        if not raw:
            return []
        return self._parse_tles(raw)

    def _cache_is_fresh(self) -> bool:
        if not TLE_CACHE_PATH.exists():
            return False
        age_hours = (time.time() - TLE_CACHE_PATH.stat().st_mtime) / 3600
        return age_hours < TLE_CACHE_HOURS

    def _download_tles(self) -> str:
        try:
            resp = requests.get(TLE_URL, timeout=self.timeout)
            resp.raise_for_status()
            logger.info("Downloaded visual TLEs (%d bytes)", len(resp.text))
            return resp.text
        except Exception as e:
            logger.warning("Failed to download TLEs: %s", e)
            return ""

    def _parse_tles(self, raw: str) -> List[EarthSatellite]:
        sats = []
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        i = 0
        while i + 2 < len(lines):
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            if line1.startswith("1 ") and line2.startswith("2 "):
                try:
                    sats.append(EarthSatellite(line1, line2, name, self._ts))
                except Exception:
                    pass
                i += 3
            else:
                i += 1
        return sats
