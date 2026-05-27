"""Mock-server tests for SeestarSystemMixin methods (no real hardware required).

Run with:  pytest tests/seestar/test_system_mock.py -m mock
"""

import pytest

from app.clients.seestar_client import SeestarClient
from tests.seestar.mock_server import MockSeestarServer

pytestmark = pytest.mark.mock


class TestSystemMockExtra:
    """Additional system management tests against the mock server."""

    @pytest.mark.asyncio
    async def test_set_location(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_location(longitude=-105.0, latitude=40.0)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("set_user_location")
        cmd = mock_server_obj.last_command("set_user_location")
        assert cmd["params"]["lat"] == 40.0
        assert cmd["params"]["lon"] == -105.0
        assert cmd["params"]["force"] is True

    @pytest.mark.asyncio
    async def test_play_notification_sound(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.play_notification_sound("backyard")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("play_sound")
        cmd = mock_server_obj.last_command("play_sound")
        assert cmd["params"]["volume"] == "backyard"

    @pytest.mark.asyncio
    async def test_play_notification_sound_silent(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.play_notification_sound("silent")
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_image_file_info_empty_path(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.get_image_file_info()
        assert isinstance(result, dict)
        assert mock_server_obj.received_method("get_img_file_info")
        cmd = mock_server_obj.last_command("get_img_file_info")
        # Empty string param
        assert cmd["params"] == ""

    @pytest.mark.asyncio
    async def test_get_image_file_info_with_path(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.get_image_file_info("/data/img.fits")
        assert isinstance(result, dict)
        cmd = mock_server_obj.last_command("get_img_file_info")
        assert cmd["params"] == "/data/img.fits"

    @pytest.mark.asyncio
    async def test_cancel_current_operation(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.cancel_current_operation()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("iscope_cancel_view")

    @pytest.mark.asyncio
    async def test_get_pi_info(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        # Mock server returns generic {"result": 0} for pi_get_info — method returns result which may be 0
        result = await mock_client.get_pi_info()
        # get_pi_info returns response.get("result", {}) — so 0 or dict are both valid from mock
        assert result is not None
        assert mock_server_obj.received_method("pi_get_info")

    @pytest.mark.asyncio
    async def test_get_pi_time(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.get_pi_time()
        # Mock server returns {"result": 0} → result is 0, not a dict
        assert result is not None
        assert mock_server_obj.received_method("pi_get_time")

    @pytest.mark.asyncio
    async def test_set_pi_time(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_pi_time(1700000000)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_set_time")
        cmd = mock_server_obj.last_command("pi_set_time")
        assert cmd["params"]["time"] == 1700000000

    @pytest.mark.asyncio
    async def test_get_station_state(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.get_station_state()
        # Mock server returns {"result": 0} for pi_station_state — 0 or dict both acceptable
        assert result is not None
        assert mock_server_obj.received_method("pi_station_state")

    @pytest.mark.asyncio
    async def test_set_dew_heater_on(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_dew_heater(enabled=True, power_level=90)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_output_set2")
        cmd = mock_server_obj.last_command("pi_output_set2")
        assert cmd["params"]["heater"]["state"] is True
        assert cmd["params"]["heater"]["value"] == 90

    @pytest.mark.asyncio
    async def test_set_dew_heater_off(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_dew_heater(enabled=False, power_level=0)
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("pi_output_set2")
        assert cmd["params"]["heater"]["state"] is False

    @pytest.mark.asyncio
    async def test_set_dew_heater_invalid_power_raises(self, mock_client: SeestarClient):
        with pytest.raises(ValueError):
            await mock_client.set_dew_heater(enabled=True, power_level=150)

    @pytest.mark.asyncio
    async def test_set_dc_output(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        config = {"enabled": True}
        result = await mock_client.set_dc_output(config)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_output_set2")

    @pytest.mark.asyncio
    async def test_check_polar_alignment(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.check_polar_alignment()
        assert isinstance(result, dict)
        assert mock_server_obj.received_method("check_pa_alt")

    @pytest.mark.asyncio
    async def test_clear_polar_alignment(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.clear_polar_alignment()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("clear_polar_align")

    @pytest.mark.asyncio
    async def test_start_compass_calibration(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.start_compass_calibration()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("start_compass_calibration")

    @pytest.mark.asyncio
    async def test_stop_compass_calibration(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.stop_compass_calibration()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("stop_compass_calibration")

    @pytest.mark.asyncio
    async def test_get_compass_state_from_device_state(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        # The mock server's device_state template doesn't have compass_sensor, so
        # it falls through to the dedicated command which returns {"result": 0} → 0
        result = await mock_client.get_compass_state()
        assert result is not None

    @pytest.mark.asyncio
    async def test_start_leveling(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.start_leveling()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("start_gsensor_calibration")

    @pytest.mark.asyncio
    async def test_get_balance_sensor_no_key(self, mock_client: SeestarClient):
        # Mock device state lacks balance keys → returns zeros
        result = await mock_client.get_balance_sensor()
        assert isinstance(result, dict)
        assert "x" in result
        assert "y" in result

    @pytest.mark.asyncio
    async def test_start_gsensor_calibration(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.start_gsensor_calibration()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("start_gsensor_calibration")

    @pytest.mark.asyncio
    async def test_reset_focuser_to_factory(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.reset_focuser_to_factory()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("reset_factory_focal_pos")

    @pytest.mark.asyncio
    async def test_join_remote_session_empty(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.join_remote_session()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("remote_join")
        cmd = mock_server_obj.last_command("remote_join")
        assert cmd["params"] == {}

    @pytest.mark.asyncio
    async def test_join_remote_session_with_id(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.join_remote_session("session-123")
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("remote_join")
        assert cmd["params"]["session_id"] == "session-123"

    @pytest.mark.asyncio
    async def test_leave_remote_session(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.leave_remote_session()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("remote_disjoin")

    @pytest.mark.asyncio
    async def test_disconnect_remote_client_empty(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.disconnect_remote_client()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("remote_disconnect")

    @pytest.mark.asyncio
    async def test_disconnect_remote_client_with_id(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.disconnect_remote_client("client-42")
        assert isinstance(result, bool)
        cmd = mock_server_obj.last_command("remote_disconnect")
        assert cmd["params"]["client_id"] == "client-42"

    @pytest.mark.asyncio
    async def test_scan_wifi_networks(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.scan_wifi_networks()
        # Mock server returns {"result": 0} → 0, which is what the method returns as-is
        assert result is not None
        assert mock_server_obj.received_method("pi_station_scan")

    @pytest.mark.asyncio
    async def test_connect_to_wifi(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.connect_to_wifi("HomeWifi")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_station_select")
        cmd = mock_server_obj.last_command("pi_station_select")
        assert cmd["params"]["ssid"] == "HomeWifi"

    @pytest.mark.asyncio
    async def test_save_wifi_network(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.save_wifi_network("HomeWifi", "secret", "WPA2-PSK")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_station_set")

    @pytest.mark.asyncio
    async def test_list_saved_wifi_networks(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.list_saved_wifi_networks()
        assert result is not None
        assert mock_server_obj.received_method("pi_station_list")

    @pytest.mark.asyncio
    async def test_remove_wifi_network(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.remove_wifi_network("OldWifi")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_station_remove")
        cmd = mock_server_obj.last_command("pi_station_remove")
        assert cmd["params"]["ssid"] == "OldWifi"

    @pytest.mark.asyncio
    async def test_enable_wifi_client_mode(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.enable_wifi_client_mode()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_station_open")

    @pytest.mark.asyncio
    async def test_disable_wifi_client_mode(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.disable_wifi_client_mode()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_station_close")

    @pytest.mark.asyncio
    async def test_configure_access_point(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.configure_access_point("Seestar_AP", "password123", is_5g=True)
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_set_ap")
        cmd = mock_server_obj.last_command("pi_set_ap")
        assert cmd["params"]["ssid"] == "Seestar_AP"
        assert cmd["params"]["is_5g"] is True

    @pytest.mark.asyncio
    async def test_set_wifi_country(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.set_wifi_country("US")
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("set_wifi_country")
        cmd = mock_server_obj.last_command("set_wifi_country")
        assert cmd["params"]["country"] == "US"

    @pytest.mark.asyncio
    async def test_start_demo_mode(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.start_demo_mode()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("start_demonstrate")

    @pytest.mark.asyncio
    async def test_stop_demo_mode(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        result = await mock_client.stop_demo_mode()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("stop_demonstrate")

    @pytest.mark.asyncio
    async def test_check_client_verified_bool_result(
        self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer
    ):
        result = await mock_client.check_client_verified()
        assert isinstance(result, bool)
        assert mock_server_obj.received_method("pi_is_verified")
