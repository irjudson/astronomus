"""Minimal mock Seestar server for testing dangerous/destructive commands.

Only handles commands that must never run on real hardware. All other commands
return a generic success response and are logged in commands_received.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Template for device state response
_DEVICE_STATE_TEMPLATE = {
    "device": {
        "firmware_ver_string": "mock-1.0.0",
        "model": "Seestar S50",
        "sn": "MOCK000001",
    },
    "mount": {
        "close": False,
        "state": "tracking",
    },
    "View": {
        "state": "idle",
        "stage": "Idle",
    },
}

# Per-command response overrides; all others return {"result": 0, "code": 0}
_COMMAND_RESPONSES: Dict[str, Any] = {
    "get_verify_str": {"result": {"str": "mock_challenge_abc123"}, "code": 0},
    "verify_client": {"result": 0, "code": 0},
    "test_connection": {"result": {}, "code": 0},
    "scope_get_equ_coord": {"result": {"ra": 0.0, "dec": 0.0, "state": "parked"}, "code": 0},
    "get_device_state": {"result": _DEVICE_STATE_TEMPLATE, "code": 0},
    "get_view_state": {"result": {"View": {"state": "idle", "stage": "Idle"}}, "code": 0},
    "get_app_state": {"result": {"state": "idle"}, "code": 0},
    "scope_get_horiz_coord": {"result": {"alt": 45.0, "az": 180.0}, "code": 0},
    "iscope_start_view": {"result": 0, "code": 0},
    "iscope_stop_view": {"result": 0, "code": 0},
    "start_record_avi": {"result": 0, "code": 0},
    "stop_record_avi": {"result": 0, "code": 0},
    "start_solve": {"result": 0, "code": 0},
    "stop_solve": {"result": 0, "code": 0},
    "start_object_detection": {"result": 0, "code": 0},
    "stop_object_detection": {"result": 0, "code": 0},
    # Focuser
    "start_auto_focuse": {"result": 0, "code": 0},  # typo preserved from firmware
    "stop_auto_focuse": {"result": 0, "code": 0},  # typo preserved from firmware
    "move_focuser": {"result": 0, "code": 0},
    "reset_factory_focal_pos": {"result": 0, "code": 0},
    "get_focuser_position": {"result": {"position": 500}, "code": 0},
    # Mount movement
    "scope_move": {"result": 0, "code": 0},
    "scope_goto": {"result": 0, "code": 0},
    "scope_speed_move": {"result": 0, "code": 0},
    "scope_move_to_horizon": {"result": 0, "code": 0},
    "mount_go_home": {"result": 0, "code": 0},
    "scope_park": {"result": 0, "code": 0},
    "iscope_stop_view": {"result": 0, "code": 0},
    # Dangerous system commands (mock only)
    "pi_shutdown": {"result": 0, "code": 0},
    "pi_reboot": {"result": 0, "code": 0},
    # Settings
    "set_setting": {"result": 0, "code": 0},
    "set_user_location": {"result": 0, "code": 0},
    # System
    "play_sound": {"result": 0, "code": 0},
    "get_file_list": {"result": {"files": []}, "code": 0},
    "get_file_info": {"result": {}, "code": 0},
    "get_img_file_info": {"result": {}, "code": 0},
    "iscope_cancel_view": {"result": 0, "code": 0},
    # Planetary
    "iscope_start_scan_planet": {"result": 0, "code": 0},
    "iscope_stop_scan_planet": {"result": 0, "code": 0},
    "iscope_start_planet_stack": {"result": 0, "code": 0},
    "iscope_stop_planet_stack": {"result": 0, "code": 0},
    "start_planet_scan": {"result": 0, "code": 0},
    # Polar alignment
    "start_pa": {"result": 0, "code": 0},
    "stop_pa": {"result": 0, "code": 0},
    "pause_pa": {"result": 0, "code": 0},
    "check_pa_alt": {"result": {"pa_error": 0.0, "status": "ok"}, "code": 0},
    # Imaging
    "get_plate_solve_result": {"result": {"solved": False}, "code": 0},
    "get_annotations": {"result": {"annotations": []}, "code": 0},
    "start_view_plan": {"result": 0, "code": 0},
    "stop_view_plan": {"result": 0, "code": 0},
    "get_view_plan_state": {"result": {"state": "idle"}, "code": 0},
    "check_client_verified": {"result": {"verified": True}, "code": 0},
    "start_stack_dso": {"result": 0, "code": 0},
    "stop_stack": {"result": 0, "code": 0},
    "is_stacking_done": {"result": {"done": False}, "code": 0},
}


class MockSeestarServer:
    """Minimal mock TCP server for Seestar dangerous command tests.

    Usage as async context manager:
        async with MockSeestarServer() as (host, port):
            client = SeestarClient(private_key_path=tmp_key_path)
            await client.connect(host, port)
            # run dangerous commands safely

    Attributes:
        commands_received: list of {"method": ..., "params": ...} dicts
                           for each command received from client
    """

    def __init__(self):
        self.commands_received: List[Dict[str, Any]] = []
        self._server: Optional[asyncio.Server] = None

    async def start(self, host: str = "127.0.0.1", port: int = 0) -> Tuple[str, int]:
        """Start listening. Returns (host, port) bound to."""
        self._server = await asyncio.start_server(self._handle_client, host, port)
        bound = self._server.sockets[0].getsockname()
        logger.debug(f"MockSeestarServer listening on {bound[0]}:{bound[1]}")
        return bound[0], bound[1]

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.debug("MockSeestarServer stopped")

    async def __aenter__(self) -> Tuple[str, int]:
        return await self.start()

    async def __aexit__(self, *_) -> None:
        await self.stop()

    def last_command(self, method: str) -> Optional[Dict[str, Any]]:
        """Return the most recent command received with the given method name."""
        for cmd in reversed(self.commands_received):
            if cmd.get("method") == method:
                return cmd
        return None

    def received_method(self, method: str) -> bool:
        """Return True if any command with given method was received."""
        return any(cmd.get("method") == method for cmd in self.commands_received)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.debug(f"Mock: client connected from {addr}")
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    command = json.loads(line.decode("utf-8").strip())
                except json.JSONDecodeError:
                    logger.warning(f"Mock: invalid JSON: {line!r}")
                    continue

                method = command.get("method", "")
                params = command.get("params")
                cmd_id = command.get("id")

                # Record the command
                self.commands_received.append({"method": method, "params": params, "id": cmd_id})
                logger.debug(f"Mock: received {method} id={cmd_id}")

                # Build response
                template = _COMMAND_RESPONSES.get(method, {"result": 0, "code": 0})
                response = dict(template)
                if cmd_id is not None:
                    response["id"] = cmd_id

                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception as e:
            logger.error(f"Mock: error handling client: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.debug(f"Mock: client {addr} disconnected")
