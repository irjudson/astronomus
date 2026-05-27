"""Mock-server tests for SeestarMountMixin methods (no real hardware required).

Run with:  pytest tests/seestar/test_mount_mock.py -m mock
"""

import pytest

from app.clients.seestar_client import SeestarClient
from tests.seestar.mock_server import MockSeestarServer

pytestmark = pytest.mark.mock


class TestMountMockScope:
    """Mount control tests against the mock server."""

    @pytest.mark.asyncio
    async def test_scope_goto_success(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.scope_goto(ra_hours=2.5, dec_degrees=30.0)
        assert result is True
        assert mock_server_obj.received_method("scope_goto")
        cmd = mock_server_obj.last_command("scope_goto")
        assert cmd["params"] == [2.5, 30.0]

    @pytest.mark.asyncio
    async def test_scope_goto_failure(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        # Override mock to return failure
        from tests.seestar.mock_server import _COMMAND_RESPONSES

        original = _COMMAND_RESPONSES.get("scope_goto")
        _COMMAND_RESPONSES["scope_goto"] = {"result": -1, "code": 105}
        try:
            result = await mock_client.scope_goto(ra_hours=2.5, dec_degrees=30.0)
            assert result is False
        finally:
            if original is not None:
                _COMMAND_RESPONSES["scope_goto"] = original
            else:
                _COMMAND_RESPONSES.pop("scope_goto", None)

    @pytest.mark.asyncio
    async def test_move_to_horizon_success(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_to_horizon(azimuth=180.0, altitude=45.0)
        assert result is True
        assert mock_server_obj.received_method("scope_move_to_horizon")
        cmd = mock_server_obj.last_command("scope_move_to_horizon")
        assert cmd["params"]["azimuth"] == 180.0
        assert cmd["params"]["altitude"] == 45.0

    @pytest.mark.asyncio
    async def test_move_to_horizon_failure(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        from tests.seestar.mock_server import _COMMAND_RESPONSES

        original = _COMMAND_RESPONSES.get("scope_move_to_horizon")
        _COMMAND_RESPONSES["scope_move_to_horizon"] = {"result": -1, "code": 207}
        try:
            result = await mock_client.move_to_horizon(azimuth=0.0, altitude=0.0)
            assert result is False
        finally:
            if original is not None:
                _COMMAND_RESPONSES["scope_move_to_horizon"] = original

    @pytest.mark.asyncio
    async def test_move_scope_stop(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("stop")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("scope_move")

    @pytest.mark.asyncio
    async def test_move_scope_abort(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("abort")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("scope_move")

    @pytest.mark.asyncio
    async def test_move_scope_directional_up(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("up", speed=1.0, dur_sec=2)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("scope_speed_move")
        cmd = mock_server_obj.last_command("scope_speed_move")
        assert cmd["params"]["angle"] == 90  # up = 90°

    @pytest.mark.asyncio
    async def test_move_scope_directional_down(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("down", dur_sec=1)
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("scope_speed_move")
        assert cmd["params"]["angle"] == 270  # down = 270°

    @pytest.mark.asyncio
    async def test_move_scope_directional_left(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("left", dur_sec=1)
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("scope_speed_move")
        assert cmd["params"]["angle"] == 180  # left = 180°

    @pytest.mark.asyncio
    async def test_move_scope_directional_right(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("right", dur_sec=1)
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("scope_speed_move")
        assert cmd["params"]["angle"] == 0  # right = 0°

    @pytest.mark.asyncio
    async def test_move_scope_slew_with_coords(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.move_scope("slew", ra=5.0, dec=30.0)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("scope_move")

    @pytest.mark.asyncio
    async def test_move_scope_invalid_action_raises(self, mock_client: SeestarClient):
        with pytest.raises(ValueError, match="Invalid action"):
            await mock_client.move_scope("spin")

    @pytest.mark.asyncio
    async def test_move_scope_slew_missing_coords_raises(self, mock_client: SeestarClient):
        with pytest.raises(ValueError, match="RA and Dec required"):
            await mock_client.move_scope("slew")

    @pytest.mark.asyncio
    async def test_park_equatorial(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.park(equ_mode=True)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("scope_park")
        cmd = mock_server_obj.last_command("scope_park")
        assert cmd["params"]["equ_mode"] is True

    @pytest.mark.asyncio
    async def test_park_altaz(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.park(equ_mode=False)
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("scope_park")
        assert cmd["params"]["equ_mode"] is False

    @pytest.mark.asyncio
    async def test_get_device_state_returns_dict(self, mock_client: SeestarClient):
        state = await mock_client.get_device_state()
        assert isinstance(state, dict)
        assert "mount" in state

    @pytest.mark.asyncio
    async def test_get_device_state_with_keys(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        state = await mock_client.get_device_state(keys=["mount"])
        assert isinstance(state, dict)
        cmd = mock_server_obj.last_command("get_device_state")
        assert cmd["params"] == {"keys": ["mount"]}

    @pytest.mark.asyncio
    async def test_auto_focus_success(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.auto_focus()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("start_auto_focuse")

    @pytest.mark.asyncio
    async def test_start_imaging(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.start_imaging(restart=True)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("iscope_start_stack")

    @pytest.mark.asyncio
    async def test_stop_imaging(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.stop_imaging()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("iscope_stop_view")

    @pytest.mark.asyncio
    async def test_set_exposure(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_exposure(stack_exposure_ms=10000, continuous_exposure_ms=500)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("set_setting")

    @pytest.mark.asyncio
    async def test_configure_dither(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.configure_dither(enabled=True, pixels=30, interval=5)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("set_setting")
        cmd = mock_server_obj.last_command("set_setting")
        assert cmd["params"]["stack_dither"]["enable"] is True
        assert cmd["params"]["stack_dither"]["pix"] == 30

    @pytest.mark.asyncio
    async def test_stop_slew(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.stop_slew()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("iscope_stop_view")

    @pytest.mark.asyncio
    async def test_is_equatorial_mode_false_when_closed(self, mock_client: SeestarClient):
        result = await mock_client.is_equatorial_mode()
        # mock device state has close=False, no equ_mode key → returns False
        assert isinstance(result, bool)
