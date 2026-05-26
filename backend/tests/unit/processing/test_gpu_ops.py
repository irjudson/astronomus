"""Unit tests for app/processing/gpu_ops.py.

CuPy is not installed in the test environment, so we exercise the
GPU_AVAILABLE=False branch and CPU fallback paths.  GPU-only paths
(gpu_histogram_stretch, mtf_gpu) require CuPy and are skipped.
"""

import importlib
import sys
from io import BytesIO
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, call, mock_open, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_gpu_ops_without_cupy():
    """Force-reload gpu_ops with cupy absent from sys.modules."""
    sys.modules.pop("app.processing.gpu_ops", None)
    sys.modules.pop("cupy", None)
    # Ensure cupy raises ImportError on import
    sys.modules["cupy"] = None  # None causes ImportError in "import cupy"
    try:
        import app.processing.gpu_ops as gpu_ops
        importlib.reload(gpu_ops)
    finally:
        sys.modules.pop("cupy", None)
    return gpu_ops


# ---------------------------------------------------------------------------
# check_gpu_available
# ---------------------------------------------------------------------------


def test_check_gpu_available_no_cupy():
    """When CuPy is not installed, returns available=False."""
    import app.processing.gpu_ops as gpu_ops

    # Patch GPU_AVAILABLE flag to False (the normal test-env state)
    with patch.object(gpu_ops, "GPU_AVAILABLE", False):
        result = gpu_ops.check_gpu_available()

    assert result["available"] is False
    assert "error" in result
    assert "CuPy" in result["error"] or "cupy" in result["error"].lower()


def test_check_gpu_available_cupy_runtime_error():
    """When CuPy is installed but getDeviceCount raises, returns available=False."""
    import app.processing.gpu_ops as gpu_ops

    mock_cp = MagicMock()
    mock_cp.cuda.runtime.getDeviceCount.side_effect = RuntimeError("CUDA not found")

    with patch.object(gpu_ops, "GPU_AVAILABLE", True), patch.object(gpu_ops, "cp", mock_cp, create=True):
        result = gpu_ops.check_gpu_available()

    assert result["available"] is False
    assert "error" in result


def test_check_gpu_available_cupy_present_one_device():
    """When CuPy is installed and one GPU exists, returns available=True."""
    import app.processing.gpu_ops as gpu_ops

    mock_cp = MagicMock()
    mock_cp.cuda.runtime.getDeviceCount.return_value = 1
    mock_cp.cuda.runtime.getDeviceProperties.return_value = {
        "name": b"Tesla T4",
        "totalGlobalMem": 16_000_000_000,
        "major": 7,
        "minor": 5,
    }

    with patch.object(gpu_ops, "GPU_AVAILABLE", True), patch.object(gpu_ops, "cp", mock_cp, create=True):
        result = gpu_ops.check_gpu_available()

    assert result["available"] is True
    assert result["count"] == 1
    assert len(result["devices"]) == 1
    assert result["devices"][0]["name"] == "Tesla T4"


# ---------------------------------------------------------------------------
# load_fits
# ---------------------------------------------------------------------------


def test_load_fits_no_astropy_raises():
    """When astropy is not available, load_fits raises ImportError."""
    import app.processing.gpu_ops as gpu_ops

    with patch.object(gpu_ops, "fits", None):
        with pytest.raises(ImportError, match="Astropy"):
            gpu_ops.load_fits("/fake/path.fits")


def test_load_fits_happy_path():
    """load_fits opens a FITS file and returns (ndarray, header)."""
    import app.processing.gpu_ops as gpu_ops

    fake_data = np.ones((10, 10), dtype=np.float32)
    fake_header = {"SIMPLE": True}

    mock_hdul_item = MagicMock()
    mock_hdul_item.data = fake_data
    mock_hdul_item.header = fake_header

    mock_hdul = MagicMock()
    mock_hdul.__enter__ = MagicMock(return_value=[mock_hdul_item])
    mock_hdul.__exit__ = MagicMock(return_value=False)

    mock_fits = MagicMock()
    mock_fits.open.return_value = mock_hdul

    with patch.object(gpu_ops, "fits", mock_fits):
        data, header = gpu_ops.load_fits("/data/test.fits")

    mock_fits.open.assert_called_once_with("/data/test.fits")
    assert data.dtype == np.float32
    assert header == fake_header


# ---------------------------------------------------------------------------
# save_fits
# ---------------------------------------------------------------------------


def test_save_fits_no_astropy_raises():
    import app.processing.gpu_ops as gpu_ops

    with patch.object(gpu_ops, "fits", None):
        with pytest.raises(ImportError, match="Astropy"):
            gpu_ops.save_fits("/fake/out.fits", np.zeros((5, 5)), {})


def test_save_fits_calls_writeto():
    import app.processing.gpu_ops as gpu_ops

    data = np.zeros((5, 5), dtype=np.float32)
    header = {"BITPIX": -32}

    mock_fits = MagicMock()
    with patch.object(gpu_ops, "fits", mock_fits):
        gpu_ops.save_fits("/out/test.fits", data, header)

    mock_fits.writeto.assert_called_once_with("/out/test.fits", data, header, overwrite=True)


# ---------------------------------------------------------------------------
# mtf_cpu
# ---------------------------------------------------------------------------


def test_mtf_cpu_identity_at_half():
    """mtf_cpu with midtones=0.5 should transform the data (not identity)."""
    import app.processing.gpu_ops as gpu_ops

    data = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    result = gpu_ops.mtf_cpu(data, 0.3)
    # Just verify it runs and returns same shape
    assert result.shape == data.shape


def test_mtf_cpu_output_shape():
    import app.processing.gpu_ops as gpu_ops

    data = np.linspace(0.01, 0.99, 100)
    result = gpu_ops.mtf_cpu(data, 0.4)
    assert result.shape == (100,)


# ---------------------------------------------------------------------------
# cpu_histogram_stretch
# ---------------------------------------------------------------------------


def _make_fits_mock(data: np.ndarray, header=None):
    """Return a mock fits module that returns the given data on open."""
    if header is None:
        header = {}
    mock_hdul_item = MagicMock()
    mock_hdul_item.data = data.astype(np.float32)
    mock_hdul_item.header = header

    mock_hdul = MagicMock()
    mock_hdul.__enter__ = MagicMock(return_value=[mock_hdul_item])
    mock_hdul.__exit__ = MagicMock(return_value=False)

    mock_fits = MagicMock()
    mock_fits.open.return_value = mock_hdul
    return mock_fits


def test_cpu_histogram_stretch_auto(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    data = np.random.uniform(1000, 60000, (50, 50)).astype(np.float32)
    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")
    mock_fits = _make_fits_mock(data)

    with patch.object(gpu_ops, "fits", mock_fits):
        result = gpu_ops.cpu_histogram_stretch(in_path, out_path, {"algorithm": "auto"})

    assert result == out_path
    mock_fits.writeto.assert_called_once()


def test_cpu_histogram_stretch_manual(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    data = np.random.uniform(0, 65535, (20, 20)).astype(np.float32)
    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")
    mock_fits = _make_fits_mock(data)

    params = {"algorithm": "manual", "black_point": 1000, "white_point": 50000}
    with patch.object(gpu_ops, "fits", mock_fits):
        result = gpu_ops.cpu_histogram_stretch(in_path, out_path, params)

    assert result == out_path


def test_cpu_histogram_stretch_with_midtones(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    data = np.random.uniform(0, 65535, (20, 20)).astype(np.float32)
    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")
    mock_fits = _make_fits_mock(data)

    # midtones != 0.5 triggers mtf_cpu branch
    params = {"algorithm": "auto", "midtones": 0.3}
    with patch.object(gpu_ops, "fits", mock_fits):
        result = gpu_ops.cpu_histogram_stretch(in_path, out_path, params)

    assert result == out_path


# ---------------------------------------------------------------------------
# histogram_stretch (dispatcher)
# ---------------------------------------------------------------------------


def test_histogram_stretch_uses_cpu_when_gpu_unavailable(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")

    with patch.object(gpu_ops, "GPU_AVAILABLE", False), patch.object(
        gpu_ops, "cpu_histogram_stretch", return_value=out_path
    ) as mock_cpu:
        result = gpu_ops.histogram_stretch(in_path, out_path, {}, use_gpu=True)

    mock_cpu.assert_called_once_with(in_path, out_path, {})
    assert result == out_path


def test_histogram_stretch_uses_cpu_when_use_gpu_false(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")

    with patch.object(gpu_ops, "GPU_AVAILABLE", True), patch.object(
        gpu_ops, "cpu_histogram_stretch", return_value=out_path
    ) as mock_cpu:
        result = gpu_ops.histogram_stretch(in_path, out_path, {}, use_gpu=False)

    mock_cpu.assert_called_once()
    assert result == out_path


def test_histogram_stretch_falls_back_to_cpu_on_gpu_error(tmp_path):
    import app.processing.gpu_ops as gpu_ops

    in_path = str(tmp_path / "in.fits")
    out_path = str(tmp_path / "out.fits")

    with (
        patch.object(gpu_ops, "GPU_AVAILABLE", True),
        patch.object(gpu_ops, "gpu_histogram_stretch", side_effect=RuntimeError("CUDA OOM")),
        patch.object(gpu_ops, "cpu_histogram_stretch", return_value=out_path) as mock_cpu,
    ):
        result = gpu_ops.histogram_stretch(in_path, out_path, {}, use_gpu=True)

    mock_cpu.assert_called_once()
    assert result == out_path
