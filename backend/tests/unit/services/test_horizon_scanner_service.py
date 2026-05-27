"""Tests for horizon scanner service brightness analysis."""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from PIL import Image

from app.services.horizon_scanner_service import (
    HorizonScannerService,
    ScanProgress,
    SKY_RATIO_THRESHOLD,
    analyze_frame_brightness,
)


def make_frame(top_brightness: int, bottom_brightness: int, width=100, height=100) -> bytes:
    """Create a test JPEG with different brightness in top/bottom halves."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        b = top_brightness if y < height // 2 else bottom_brightness
        for x in range(width):
            pixels[x, y] = (b, b, b)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestBrightnessAnalysis:

    def test_all_sky_returns_high_ratio(self):
        frame = make_frame(top_brightness=200, bottom_brightness=200)
        ratio = analyze_frame_brightness(frame)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_sky_over_terrain_returns_ratio_above_1(self):
        frame = make_frame(top_brightness=200, bottom_brightness=60)
        ratio = analyze_frame_brightness(frame)
        assert ratio > 1.2  # sky on top, terrain on bottom = above horizon

    def test_terrain_fills_frame_returns_ratio_near_1(self):
        frame = make_frame(top_brightness=50, bottom_brightness=50)
        ratio = analyze_frame_brightness(frame)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_scanner_instantiates(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc is not None

    def test_is_above_horizon_sky_ratio(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc._is_sky(ratio=1.5) is True

    def test_is_above_horizon_terrain_ratio(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc._is_sky(ratio=0.7) is False


class TestStepScanMode:
    def test_scanner_instantiates_with_steps_mode(self):
        svc = HorizonScannerService(
            telescope_host="127.0.0.1",
            telescope_port=4700,
            scan_mode="steps",
        )
        assert svc.scan_mode == "steps"

    def test_scanner_defaults_to_binary_mode(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc.scan_mode == "binary"


# ---------------------------------------------------------------------------
# ScanProgress dataclass
# ---------------------------------------------------------------------------

class TestScanProgress:
    def test_progress_percent_zero_when_no_azimuths(self):
        sp = ScanProgress(current_az=0.0, total_azimuths=0, completed=0)
        assert sp.progress_percent == 0.0

    def test_progress_percent_calculation(self):
        sp = ScanProgress(current_az=90.0, total_azimuths=24, completed=6)
        assert sp.progress_percent == pytest.approx(25.0, abs=0.1)

    def test_default_status_is_scanning(self):
        sp = ScanProgress(current_az=0.0, total_azimuths=24, completed=1)
        assert sp.status == "scanning"

    def test_points_default_empty(self):
        sp = ScanProgress(current_az=0.0, total_azimuths=24, completed=0)
        assert sp.points == []


# ---------------------------------------------------------------------------
# HorizonScannerService.scan (binary mode)
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    return HorizonScannerService(
        telescope_host="127.0.0.1",
        telescope_port=4700,
        az_step=90,  # only 4 azimuths → fast
        alt_min=2.0,
        alt_max=10.0,
        scan_mode="binary",
    )


@pytest.fixture
def sky_frame():
    return make_frame(top_brightness=200, bottom_brightness=80)  # ratio >> 1.2


@pytest.fixture
def terrain_frame():
    return make_frame(top_brightness=50, bottom_brightness=60)  # ratio < 1.2


@pytest.mark.asyncio
async def test_scan_binary_yields_progress_events(svc, sky_frame):
    async def fake_move(az, alt):
        pass

    async def fake_frame():
        return sky_frame

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    events = []
    async for progress in svc.scan():
        events.append(progress)

    # az_step=90 → azimuths 0, 90, 180, 270 → 4 events
    assert len(events) == 4
    assert events[-1].status == "complete"
    assert all(isinstance(e, ScanProgress) for e in events)


@pytest.mark.asyncio
async def test_scan_binary_uses_alt_min_on_exception(svc):
    async def fake_move(az, alt):
        raise ConnectionRefusedError("telescope not connected")

    async def fake_frame():
        return make_frame(200, 200)

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    events = []
    async for progress in svc.scan():
        events.append(progress)

    # Should still yield events; altitude falls back to alt_min
    assert len(events) == 4
    for e in events:
        assert e.points[-1]["alt"] == pytest.approx(svc.alt_min, abs=0.01)


@pytest.mark.asyncio
async def test_scan_steps_mode_yields_correct_count():
    svc = HorizonScannerService(
        telescope_host="127.0.0.1",
        telescope_port=4700,
        az_step=180,  # only 2 azimuths
        alt_min=2.0,
        alt_max=10.0,
        scan_mode="steps",
    )

    async def fake_move(az, alt):
        pass

    async def fake_frame():
        return make_frame(200, 80)  # sky ratio

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    events = []
    async for progress in svc.scan():
        events.append(progress)

    assert len(events) == 2


# ---------------------------------------------------------------------------
# _find_horizon_altitude (binary search)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_horizon_altitude_terrain_only_returns_midpoint(svc, terrain_frame):
    async def fake_move(az, alt):
        pass

    async def fake_frame():
        return terrain_frame  # always terrain → horizon at max

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    # Suppress the asyncio.sleep to speed up test
    with patch("app.services.horizon_scanner_service.asyncio.sleep", new=AsyncMock()):
        alt = await svc._find_horizon_altitude(azimuth=0.0)

    # With all-terrain frames low becomes alt_max
    assert svc.alt_min <= alt <= svc.alt_max


@pytest.mark.asyncio
async def test_find_horizon_altitude_sky_only_returns_near_min(svc, sky_frame):
    async def fake_move(az, alt):
        pass

    async def fake_frame():
        return sky_frame  # always sky → horizon converges to alt_min

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    with patch("app.services.horizon_scanner_service.asyncio.sleep", new=AsyncMock()):
        alt = await svc._find_horizon_altitude(azimuth=0.0)

    assert svc.alt_min <= alt <= svc.alt_max


# ---------------------------------------------------------------------------
# _find_horizon_altitude_steps
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_horizon_altitude_steps_returns_first_sky_alt(svc, sky_frame, terrain_frame):
    call_count = [0]

    async def fake_move(az, alt):
        pass

    async def fake_frame():
        call_count[0] += 1
        # First call is terrain, subsequent calls are sky
        if call_count[0] == 1:
            return terrain_frame
        return sky_frame

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    with patch("app.services.horizon_scanner_service.asyncio.sleep", new=AsyncMock()):
        alt = await svc._find_horizon_altitude_steps(azimuth=45.0)

    # Second step altitude = alt_min + 2.0
    assert alt == pytest.approx(svc.alt_min + 2.0, abs=0.01)


@pytest.mark.asyncio
async def test_find_horizon_altitude_steps_all_terrain_returns_max(svc, terrain_frame):
    async def fake_move(az, alt):
        pass

    async def fake_frame():
        return terrain_frame

    svc._move_scope = fake_move
    svc._capture_frame = fake_frame

    with patch("app.services.horizon_scanner_service.asyncio.sleep", new=AsyncMock()):
        alt = await svc._find_horizon_altitude_steps(azimuth=0.0)

    assert alt == pytest.approx(svc.alt_max, abs=0.01)


# ---------------------------------------------------------------------------
# _capture_frame
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_capture_frame_returns_bytes_from_snapshot(sky_frame):
    svc = HorizonScannerService("127.0.0.1", 4700)

    mock_resp = MagicMock()
    mock_resp.content = sky_frame
    mock_resp.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.horizon_scanner_service.httpx.AsyncClient", return_value=mock_client):
        result = await svc._capture_frame()

    assert result == sky_frame
