"""Real-time observation state and automated sequences."""

from __future__ import annotations

from typing import Any, Dict

from .types import SeestarState


class SeestarObservationMixin:
    """Mixin providing real-time observation and sequencing commands."""

    # ========================================================================
    # Phase 1: Real-Time Observation & Tracking
    # ========================================================================

    async def get_current_coordinates(self) -> Dict[str, float]:
        """Get current telescope RA/Dec coordinates.

        Returns:
            Dict with 'ra' (hours) and 'dec' (degrees)

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("scope_get_equ_coord", {})

        result = response.get("result", {})

        # Update internal status
        if "ra" in result and "dec" in result:
            self._update_status(current_ra_hours=result["ra"], current_dec_degrees=result["dec"])

        return {"ra": result.get("ra", 0.0), "dec": result.get("dec", 0.0)}

    async def get_app_state(self) -> Dict[str, Any]:
        """Get current application/operation state.

        Returns detailed state including:
        - stage: Current operation stage (AutoGoto, AutoFocus, Stack, etc.)
        - state: Current state within stage
        - progress: Operation progress information
        - frame_count: Number of frames captured
        - etc.

        Returns:
            Application state dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("iscope_get_app_state", {})

        result = response.get("result", {})

        # Update internal status based on stage
        stage = result.get("stage")
        if stage == "AutoGoto":
            self._update_status(state=SeestarState.SLEWING)
        elif stage == "AutoFocus":
            self._update_status(state=SeestarState.FOCUSING)
        elif stage == "Stack":
            self._update_status(state=SeestarState.IMAGING)
        elif stage == "ScopeHome":
            self._update_status(state=SeestarState.PARKING)
        elif stage == "Idle" or stage is None:
            # stage=None or "Idle" means telescope is idle/ready
            # Will be overridden to PARKED by get_device_state if mount.close=True
            self._update_status(state=SeestarState.TRACKING)

        return result

    async def check_stacking_complete(self) -> bool:
        """Check if stacking is complete.

        Returns:
            True if stacking has finished

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("is_stacked", {})

        return response.get("result", {}).get("is_stacked", False)

    async def get_plate_solve_result(self) -> Dict[str, Any]:
        """Get plate solving result.

        Returns plate solve information including:
        - Actual solved RA/Dec
        - Field rotation
        - Solve status
        - Error information if solve failed

        Returns:
            Plate solve result dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("get_solve_result", {})

        return response.get("result", {})

    async def get_field_annotations(self) -> Dict[str, Any]:
        """Get annotations for objects in current field of view.

        Returns information about identified objects including:
        - Catalog objects (stars, galaxies, nebulae)
        - Object coordinates
        - Object names and identifiers

        Returns:
            Annotation results dict

        Raises:
            CommandError: If query fails
        """
        response = await self._send_command("get_annotate_result", {})

        return response.get("result", {})

    # ========================================================================
    # Phase 2: View Plans & Automated Sequences
    # ========================================================================

    async def start_view_plan(self, plan_config: Dict[str, Any]) -> bool:
        """Execute an automated observation plan.

        Starts a multi-target imaging sequence based on plan configuration.

        Args:
            plan_config: Plan configuration dict with targets, exposures, etc.

        Returns:
            True if plan started successfully

        Raises:
            CommandError: If plan start fails
        """
        self.logger.info(f"Starting view plan: {plan_config}")

        response = await self._send_command("start_view_plan", plan_config)

        self.logger.info(f"Start view plan response: {response}")
        return response.get("result") == 0

    async def stop_view_plan(self) -> bool:
        """Stop/cancel running observation plan.

        Returns:
            True if plan stopped successfully

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping view plan")

        response = await self._send_command("stop_view_plan", {})

        self.logger.info(f"Stop view plan response: {response}")
        return response.get("result") == 0

    async def get_view_plan_state(self) -> Dict[str, Any]:
        """Get current view plan execution state.

        Returns plan progress information including:
        - Current target
        - Targets completed
        - Overall progress
        - Estimated time remaining

        Returns:
            View plan state dict

        Raises:
            CommandError: If query fails
        """
        # Fixed: Use correct command name from MainCameraConstants.java
        # Was using "get_view_plan_state" (doesn't exist)
        # Correct command is "get_view_state" (line 136 in MainCameraConstants.java)
        response = await self._send_command("get_view_state", {})

        return response.get("result", {})

    # ========================================================================
    # Phase 3: Planetary Observation Mode
    # ========================================================================

    async def start_planet_scan(self, planet_name: str, exposure_ms: int = 30, gain: float = 100.0) -> bool:
        """Start planetary imaging mode.

        Uses specialized stacking optimized for planetary imaging.

        Args:
            planet_name: Name of planet to image
            exposure_ms: Exposure time in milliseconds (shorter for planets)
            gain: Camera gain (higher for planets)

        Returns:
            True if planetary mode started successfully

        Raises:
            CommandError: If start fails
        """
        self.logger.info(f"Starting planet scan: {planet_name}, exp={exposure_ms}ms, gain={gain}")

        params = {
            "planet": planet_name,
            "exposure_ms": exposure_ms,
            "gain": gain,
        }

        response = await self._send_command("start_scan_planet", params)

        self.logger.info(f"Start planet scan response: {response}")
        return response.get("result") == 0

    async def configure_planetary_imaging(
        self,
        frame_count: int = 1000,
        save_frames: bool = True,
        denoise: bool = True,
    ) -> bool:
        """Configure settings for planetary imaging.

        Args:
            frame_count: Number of frames to capture
            save_frames: Save individual frames for stacking
            denoise: Apply denoising to planetary images

        Returns:
            True if settings applied successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Configuring planetary imaging: frames={frame_count}, save={save_frames}, denoise={denoise}")

        params = {
            "stack": {
                "capt_type": "planet",
                "capt_num": frame_count,
                "save_discrete_frame": save_frames,
                "wide_denoise": denoise,
            }
        }

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Configure planetary imaging response: {response}")
        return response.get("result") == 0

    # ========================================================================
    # Phase 4: Enhanced Control
    # ========================================================================

    async def slew_to_coordinates(self, ra_hours: float, dec_degrees: float) -> bool:
        """Slew telescope to specific RA/Dec coordinates.

        Direct mount movement command (lower level than goto_target).

        Args:
            ra_hours: Right ascension in hours
            dec_degrees: Declination in degrees

        Returns:
            True if slew initiated successfully

        Raises:
            CommandError: If slew command fails
        """
        self.logger.info(f"Slewing to RA={ra_hours}h, Dec={dec_degrees}°")

        params = {"action": "slew", "ra": ra_hours, "dec": dec_degrees}

        self._update_status(state=SeestarState.SLEWING)

        response = await self._send_command("scope_move", params)

        self.logger.info(f"Slew response: {response}")
        return response.get("result") == 0

    async def stop_telescope_movement(self) -> bool:
        """Stop any telescope movement immediately.

        Emergency stop for mount movement.

        Returns:
            True if stop successful

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping telescope movement")

        # Firmware expects a JSON array ["none"], not a string or dict (code 105 otherwise)
        response = await self._send_command("scope_move", ["none"])

        self.logger.info(f"Stop movement response: {response}")
        return response.get("result") == 0

    async def move_focuser_to_position(self, position: int) -> bool:
        """Move focuser to specific position.

        Args:
            position: Focuser position (0 to max_step, typically 0-2600)

        Returns:
            True if move initiated successfully

        Raises:
            CommandError: If move fails
        """
        self.logger.info(f"Moving focuser to position {position}")

        params = {"step": position}

        self._update_status(state=SeestarState.FOCUSING)

        response = await self._send_command("move_focuser", params)

        self.logger.info(f"Move focuser response: {response}")
        return response.get("result") == 0

    async def move_focuser_relative(self, offset: int) -> bool:
        """Move focuser by relative offset.

        Fetches current position then sends an absolute target step, which is
        the format the firmware accepts (upstream seestar_alp pattern).

        Args:
            offset: Steps to move (positive = out, negative = in)

        Returns:
            True if move initiated successfully

        Raises:
            CommandError: If move fails
        """
        self.logger.info(f"Moving focuser by relative offset {offset}")

        # Firmware accepts absolute "step" value only; fetch current position first
        pos_response = await self._send_command("get_focuser_position", {})
        current_pos = pos_response.get("result", 0)
        if isinstance(current_pos, dict):
            current_pos = current_pos.get("step", 0)

        target = int(current_pos) + offset
        self.logger.info(f"Focuser: current={current_pos}, target={target}")

        params = {"step": target, "ret_step": True}

        self._update_status(state=SeestarState.FOCUSING)

        response = await self._send_command("move_focuser", params)

        self.logger.info(f"Move focuser response: {response}")
        return response.get("result") == 0

    async def stop_autofocus(self) -> bool:
        """Stop autofocus operation.

        Returns:
            True if stop successful

        Raises:
            CommandError: If stop fails
        """
        self.logger.info("Stopping autofocus")

        response = await self._send_command("stop_auto_focuse", {})

        self.logger.info(f"Stop autofocus response: {response}")
        return response.get("result") == 0

    async def configure_advanced_stacking(
        self,
        dark_background_extraction: bool = False,
        star_correction: bool = True,
        airplane_removal: bool = False,
        drizzle_2x: bool = False,
    ) -> bool:
        """Configure advanced stacking options.

        Args:
            dark_background_extraction: Enable DBE for light pollution removal
            star_correction: Enable star shape correction
            airplane_removal: Remove satellite/airplane trails
            drizzle_2x: Enable 2x drizzle upsampling

        Returns:
            True if settings applied successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(
            f"Configuring advanced stacking: dbe={dark_background_extraction}, "
            f"star_corr={star_correction}, airplane={airplane_removal}, drizzle={drizzle_2x}"
        )

        params = {
            "stack": {
                "dbe": dark_background_extraction,
                "star_correction": star_correction,
                "airplane_line_removal": airplane_removal,
                "drizzle2x": drizzle_2x,
            }
        }

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Configure advanced stacking response: {response}")
        return response.get("result") == 0

    async def set_manual_exposure(self, exposure_ms: float, gain: float) -> bool:
        """Set manual exposure and gain.

        Args:
            exposure_ms: Exposure time in milliseconds
            gain: Camera gain

        Returns:
            True if settings applied successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting manual exposure: {exposure_ms}ms, gain={gain}")

        params = {
            "manual_exp": True,
            "isp_exp_ms": exposure_ms,
            "isp_gain": gain,
        }

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Set manual exposure response: {response}")
        return response.get("result") == 0

    async def set_auto_exposure(self, brightness_target: float = 50.0) -> bool:
        """Enable auto exposure with brightness target.

        Args:
            brightness_target: Target brightness percentage (0-100)

        Returns:
            True if settings applied successfully

        Raises:
            CommandError: If setting fails
        """
        self.logger.info(f"Setting auto exposure: brightness={brightness_target}%")

        params = {
            "manual_exp": False,
            "ae_bri_percent": brightness_target,
        }

        response = await self._send_command("set_setting", params)

        self.logger.info(f"Set auto exposure response: {response}")
        return response.get("result") == 0
