"""Hardware tests: connect, authenticate, heartbeat, disconnect.

Run with:  pytest tests/seestar/test_connection.py --telescope-host=<ip>
"""

import asyncio

import pytest
import pytest_asyncio

from app.clients.seestar_client import SeestarClient, SeestarState

pytestmark = pytest.mark.hardware


class TestConnection:
    """Tests that require a live Seestar S50 telescope."""

    @pytest.mark.asyncio
    async def test_connect_and_authenticate(self, telescope: SeestarClient):
        """connect() returns True and client is in CONNECTED state."""
        assert telescope.connected is True
        assert telescope.status.state != SeestarState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_initial_state_populated(self, telescope: SeestarClient):
        """After connect, get_device_state() returns a non-empty dict."""
        state = await telescope.get_device_state()
        assert isinstance(state, dict)
        assert len(state) > 0

    @pytest.mark.asyncio
    async def test_heartbeat_maintained(self, telescope: SeestarClient):
        """Client remains connected after waiting past the heartbeat interval."""
        # Heartbeat fires every 2 seconds; wait 5 to confirm it fires at least once
        await asyncio.sleep(5)
        assert telescope.connected is True

    @pytest.mark.asyncio
    async def test_disconnect_cleanly(self, telescope: SeestarClient):
        """disconnect() completes without error and leaves connected=False."""
        await telescope.disconnect()
        assert telescope.connected is False

    @pytest.mark.asyncio
    async def test_get_current_coordinates(self, telescope: SeestarClient):
        """get_current_coordinates() returns a dict with 'ra' and 'dec' keys."""
        coords = await telescope.get_current_coordinates()
        assert "ra" in coords
        assert "dec" in coords
        assert isinstance(coords["ra"], (int, float))
        assert isinstance(coords["dec"], (int, float))
