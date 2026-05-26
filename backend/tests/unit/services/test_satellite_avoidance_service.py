"""Tests for satellite avoidance service."""

import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytz

from app.models import Location
from app.services.satellite_avoidance_service import (
    TLE_CACHE_HOURS,
    TLE_CACHE_PATH,
    TLE_URL,
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

    def test_blocked_interval_duration_minutes(self):
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 10, tzinfo=pytz.UTC)
        interval = BlockedInterval(start_time=start, end_time=end, satellite_name="IRIDIUM 33")
        assert interval.duration_minutes == 10

    def test_overlaps_empty_blocked_list(self):
        svc = SatelliteAvoidanceService()
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 20, tzinfo=pytz.UTC)
        assert svc.overlaps_blocked(start, end, []) is False


class TestLoadTleData:

    @patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH")
    def test_returns_empty_list_when_download_fails_and_no_cache(self, mock_path):
        mock_path.exists.return_value = False
        svc = SatelliteAvoidanceService()
        with patch.object(svc, "_download_tles", return_value=""):
            result = svc._load_tle_data()
        assert result == []

    @patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH")
    def test_reads_from_fresh_cache(self, mock_path):
        tle_text = (
            "ISS (ZARYA)\n"
            "1 25544U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9999\n"
            "2 25544  51.6400 000.0000 0000001   0.0000 000.0000 15.50000000000000\n"
        )
        mock_path.exists.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_mtime = time.time()  # very fresh
        mock_path.stat.return_value = mock_stat
        mock_path.read_text.return_value = tle_text

        svc = SatelliteAvoidanceService()
        with patch.object(svc, "_cache_is_fresh", return_value=True):
            result = svc._load_tle_data()
        mock_path.read_text.assert_called_once()
        assert isinstance(result, list)

    @patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH")
    def test_downloads_when_cache_stale(self, mock_path):
        tle_text = (
            "ISS (ZARYA)\n"
            "1 25544U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9999\n"
            "2 25544  51.6400 000.0000 0000001   0.0000 000.0000 15.50000000000000\n"
        )
        svc = SatelliteAvoidanceService()
        with patch.object(svc, "_cache_is_fresh", return_value=False), \
             patch.object(svc, "_download_tles", return_value=tle_text) as mock_dl, \
             patch.object(mock_path, "write_text"):
            result = svc._load_tle_data()
        mock_dl.assert_called_once()

    @patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH")
    def test_returns_empty_on_download_failure(self, mock_path):
        svc = SatelliteAvoidanceService()
        with patch.object(svc, "_cache_is_fresh", return_value=False), \
             patch.object(svc, "_download_tles", return_value=""):
            result = svc._load_tle_data()
        assert result == []


class TestCacheIsFresh:

    def test_returns_false_when_file_missing(self, tmp_path):
        svc = SatelliteAvoidanceService()
        missing = tmp_path / "nonexistent.txt"
        with patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH", missing):
            assert svc._cache_is_fresh() is False

    def test_returns_true_when_file_fresh(self, tmp_path):
        cache_file = tmp_path / "tle_cache.txt"
        cache_file.write_text("data")
        svc = SatelliteAvoidanceService()
        with patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH", cache_file):
            assert svc._cache_is_fresh() is True

    def test_returns_false_when_file_stale(self, tmp_path):
        cache_file = tmp_path / "tle_cache.txt"
        cache_file.write_text("data")
        stale_mtime = time.time() - (TLE_CACHE_HOURS + 1) * 3600
        import os
        os.utime(str(cache_file), (stale_mtime, stale_mtime))
        svc = SatelliteAvoidanceService()
        with patch("app.services.satellite_avoidance_service.TLE_CACHE_PATH", cache_file):
            assert svc._cache_is_fresh() is False


class TestDownloadTles:

    @patch("app.services.satellite_avoidance_service.requests.get")
    def test_returns_text_on_success(self, mock_get):
        mock_resp = Mock()
        mock_resp.text = "TLE data here"
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp
        svc = SatelliteAvoidanceService()
        result = svc._download_tles()
        assert result == "TLE data here"

    @patch("app.services.satellite_avoidance_service.requests.get", side_effect=Exception("timeout"))
    def test_returns_empty_string_on_failure(self, mock_get):
        svc = SatelliteAvoidanceService()
        result = svc._download_tles()
        assert result == ""


class TestParseTles:

    def test_parses_valid_tle_block(self):
        raw = (
            "ISS (ZARYA)\n"
            "1 25544U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9999\n"
            "2 25544  51.6400 000.0000 0000001   0.0000 000.0000 15.50000000000000\n"
        )
        svc = SatelliteAvoidanceService()
        sats = svc._parse_tles(raw)
        assert len(sats) == 1
        assert sats[0].name == "ISS (ZARYA)"

    def test_parses_multiple_tle_blocks(self):
        raw = (
            "SAT1\n"
            "1 11111U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9999\n"
            "2 11111  51.6400 000.0000 0000001   0.0000 000.0000 15.50000000000000\n"
            "SAT2\n"
            "1 22222U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9999\n"
            "2 22222  51.6400 000.0000 0000001   0.0000 000.0000 15.50000000000000\n"
        )
        svc = SatelliteAvoidanceService()
        sats = svc._parse_tles(raw)
        assert len(sats) == 2

    def test_skips_malformed_blocks(self):
        raw = (
            "BAD BLOCK\n"
            "not a tle line 1\n"
            "not a tle line 2\n"
        )
        svc = SatelliteAvoidanceService()
        sats = svc._parse_tles(raw)
        assert len(sats) == 0

    def test_returns_empty_list_for_empty_input(self):
        svc = SatelliteAvoidanceService()
        assert svc._parse_tles("") == []


class TestGetBlockedIntervals:

    @patch("app.services.satellite_avoidance_service.SatelliteAvoidanceService._load_tle_data")
    def test_no_satellites_returns_empty(self, mock_load):
        mock_load.return_value = []
        svc = SatelliteAvoidanceService()
        location = Location(name="Test", latitude=45.0, longitude=-111.0, elevation=1000.0, timezone="America/Denver")
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        result = svc.get_blocked_intervals(location, start, end)
        assert result == []

    @patch("app.services.satellite_avoidance_service.SatelliteAvoidanceService._load_tle_data")
    def test_satellite_with_pass_returns_interval(self, mock_load):
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)

        # Build a mock satellite that reports a rise and set event
        mock_sat = MagicMock()
        mock_sat.name = "ISS"

        rise_t = MagicMock()
        rise_t.utc_datetime.return_value = datetime(2025, 1, 15, 22, 30, tzinfo=pytz.UTC)
        set_t = MagicMock()
        set_t.utc_datetime.return_value = datetime(2025, 1, 15, 22, 35, tzinfo=pytz.UTC)

        mock_sat.find_events.return_value = (
            [rise_t, set_t],
            [0, 2],  # event 0 = rise, event 2 = set
        )
        mock_load.return_value = [mock_sat]

        svc = SatelliteAvoidanceService()
        location = Location(name="Test", latitude=45.0, longitude=-111.0, elevation=1000.0, timezone="America/Denver")
        intervals = svc.get_blocked_intervals(location, start, end)

        assert len(intervals) == 1
        assert intervals[0].satellite_name == "ISS"

    @patch("app.services.satellite_avoidance_service.SatelliteAvoidanceService._load_tle_data")
    def test_satellite_exception_is_swallowed(self, mock_load):
        mock_sat = MagicMock()
        mock_sat.name = "BADSAT"
        mock_sat.find_events.side_effect = Exception("compute error")
        mock_load.return_value = [mock_sat]

        svc = SatelliteAvoidanceService()
        location = Location(name="Test", latitude=45.0, longitude=-111.0, elevation=1000.0, timezone="America/Denver")
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        result = svc.get_blocked_intervals(location, start, end)
        assert result == []
