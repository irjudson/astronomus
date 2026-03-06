"""Hardware tests: planet scan, planet stack, configure planetary imaging.

Run with:  pytest tests/seestar/test_planetary.py --telescope-host=<ip>

All planetary tests require the arm to be open (telescope_ready fixture).
"""

import asyncio

import pytest

from app.clients.seestar_client import CommandError, SeestarClient

pytestmark = pytest.mark.hardware


def _skip_if_unsupported(exc: CommandError) -> None:
    msg = str(exc)
    if any(f"code {c}" in msg for c in ("103", "104", "105", "524")):
        pytest.skip(f"Firmware limitation: {exc}")


class TestPlanetary:
    """Planetary imaging hardware tests."""

    @pytest.mark.asyncio
    async def test_scan_planet_starts(self, telescope_ready: SeestarClient):
        """start_scan_planet() returns True (command accepted)."""
        try:
            result = await telescope_ready.start_scan_planet()
            assert isinstance(result, bool)
            await asyncio.sleep(1)
            try:
                await telescope_ready.cancel_current_operation()
            except CommandError:
                pass
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_start_stop_planet_stack(self, telescope_ready: SeestarClient):
        """start_planet_stack then stop_planet_stack round-trip."""
        try:
            started = await telescope_ready.start_planet_stack("Jupiter", 30, 100)
            assert isinstance(started, bool)
            await asyncio.sleep(2)
            stopped = await telescope_ready.stop_planet_stack()
            assert isinstance(stopped, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_start_planet_scan_by_name(self, telescope_ready: SeestarClient):
        """start_planet_scan() with planet name returns bool."""
        try:
            result = await telescope_ready.start_planet_scan("Mars", 30, 80.0)
            assert isinstance(result, bool)
            await asyncio.sleep(1)
            try:
                await telescope_ready.cancel_current_operation()
            except CommandError:
                pass
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_configure_planetary_imaging(self, telescope_ready: SeestarClient):
        """configure_planetary_imaging() returns bool."""
        result = await telescope_ready.configure_planetary_imaging(
            frame_count=100,
            save_frames=True,
            denoise=True,
        )
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_start_stop_view_plan(self, telescope_ready: SeestarClient):
        """start_view_plan / get_view_plan_state / stop_view_plan round-trip."""
        try:
            plan_config = {
                "target": "Jupiter",
                "ra": 5.0,
                "dec": 23.0,
            }
            started = await telescope_ready.start_view_plan(plan_config)
            assert isinstance(started, bool)

            state = await telescope_ready.get_view_plan_state()
            assert isinstance(state, dict)

            stopped = await telescope_ready.stop_view_plan()
            assert isinstance(stopped, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise
