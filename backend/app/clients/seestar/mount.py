"""Mount control: goto, slew, park, move scope."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .types import SeestarState, MountMode, CommandError


class SeestarMountMixin:
    """Mixin providing telescope mount control commands."""

    async def scope_goto(self, ra_hours: float, dec_degrees: float) -> bool:
        """Low-level mount goto command without starting viewing mode.

        This uses the scope_goto command which moves the mount without
        activating imaging or viewing mode. Useful for simple slewing.

        Args:
            ra_hours: Right ascension in decimal hours (0-24)
            dec_degrees: Declination in decimal degrees (-90 to 90)

        Returns:
            True if goto initiated successfully

        Raises:
            CommandError: If goto command fails
        """
        self.logger.info(f"Scope goto: RA={ra_hours}h, Dec={dec_degrees}°")

        params = [ra_hours, dec_degrees]
        self._update_status(state=SeestarState.SLEWING)
        response = await self._send_command("scope_goto", params)

        self.logger.debug("scope_goto response: %s", response)

        result = response.get("result", -1)
        code = response.get("code", -1)

        if result == 0 and code == 0:
            self.logger.info("scope_goto accepted — telescope slewing to RA=%sh Dec=%s°", ra_hours, dec_degrees)
            return True
        else:
            error_msg = f"Goto failed with result={result}, code={code}"
            self.logger.error(error_msg)
            return False

    async def initialize_equatorial_mode(self) -> bool:
        """Initialize equatorial coordinate system.

        Performs mount homing sequence to establish reference point for
        equatorial tracking. Required before using iscope_start_view with
        RA/Dec coordinates.

        Returns:
            True if initialization successful

        Raises:
            CommandError: If initialization fails
        """
        import asyncio

        self.logger.info("Initializing equatorial mode (mount go-home sequence)...")

        try:
            # Execute mount_go_home
            response = await self._send_command("mount_go_home", {})

            if response.get("code") == 0:
                self.logger.info("Go home accepted — waiting ~45s for homing to complete...")

                # Wait for homing to complete (typically 30-60 seconds)
                await asyncio.sleep(45)

                # Mark as initialized
                self._update_status(mount_mode=MountMode.EQUATORIAL, equatorial_initialized=True)
                self.logger.info("Equatorial mode initialized successfully")
                return True
            else:
                error_msg = f"Go home failed: code={response.get('code')}"
                self.logger.error(error_msg)
                raise CommandError(error_msg)

        except Exception as e:
            self.logger.error(f"Equatorial initialization failed: {e}")
            raise

    async def set_mount_mode(self, mode: MountMode) -> bool:
        """Set mount coordinate mode.

        Args:
            mode: Target mount mode (ALTAZ or EQUATORIAL)

        Returns:
            True if mode set successfully

        Raises:
            CommandError: If mode change fails or equatorial mode not initialized
        """
        self.logger.info(f"Setting mount mode to {mode.value}")

        if mode == MountMode.EQUATORIAL:
            if not self.status.equatorial_initialized:
                self.logger.warning("Equatorial mode requested but not initialized")
                raise CommandError(
                    "Equatorial mode requires initialization. " "Call initialize_equatorial_mode() first."
                )

        self._update_status(mount_mode=mode)
        return True

    async def goto_target(
        self, ra_hours: float, dec_degrees: float, target_name: str = "Target", use_lp_filter: bool = False
    ) -> bool:
        """Slew telescope to target and start viewing.

        Automatically uses the appropriate slewing method based on current mount mode:
        - ALTAZ mode: Converts RA/Dec to Alt/Az and uses move_to_horizon
        - EQUATORIAL mode: Uses iscope_start_view with RA/Dec directly

        Args:
            ra_hours: Right ascension in decimal hours (0-24)
            dec_degrees: Declination in decimal degrees (-90 to 90)
            target_name: Name of target for display
            use_lp_filter: Whether to use light pollution filter

        Returns:
            True if goto initiated successfully

        Raises:
            CommandError: If goto command fails
        """
        import asyncio

        self.logger.info(
            f"Goto target: {target_name} at RA={ra_hours}h, Dec={dec_degrees}° (mode={self.status.mount_mode.value})"
        )

        # CRITICAL: Cancel any active operations before movement
        # Check if telescope is currently imaging/viewing
        try:
            view_state_response = await self._send_command("get_view_state", {})
            view = view_state_response.get("result", {}).get("View", {})
            view_status = view.get("state")
            view_stage = view.get("stage")

            self.logger.debug("View state before goto: status=%s stage=%s", view_status, view_stage)

            # If actively imaging or viewing, cancel it
            if view_status == "working" or view_stage in ["ContinuousExposure", "Stacking"]:
                self.logger.warning(f"Canceling active {view_stage} before goto")
                try:
                    await self._send_command("iscope_cancel_view", {})
                    await asyncio.sleep(1)  # Give it time to cancel
                    self.logger.info("Active operation canceled")
                except Exception as cancel_error:
                    self.logger.warning(f"Cancel view failed (may be OK): {cancel_error}")
        except Exception as e:
            self.logger.warning(f"Could not check view state: {e}")

        # CRITICAL: Ensure mount is in correct mode before movement
        # Check actual device state, not just our internal state
        device_state = await self.get_device_state()
        mount = device_state.get("mount", {})
        actual_equ_mode = mount.get("equ_mode", False)

        self.logger.debug("Device mount state: equ_mode=%s", actual_equ_mode)

        # If we want alt/az mode but device is in equatorial mode, fix it
        if self.status.mount_mode == MountMode.ALTAZ and actual_equ_mode is True:
            self.logger.warning("Device in equatorial mode but client wants alt/az - clearing polar alignment")
            try:
                await self.clear_polar_alignment()
                self.logger.info("Successfully switched to alt/az mode")
            except Exception as e:
                self.logger.error(f"Failed to clear polar alignment: {e}")
                raise CommandError(f"Failed to switch mount to alt/az mode: {e}")

        # If we want equatorial mode but mount not initialized, warn
        elif self.status.mount_mode == MountMode.EQUATORIAL and not self.status.equatorial_initialized:
            self.logger.warning("Equatorial mode requested but not initialized")
            raise CommandError(
                "Equatorial mode requires initialization. " "Call initialize_equatorial_mode() first or use ALTAZ mode."
            )

        # Use appropriate method based on mount mode
        if self.status.mount_mode == MountMode.ALTAZ:
            self.logger.debug("Converting RA/Dec to Alt/Az for alt/az mount")

            try:
                from datetime import datetime

                import astropy.units as u
                from astropy.coordinates import AltAz, EarthLocation, SkyCoord
                from astropy.time import Time

                # Use cached observer location, or fetch from DB (then cache)
                if self._observer_location is None:
                    from app.core.config import get_settings as _get_cfg

                    _cfg = _get_cfg()
                    lat, lon, elevation = _cfg.default_lat, _cfg.default_lon, 0
                    try:
                        from app.database import SessionLocal
                        from app.models.settings_models import ObservingLocation as _ObsLoc

                        _db = SessionLocal()
                        _loc = _db.query(_ObsLoc).filter(_ObsLoc.is_default == True, _ObsLoc.is_active == True).first()
                        _db.close()
                        if _loc:
                            lat, lon, elevation = _loc.latitude, _loc.longitude, (_loc.elevation or 0)
                    except Exception:
                        pass
                    self._observer_location = (lat, lon, elevation)
                    self.logger.debug("Observer location loaded: lat=%.4f lon=%.4f elev=%.0fm", lat, lon, elevation)

                lat, lon, elevation = self._observer_location

                # Convert RA/Dec to Alt/Az
                coord = SkyCoord(ra=ra_hours * u.hourangle, dec=dec_degrees * u.deg, frame="icrs")
                location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
                obs_time = Time(datetime.utcnow())
                altaz_frame = AltAz(obstime=obs_time, location=location)
                altaz_coord = coord.transform_to(altaz_frame)

                azimuth = altaz_coord.az.deg
                altitude = altaz_coord.alt.deg

                self.logger.info("Coordinate conversion: Az=%.2f° Alt=%.2f° for %s", azimuth, altitude, target_name)

                # Check if target is above horizon
                if altitude < 10:
                    self.logger.warning(f"Target {target_name} is low (alt={altitude:.1f}°) - may not be visible")

                self._update_status(state=SeestarState.SLEWING, current_target=target_name)
                success = await self.move_to_horizon(azimuth=azimuth, altitude=altitude)

                if success:
                    self.logger.info("move_to_horizon accepted — slewing to %s", target_name)
                    return True
                else:
                    self.logger.error("move_to_horizon failed for %s", target_name)
                    return False

            except Exception as e:
                self.logger.error(f"Coordinate conversion failed: {e}")
                raise CommandError(f"Failed to convert coordinates: {e}")

        else:
            # Use iscope_start_view directly (for initialized equatorial mode)
            # Same as official Seestar app - see StartGoToCmd.java line 99
            params = {
                "mode": "star",
                "target_ra_dec": [ra_hours, dec_degrees],
                "target_name": target_name,
                "lp_filter": use_lp_filter,
            }
            self.logger.debug("Sending iscope_start_view: %s", params)
            self._update_status(state=SeestarState.SLEWING, current_target=target_name)
            response = await self._send_command("iscope_start_view", params)

            self.logger.debug("iscope_start_view response: %s", response)

            # Check for error codes
            result = response.get("result", -1)
            code = response.get("code", -1)

            if result == 0 and code == 0:
                self.logger.info("iscope_start_view accepted — slewing to %s", target_name)
                return True
            else:
                error_msg = f"Goto failed with result={result}, code={code}"
                self.logger.error(f"[SLEW DIAGNOSTIC] {error_msg}")
                # Common error codes from Seestar:
                # 203 = telescope is moving
                # 207 = fail to operate (mount not ready - needs homing/init)
                # 259 = stack is already running
                if code == 203:
                    raise CommandError("Telescope is already moving - stop current operation first")
                elif code == 207:
                    raise CommandError(
                        "Mount not ready - needs initialization (try use_altaz=True or run mount_go_home)"
                    )
                elif code == 259:
                    raise CommandError("Imaging is active - stop imaging before slewing")
                else:
                    raise CommandError(error_msg)
                return False

    async def start_preview(self, mode: str = "scenery", brightness: float = 50.0) -> bool:
        """Start preview/viewing mode without coordinates.

        This enables RTMP streaming for various viewing modes without requiring
        celestial coordinates. Useful for daytime viewing, testing, landscape,
        moon, planet, or solar observation.

        Args:
            mode: Viewing mode - "scenery" (landscape), "moon", "planet", "sun", or "star"
            brightness: Auto-exposure brightness target (0-100), default 50.0

        Returns:
            True if preview started successfully

        Raises:
            CommandError: If command fails

        Note:
            Based on decompiled Java code:
            - StartVideoAction.java uses mode="scenery" for landscape
            - StartMoonAction.java uses mode="moon"
            - StartPlanetAction.java uses mode="planet"
            - StartSunAction.java uses mode="sun"
            RTMP stream will be available on ports 4554 (telephoto) and 4555 (wide angle)
        """
        self.logger.info(f"Starting preview mode={mode}, brightness={brightness}")

        # Start view with specified mode (no target required for these modes)
        params = {"mode": mode}

        mode_labels = {
            "scenery": "Landscape View",
            "moon": "Moon",
            "planet": "Planet",
            "sun": "Sun",
            "star": "Star Preview",
        }
        target_label = mode_labels.get(mode, f"{mode.title()} View")

        self._update_status(state=SeestarState.TRACKING, current_target=target_label)

        response = await self._send_command("iscope_start_view", params)

        if response.get("result") == 0:
            # Start RTMP stream for live video
            # Based on StartAviRtmpCmd.java
            try:
                rtmp_params = {"name": f"{mode}_preview"}
                rtmp_response = await self._send_command("start_avi_rtmp", rtmp_params)
                if rtmp_response.get("code") == 0:
                    self.logger.info("RTMP stream started successfully")
                else:
                    self.logger.warning(f"RTMP stream start returned code {rtmp_response.get('code')}")
            except Exception as e:
                self.logger.warning(f"Failed to start RTMP stream: {e}")
                # Don't fail the whole operation if RTMP fails

            # Optionally set auto-exposure brightness
            # Based on SetSettingAEBrightCmd from Java code (though it returns error 109)
            try:
                await self._send_command(
                    "set_setting", {"exp_ms": None, "target_brightness": brightness, "is_auto": True}
                )
            except Exception as e:
                self.logger.warning(f"Failed to set AE brightness: {e}")
                # Don't fail the whole operation if brightness setting fails

        self.logger.info(f"Start preview response: {response}")
        return response.get("result") == 0

    async def start_imaging(self, restart: bool = True) -> bool:
        """Start stacking/imaging.

        Args:
            restart: Whether to restart stacking from scratch

        Returns:
            True if imaging started successfully

        Raises:
            CommandError: If start imaging fails
        """
        self.logger.info(f"Starting imaging (restart={restart})")

        params = {"restart": restart}

        self._update_status(state=SeestarState.IMAGING)

        response = await self._send_command("iscope_start_stack", params)

        self.logger.info(f"Start imaging response: {response}")
        return response.get("result") == 0

    async def stop_imaging(self) -> bool:
        """Stop current imaging/stacking.

        Returns:
            True if stop successful

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping imaging")

        params = {"stage": "Stack"}

        self._update_status(state=SeestarState.TRACKING)

        response = await self._send_command("iscope_stop_view", params)

        self.logger.info(f"Stop imaging response: {response}")
        return response.get("result") == 0

    async def start_record_avi(self, filename: Optional[str] = None) -> bool:
        """Start AVI video recording.

        Args:
            filename: Optional filename for recording (without extension)

        Returns:
            True if recording started successfully

        Raises:
            CommandError: If recording fails to start
        """
        params = {}
        if filename:
            params["name"] = filename

        response = await self._send_command("start_record_avi", params)

        if response.get("code") == 0:
            self.logger.info(f"Video recording started: {filename or 'auto'}")
            return True
        else:
            error_msg = f"Failed to start video recording: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def stop_record_avi(self) -> bool:
        """Stop AVI video recording.

        Returns:
            True if recording stopped successfully

        Raises:
            CommandError: If recording fails to stop
        """
        response = await self._send_command("stop_record_avi", {})

        if response.get("code") == 0:
            self.logger.info("Video recording stopped")
            return True
        else:
            error_msg = f"Failed to stop video recording: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def start_track_object(self, object_type: str, object_id: str) -> bool:
        """Start tracking a satellite, comet, or asteroid.

        Args:
            object_type: Type of object - "satellite", "comet", or "asteroid"
            object_id: Identifier of the object to track

        Returns:
            True if tracking started successfully

        Raises:
            CommandError: If tracking fails to start
        """
        params = {"type": object_type, "id": object_id}

        response = await self._send_command("start_track_object", params)

        if response.get("code") == 0:
            self.logger.info(f"Object tracking started: {object_type} - {object_id}")
            return True
        else:
            error_msg = f"Failed to start tracking {object_type} '{object_id}': {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def stop_track_object(self) -> bool:
        """Stop tracking current object.

        Returns:
            True if tracking stopped successfully

        Raises:
            CommandError: If tracking fails to stop
        """
        response = await self._send_command("stop_track_object", {})

        if response.get("code") == 0:
            self.logger.info("Object tracking stopped")
            return True
        else:
            error_msg = f"Failed to stop tracking object: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def start_annotate(self) -> bool:
        """Enable annotations on preview.

        Returns:
            True if annotations started successfully

        Raises:
            CommandError: If annotation start fails
        """
        response = await self._send_command("start_annotate")

        if response.get("code") == 0:
            self.logger.info("Annotations started")
            return True
        else:
            error_msg = f"Failed to start annotations: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def stop_annotate(self) -> bool:
        """Disable annotations on preview.

        Returns:
            True if annotations stopped successfully

        Raises:
            CommandError: If annotation stop fails
        """
        response = await self._send_command("stop_annotate", {})

        if response.get("code") == 0:
            self.logger.info("Annotations stopped")
            return True
        else:
            error_msg = f"Failed to stop annotations: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def start_scan_planet(self) -> bool:
        """Start scanning for visible planets.

        Returns:
            True if planet scan started successfully

        Raises:
            CommandError: If planet scan fails to start
        """
        response = await self._send_command("iscope_start_scan_planet", {})

        if response.get("code") == 0:
            self.logger.info("Planet scan started")
            return True
        else:
            error_msg = f"Failed to start planet scan: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def start_planet_stack(self, planet_name: str, exposure: int, gain: int) -> bool:
        """Start planetary imaging stack.

        Args:
            planet_name: Name of the planet to image
            exposure: Exposure time in milliseconds
            gain: Gain value (0-300)

        Returns:
            True if planetary stack started successfully

        Raises:
            CommandError: If planetary stack fails to start
        """
        params = {"target": planet_name, "exposure": exposure, "gain": gain}
        response = await self._send_command("iscope_start_planet_stack", params)

        if response.get("code") == 0:
            self.logger.info(f"Planet stack started: {planet_name} (exp={exposure}ms, gain={gain})")
            return True
        else:
            error_msg = f"Failed to start planet stack: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def stop_planet_stack(self) -> bool:
        """Stop planetary imaging stack.

        Returns:
            True if planetary stack stopped successfully

        Raises:
            CommandError: If planetary stack fails to stop
        """
        response = await self._send_command("iscope_stop_planet_stack", {})

        if response.get("code") == 0:
            self.logger.info("Planet stack stopped")
            return True
        else:
            error_msg = f"Failed to stop planet stack: {response}"
            self.logger.error(error_msg)
            raise CommandError(error_msg)

    async def stop_slew(self) -> bool:
        """Stop current slew/goto operation.

        Returns:
            True if stop successful

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping slew")

        params = {"stage": "AutoGoto"}

        response = await self._send_command("iscope_stop_view", params)

        self.logger.info(f"Stop slew response: {response}")
        return response.get("result") == 0

    async def auto_focus(self) -> bool:
        """Perform automatic focusing.

        Returns:
            True if focus initiated successfully

        Raises:
            CommandError: If focus command fails
        """
        self.logger.info("Starting auto focus")

        self._update_status(state=SeestarState.FOCUSING)

        response = await self._send_command("start_auto_focuse")

        self.logger.info(f"Auto focus response: {response}")
        return response.get("result") == 0

    async def park(self, equ_mode: bool = True) -> bool:
        """Park telescope at home position.

        Uses the scope_park command which sets the telescope to its parked
        position and switches tracking mode.

        Args:
            equ_mode: If True, park in equatorial mode. If False, park in alt/az mode.
                     When False, automatically calls stop_polar_align first.

        Returns:
            True if park initiated successfully

        Raises:
            CommandError: If park command fails
        """
        mode_str = "equatorial" if equ_mode else "alt/az"
        self.logger.info(f"Parking telescope in {mode_str} mode")

        self._update_status(state=SeestarState.PARKING)

        # Park telescope with specified mode
        response = await self._send_command("scope_park", {"equ_mode": equ_mode})

        self.logger.info(f"Park response: {response}")
        return response.get("result") == 0

    async def is_equatorial_mode(self) -> bool:
        """Check if telescope is in equatorial tracking mode.

        Returns:
            True if in equatorial mode, False if in alt/az mode

        Raises:
            CommandError: If unable to determine mode
        """
        try:
            device_state = await self.get_device_state()
            mount = device_state.get("mount", {})

            # Check if mount has tracking mode indicator
            # The exact field name may vary - checking common possibilities
            is_equ = mount.get("is_equ", mount.get("equ_mode", mount.get("tracking_mode") == "equatorial"))

            self.logger.debug(f"Mount mode check: is_equatorial={is_equ}, mount state={mount}")
            return bool(is_equ)
        except Exception as e:
            self.logger.warning(f"Could not determine mount mode, assuming alt/az: {e}")
            # Default to alt/az mode if we can't determine
            return False

    async def move_scope(
        self,
        action: str,
        ra: Optional[float] = None,
        dec: Optional[float] = None,
        speed: Optional[float] = None,
        dur_sec: Optional[int] = None,
        percent: Optional[int] = None,
    ) -> bool:
        """Direct mount movement control.

        Automatically detects mount mode (alt/az vs equatorial) and uses
        appropriate coordinate system for directional movements.

        Args:
            action: Movement action - "slew", "stop", "abort", "up", "down", "left", "right"
            ra: RA in hours (for slew action in equatorial mode)
            dec: Dec in degrees (for slew action in equatorial mode)
            speed: Movement speed multiplier for directional moves (default: 1.0)
                   Examples: 0.5 = half speed (0.25°), 2.0 = double speed (1.0°)

        Returns:
            True if command successful

        Raises:
            CommandError: If move command fails
            ValueError: If invalid action or missing coordinates for slew
        """
        valid_actions = ["slew", "stop", "abort", "up", "down", "left", "right"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {valid_actions}")

        # Handle stop/abort actions directly
        # Firmware expects a JSON array ["none"], not a string or dict (code 105 otherwise)
        if action in ["stop", "abort"]:
            self.logger.info(f"Scope move: {action}")
            response = await self._send_command("scope_move", ["none"])
            self.logger.info(f"Scope move response: {response}")
            return response.get("result") == 0

        # Handle directional movement using scope_speed_move command
        if action in ["up", "down", "left", "right"]:
            # Map direction to angle (degrees)
            # Based on empirical testing with seestar_alp reference:
            # 0° = increase azimuth (turn right/clockwise)
            # 90° = increase altitude (tilt up)
            # 180° = decrease azimuth (turn left/counter-clockwise)
            # 270° = decrease altitude (tilt down)
            direction_angles = {
                "up": 90,  # Increase altitude
                "down": 270,  # Decrease altitude
                "right": 0,  # Increase azimuth
                "left": 180,  # Decrease azimuth
            }
            angle = direction_angles[action]

            # percent maps joystick distance to 1-100; level is always 1
            # percent and dur_sec can be provided directly by caller, or derived from speed multiplier
            if percent is None:
                speed_multiplier = speed if speed is not None else 1.0
                percent = int(min(100, max(1, speed_multiplier * 100)))
            else:
                percent = int(min(100, max(1, percent)))
            effective_dur = dur_sec if dur_sec is not None else 3

            self.logger.info(f"Directional move {action}: angle={angle}°, percent={percent}, dur_sec={effective_dur}")

            params = {"angle": angle, "percent": percent, "level": 1, "dur_sec": effective_dur}

            response = await self._send_command("scope_speed_move", params)
            return response.get("result") == 0

        # Handle explicit slew action with coordinates
        else:
            if ra is None or dec is None:
                raise ValueError("RA and Dec required for slew action")
            params = {"action": action, "ra": ra, "dec": dec}
            self.logger.info(f"Scope move: {action} with params {params}")
            response = await self._send_command("scope_move", params)

        self.logger.info(f"Scope move response: {response}")
        return response.get("result") == 0

    async def get_device_state(self, keys: Optional[list] = None) -> Dict[str, Any]:
        """Get current device state.

        Args:
            keys: Optional list of specific keys to query

        Returns:
            Device state dict

        Raises:
            CommandError: If query fails
        """
        params = {"keys": keys} if keys else {}

        response = await self._send_command("get_device_state", params)

        result = response.get("result", {})

        # Update internal status from result
        if "device" in result:
            device = result["device"]
            if "firmware_ver_string" in device:
                self._update_status(firmware_version=device["firmware_ver_string"])

        # Check mount state to detect parked (arm closed)
        if "mount" in result:
            mount = result["mount"]
            # mount.close=True means arm is closed/parked
            if mount.get("close") is True:
                self._update_status(state=SeestarState.PARKED)

        return result

    async def set_exposure(self, stack_exposure_ms: int = 10000, continuous_exposure_ms: int = 500) -> bool:
        """Set exposure times.

        Args:
            stack_exposure_ms: Stacking exposure in milliseconds (default: 10000 = 10s)
            continuous_exposure_ms: Continuous/preview exposure in ms (default: 500)

        Returns:
            True if setting successful

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting exposure: stack={stack_exposure_ms}ms, continuous={continuous_exposure_ms}ms")

        params = {"exp_ms": {"stack_l": stack_exposure_ms, "continuous": continuous_exposure_ms}}

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Set exposure response: {response}")
        return response.get("result") == 0

    async def configure_dither(self, enabled: bool = True, pixels: int = 50, interval: int = 10) -> bool:
        """Configure dithering settings.

        Args:
            enabled: Whether dithering is enabled
            pixels: Dither distance in pixels
            interval: Number of frames between dither

        Returns:
            True if setting successful

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Configuring dither: enabled={enabled}, pixels={pixels}, interval={interval}")

        params = {"stack_dither": {"enable": enabled, "pix": pixels, "interval": interval}}

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Configure dither response: {response}")
        return response.get("result") == 0
