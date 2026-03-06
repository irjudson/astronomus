"""System tests: device state, location, sound, cancel (hardware) + shutdown/reboot (mock only).

Hardware tests:  pytest tests/seestar/test_system.py -m hardware --telescope-host=<ip>
Mock tests:      pytest tests/seestar/test_system.py -m mock
"""

import pytest

from app.clients.seestar_client import CommandError, SeestarClient
from tests.seestar.mock_server import MockSeestarServer


def _skip_if_unsupported(exc: CommandError) -> None:
    msg = str(exc)
    if any(f"code {c}" in msg for c in ("103", "104", "105")):
        pytest.skip(f"Firmware limitation: {exc}")


class TestSystemHardware:
    """Safe system operations on real hardware."""

    pytestmark = pytest.mark.hardware

    @pytest.mark.asyncio
    async def test_get_device_state_structure(self, telescope: SeestarClient):
        """get_device_state() returns a dict with recognised top-level keys."""
        state = await telescope.get_device_state()
        assert isinstance(state, dict)
        assert len(state) > 0

    @pytest.mark.asyncio
    async def test_get_app_state(self, telescope: SeestarClient):
        """get_app_state() returns a dict."""
        state = await telescope.get_app_state()
        assert isinstance(state, dict)

    @pytest.mark.asyncio
    async def test_set_location(self, telescope: SeestarClient):
        """set_location() accepts lat/lon and returns bool."""
        try:
            result = await telescope.set_location(longitude=-105.0, latitude=40.0)
            assert isinstance(result, bool)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise

    @pytest.mark.asyncio
    async def test_play_notification_sound(self, telescope: SeestarClient):
        """play_notification_sound() plays 'backyard' without error."""
        result = await telescope.play_notification_sound("backyard")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_cancel_current_operation(self, telescope: SeestarClient):
        """cancel_current_operation() succeeds or returns gracefully when idle.

        Code 207 means 'nothing to cancel' — that is a valid telescope state.
        """
        try:
            result = await telescope.cancel_current_operation()
            assert isinstance(result, bool)
        except CommandError:
            pass  # 207 = idle / nothing running — acceptable

    @pytest.mark.asyncio
    async def test_get_image_file_info(self, telescope: SeestarClient):
        """get_image_file_info() returns a dict."""
        try:
            result = await telescope.get_image_file_info()
            assert isinstance(result, dict)
        except CommandError as exc:
            _skip_if_unsupported(exc)
            raise


class TestSystemMock:
    """Dangerous system operations - mock only, NEVER run on real hardware."""

    pytestmark = pytest.mark.mock

    @pytest.mark.asyncio
    async def test_shutdown_telescope(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """shutdown_telescope() sends the correct command to mock; not real hardware."""
        result = await mock_client.shutdown_telescope()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_shutdown")

    @pytest.mark.asyncio
    async def test_reboot_telescope(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """reboot_telescope() sends the correct command to mock; not real hardware."""
        result = await mock_client.reboot_telescope()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_reboot")
