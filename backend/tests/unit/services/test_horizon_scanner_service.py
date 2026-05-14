"""Tests for horizon scanner service brightness analysis."""

import io

import pytest
from PIL import Image

from app.services.horizon_scanner_service import HorizonScannerService, analyze_frame_brightness


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
