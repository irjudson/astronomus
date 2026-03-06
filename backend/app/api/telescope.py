"""Telescope control API routes."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clients.seestar_client import SeestarClient
from app.database import get_db
from app.models import ScheduledTarget
from app.models.settings_models import SeestarDevice

logger = logging.getLogger(__name__)

router = APIRouter()

# Global telescope client singleton
seestar_client: Optional[SeestarClient] = None


def get_current_telescope() -> SeestarClient:
    """
    Dependency function to get the current telescope client.

    Returns:
        The current SeestarClient instance if connected, None otherwise

    Raises:
        HTTPException: If no telescope is connected
    """
    if seestar_client is None:
        raise HTTPException(status_code=503, detail="Telescope not connected")
    return seestar_client


# Request/Response models for telescope endpoints
class TelescopeConnectRequest(BaseModel):
    host: Optional[str] = None  # Optional: can specify host directly
    port: Optional[int] = None  # Optional: can specify port directly
    device_id: Optional[int] = None  # Optional: or specify device_id to load from database


class ExecutePlanRequest(BaseModel):
    scheduled_targets: List[ScheduledTarget]
    park_when_done: bool = True  # Default to True (park telescope when complete)
    saved_plan_id: Optional[int] = None  # Optional: link execution to saved plan


class AnnotationRequest(BaseModel):
    enabled: bool


class StartTrackingRequest(BaseModel):
    object_type: str  # "satellite", "comet", or "asteroid"
    object_id: str


@router.post("/telescope/connect")
async def connect_telescope(request: TelescopeConnectRequest, db: Session = Depends(get_db)):
    """
    Connect to Seestar telescope.

    Can connect either by:
    1. Specifying device_id (loads configuration from database)
    2. Specifying host and port directly

    Args:
        request: Connection details (device_id OR host/port)
        db: Database session

    Returns:
        Connection status and telescope info
    """
    global seestar_client

    try:
        # Determine which device to connect to
        if request.device_id is not None:
            # Load device from database
            device = db.query(SeestarDevice).filter(SeestarDevice.id == request.device_id).first()
            if not device:
                raise HTTPException(status_code=404, detail=f"Device {request.device_id} not found")

            if not device.is_control_enabled:
                raise HTTPException(
                    status_code=400, detail=f"Device '{device.name}' control is not enabled. Enable in settings first."
                )

            host = device.control_host
            port = device.control_port

        elif request.host is not None:
            host = request.host
            port = request.port or 4700

        else:
            raise HTTPException(status_code=400, detail="Must provide either device_id or host parameter")

        # Create client and connect
        seestar_client = SeestarClient()
        success = await seestar_client.connect(host, port)

        if not success:
            seestar_client = None  # Reset on failure
            raise HTTPException(status_code=500, detail="Connection failed")

        return {
            "connected": True,
            "host": host,
            "port": port,
            "state": seestar_client.status.state.value,
            "firmware_version": seestar_client.status.firmware_version,
            "message": f"Connected to Seestar at {host}:{port}",
        }
    except HTTPException:
        seestar_client = None  # Reset on any error
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        seestar_client = None  # Reset on any error
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.post("/telescope/disconnect")
async def disconnect_telescope():
    """
    Disconnect from telescope.

    Returns:
        Disconnection status
    """
    global seestar_client

    try:
        if seestar_client is None:
            return {"connected": False, "message": "No telescope connected"}

        await seestar_client.disconnect()
        seestar_client = None

        return {"connected": False, "message": "Disconnected from telescope"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


@router.get("/telescope/status")
async def get_telescope_status():
    """
    Get current telescope status.

    Returns:
        Telescope connection and state information
    """
    if seestar_client is None:
        return {
            "connected": False,
            "state": "disconnected",
            "message": "No telescope connected",
        }

    try:
        # Actively poll telescope to keep connection alive and sync state
        # This sends iscope_get_app_state command which updates internal state
        # based on telescope's actual stage (AutoGoto, AutoFocus, Stack, Idle, ScopeHome, etc.)
        app_state = await seestar_client.get_app_state()
        logger.debug("Status poll: app_state stage=%s", app_state.get("stage"))

        # Also check device state to detect parked (mount.close=True)
        device_state = await seestar_client.get_device_state()
        mount = device_state.get("mount", {})
        logger.debug("Status poll: mount.close=%s", mount.get("close"))

        # Get current RA/Dec coordinates
        try:
            await seestar_client.get_current_coordinates()
        except Exception as e:
            logger.debug("Status poll: failed to get coordinates: %s", e)

        status = seestar_client.status
        logger.debug("Status poll: internal state=%s", status.state.value if status.state else "unknown")

        # Extract compass heading from device_state (direction field confirmed in firmware)
        compass_data = device_state.get("compass_sensor", {}).get("data", {})
        compass_heading = compass_data.get("direction") or compass_data.get("heading") or compass_data.get("yaw")

        # Extract level/balance angle from device_state
        level_angle = None
        for key in ("balance_sensor", "balance", "imu", "gsensor", "accelerometer"):
            sensor = device_state.get(key, {})
            if sensor:
                data = sensor.get("data", sensor)
                level_angle = data.get("angle")
                if level_angle is not None:
                    break

        # Alt/Az via scope_get_horiz_coord (returns {result: [alt, az]} per firmware)
        alt_degrees = None
        az_degrees = None
        try:
            horiz_resp = await seestar_client._send_command("scope_get_horiz_coord", {})
            horiz = horiz_resp.get("result") if isinstance(horiz_resp, dict) else horiz_resp
            if isinstance(horiz, list) and len(horiz) == 2:
                alt_degrees, az_degrees = horiz[0], horiz[1]
        except Exception:
            pass

        return {
            "connected": status.connected,
            "state": status.state.value if status.state else "unknown",
            "firmware_version": status.firmware_version,
            "is_tracking": status.is_tracking,
            "current_target": status.current_target,
            "current_ra_hours": status.current_ra_hours,
            "current_dec_degrees": status.current_dec_degrees,
            "last_error": status.last_error,
            "mount_mode": status.mount_mode.value if status.mount_mode else "altaz",
            "compass_heading": round(compass_heading) if compass_heading is not None else None,
            "level_angle": round(level_angle, 1) if level_angle is not None else None,
            "alt_degrees": round(alt_degrees, 2) if alt_degrees is not None else None,
            "az_degrees": round(az_degrees, 2) if az_degrees is not None else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/telescope/execute")
async def execute_plan(request: ExecutePlanRequest):
    """
    Execute an observation plan on the telescope.

    This starts background execution of the provided scheduled targets via Celery.
    Use /telescope/progress to monitor execution.

    Args:
        request: List of scheduled targets to execute

    Returns:
        Execution ID and initial status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(
                status_code=400, detail="Telescope not connected. Connect first using /telescope/connect"
            )

        # Check if there's already an active execution
        from app.database import SessionLocal
        from app.models.telescope_models import TelescopeExecution

        db = SessionLocal()
        try:
            active_execution = (
                db.query(TelescopeExecution).filter(TelescopeExecution.state.in_(["starting", "running"])).first()
            )

            if active_execution:
                raise HTTPException(
                    status_code=400, detail=f"Execution already in progress: {active_execution.execution_id}"
                )
        finally:
            db.close()

        # Generate execution ID
        execution_id = str(uuid.uuid4())[:8]

        # Get telescope connection info
        telescope_host = request.dict().get("telescope_host") or seestar_client.host or "192.168.2.47"
        telescope_port = request.dict().get("telescope_port") or seestar_client.port or 4700

        # Convert targets to dict for Celery serialization
        targets_data = [t.dict() for t in request.scheduled_targets]

        # Start execution via Celery task
        from app.tasks.telescope_tasks import execute_observation_plan_task

        task = execute_observation_plan_task.delay(
            execution_id=execution_id,
            targets_data=targets_data,
            telescope_host=telescope_host,
            telescope_port=telescope_port,
            park_when_done=request.park_when_done,
            saved_plan_id=request.saved_plan_id,
        )

        return {
            "execution_id": execution_id,
            "celery_task_id": task.id,
            "status": "started",
            "total_targets": len(request.scheduled_targets),
            "message": "Execution started. Use /telescope/progress to monitor.",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/telescope/progress")
async def get_execution_progress():
    """
    Get current execution progress.

    Returns detailed progress information including:
    - Current execution state
    - Current target being executed
    - Progress percentage
    - Elapsed and estimated remaining time
    - Errors encountered

    Returns:
        Execution progress details
    """
    from datetime import timedelta

    from app.database import SessionLocal
    from app.models.telescope_models import TelescopeExecution

    db = SessionLocal()
    try:
        # Get most recent active or recent execution
        execution = db.query(TelescopeExecution).order_by(TelescopeExecution.started_at.desc()).first()

        if not execution:
            return {"state": "idle", "message": "No execution in progress"}

        # Format elapsed time
        elapsed_time = None
        if execution.elapsed_seconds:
            elapsed_time = str(timedelta(seconds=execution.elapsed_seconds))

        # Format estimated remaining time
        estimated_remaining = None
        if execution.estimated_remaining_seconds:
            estimated_remaining = str(timedelta(seconds=execution.estimated_remaining_seconds))

        # Parse error log
        errors = []
        if execution.error_log:
            errors = execution.error_log if isinstance(execution.error_log, list) else []

        return {
            "execution_id": execution.execution_id,
            "state": execution.state,
            "total_targets": execution.total_targets,
            "current_target_index": execution.current_target_index,
            "targets_completed": execution.targets_completed,
            "targets_failed": execution.targets_failed,
            "current_target_name": execution.current_target_name,
            "current_phase": execution.current_phase,
            "progress_percent": round(execution.progress_percent, 1),
            "elapsed_time": elapsed_time,
            "estimated_remaining": estimated_remaining,
            "errors": errors,
        }

    finally:
        db.close()


@router.post("/telescope/abort")
async def abort_execution():
    """
    Abort the current execution.

    Stops the current imaging operation and cancels remaining targets.

    Returns:
        Abort status
    """
    try:
        from app.database import SessionLocal
        from app.models.telescope_models import TelescopeExecution
        from app.tasks.telescope_tasks import abort_observation_plan_task

        db = SessionLocal()
        try:
            # Find running execution
            execution = (
                db.query(TelescopeExecution).filter(TelescopeExecution.state.in_(["starting", "running"])).first()
            )

            if not execution:
                raise HTTPException(status_code=400, detail="No execution in progress to abort")

            execution_id = execution.execution_id

        finally:
            db.close()

        # Abort via Celery task
        result = abort_observation_plan_task.delay(execution_id).get(timeout=5)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error aborting execution"))

        return {"status": "aborted", "execution_id": execution_id, "message": "Execution aborted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abort failed: {str(e)}")


@router.post("/telescope/unpark")
async def unpark_telescope():
    """
    Unpark/open telescope and make ready for observing.

    For Seestar S50, unparking is done by moving to horizon position
    at azimuth=180° (south), altitude=45° to open the arm and prepare
    for observation.

    Returns:
        Unpark status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        # Unpark Seestar by moving to horizon position (south, 45° altitude)
        # This opens the telescope arm and makes it ready for observing
        logger.info("Unparking telescope: move_to_horizon(azimuth=180, altitude=45)")
        success = await seestar_client.move_to_horizon(azimuth=180.0, altitude=45.0)
        logger.info("Unpark result: %s", success)

        if success:
            return {"status": "active", "message": "Telescope unparked and ready"}
        else:
            return {"status": "error", "message": "Failed to unpark telescope"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unpark failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unpark failed: {str(e)}")


@router.post("/telescope/park")
async def park_telescope():
    """
    Park telescope at home position.

    Returns:
        Park status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.park()

        if success:
            return {"status": "parking", "message": "Telescope parking"}
        else:
            return {"status": "error", "message": "Failed to park telescope"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Park failed: {str(e)}")


@router.post("/telescope/switch-mode")
async def switch_telescope_mode(request: dict):
    """
    Switch telescope between equatorial and alt/az tracking modes.

    This parks the telescope and switches the tracking mode. When switching to
    alt/az mode, it automatically calls stop_polar_align first.

    Args:
        request: JSON with mode parameter
            - mode: "equatorial" or "altaz"

    Returns:
        Mode switch status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        mode = request.get("mode", "").lower()
        if mode not in ["equatorial", "altaz"]:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'equatorial' or 'altaz'")

        equ_mode = mode == "equatorial"

        # Park with the specified mode
        success = await seestar_client.park(equ_mode=equ_mode)

        if success:
            return {"status": "success", "message": f"Switched to {mode} mode and parking", "mode": mode}
        else:
            return {"status": "error", "message": "Failed to switch mode"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mode switch failed: {str(e)}")


@router.post("/telescope/move")
async def move_telescope(request: dict):
    """
    Direct mount movement control.

    Args:
        request: JSON with movement parameters
            - action: Movement direction ("up", "down", "left", "right", "stop")
            - speed: Optional movement speed

    Returns:
        Movement status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        action = request.get("action")
        speed = request.get("speed")
        dur_sec = request.get("dur_sec")  # override default duration
        percent = request.get("percent")  # override default percent (1-100)

        if not action:
            raise HTTPException(status_code=400, detail="Missing action parameter")

        valid_actions = ["up", "down", "left", "right", "stop", "abort"]
        if action not in valid_actions:
            raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")

        success = await seestar_client.move_scope(action=action, speed=speed, dur_sec=dur_sec, percent=percent)

        if success:
            return {"status": "moving" if action not in ["stop", "abort"] else "stopped", "action": action}
        else:
            return {"status": "error", "message": f"Failed to execute movement action: {action}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Move failed: {str(e)}")


@router.post("/telescope/move-joystick")
async def move_telescope_joystick(request: dict):
    """
    Joystick-style movement: raw angle (0-360°) + percent (1-100) + dur_sec.
    Maps directly to scope_speed_move without converting direction strings.
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        angle = request.get("angle")
        percent = request.get("percent", 50)
        dur_sec = request.get("dur_sec", 2)

        if angle is None:
            raise HTTPException(status_code=400, detail="angle required (0-360 degrees)")

        params = {
            "angle": int(angle % 360),
            "percent": int(min(100, max(1, percent))),
            "level": 1,
            "dur_sec": int(dur_sec),
        }
        response = await seestar_client._send_command("scope_speed_move", params)
        success = response.get("result") == 0
        return {"status": "moving" if success else "error", "angle": angle, "percent": percent}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Joystick move failed: {str(e)}")


@router.post("/telescope/goto")
async def goto_coordinates(request: dict):
    """
    Slew telescope to RA/Dec coordinates.

    Args:
        request: {"ra": float (hours), "dec": float (degrees), "target_name": str (optional)}

    Returns:
        Goto status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        ra = request.get("ra")
        dec = request.get("dec")
        target_name = request.get("target_name", "Manual Target")

        if ra is None or dec is None:
            raise HTTPException(status_code=400, detail="Must provide ra and dec coordinates")

        logger.info("Goto: RA=%.4f Dec=%.4f target=%s", ra, dec, target_name)
        success = await seestar_client.goto_target(ra, dec, target_name)

        if success:
            return {"status": "slewing", "message": f"Slewing to RA={ra}, Dec={dec}"}
        else:
            return {"status": "error", "message": "Failed to start goto"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Goto failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Goto failed: {str(e)}")


@router.post("/telescope/stop-slew")
async def stop_slew():
    """
    Stop current slew/goto operation.

    Returns:
        Stop status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.stop_slew()

        if success:
            return {"status": "stopped", "message": "Slew stopped"}
        else:
            return {"status": "error", "message": "Failed to stop slew"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop slew failed: {str(e)}")


@router.post("/telescope/polar-align/start")
async def start_polar_align():
    """
    Start polar alignment process.

    Returns:
        Polar alignment start status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.start_polar_align()

        if success:
            return {"status": "active", "message": "Polar alignment started"}
        else:
            return {"status": "error", "message": "Failed to start polar alignment"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start polar alignment failed: {str(e)}")


@router.post("/telescope/polar-align/stop")
async def stop_polar_align():
    """
    Stop polar alignment process.

    Returns:
        Polar alignment stop status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.stop_polar_align()

        if success:
            return {"status": "stopped", "message": "Polar alignment stopped"}
        else:
            return {"status": "error", "message": "Failed to stop polar alignment"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop polar alignment failed: {str(e)}")


@router.post("/telescope/polar-align/pause")
async def pause_polar_align():
    """
    Pause polar alignment process.

    Returns:
        Polar alignment pause status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.pause_polar_align()

        if success:
            return {"status": "paused", "message": "Polar alignment paused"}
        else:
            return {"status": "error", "message": "Failed to pause polar alignment"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pause polar alignment failed: {str(e)}")


@router.post("/telescope/start-imaging")
async def start_imaging(request: dict = None):
    """
    Start imaging/stacking.

    Args:
        request: {"restart": bool (optional, default True)}

    Returns:
        Imaging status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        restart = True if request is None else request.get("restart", True)

        success = await seestar_client.start_imaging(restart=restart)

        if success:
            return {"status": "imaging", "message": "Imaging started"}
        else:
            return {"status": "error", "message": "Failed to start imaging"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start imaging failed: {str(e)}")


@router.post("/telescope/stop-imaging")
async def stop_imaging():
    """
    Stop current imaging/stacking.

    Returns:
        Stop status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.stop_imaging()

        if success:
            return {"status": "stopped", "message": "Imaging stopped"}
        else:
            return {"status": "error", "message": "Failed to stop imaging"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop imaging failed: {str(e)}")


@router.post("/telescope/recording/start")
async def start_recording(request: dict = None):
    """
    Start AVI video recording.

    Args:
        request: {"filename": str (optional)} - Optional filename for recording

    Returns:
        Recording status with filename
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        filename = None if request is None else request.get("filename")

        success = await seestar_client.start_record_avi(filename=filename)

        if success:
            return {"status": "recording_started", "filename": filename or "auto"}
        else:
            return {"status": "error", "message": "Failed to start recording"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")


@router.post("/telescope/recording/stop")
async def stop_recording():
    """
    Stop AVI video recording.

    Returns:
        Recording status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.stop_record_avi()

        if success:
            return {"status": "recording_stopped"}
        else:
            return {"status": "error", "message": "Failed to stop recording"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop recording: {str(e)}")


@router.post("/telescope/tracking/start")
async def start_tracking(request: StartTrackingRequest, client: SeestarClient = Depends(get_current_telescope)):
    """
    Start tracking an object (satellite, comet, or asteroid).

    Args:
        request: StartTrackingRequest with object_type and object_id
        client: Connected telescope client

    Returns:
        Tracking status with object details
    """
    try:
        success = await client.start_track_object(object_type=request.object_type, object_id=request.object_id)

        if success:
            return {"status": "tracking_started", "object_type": request.object_type, "object_id": request.object_id}
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to start tracking {request.object_type} {request.object_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start tracking: {str(e)}")


@router.post("/telescope/tracking/stop")
async def stop_tracking(client: SeestarClient = Depends(get_current_telescope)):
    """
    Stop tracking the current object.

    Args:
        client: Connected telescope client

    Returns:
        Tracking status
    """
    try:
        success = await client.stop_track_object()

        if success:
            return {"status": "tracking_stopped"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop tracking")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop tracking: {str(e)}")


@router.post("/telescope/start-preview")
async def start_preview(request: dict = None):
    """
    Start preview/viewing mode without coordinates.

    Supports various viewing modes for terrestrial, solar system, and deep sky objects
    without requiring specific coordinates. Enables RTMP streaming.

    Args:
        request: {
            "mode": str (optional) - "scenery", "moon", "planet", "sun", or "star" (default: "scenery")
            "brightness": float (optional, 0-100, default 50.0)
        }

    Returns:
        Preview status with RTMP port information
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        mode = "scenery" if request is None else request.get("mode", "scenery")
        brightness = 50.0 if request is None else request.get("brightness", 50.0)

        # Validate mode
        valid_modes = ["scenery", "moon", "planet", "sun", "star"]
        if mode not in valid_modes:
            raise HTTPException(
                status_code=400, detail=f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"
            )

        success = await seestar_client.start_preview(mode=mode, brightness=brightness)

        if success:
            mode_descriptions = {
                "scenery": "Landscape view",
                "moon": "Moon viewing",
                "planet": "Planet viewing",
                "sun": "Solar viewing",
                "star": "Star preview",
            }
            return {
                "status": "preview_started",
                "mode": mode,
                "message": f"{mode_descriptions.get(mode, 'Preview')} started - RTMP stream available",
                "rtmp_url": "rtmp://192.168.2.47:4554",
            }
        else:
            return {"status": "error", "message": f"Failed to start {mode} preview"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start preview failed: {str(e)}")


@router.get("/telescope/live-preview")
async def get_live_preview():
    """
    Get live RTMP preview frame from telescope.

    This endpoint captures a frame from the telescope's RTMP stream.
    Requires that a preview mode is active (scenery, moon, planet, sun, or star).

    Returns:
        JPEG image bytes from RTMP stream
    """
    from fastapi.responses import Response

    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        # Get live preview frame from RTMP stream
        frame_bytes = await seestar_client.get_live_preview()

        # Return as JPEG image
        return Response(content=frame_bytes, media_type="image/jpeg")

    except ConnectionError as e:
        raise HTTPException(
            status_code=503, detail=f"RTMP stream not available. Start a preview mode first. ({str(e)})"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live preview failed: {str(e)}")


@router.get("/telescope/preview-info")
async def get_preview_info():
    """
    Get information about the current RTSP preview stream.

    Returns frame dimensions, timestamp, and availability status.
    Useful for debugging aspect ratio and video display issues.
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        from app.services.rtmp_preview_service import get_preview_service

        preview_service = get_preview_service(host=seestar_client._host or "192.168.2.47", port=4554)

        frame_info = preview_service.get_frame_info()
        return frame_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview info error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get preview info: {str(e)}")


@router.get("/telescope/preview")
async def get_telescope_preview():
    """
    Get the latest preview image from telescope.

    This endpoint looks for the most recent stacked JPEG image in the
    telescope's FITS directory. Returns image metadata and access path.

    Returns:
        Preview image information with path for download
    """
    import os

    try:
        # Look for recent JPEG files in /fits directory
        fits_root = Path(os.getenv("FITS_DIR", "/fits"))

        if not fits_root.exists():
            return {
                "available": False,
                "message": "Telescope image directory not mounted. Configure FITS_DIR environment variable.",
            }

        # Find all JPEG files (Seestar creates preview JPEGs during stacking)
        jpeg_files = []
        for ext in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]:
            jpeg_files.extend(fits_root.rglob(ext))

        if not jpeg_files:
            return {"available": False, "message": "No preview images found. Start imaging on the telescope first."}

        # Sort by modification time, get most recent
        latest_image = max(jpeg_files, key=lambda p: p.stat().st_mtime)

        # Get file info
        file_stats = latest_image.stat()
        modified_time = datetime.fromtimestamp(file_stats.st_mtime)

        # Return relative path from FITS_DIR for frontend to request
        relative_path = latest_image.relative_to(fits_root)

        return {
            "available": True,
            "filename": latest_image.name,
            "path": str(relative_path),
            "size_bytes": file_stats.st_size,
            "modified_at": modified_time.isoformat(),
            "download_url": f"/api/telescope/preview/download?path={relative_path}",
            "message": f"Latest image from {modified_time.strftime('%H:%M:%S')}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preview: {str(e)}")


@router.get("/telescope/preview/latest")
async def get_latest_preview():
    """
    Get the latest preview image from telescope as raw image bytes.

    This endpoint returns the most recent JPEG image directly for display
    in the live preview panel. Polls this endpoint to get updated images.

    Returns:
        Latest preview image (JPEG bytes)
    """
    import os

    from fastapi.responses import Response

    try:
        # Look for recent JPEG files in /fits directory
        fits_root = Path(os.getenv("FITS_DIR", "/fits"))

        if not fits_root.exists():
            raise HTTPException(status_code=503, detail="Telescope image directory not mounted")

        # Find all JPEG files (Seestar creates preview JPEGs during stacking)
        jpeg_files = []
        for ext in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]:
            jpeg_files.extend(fits_root.rglob(ext))

        if not jpeg_files:
            raise HTTPException(status_code=404, detail="No preview images available. Start imaging first.")

        # Sort by modification time, get most recent
        latest_image = max(jpeg_files, key=lambda p: p.stat().st_mtime)

        # Read and return image bytes
        image_bytes = latest_image.read_bytes()

        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest preview: {str(e)}")


@router.get("/telescope/preview/download")
async def download_telescope_preview(path: str = Query(..., description="Relative path to image")):
    """
    Download a specific preview image from telescope storage.

    Args:
        path: Relative path to the image file

    Returns:
        Image file for display
    """
    import os

    try:
        fits_root = Path(os.getenv("FITS_DIR", "/fits"))

        # Sanitize path to prevent directory traversal
        requested_path = fits_root / path.lstrip("/")
        requested_path = requested_path.resolve()

        # Ensure we're still within FITS_DIR
        if not str(requested_path).startswith(str(fits_root)):
            raise HTTPException(status_code=403, detail="Access denied")

        if not requested_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        if not requested_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Return image with appropriate MIME type
        return FileResponse(path=str(requested_path), media_type="image/jpeg", filename=requested_path.name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download preview: {str(e)}")


# NOTE: This endpoint is disabled while transitioning to adapter pattern
# It provided direct access to SeestarClient methods which doesn't fit the adapter abstraction
# Telescope-specific commands should be implemented as proper adapter methods
# ==========================================
# REAL-TIME TRACKING & STATUS
# ==========================================


@router.get("/telescope/coordinates")
async def get_current_coordinates():
    """
    Get current telescope RA/Dec coordinates.

    For real-time tracking display. Poll every 1-5 seconds during observation.

    Returns:
        Current RA (hours) and Dec (degrees)
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        coords = await seestar_client.get_current_coordinates()
        return {
            "ra_hours": coords.get("ra", 0.0),
            "dec_degrees": coords.get("dec", 0.0),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coordinates: {str(e)}")


@router.get("/telescope/app-state")
async def get_app_state():
    """
    Get application state for progress monitoring.

    Returns current operation status including:
    - Stage (slewing, focusing, stacking, etc.)
    - Progress percentage
    - Frame counts
    - Operation details

    Poll during operations for status updates.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        state = await seestar_client.get_app_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get app state: {str(e)}")


@router.get("/telescope/stacking-status")
async def check_stacking_complete():
    """
    Check if stacking is complete.

    Returns:
        Boolean indicating if enough frames have been captured
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        is_complete = await seestar_client.check_stacking_complete()
        return {"is_stacked": is_complete}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check stacking status: {str(e)}")


# ==========================================
# VIEW PLANS (AUTOMATION)
# ==========================================


@router.post("/telescope/plan/start")
async def start_view_plan(plan_config: Dict[str, Any]):
    """
    Execute automated observation plan.

    Starts multi-target imaging sequence using telescope's built-in
    view plan system.

    Args:
        plan_config: Plan configuration object with targets and settings

    Returns:
        Success status
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        success = await seestar_client.start_view_plan(plan_config)
        return {"success": success, "message": "View plan started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start view plan: {str(e)}")


@router.post("/telescope/plan/stop")
async def stop_view_plan():
    """
    Stop running view plan.

    Cancels automated sequence.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        success = await seestar_client.stop_view_plan()
        return {"success": success, "message": "View plan stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop view plan: {str(e)}")


@router.get("/telescope/plan/state")
async def get_view_plan_state():
    """
    Get view plan execution state.

    Returns current plan status, target, and progress.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        state = await seestar_client.get_view_plan_state()
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get view plan state: {str(e)}")


# ==========================================
# PLATE SOLVING & ANNOTATION
# ==========================================


@router.get("/telescope/solve-result")
async def get_plate_solve_result():
    """
    Get plate solve result.

    Returns actual RA/Dec after goto to verify pointing accuracy.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        result = await seestar_client.get_plate_solve_result()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get solve result: {str(e)}")


@router.get("/telescope/field-annotations")
async def get_field_annotations():
    """
    Get annotation results.

    Returns identified objects in current field of view.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        annotations = await seestar_client.get_field_annotations()
        return annotations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get annotations: {str(e)}")


@router.post("/telescope/annotation/toggle")
async def toggle_annotations(request: AnnotationRequest, telescope: SeestarClient = Depends(get_current_telescope)):
    """
    Toggle field annotations on/off.

    Args:
        request: AnnotationRequest with enabled flag
        telescope: Connected telescope client
    """
    try:
        if request.enabled:
            success = await telescope.start_annotate()
        else:
            success = await telescope.stop_annotate()
        return {"success": success, "enabled": request.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle annotations: {str(e)}")


# ==========================================
# PLANETARY IMAGING
# ==========================================


@router.post("/telescope/imaging/planet/scan")
async def scan_planets():
    """
    Get list of planets/moons available for imaging.

    Returns major solar system imaging targets:
    Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Moon

    Note: Sun excluded for safety (requires special solar filter).
    """
    try:
        from app.services.planet_service import PlanetService

        planet_service = PlanetService()
        all_planets = planet_service.get_all_planets()

        # Return all major planets/moons except Sun (safety)
        imaging_targets = [p.name for p in all_planets if p.name != "Sun"]

        return {"planets": imaging_targets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get planets: {str(e)}")


@router.post("/telescope/imaging/planet/start")
async def start_planetary_imaging(
    planet_name: str, exposure: int = 10, gain: int = 80, telescope: SeestarClient = Depends(get_current_telescope)
):
    """
    Start planetary imaging.

    Args:
        planet_name: Name of planet to image
        exposure: Exposure time in milliseconds
        gain: Gain value (0-200)
    """
    try:
        success = await telescope.start_planet_stack(planet_name, exposure, gain)
        return {"success": success, "message": f"Planetary imaging started for {planet_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start planetary imaging: {str(e)}")


@router.post("/telescope/imaging/planet/stop")
async def stop_planetary_imaging(telescope: SeestarClient = Depends(get_current_telescope)):
    """
    Stop planetary imaging.
    """
    try:
        success = await telescope.stop_planet_stack()
        return {"success": success, "message": "Planetary imaging stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop planetary imaging: {str(e)}")


# ==========================================
# UTILITY OPERATIONS
# ==========================================


@router.post("/telescope/cancel")
async def cancel_current_operation():
    """
    Cancel current operation.

    Emergency abort for any running operation.
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        success = await seestar_client.cancel_current_operation()
        return {"success": success, "message": "Operation cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel operation: {str(e)}")


@router.post("/telescope/sound/play")
async def play_notification_sound(volume: str = "backyard"):
    """
    Play notification sound.

    Args:
        volume: Sound volume preset (e.g., "backyard", "city", "remote")
    """
    if seestar_client is None or not seestar_client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    try:
        success = await seestar_client.play_notification_sound(volume)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to play sound: {str(e)}")


#
# @router.post("/telescope/command/{command}")
# async def execute_telescope_command(command: str, params: Optional[Dict[str, Any]] = None):
#     """Generic telescope command proxy (DISABLED)."""
#     raise HTTPException(status_code=501, detail="Generic command endpoint not implemented with adapter pattern")


@router.post("/telescope/session/join")
async def join_remote_session(request: dict):
    """
    Join a remote observation session (multi-client control).

    Args:
        request: JSON with session parameters
            - session_id: Optional session identifier

    Returns:
        Join status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        session_id = request.get("session_id", "")
        success = await seestar_client.join_remote_session(session_id)

        if success:
            return {"status": "joined", "message": "Joined remote session", "session_id": session_id}
        else:
            return {"status": "error", "message": "Failed to join remote session"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Join session failed: {str(e)}")


@router.post("/telescope/session/leave")
async def leave_remote_session():
    """
    Leave the current remote observation session.

    Returns:
        Leave status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        success = await seestar_client.leave_remote_session()

        if success:
            return {"status": "left", "message": "Left remote session"}
        else:
            return {"status": "error", "message": "Failed to leave remote session"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leave session failed: {str(e)}")


@router.post("/telescope/session/disconnect")
async def disconnect_remote_client(request: dict = None):
    """
    Disconnect a remote client from the session.

    Args:
        request: JSON with client parameters
            - client_id: Optional client identifier

    Returns:
        Disconnect status
    """
    try:
        if seestar_client is None or not seestar_client.connected:
            raise HTTPException(status_code=400, detail="Telescope not connected")

        client_id = request.get("client_id", "") if request else ""
        success = await seestar_client.disconnect_remote_client(client_id)

        if success:
            return {"status": "disconnected", "message": "Remote client disconnected"}
        else:
            return {"status": "error", "message": "Failed to disconnect remote client"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disconnect client failed: {str(e)}")
