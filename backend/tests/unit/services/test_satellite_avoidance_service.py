"""Tests for satellite avoidance service."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytz

from app.models import Location
from app.services.satellite_avoidance_service import (
    BlockedInterval,
    SatelliteAvoidanceService,
)


class TestSatelliteAvoidanceService:

    def test_init_creates_service(self):
        svc = SatelliteAvoidanceService()
        assert svc is not None

    def test_blocked_interval_model(self):
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 5, tzinfo=pytz.UTC)
        interval = BlockedInterval(start_time=start, end_time=end, satellite_name="ISS")
        assert interval.satellite_name == "ISS"
        assert interval.duration_minutes == 5

    @patch("app.services.satellite_avoidance_service.SatelliteAvoidanceService._load_tle_data")
    def test_get_blocked_intervals_returns_list(self, mock_load):
        mock_load.return_value = []
        svc = SatelliteAvoidanceService()
        location = Location(name="Test", latitude=46.8, longitude=-112.0, elevation=1000.0, timezone="America/Denver")
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        intervals = svc.get_blocked_intervals(location, start, end)
        assert isinstance(intervals, list)

    def test_overlaps_interval(self):
        svc = SatelliteAvoidanceService()
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        blocked = [
            BlockedInterval(
                start_time=datetime(2025, 1, 15, 22, 30, tzinfo=pytz.UTC),
                end_time=datetime(2025, 1, 15, 22, 35, tzinfo=pytz.UTC),
                satellite_name="ISS",
            )
        ]
        assert svc.overlaps_blocked(start, end, blocked) is True

    def test_no_overlap_returns_false(self):
        svc = SatelliteAvoidanceService()
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 20, tzinfo=pytz.UTC)
        blocked = [
            BlockedInterval(
                start_time=datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC),
                end_time=datetime(2025, 1, 15, 23, 5, tzinfo=pytz.UTC),
                satellite_name="ISS",
            )
        ]
        assert svc.overlaps_blocked(start, end, blocked) is False
