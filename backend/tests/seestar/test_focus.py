"""Focus tests: safe moves on hardware, dangerous extremes via mock only.

Hardware tests:  pytest tests/seestar/test_focus.py -m hardware --telescope-host=<ip>
Mock tests:      pytest tests/seestar/test_focus.py -m mock
"""

import pytest

from app.clients.seestar_client import CommandError, SeestarClient
from tests.seestar.mock_server import MockSeestarServer


class TestFocusHardware:
    """Safe focus operations on real hardware.

    Requires telescope_ready so the arm is open (focuser commands fail with
    code 207 when the arm is parked / not in a view session).
    """

    pytestmark = pytest.mark.hardware

    @pytest.mark.asyncio
    async def test_auto_focus(self, telescope_ready: SeestarClient):
        """auto_focus() sends command and returns bool."""
        result = await telescope_ready.auto_focus()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_stop_autofocus(self, telescope_ready: SeestarClient):
        """stop_autofocus() clears any focus operation."""
        result = await telescope_ready.stop_autofocus()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_move_focuser_relative_plus(self, telescope_ready: SeestarClient):
        """move_focuser_relative(+10) stays within safe range."""
        try:
            result = await telescope_ready.move_focuser_relative(10)
            assert isinstance(result, bool)
        except CommandError as exc:
            msg = str(exc)
            if any(f"code {c}" in msg for c in ("103", "104", "105")):
                pytest.skip(f"Firmware does not accept relative focuser offset param: {exc}")
            raise

    @pytest.mark.asyncio
    async def test_move_focuser_relative_minus(self, telescope_ready: SeestarClient):
        """move_focuser_relative(-10) stays within safe range."""
        try:
            result = await telescope_ready.move_focuser_relative(-10)
            assert isinstance(result, bool)
        except CommandError as exc:
            msg = str(exc)
            if any(f"code {c}" in msg for c in ("103", "104", "105")):
                pytest.skip(f"Firmware does not accept relative focuser offset param: {exc}")
            raise


class TestFocusMock:
    """Dangerous focus operations - validated against mock, never on hardware."""

    pytestmark = pytest.mark.mock

    @pytest.mark.asyncio
    async def test_move_focuser_extreme_position(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """move_focuser_to_position(999999) is sent to mock but never real hardware."""
        result = await mock_client.move_focuser_to_position(999999)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("move_focuser"), "Expected 'move_focuser' command in commands_received"

    @pytest.mark.asyncio
    async def test_reset_focuser_sends_command(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """reset_focuser_to_factory() is validated against mock server."""
        result = await mock_client.reset_focuser_to_factory()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("reset_factory_focal_pos")
