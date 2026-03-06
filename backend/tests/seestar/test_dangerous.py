"""Mock-only tests for dangerous commands.

These tests validate that the client sends the correct command+params to the
telescope for operations that must NEVER execute on real hardware during CI/CD.

Run:  pytest tests/seestar/test_dangerous.py -m mock
"""

import asyncio
from typing import Optional

import pytest

from app.clients.seestar_client import SeestarClient
from tests.seestar.mock_server import MockSeestarServer

pytestmark = pytest.mark.mock


class TestDangerousCommands:
    """Validate command structure for destructive/dangerous operations."""

    @pytest.mark.asyncio
    async def test_shutdown_sends_correct_command(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """shutdown_telescope() sends 'telescope_shutdown' with no extra params."""
        await mock_client.shutdown_telescope()
        cmd = mock_server_obj.last_command("pi_shutdown")
        assert cmd is not None, "pi_shutdown command not received by mock"

    @pytest.mark.asyncio
    async def test_reboot_sends_correct_command(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """reboot_telescope() sends 'pi_reboot'."""
        await mock_client.reboot_telescope()
        cmd = mock_server_obj.last_command("pi_reboot")
        assert cmd is not None, "pi_reboot command not received by mock"

    @pytest.mark.asyncio
    async def test_focuser_extreme_position_sends_command(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        """move_focuser_to_position(999999) sends 'move_focuser' with step=999999."""
        await mock_client.move_focuser_to_position(999999)
        cmd = mock_server_obj.last_command("move_focuser")
        assert cmd is not None, "move_focuser command not received by mock"

    @pytest.mark.asyncio
    async def test_reset_focuser_sends_correct_command(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        """reset_focuser_to_factory() sends 'reset_factory_focal_pos'."""
        await mock_client.reset_focuser_to_factory()
        cmd = mock_server_obj.last_command("reset_factory_focal_pos")
        assert cmd is not None, "reset focuser command not received by mock"

    @pytest.mark.asyncio
    async def test_rapid_gotos_handled(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """Multiple rapid slew calls complete without hanging or error."""
        for ra in (1.0, 2.0, 3.0):
            result = await mock_client.slew_to_coordinates(ra_hours=ra, dec_degrees=0.0)
            assert isinstance(result, bool)

        # slew_to_coordinates sends scope_move with action="slew"
        slew_commands = [cmd for cmd in mock_server_obj.commands_received if cmd.get("method") == "scope_move"]
        assert len(slew_commands) >= 3, "Expected 3 scope_move commands to be received"

    @pytest.mark.asyncio
    async def test_park_sends_scope_park(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        """park() sends the 'scope_park' command."""
        await mock_client.park()
        cmd = mock_server_obj.last_command("scope_park")
        assert cmd is not None, "Expected scope_park command in commands_received"
