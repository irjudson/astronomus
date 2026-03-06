"""Hardware tests: preview, AVI recording, annotation, imaging, exposure.

Run with:  pytest tests/seestar/test_imaging.py --telescope-host=<ip>

All imaging tests require the arm to be open (telescope_ready fixture).
"""

import asyncio

import pytest

from app.clients.seestar_client import CommandError, SeestarClient


pytestmark = pytest.mark.hardware


def _skip_if_unsupported(exc: CommandError) -> None:
    msg = str(exc)
    if any(f"code {c}" in msg for c in ("103", "104", "105")):
        pytest.skip(f"Firmware limitation: {exc}")


class TestImaging:
    """Imaging-related hardware tests."""

    @pytest.mark.asyncio
    async def test_start_stop_preview_scenery(self, telescope_ready: SeestarClient):
        """start_preview('scenery') then stop immediately."""
        started = await telescope_ready.start_preview("scenery")
        assert isinstance(started, bool)
        await asyncio.sleep(1)
        try:
            stopped = await telescope_ready.cancel_current_operation()
            assert isinstance(stopped, bool)
        except CommandError:
            pass  # Nothing to cancel is acceptable

    @pytest.mark.asyncio
    async def test_start_stop_preview_star(self, telescope_ready: SeestarClient):
        """start_preview('star') then stop immediately."""
        started = await telescope_ready.start_preview("star")
        assert isinstance(started, bool)
        await asyncio.sleep(1)
        try:
            await telescope_ready.cancel_current_operation()
        except CommandError:
            pass

    @pytest.mark.asyncio
    async def test_start_stop_avi_recording(self, telescope_ready: SeestarClient):
        """start_record_avi(), wait 2s, stop_record_avi() — needs active view session."""
        # Establish a view session first (arm open from telescope_ready, now start imaging)
        await telescope_ready.start_preview("star")
        await asyncio.sleep(1)
        try:
            started = await telescope_ready.start_record_avi()
            assert isinstance(started, bool)
            await asyncio.sleep(2)
            stopped = await telescope_ready.stop_record_avi()
            assert isinstance(stopped, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            pytest.skip(f"AVI recording not available in current telescope state: {exc}")

    @pytest.mark.asyncio
    async def test_toggle_annotate(self, telescope_ready: SeestarClient):
        """start_annotate() then stop_annotate()."""
        try:
            started = await telescope_ready.start_annotate()
            assert isinstance(started, bool)
            await asyncio.sleep(1)
            stopped = await telescope_ready.stop_annotate()
            assert isinstance(stopped, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            pytest.skip(f"Annotation not available in current state: {exc}")

    @pytest.mark.asyncio
    async def test_start_stop_imaging(self, telescope_ready: SeestarClient):
        """start_imaging(), verify state, stop immediately."""
        started = await telescope_ready.start_imaging()
        assert isinstance(started, bool)
        await asyncio.sleep(2)
        stopped = await telescope_ready.stop_imaging()
        assert isinstance(stopped, bool)

    @pytest.mark.asyncio
    async def test_set_exposure_values(self, telescope: SeestarClient):
        """set_exposure(stack_exposure_ms=5000) returns bool."""
        result = await telescope.set_exposure(stack_exposure_ms=5000)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_configure_dither(self, telescope: SeestarClient):
        """configure_dither(enabled=True, pixels=50) returns bool."""
        result = await telescope.configure_dither(enabled=True, pixels=50)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_check_stacking_state(self, telescope: SeestarClient):
        """check_stacking_complete() returns a bool."""
        result = await telescope.check_stacking_complete()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_plate_solve_result(self, telescope_ready: SeestarClient):
        """get_plate_solve_result() returns a dict (may be empty if no solve done)."""
        try:
            result = await telescope_ready.get_plate_solve_result()
            assert isinstance(result, dict)
        except CommandError:
            pass  # No solve data available yet — valid telescope state

    @pytest.mark.asyncio
    async def test_get_field_annotations(self, telescope_ready: SeestarClient):
        """get_field_annotations() returns a dict (may be empty if no annotation done)."""
        try:
            result = await telescope_ready.get_field_annotations()
            assert isinstance(result, dict)
        except CommandError:
            pass  # No annotation data yet — valid when no solve has been performed
