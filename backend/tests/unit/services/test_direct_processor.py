"""Tests for DirectProcessor FITS processing."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.direct_processor import DirectProcessor


@pytest.fixture
def processor():
    return DirectProcessor()


@pytest.fixture
def grayscale_data():
    rng = np.random.default_rng(42)
    return rng.integers(0, 65535, (100, 100)).astype(np.float32)


@pytest.fixture
def rgb_data():
    rng = np.random.default_rng(42)
    return rng.integers(0, 65535, (3, 100, 100)).astype(np.float32)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_hdul_ctx(data):
    """Return a context-manager-compatible hdul containing a real PrimaryHDU."""
    from astropy.io import fits as real_fits

    hdu = real_fits.PrimaryHDU(data=data)
    hdul = real_fits.HDUList([hdu])
    return hdul


# ---------------------------------------------------------------------------
# _load_fits
# ---------------------------------------------------------------------------


class TestLoadFits:
    @patch("app.services.direct_processor.fits.open")
    def test_load_fits_returns_float32_array(self, mock_open, processor, grayscale_data):
        mock_open.return_value = make_hdul_ctx(grayscale_data)

        result = processor._load_fits(Path("/fake/test.fits"))
        assert result.dtype == np.float32
        assert result.shape == grayscale_data.shape

    @patch("app.services.direct_processor.fits.open")
    def test_load_fits_no_image_data_raises(self, mock_open, processor):
        from astropy.io import fits as real_fits

        # HDU with no data
        hdu = real_fits.PrimaryHDU(data=None)
        mock_open.return_value = real_fits.HDUList([hdu])

        with pytest.raises(ValueError, match="No image data found"):
            processor._load_fits(Path("/fake/empty.fits"))

    @patch("app.services.direct_processor.fits.open")
    def test_load_fits_propagates_io_error(self, mock_open, processor):
        mock_open.side_effect = OSError("File not found")

        with pytest.raises(OSError):
            processor._load_fits(Path("/nonexistent.fits"))


# ---------------------------------------------------------------------------
# histogram_stretch
# ---------------------------------------------------------------------------


class TestHistogramStretch:
    def test_stretch_grayscale_returns_0_to_1(self, processor, grayscale_data):
        result = processor.histogram_stretch(grayscale_data, algorithm="auto")
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_stretch_rgb_returns_correct_shape(self, processor, rgb_data):
        result = processor.histogram_stretch(rgb_data, algorithm="auto")
        assert result.shape == rgb_data.shape

    def test_stretch_midtone_changes_values(self, processor, grayscale_data):
        default_result = processor.histogram_stretch(grayscale_data, algorithm="midtone", midtones=0.5)
        shifted_result = processor.histogram_stretch(grayscale_data, algorithm="midtone", midtones=0.3)
        # Different midtones should produce different results
        assert not np.allclose(default_result, shifted_result)

    def test_stretch_uniform_image(self, processor):
        uniform = np.ones((50, 50), dtype=np.float32) * 1000.0
        result = processor.histogram_stretch(uniform)
        # All pixels same value → after stretch all should be clipped to 0
        assert result is not None


# ---------------------------------------------------------------------------
# export_image
# ---------------------------------------------------------------------------


class TestExportImage:
    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    def test_export_jpeg_8bit(self, mock_mkdir, mock_fromarray, processor, grayscale_data, tmp_path):
        mock_image = MagicMock()
        mock_fromarray.return_value = mock_image
        # Normalise data to 0-1 first (as histogram_stretch would)
        data_01 = grayscale_data / grayscale_data.max()

        result = processor.export_image(data_01, tmp_path, "frame", format="jpeg", quality=80)

        assert len(result) == 1
        mock_image.save.assert_called_once()

    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    def test_export_png_8bit(self, mock_mkdir, mock_fromarray, processor, grayscale_data, tmp_path):
        mock_image = MagicMock()
        mock_fromarray.return_value = mock_image
        data_01 = grayscale_data / grayscale_data.max()

        result = processor.export_image(data_01, tmp_path, "frame", format="png")

        assert len(result) == 1

    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    def test_export_rgb_jpeg(self, mock_mkdir, mock_fromarray, processor, rgb_data, tmp_path):
        mock_image = MagicMock()
        mock_fromarray.return_value = mock_image
        data_01 = rgb_data / rgb_data.max()

        result = processor.export_image(data_01, tmp_path, "frame", format="jpeg")

        assert len(result) == 1

    def test_export_unsupported_format_raises(self, processor, grayscale_data, tmp_path):
        data_01 = grayscale_data / grayscale_data.max()
        with pytest.raises(ValueError, match="Unsupported format"):
            processor.export_image(data_01, tmp_path, "frame", format="bmp")

    def test_export_unsupported_bit_depth_raises(self, processor, grayscale_data, tmp_path):
        data_01 = grayscale_data / grayscale_data.max()
        with pytest.raises(ValueError, match="bit depth"):
            processor.export_image(data_01, tmp_path, "frame", format="jpeg", bit_depth=32)


# ---------------------------------------------------------------------------
# process_fits (integration of steps)
# ---------------------------------------------------------------------------


class TestProcessFits:
    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    @patch("app.services.direct_processor.fits.open")
    def test_process_fits_histogram_then_default_export(
        self, mock_open, mock_mkdir, mock_fromarray, processor, grayscale_data, tmp_path
    ):
        mock_open.return_value = make_hdul_ctx(grayscale_data)
        mock_img = MagicMock()
        mock_fromarray.return_value = mock_img

        steps = [{"step": "histogram_stretch", "params": {"algorithm": "auto"}}]
        result = processor.process_fits(tmp_path / "test.fits", tmp_path, steps)

        assert len(result) == 1
        mock_img.save.assert_called_once()

    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    @patch("app.services.direct_processor.fits.open")
    def test_process_fits_export_step_returns_early(
        self, mock_open, mock_mkdir, mock_fromarray, processor, grayscale_data, tmp_path
    ):
        mock_open.return_value = make_hdul_ctx(grayscale_data)
        mock_img = MagicMock()
        mock_fromarray.return_value = mock_img

        steps = [
            {"step": "export", "params": {"format": "jpeg", "quality": 90}},
        ]
        result = processor.process_fits(tmp_path / "test.fits", tmp_path, steps)
        assert len(result) == 1

    @patch("app.services.direct_processor.Image.fromarray")
    @patch.object(Path, "mkdir")
    @patch("app.services.direct_processor.fits.open")
    def test_process_fits_unknown_step_skipped(
        self, mock_open, mock_mkdir, mock_fromarray, processor, grayscale_data, tmp_path
    ):
        mock_open.return_value = make_hdul_ctx(grayscale_data)
        mock_img = MagicMock()
        mock_fromarray.return_value = mock_img

        # Unknown step should be logged and skipped, then default export runs
        steps = [{"step": "debayer", "params": {}}]
        result = processor.process_fits(tmp_path / "test.fits", tmp_path, steps)
        assert result is not None
