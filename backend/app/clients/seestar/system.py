"""System management: alignment, focuser, WiFi, RPi, hardware."""

from __future__ import annotations

from typing import Any, Dict

from .types import SeestarState


class SeestarSystemMixin:
    """Mixin providing system management and hardware control commands."""

    # ========================================================================
    # Phase 5+: System Management & Utilities
    # ========================================================================

    async def shutdown_telescope(self) -> bool:
        """Safely shutdown the telescope.

        Returns:
            True if shutdown initiated successfully

        Raises:
            CommandError: If shutdown fails
        """
        self.logger.info("Initiating telescope shutdown")

        response = await self._send_command("pi_shutdown", {})

        self.logger.info(f"Shutdown response: {response}")
        return response.get("result") == 0

    async def reboot_telescope(self) -> bool:
        """Reboot the telescope.

        Returns:
            True if reboot initiated successfully

        Raises:
            CommandError: If reboot fails
        """
        self.logger.info("Initiating telescope reboot")

        response = await self._send_command("pi_reboot", {})

        self.logger.info(f"Reboot response: {response}")
        return response.get("result") == 0

    async def play_notification_sound(self, volume: str = "backyard") -> bool:
        """Play notification sound on telescope.

        Args:
            volume: Volume level ("silent", "backyard", "outdoor")

        Returns:
            True if sound played successfully

        Raises:
            CommandError: If play fails
        """
        self.logger.info(f"Playing notification sound at volume: {volume}")

        params = {"volume": volume}

        response = await self._send_command("play_sound", params)

        self.logger.info(f"Play sound response: {response}")
        return response.get("result") == 0

    async def get_image_file_info(self, file_path: str = "") -> Dict[str, Any]:
        """Get information about captured image files.

        Args:
            file_path: Optional specific file path to query

        Returns:
            File information dict

        Raises:
            CommandError: If query fails
        """
        # Firmware expects a string param (code 105 otherwise); pass path string directly
        params = file_path  # may be "" — firmware accepts empty string to list recent files

        response = await self._send_command("get_img_file_info", params)

        return response.get("result", {})

    async def cancel_current_operation(self) -> bool:
        """Cancel current view/operation.

        Alternative to stop commands.

        Returns:
            True if cancel successful

        Raises:
            CommandError: If cancel fails
        """
        self.logger.info("Canceling current operation")

        response = await self._send_command("iscope_cancel_view", {})

        self.logger.info(f"Cancel operation response: {response}")
        return response.get("result") == 0

    async def set_location(self, longitude: float, latitude: float) -> bool:
        """Set user location for telescope calculations.

        Args:
            longitude: Longitude in degrees (-180 to 180, west is negative)
            latitude: Latitude in degrees (-90 to 90)

        Returns:
            True if location set successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting location: lon={longitude}, lat={latitude}")

        # Upstream seestar_alp uses separate lat/lon keys with force=True
        params = {"lat": latitude, "lon": longitude, "force": True}

        response = await self._send_command("set_user_location", params)

        self.logger.info(f"Set location response: {response}")
        return response.get("result") == 0

    async def move_to_horizon(self, azimuth: float, altitude: float) -> bool:
        """Move telescope to horizon coordinates.

        Args:
            azimuth: Azimuth in degrees (0-360)
            altitude: Altitude in degrees (0-90)

        Returns:
            True if move initiated successfully

        Raises:
            CommandError: If move fails
        """
        self.logger.info(f"Moving to horizon: az={azimuth}°, alt={altitude}°")

        params = {"azimuth": azimuth, "altitude": altitude}

        self._update_status(state=SeestarState.SLEWING)

        response = await self._send_command("scope_move_to_horizon", params)

        self.logger.debug(
            "scope_move_to_horizon response: result=%s code=%s", response.get("result"), response.get("code")
        )
        success = response.get("result") == 0
        return success

    async def reset_focuser_to_factory(self) -> bool:
        """Reset focuser to factory default position.

        Returns:
            True if reset successful

        Raises:
            CommandError: If reset fails
        """
        self.logger.info("Resetting focuser to factory position")

        response = await self._send_command("reset_factory_focal_pos", {})

        self.logger.info(f"Reset focuser response: {response}")
        return response.get("result") == 0

    async def check_polar_alignment(self) -> Dict[str, Any]:
        """Check polar alignment quality.

        Returns polar alignment information including error in arc-minutes.

        Returns:
            Polar alignment status dict

        Raises:
            CommandError: If check fails
        """
        response = await self._send_command("check_pa_alt", {})

        return response.get("result", {})

    async def clear_polar_alignment(self) -> bool:
        """Clear polar alignment calibration.

        Returns:
            True if clear successful

        Raises:
            CommandError: If clear fails
        """
        self.logger.info("Clearing polar alignment")

        response = await self._send_command("clear_polar_align", {})

        self.logger.info(f"Clear polar alignment response: {response}")
        return response.get("result") == 0

    async def start_compass_calibration(self) -> bool:
        """Start compass calibration procedure.

        Returns:
            True if calibration started successfully

        Raises:
            CommandError: If start fails
        """
        self.logger.info("Starting compass calibration")

        response = await self._send_command("start_compass_calibration", {})

        self.logger.info(f"Start compass calibration response: {response}")
        return response.get("result") == 0

    async def stop_compass_calibration(self) -> bool:
        """Stop compass calibration procedure.

        Returns:
            True if stop successful

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping compass calibration")

        response = await self._send_command("stop_compass_calibration", {})

        self.logger.info(f"Stop compass calibration response: {response}")
        return response.get("result") == 0

    async def get_compass_state(self) -> Dict[str, Any]:
        """Get compass heading and calibration state.

        Reads from device_state (compass_sensor key) which we confirmed is populated
        by the firmware.  Same nested-data pattern as balance_sensor.

        Returns:
            Dict with at minimum a 'heading' field (degrees 0-360).
        """
        response = await self._send_command("get_device_state", {})
        result = response.get("result", {})
        if "compass_sensor" in result:
            sensor = result["compass_sensor"]
            return sensor.get("data", sensor)
        # Fall back to dedicated command if key is absent
        response = await self._send_command("get_compass_state", {})
        return response.get("result", {})

    async def start_leveling(self) -> bool:
        """Activate the IMU leveling mode (mirrors the Seestar app's 'Please level' screen).

        Sends start_gsensor_calibration with no params, which is the command the Seestar
        app issues before displaying the bubble level.  After calling this, the firmware
        begins populating balance sensor data so get_balance_sensor() returns live values.

        Returns:
            True if the command was accepted (code == 0)
        """
        self.logger.info("Activating IMU leveling mode")
        response = await self._send_command("start_gsensor_calibration")
        self.logger.info(f"start_leveling (start_gsensor_calibration) response: {response}")
        return response.get("code") == 0

    async def get_balance_sensor(self) -> Dict[str, Any]:
        """Get current balance sensor data for leveling.

        Returns:
            Dict with x, y, z (accelerometer) and angle (total tilt in degrees).

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("get_device_state", {})
        result = response.get("result", {})
        for key in ("balance_sensor", "balance", "imu", "gsensor", "accelerometer"):
            if key in result:
                sensor = result[key]
                # Firmware wraps values in a nested 'data' key: {'code': 0, 'data': {x, y, z, angle}}
                return sensor.get("data", sensor)
        self.logger.warning("Balance sensor key not found in device state; keys: %s", list(result.keys()))
        return {"x": 0, "y": 0, "z": 0, "angle": 0}

    async def start_gsensor_calibration(self) -> bool:
        """Calibrate G-sensor (IMU accelerometer reference point).

        Sends no params — same wire format as start_annotate.

        Returns:
            True if calibration accepted (code == 0)

        Raises:
            CommandError: If command fails
        """
        self.logger.info("Starting G-sensor calibration")
        response = await self._send_command("start_gsensor_calibration")
        self.logger.info(f"start_gsensor_calibration response: {response}")
        return response.get("code") == 0

    # ========================================================================
    # Phase 6: Remote Connection Management
    # ========================================================================

    async def join_remote_session(self, session_id: str = "") -> bool:
        """Join a remote observation session.

        Allows multiple clients to control the telescope.

        Args:
            session_id: Optional session identifier

        Returns:
            True if join successful

        Raises:
            CommandError: If join fails
        """
        self.logger.info(f"Joining remote session: {session_id}")

        params = {"session_id": session_id} if session_id else {}

        response = await self._send_command("remote_join", params)

        self.logger.info(f"Join remote session response: {response}")
        return response.get("result") == 0

    async def leave_remote_session(self) -> bool:
        """Leave current remote session.

        Returns:
            True if leave successful

        Raises:
            CommandError: If leave fails
        """
        self.logger.info("Leaving remote session")

        response = await self._send_command("remote_disjoin", {})

        self.logger.info(f"Leave remote session response: {response}")
        return response.get("result") == 0

    async def disconnect_remote_client(self, client_id: str = "") -> bool:
        """Disconnect a remote client.

        Args:
            client_id: Optional client identifier to disconnect

        Returns:
            True if disconnect successful

        Raises:
            CommandError: If disconnect fails
        """
        self.logger.info(f"Disconnecting remote client: {client_id}")

        params = {"client_id": client_id} if client_id else {}

        response = await self._send_command("remote_disconnect", params)

        self.logger.info(f"Disconnect remote client response: {response}")
        return response.get("result") == 0

    # ========================================================================
    # Phase 7: Network/WiFi Management
    # ========================================================================

    async def configure_access_point(self, ssid: str, password: str, is_5g: bool = True) -> bool:
        """Configure WiFi access point settings.

        Args:
            ssid: Access point SSID
            password: Access point password
            is_5g: Use 5GHz band (True) or 2.4GHz (False)

        Returns:
            True if configuration successful

        Raises:
            CommandError: If configuration fails
        """
        self.logger.info(f"Configuring AP: {ssid}, 5G={is_5g}")

        params = {"ssid": ssid, "passwd": password, "is_5g": is_5g}

        response = await self._send_command("pi_set_ap", params)

        self.logger.info(f"Configure AP response: {response}")
        return response.get("result") == 0

    async def set_wifi_country(self, country_code: str) -> bool:
        """Set WiFi regulatory country/region.

        Args:
            country_code: Two-letter country code (e.g., "US", "GB", "JP")

        Returns:
            True if setting successful

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting WiFi country: {country_code}")

        params = {"country": country_code}

        response = await self._send_command("set_wifi_country", params)

        self.logger.info(f"Set WiFi country response: {response}")
        return response.get("result") == 0

    async def enable_wifi_client_mode(self) -> bool:
        """Enable WiFi client/station mode.

        Allows telescope to connect to existing WiFi networks.

        Returns:
            True if enabled successfully

        Raises:
            CommandError: If enable fails
        """
        self.logger.info("Enabling WiFi client mode")

        response = await self._send_command("pi_station_open", {})

        self.logger.info(f"Enable WiFi client response: {response}")
        return response.get("result") == 0

    async def disable_wifi_client_mode(self) -> bool:
        """Disable WiFi client/station mode.

        Returns to AP-only mode.

        Returns:
            True if disabled successfully

        Raises:
            CommandError: If disable fails
        """
        self.logger.info("Disabling WiFi client mode")

        response = await self._send_command("pi_station_close", {})

        self.logger.info(f"Disable WiFi client response: {response}")
        return response.get("result") == 0

    async def scan_wifi_networks(self) -> Dict[str, Any]:
        """Scan for available WiFi networks.

        Returns:
            Dict with list of available networks

        Raises:
            CommandError: If scan fails
        """
        self.logger.info("Scanning for WiFi networks")

        response = await self._send_command("pi_station_scan", {})

        return response.get("result", {})

    async def connect_to_wifi(self, ssid: str) -> bool:
        """Connect to a WiFi network.

        Network must already be saved with credentials.

        Args:
            ssid: Network SSID to connect to

        Returns:
            True if connection initiated successfully

        Raises:
            CommandError: If connection fails
        """
        self.logger.info(f"Connecting to WiFi: {ssid}")

        params = {"ssid": ssid}

        response = await self._send_command("pi_station_select", params)

        self.logger.info(f"Connect to WiFi response: {response}")
        return response.get("result") == 0

    async def save_wifi_network(self, ssid: str, password: str, security: str = "WPA2-PSK") -> bool:
        """Save WiFi network credentials.

        Args:
            ssid: Network SSID
            password: Network password
            security: Security type (WPA2-PSK, WPA-PSK, WEP, etc.)

        Returns:
            True if saved successfully

        Raises:
            CommandError: If save fails
        """
        self.logger.info(f"Saving WiFi network: {ssid}")

        params = {"ssid": ssid, "passwd": password, "security": security}

        response = await self._send_command("pi_station_set", params)

        self.logger.info(f"Save WiFi network response: {response}")
        return response.get("result") == 0

    async def list_saved_wifi_networks(self) -> Dict[str, Any]:
        """List saved WiFi networks.

        Returns:
            Dict with list of saved networks

        Raises:
            CommandError: If list fails
        """
        response = await self._send_command("pi_station_list", {})

        return response.get("result", {})

    async def remove_wifi_network(self, ssid: str) -> bool:
        """Remove saved WiFi network.

        Args:
            ssid: Network SSID to remove

        Returns:
            True if removed successfully

        Raises:
            CommandError: If remove fails
        """
        self.logger.info(f"Removing WiFi network: {ssid}")

        params = {"ssid": ssid}

        response = await self._send_command("pi_station_remove", params)

        self.logger.info(f"Remove WiFi network response: {response}")
        return response.get("result") == 0

    # ========================================================================
    # Phase 8: Raspberry Pi System Commands
    # ========================================================================

    async def get_pi_info(self) -> Dict[str, Any]:
        """Get Raspberry Pi system information.

        Returns info about CPU, memory, disk, temperature, etc.

        Returns:
            System information dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("pi_get_info", {})

        return response.get("result", {})

    async def get_pi_time(self) -> Dict[str, Any]:
        """Get Raspberry Pi system time.

        Returns:
            Time information dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("pi_get_time", {})

        return response.get("result", {})

    async def set_pi_time(self, unix_timestamp: int) -> bool:
        """Set Raspberry Pi system time.

        Args:
            unix_timestamp: Unix timestamp (seconds since epoch)

        Returns:
            True if time set successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting Pi time: {unix_timestamp}")

        params = {"time": unix_timestamp}

        response = await self._send_command("pi_set_time", params)

        self.logger.info(f"Set Pi time response: {response}")
        return response.get("result") == 0

    async def get_station_state(self) -> Dict[str, Any]:
        """Get WiFi station state.

        Returns connection status, signal strength, IP address, etc.

        Returns:
            Station state dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("pi_station_state", {})

        return response.get("result", {})

    # ========================================================================
    # Phase 9: Hardware Control (Dew Heater, Filters, Accessories)
    # ========================================================================

    async def set_dew_heater(self, enabled: bool, power_level: int = 90) -> bool:
        """Control dew heater via pi_output_set2.

        CRITICAL: Uses pi_output_set2, NOT set_setting!
        From APK analysis: BaseDeviceViewModel.java:1310

        Args:
            enabled: True to enable heater, False to disable
            power_level: Heater power level 0-100 (default: 90, same as official app)

        Returns:
            True if setting successful

        Raises:
            CommandError: If setting fails
        """
        if not 0 <= power_level <= 100:
            raise ValueError(f"Power level must be 0-100, got {power_level}")

        self.logger.info(f"Setting dew heater: {'ON' if enabled else 'OFF'} at {power_level}% power")

        # Correct implementation from APK decompilation
        params = {"heater": {"state": enabled, "value": power_level}}

        response = await self._send_command("pi_output_set2", params)

        self.logger.info(f"Set dew heater response: {response}")
        return response.get("result") == 0

    async def set_dc_output(self, output_config: Dict[str, Any]) -> bool:
        """Set DC output configuration for accessories.

        Controls external devices via DC output ports.

        Args:
            output_config: Output configuration dict
                Example: {"port": 1, "enabled": True, "voltage": 12}

        Returns:
            True if setting successful

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting DC output: {output_config}")

        response = await self._send_command("pi_output_set2", output_config)

        self.logger.info(f"Set DC output response: {response}")
        return response.get("result") == 0

    async def get_dc_output(self) -> Dict[str, Any]:
        """Get current DC output configuration.

        Returns:
            DC output state dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("pi_output_get2", {})

        return response.get("result", {})

    # ========================================================================
    # Phase 10: Demo Mode & Miscellaneous
    # ========================================================================

    async def start_demo_mode(self) -> bool:
        """Start demonstration/exhibition mode.

        Simulates telescope movements without actually moving hardware.

        Returns:
            True if demo mode started successfully

        Raises:
            CommandError: If start fails
        """
        self.logger.info("Starting demo mode")

        response = await self._send_command("start_demonstrate", {})

        self.logger.info(f"Start demo mode response: {response}")
        return response.get("result") == 0

    async def stop_demo_mode(self) -> bool:
        """Stop demonstration/exhibition mode.

        Returns:
            True if demo mode stopped successfully

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping demo mode")

        response = await self._send_command("stop_demonstrate", {})

        self.logger.info(f"Stop demo mode response: {response}")
        return response.get("result") == 0

    async def start_polar_align(self) -> bool:
        """Start polar alignment process.

        Returns:
            True if polar alignment started successfully

        Raises:
            CommandError: If start fails
        """
        self.logger.info("Starting polar alignment")

        response = await self._send_command("start_polar_align")

        self.logger.info(f"Start polar align response: {response}")
        return response.get("code") == 0

    async def stop_polar_align(self) -> bool:
        """Stop polar alignment process.

        Returns:
            True if polar alignment stopped successfully

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping polar alignment")

        response = await self._send_command("stop_polar_align")

        self.logger.info(f"Stop polar align response: {response}")
        return response.get("code") == 0

    async def pause_polar_align(self) -> bool:
        """Pause polar alignment process.

        Returns:
            True if polar alignment paused successfully

        Raises:
            CommandError: If pause fails
        """
        self.logger.info("Pausing polar alignment")

        response = await self._send_command("pause_polar_align")

        self.logger.info(f"Pause polar align response: {response}")
        return response.get("code") == 0

    async def check_client_verified(self) -> bool:
        """Check if current client is verified/authenticated.

        Returns:
            True if client is verified

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("pi_is_verified", {})

        # Result can be either a bool directly or nested in a dict
        result = response.get("result", False)
        if isinstance(result, bool):
            return result
        elif isinstance(result, dict):
            return result.get("is_verified", False)
        return False
