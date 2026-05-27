"""Tests for StackingService."""

import numpy as np
import pytest

from app.services.stacking_service import StackingResult, StackingService


@pytest.fixture
def svc():
    return StackingService(use_gpu=False)


@pytest.fixture
def small_frame():
    rng = np.random.default_rng(7)
    return rng.integers(0, 65535, (10, 10)).astype(np.float32)


def make_hdul(data):
    """Return a real astropy HDUList for the given data array."""
    from astropy.io import fits

    hdu = fits.PrimaryHDU(data=data)
    return fits.HDUList([hdu])


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestStackingServiceInit:
    def test_gpu_false_when_cupy_absent(self):
        svc = StackingService(use_gpu=False)
        assert svc.use_gpu is False

    def test_gpu_flag_stored(self):
        svc = StackingService(use_gpu=True)
        # Without CuPy HAS_CUPY=False, so use_gpu is always False
        assert isinstance(svc.use_gpu, bool)


# ---------------------------------------------------------------------------
# load_subframes
# ---------------------------------------------------------------------------


class TestLoadSubframes:
    def test_no_files_raises(self, svc, tmp_path):
        with pytest.raises(ValueError, match="No files matching"):
            svc.load_subframes(tmp_path, pattern="Light_*.fit")

    def test_loads_matching_files(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        fits_path = tmp_path / "Light_001.fit"
        fits.PrimaryHDU(data=small_frame).writeto(fits_path)

        frames = svc.load_subframes(tmp_path, pattern="Light_*.fit")
        assert len(frames) == 1
        assert frames[0].shape == small_frame.shape
        assert frames[0].dtype == np.float32

    def test_corrupt_file_is_skipped_but_raises_if_all_fail(self, svc, tmp_path):
        # Write a non-FITS file with .fit extension
        bad_file = tmp_path / "Light_bad.fit"
        bad_file.write_bytes(b"not a fits file")

        with pytest.raises(ValueError, match="No frames could be loaded"):
            svc.load_subframes(tmp_path, pattern="Light_*.fit")

    def test_loads_multiple_frames(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        for i in range(3):
            fits.PrimaryHDU(data=small_frame + i).writeto(tmp_path / f"Light_{i:03d}.fit")

        frames = svc.load_subframes(tmp_path, pattern="Light_*.fit")
        assert len(frames) == 3


# ---------------------------------------------------------------------------
# debayer_rggb
# ---------------------------------------------------------------------------


class TestDebayerRggb:
    def test_output_shape_is_3_h_w(self, svc, small_frame):
        result = svc.debayer_rggb(small_frame)
        h, w = small_frame.shape
        assert result.shape == (3, h, w)

    def test_output_dtype_is_float32(self, svc, small_frame):
        result = svc.debayer_rggb(small_frame)
        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# sigma_clip_stack
# ---------------------------------------------------------------------------


class TestSigmaClipStack:
    def test_stack_returns_correct_shape(self, svc, small_frame):
        frames = [small_frame.copy() for _ in range(3)]
        result, rejected = svc.sigma_clip_stack(frames, sigma=2.5)
        assert result.shape == small_frame.shape
        assert result.dtype == np.float32
        assert isinstance(rejected, int)

    def test_stack_single_frame(self, svc, small_frame):
        result, rejected = svc.sigma_clip_stack([small_frame])
        assert result.shape == small_frame.shape

    def test_stack_identical_frames_has_zero_rejected(self, svc):
        # Identical frames → no sigma outliers
        frame = np.ones((8, 8), dtype=np.float32) * 1000.0
        frames = [frame.copy() for _ in range(5)]
        _, rejected = svc.sigma_clip_stack(frames, sigma=3.0, max_iterations=2)
        assert rejected == 0

    def test_stack_with_spike_rejects_pixels(self, svc):
        # Use a constant-value stack so std is zero initially; spike is always an outlier
        # after the first iteration raises std from 0 → but numpy std on all-same is 0.
        # Instead: use values spread slightly so std is non-zero, and spike is far outside.
        base = np.full((8, 8), 1000.0, dtype=np.float32)
        frames = [base + float(i) for i in range(10)]
        # Add a massive spike in frame 0 at pixel [0, 0] — 100× larger than others
        frames[0][0, 0] = 1000000.0
        _, rejected = svc.sigma_clip_stack(frames, sigma=1.0, max_iterations=3)
        assert rejected > 0


# ---------------------------------------------------------------------------
# save_stacked_fits
# ---------------------------------------------------------------------------


class TestSaveStackedFits:
    def test_saves_file(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        rgb = np.stack([small_frame, small_frame, small_frame], axis=0)
        out_path = tmp_path / "stacked.fit"
        svc.save_stacked_fits(rgb, out_path, num_frames=5)
        assert out_path.exists()

        with fits.open(out_path) as hdul:
            assert hdul[0].header["STACKED"] == 5

    def test_saves_with_original_header(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        rgb = np.stack([small_frame, small_frame, small_frame], axis=0)
        original_header = fits.Header()
        original_header["INSTRUME"] = "Seestar S50"
        out_path = tmp_path / "stacked_hdr.fit"
        svc.save_stacked_fits(rgb, out_path, num_frames=3, original_header=original_header)
        with fits.open(out_path) as hdul:
            assert hdul[0].header.get("INSTRUME") == "Seestar S50"


# ---------------------------------------------------------------------------
# stack_folder
# ---------------------------------------------------------------------------


class TestStackFolder:
    def test_stack_folder_raises_when_no_files(self, svc, tmp_path):
        with pytest.raises(ValueError):
            svc.stack_folder(tmp_path, pattern="Light_*.fit")

    def test_stack_folder_full_pipeline(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        sub_dir = tmp_path / "NGC1234_sub"
        sub_dir.mkdir()
        for i in range(2):
            fits.PrimaryHDU(data=small_frame + float(i)).writeto(sub_dir / f"Light_{i:03d}.fit")

        result = svc.stack_folder(sub_dir, pattern="Light_*.fit")

        assert isinstance(result, StackingResult)
        assert result.num_frames == 2
        assert result.stacked_file.exists()

    def test_stack_folder_with_explicit_output_path(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        sub_dir = tmp_path / "frames"
        sub_dir.mkdir()
        for i in range(2):
            fits.PrimaryHDU(data=small_frame + float(i)).writeto(sub_dir / f"Light_{i:03d}.fit")

        out_file = tmp_path / "my_stack.fit"
        result = svc.stack_folder(sub_dir, pattern="Light_*.fit", output_path=out_file)

        assert result.stacked_file == out_file
        assert out_file.exists()

    def test_stack_folder_removes_sub_suffix_from_object_name(self, svc, tmp_path, small_frame):
        from astropy.io import fits

        sub_dir = tmp_path / "M42_sub"
        sub_dir.mkdir()
        for i in range(2):
            fits.PrimaryHDU(data=small_frame + float(i)).writeto(sub_dir / f"Light_{i:03d}.fit")

        result = svc.stack_folder(sub_dir, pattern="Light_*.fit")
        # Output filename should contain object name without _sub
        assert "M42" in result.stacked_file.name
        assert "_sub" not in result.stacked_file.name
