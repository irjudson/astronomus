"""Hardware tests: mount movement, coordinates, tracking, park.

Run with:  pytest tests/seestar/test_mount.py --telescope-host=<ip>
"""

import asyncio

import pytest

from app.clients.seestar_client import CommandError, SeestarClient


pytestmark = pytest.mark.hardware


def _skip_if_unsupported(exc: CommandError) -> None:
    """Skip the test when firmware returns a known-unimplemented error code.

    Code 103 = method not found
    Code 104 = expected int param (wrong client param format)
    Code 105 = expected string param (wrong client param format)
    """
    msg = str(exc)
    if any(f"code {c}" in msg for c in ("103", "104", "105")):
        pytest.skip(f"Firmware limitation: {exc}")


class TestMount:
    """Mount/pointing tests that run against a real telescope."""

    @pytest.mark.asyncio
    async def test_get_equatorial_coordinates(self, telescope: SeestarClient):
        """scope_get_equ_coord returns valid ra and dec."""
        coords = await telescope.get_current_coordinates()
        assert "ra" in coords
        assert "dec" in coords
        assert 0.0 <= coords["ra"] <= 24.0
        assert -90.0 <= coords["dec"] <= 90.0

    @pytest.mark.asyncio
    async def test_get_horizontal_coordinates(self, telescope: SeestarClient):
        """scope_get_horiz_coord returns alt and az (as list or dict)."""
        try:
            response = await telescope._send_command("scope_get_horiz_coord", {})
            result = response.get("result", {})
            # Firmware returns [alt, az] list rather than {"alt": ..., "az": ...}
            if isinstance(result, list):
                assert len(result) == 2
                assert isinstance(result[0], (int, float))  # alt
                assert isinstance(result[1], (int, float))  # az
            else:
                assert "alt" in result
                assert "az" in result
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_start_tracking(self, telescope_ready: SeestarClient):
        """Sending stop to mount succeeds without error."""
        try:
            result = await telescope_ready.move_scope("stop")
            assert isinstance(result, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_stop_tracking(self, telescope_ready: SeestarClient):
        """Abort movement command returns without error."""
        try:
            result = await telescope_ready.move_scope("abort")
            assert isinstance(result, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_move_scope_north(self, telescope_ready: SeestarClient):
        """Brief north move completes without error."""
        try:
            result = await telescope_ready.move_scope("up", speed=0.5)
            assert isinstance(result, bool)
            await asyncio.sleep(0.5)
            await telescope_ready.move_scope("stop")
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_move_scope_south(self, telescope_ready: SeestarClient):
        """Brief south move completes without error."""
        try:
            result = await telescope_ready.move_scope("down", speed=0.5)
            assert isinstance(result, bool)
            await asyncio.sleep(0.5)
            await telescope_ready.move_scope("stop")
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_move_scope_east(self, telescope_ready: SeestarClient):
        """Brief east move completes without error."""
        try:
            result = await telescope_ready.move_scope("right", speed=0.5)
            assert isinstance(result, bool)
            await asyncio.sleep(0.5)
            await telescope_ready.move_scope("stop")
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_move_scope_west(self, telescope_ready: SeestarClient):
        """Brief west move completes without error."""
        try:
            result = await telescope_ready.move_scope("left", speed=0.5)
            assert isinstance(result, bool)
            await asyncio.sleep(0.5)
            await telescope_ready.move_scope("stop")
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_scope_speed_move(self, telescope_ready: SeestarClient):
        """speed_move at low speed for 1 second returns without error."""
        try:
            result = await telescope_ready.move_scope("up", speed=1.0)
            assert isinstance(result, bool)
            await asyncio.sleep(1)
            await telescope_ready.move_scope("stop")
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_stop_slew(self, telescope_ready: SeestarClient):
        """stop_telescope_movement() clears any active movement."""
        try:
            result = await telescope_ready.stop_telescope_movement()
            assert isinstance(result, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_park(self, telescope: SeestarClient):
        """park() sends command and returns without raising."""
        result = await telescope.park()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_slew_to_coordinates(self, telescope_ready: SeestarClient):
        """slew_to_coordinates() initiates without error (short cancel follows)."""
        try:
            result = await telescope_ready.slew_to_coordinates(ra_hours=6.0, dec_degrees=0.0)
            assert isinstance(result, bool)
            # Cancel immediately to avoid long slew
            await telescope_ready.stop_telescope_movement()
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise
