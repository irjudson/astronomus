"""Extended mock-server tests for SeestarMountMixin — covering goto_target and
other uncovered methods.

Run with:  pytest tests/seestar/test_mount_mock_extended.py -m mock
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.seestar.types import CommandError, MountMode
from app.clients.seestar_client import SeestarClient
from tests.seestar.mock_server import MockSeestarServer, _COMMAND_RESPONSES

pytestmark = pytest.mark.mock


# ---------------------------------------------------------------------------
# initialize_equatorial_mode
# ---------------------------------------------------------------------------


class TestInitializeEquatorialMode:
    @pytest.mark.asyncio
    async def test_initialize_equatorial_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        with patch("asyncio.sleep", new=AsyncMock()):
            result = await mock_client.initialize_equatorial_mode()
        assert result is True
        assert mock_server_obj.received_method("mount_go_home")

    @pytest.mark.asyncio
    async def test_initialize_equatorial_failure_raises(
        self, mock_client: SeestarClient
    ):
        original = _COMMAND_RESPONSES.get("mount_go_home")
        _COMMAND_RESPONSES["mount_go_home"] = {"result": -1, "code": 207}
        try:
            with pytest.raises(CommandError, match="Go home failed"):
                await mock_client.initialize_equatorial_mode()
        finally:
            if original is not None:
                _COMMAND_RESPONSES["mount_go_home"] = original


# ---------------------------------------------------------------------------
# set_mount_mode
# ---------------------------------------------------------------------------


class TestSetMountMode:
    @pytest.mark.asyncio
    async def test_set_mount_mode_altaz_success(self, mock_client: SeestarClient):
        result = await mock_client.set_mount_mode(MountMode.ALTAZ)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_mount_mode_equatorial_not_initialized_raises(
        self, mock_client: SeestarClient
    ):
        # Default mock client has equatorial_initialized=False
        with pytest.raises(CommandError, match="requires initialization"):
            await mock_client.set_mount_mode(MountMode.EQUATORIAL)

    @pytest.mark.asyncio
    async def test_set_mount_mode_equatorial_after_init(self, mock_client: SeestarClient):
        mock_client.status.equatorial_initialized = True
        result = await mock_client.set_mount_mode(MountMode.EQUATORIAL)
        assert result is True


# ---------------------------------------------------------------------------
# goto_target — ALTAZ mode (the large uncovered block)
# ---------------------------------------------------------------------------


class TestGotoTargetAltaz:
    @pytest.mark.asyncio
    async def test_goto_target_altaz_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client.status.equatorial_initialized = False
        # Pre-set observer location so DB lookup is skipped
        mock_client._observer_location = (40.0, -105.0, 1500)

        with patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=True)):
            result = await mock_client.goto_target(
                ra_hours=5.919, dec_degrees=-5.39, target_name="M42"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_goto_target_altaz_move_fails(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client._observer_location = (40.0, -105.0, 1500)

        with patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=False)):
            result = await mock_client.goto_target(
                ra_hours=5.919, dec_degrees=-5.39, target_name="M42"
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_goto_target_altaz_low_altitude_warning(
        self, mock_client: SeestarClient
    ):
        """Target below 10° altitude should still attempt and succeed."""
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client._observer_location = (40.0, -105.0, 0)

        with patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=True)):
            result = await mock_client.goto_target(
                ra_hours=5.0, dec_degrees=-80.0, target_name="LowTarget"
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_goto_target_altaz_cancels_active_view(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        """If get_view_state says working, cancel is sent first."""
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client._observer_location = (40.0, -105.0, 0)

        # Override get_view_state to return "working" / "ContinuousExposure"
        original = _COMMAND_RESPONSES.get("get_view_state")
        _COMMAND_RESPONSES["get_view_state"] = {
            "result": {"View": {"state": "working", "stage": "ContinuousExposure"}},
            "code": 0,
        }
        try:
            with patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=True)):
                result = await mock_client.goto_target(
                    ra_hours=5.0, dec_degrees=-5.0, target_name="M42"
                )
            assert result is True
            assert mock_server_obj.received_method("iscope_cancel_view")
        finally:
            if original is not None:
                _COMMAND_RESPONSES["get_view_state"] = original

    @pytest.mark.asyncio
    async def test_goto_target_caches_observer_location(
        self, mock_client: SeestarClient
    ):
        """After a successful goto, _observer_location is cached (non-None)."""
        mock_client.status.mount_mode = MountMode.ALTAZ
        # Pre-set location so DB lookup is not triggered
        mock_client._observer_location = (40.0, -105.0, 1500)

        with patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=True)):
            result = await mock_client.goto_target(
                ra_hours=5.0, dec_degrees=-5.0, target_name="M42"
            )
        assert result is True
        # Location should still be cached after the call
        assert mock_client._observer_location == (40.0, -105.0, 1500)

    @pytest.mark.asyncio
    async def test_goto_target_switches_from_equatorial_to_altaz(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        """Device is in equatorial mode but client wants altaz — calls clear_polar_alignment."""
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client._observer_location = (40.0, -105.0, 0)

        # Device state says equ_mode=True
        original = _COMMAND_RESPONSES.get("get_device_state")
        _COMMAND_RESPONSES["get_device_state"] = {
            "result": {
                "device": {"firmware_ver_string": "mock-1.0"},
                "mount": {"close": False, "equ_mode": True},
            },
            "code": 0,
        }
        try:
            with (
                patch.object(mock_client, "clear_polar_alignment", new=AsyncMock(return_value=True)),
                patch.object(mock_client, "move_to_horizon", new=AsyncMock(return_value=True)),
            ):
                result = await mock_client.goto_target(
                    ra_hours=5.0, dec_degrees=-5.0, target_name="M42"
                )
            assert result is True
        finally:
            if original is not None:
                _COMMAND_RESPONSES["get_device_state"] = original

    @pytest.mark.asyncio
    async def test_goto_target_clear_polar_fail_raises(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.ALTAZ
        mock_client._observer_location = (40.0, -105.0, 0)

        original = _COMMAND_RESPONSES.get("get_device_state")
        _COMMAND_RESPONSES["get_device_state"] = {
            "result": {
                "device": {"firmware_ver_string": "mock-1.0"},
                "mount": {"close": False, "equ_mode": True},
            },
            "code": 0,
        }
        try:
            with patch.object(
                mock_client, "clear_polar_alignment", new=AsyncMock(side_effect=Exception("clear failed"))
            ):
                with pytest.raises(CommandError, match="Failed to switch mount"):
                    await mock_client.goto_target(
                        ra_hours=5.0, dec_degrees=-5.0, target_name="M42"
                    )
        finally:
            if original is not None:
                _COMMAND_RESPONSES["get_device_state"] = original


# ---------------------------------------------------------------------------
# goto_target — EQUATORIAL mode
# ---------------------------------------------------------------------------


class TestGotoTargetEquatorial:
    @pytest.mark.asyncio
    async def test_goto_target_equatorial_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        result = await mock_client.goto_target(
            ra_hours=5.919, dec_degrees=-5.39, target_name="M42"
        )
        assert result is True
        assert mock_server_obj.received_method("iscope_start_view")

    @pytest.mark.asyncio
    async def test_goto_target_equatorial_not_initialized_raises(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = False

        with pytest.raises(CommandError, match="requires initialization"):
            await mock_client.goto_target(
                ra_hours=5.0, dec_degrees=-5.0, target_name="M42"
            )

    @pytest.mark.asyncio
    async def test_goto_target_equatorial_command_fails_203(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        original = _COMMAND_RESPONSES.get("iscope_start_view")
        _COMMAND_RESPONSES["iscope_start_view"] = {"result": -1, "code": 203}
        try:
            with pytest.raises(CommandError, match="already moving"):
                await mock_client.goto_target(ra_hours=5.0, dec_degrees=-5.0, target_name="M42")
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_view"] = original

    @pytest.mark.asyncio
    async def test_goto_target_equatorial_command_fails_207(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        original = _COMMAND_RESPONSES.get("iscope_start_view")
        _COMMAND_RESPONSES["iscope_start_view"] = {"result": -1, "code": 207}
        try:
            with pytest.raises(CommandError, match="Mount not ready"):
                await mock_client.goto_target(ra_hours=5.0, dec_degrees=-5.0, target_name="M42")
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_view"] = original

    @pytest.mark.asyncio
    async def test_goto_target_equatorial_command_fails_259(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        original = _COMMAND_RESPONSES.get("iscope_start_view")
        _COMMAND_RESPONSES["iscope_start_view"] = {"result": -1, "code": 259}
        try:
            with pytest.raises(CommandError, match="Imaging is active"):
                await mock_client.goto_target(ra_hours=5.0, dec_degrees=-5.0, target_name="M42")
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_view"] = original

    @pytest.mark.asyncio
    async def test_goto_target_equatorial_command_fails_unknown_code(
        self, mock_client: SeestarClient
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        original = _COMMAND_RESPONSES.get("iscope_start_view")
        _COMMAND_RESPONSES["iscope_start_view"] = {"result": -1, "code": 999}
        try:
            with pytest.raises(CommandError, match="Goto failed"):
                await mock_client.goto_target(ra_hours=5.0, dec_degrees=-5.0, target_name="M42")
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_view"] = original

    @pytest.mark.asyncio
    async def test_goto_target_with_lp_filter(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        mock_client.status.mount_mode = MountMode.EQUATORIAL
        mock_client.status.equatorial_initialized = True

        result = await mock_client.goto_target(
            ra_hours=5.0, dec_degrees=-5.0, target_name="M42", use_lp_filter=True
        )
        assert result is True
        cmd = mock_server_obj.last_command("iscope_start_view")
        assert cmd["params"]["lp_filter"] is True


# ---------------------------------------------------------------------------
# start_preview
# ---------------------------------------------------------------------------


class TestStartPreview:
    @pytest.mark.asyncio
    async def test_start_preview_scenery(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_preview(mode="scenery")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("iscope_start_view")
        cmd = mock_server_obj.last_command("iscope_start_view")
        assert cmd["params"]["mode"] == "scenery"

    @pytest.mark.asyncio
    async def test_start_preview_moon(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_preview(mode="moon")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_start_preview_sun(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_preview(mode="sun")
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# start_record_avi / stop_record_avi
# ---------------------------------------------------------------------------


class TestRecordAvi:
    @pytest.mark.asyncio
    async def test_start_record_avi_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_record_avi(filename="test_session")
        assert result is True
        assert mock_server_obj.received_method("start_record_avi")

    @pytest.mark.asyncio
    async def test_start_record_avi_no_filename(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_record_avi()
        assert result is True

    @pytest.mark.asyncio
    async def test_start_record_avi_failure_raises(self, mock_client: SeestarClient):
        original = _COMMAND_RESPONSES.get("start_record_avi")
        _COMMAND_RESPONSES["start_record_avi"] = {"result": -1, "code": 207}
        try:
            with pytest.raises(CommandError):
                await mock_client.start_record_avi()
        finally:
            if original is not None:
                _COMMAND_RESPONSES["start_record_avi"] = original

    @pytest.mark.asyncio
    async def test_stop_record_avi_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.stop_record_avi()
        assert result is True
        assert mock_server_obj.received_method("stop_record_avi")

    @pytest.mark.asyncio
    async def test_stop_record_avi_failure_raises(self, mock_client: SeestarClient):
        original = _COMMAND_RESPONSES.get("stop_record_avi")
        _COMMAND_RESPONSES["stop_record_avi"] = {"result": -1, "code": 105}
        try:
            with pytest.raises(CommandError):
                await mock_client.stop_record_avi()
        finally:
            if original is not None:
                _COMMAND_RESPONSES["stop_record_avi"] = original


# ---------------------------------------------------------------------------
# start/stop track object
# ---------------------------------------------------------------------------


class TestTrackObject:
    @pytest.mark.asyncio
    async def test_start_track_object_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        original = _COMMAND_RESPONSES.get("start_track_object")
        _COMMAND_RESPONSES["start_track_object"] = {"result": 0, "code": 0}
        try:
            result = await mock_client.start_track_object("satellite", "ISS")
            assert result is True
        finally:
            if original is not None:
                _COMMAND_RESPONSES["start_track_object"] = original
            else:
                _COMMAND_RESPONSES.pop("start_track_object", None)

    @pytest.mark.asyncio
    async def test_start_track_object_failure_raises(self, mock_client: SeestarClient):
        _COMMAND_RESPONSES["start_track_object"] = {"result": -1, "code": 105}
        try:
            with pytest.raises(CommandError):
                await mock_client.start_track_object("satellite", "ISS")
        finally:
            _COMMAND_RESPONSES.pop("start_track_object", None)

    @pytest.mark.asyncio
    async def test_stop_track_object_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        _COMMAND_RESPONSES["stop_track_object"] = {"result": 0, "code": 0}
        try:
            result = await mock_client.stop_track_object()
            assert result is True
        finally:
            _COMMAND_RESPONSES.pop("stop_track_object", None)

    @pytest.mark.asyncio
    async def test_stop_track_object_failure_raises(self, mock_client: SeestarClient):
        _COMMAND_RESPONSES["stop_track_object"] = {"result": -1, "code": 105}
        try:
            with pytest.raises(CommandError):
                await mock_client.stop_track_object()
        finally:
            _COMMAND_RESPONSES.pop("stop_track_object", None)


# ---------------------------------------------------------------------------
# scan_planet / planet_stack
# ---------------------------------------------------------------------------


class TestPlanetaryMountCommands:
    @pytest.mark.asyncio
    async def test_start_scan_planet_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_scan_planet()
        assert result is True
        assert mock_server_obj.received_method("iscope_start_scan_planet")

    @pytest.mark.asyncio
    async def test_start_scan_planet_failure_raises(self, mock_client: SeestarClient):
        original = _COMMAND_RESPONSES.get("iscope_start_scan_planet")
        _COMMAND_RESPONSES["iscope_start_scan_planet"] = {"result": -1, "code": 103}
        try:
            with pytest.raises(CommandError):
                await mock_client.start_scan_planet()
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_scan_planet"] = original

    @pytest.mark.asyncio
    async def test_start_planet_stack_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.start_planet_stack("Jupiter", 100, 200)
        assert result is True
        assert mock_server_obj.received_method("iscope_start_planet_stack")

    @pytest.mark.asyncio
    async def test_start_planet_stack_failure_raises(self, mock_client: SeestarClient):
        original = _COMMAND_RESPONSES.get("iscope_start_planet_stack")
        _COMMAND_RESPONSES["iscope_start_planet_stack"] = {"result": -1, "code": 103}
        try:
            with pytest.raises(CommandError):
                await mock_client.start_planet_stack("Jupiter", 100, 200)
        finally:
            if original is not None:
                _COMMAND_RESPONSES["iscope_start_planet_stack"] = original

    @pytest.mark.asyncio
    async def test_stop_planet_stack_success(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.stop_planet_stack()
        assert result is True
        assert mock_server_obj.received_method("iscope_stop_planet_stack")
