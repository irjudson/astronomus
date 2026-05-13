"""Transport layer: thin wrapper over the canonical `seestar` package.

This file replaced a ~870-line in-tree TCP/RSA/heartbeat implementation
with a shim that delegates to `seestar.SeestarClient`. The external
API (SeestarTransport class, its methods, its private attrs used by
the mixins) is preserved bit-for-bit so the mount/observation/system/
files mixins and the 130+ scripts that call `_send_command` keep working
unchanged.

Responsibilities retained here:
  * Backward-compatible constants (DEFAULT_PORT, FILE_TRANSFER_PORT, etc.)
  * The astronomus-flavored event / status / progress subscription API
  * Translation of seestar-api EventMessage → astronomus SeestarEvent
  * Status bookkeeping (SeestarStatus dataclass)
  * `wait_for_goto_complete` / `wait_for_focus_complete` /
    `wait_for_imaging_complete` — the higher-level wait helpers

Responsibilities delegated to seestar-api:
  * TCP connection lifecycle
  * RSA handshake
  * Heartbeat
  * Command/response matching
  * Background read loop and raw event dispatch
  * Auto-reconnect

The private key is passed through via the `SEESTAR_PRIVATE_KEY_FILE`
environment variable at init time (seestar-api reads it at handshake).
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from seestar.models import EventMessage

from app.core.config import get_settings
from seestar import SeestarClient as _SeestarClient

from .types import (
    CommandError,
    ConnectionError,
    EventType,
    SeestarEvent,
    SeestarState,
    SeestarStatus,
    TimeoutError,
)


class SeestarTransport:
    """TCP transport for Seestar S50 smart telescope.

    Thin backward-compat wrapper around `seestar.SeestarClient`.
    """

    DEFAULT_PORT = 4700
    UDP_DISCOVERY_PORT = 4720
    FILE_TRANSFER_PORT = 4801
    CONNECTION_TIMEOUT = 10.0
    COMMAND_TIMEOUT = 30.0
    RECEIVE_BUFFER_SIZE = 4096

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        private_key_path: Optional[str] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)

        settings = get_settings()
        raw = private_key_path or settings.seestar_private_key_path
        p = Path(raw)
        if not p.is_absolute():
            # Relative to backend/ (this file is backend/app/clients/seestar/transport.py)
            p = Path(__file__).parent.parent.parent.parent / p
        self._private_key_path = p

        # Tell seestar-api where to find the key. seestar-api reads this at
        # handshake time via its `_load_key_from_env()` helper.
        os.environ["SEESTAR_PRIVATE_KEY_FILE"] = str(self._private_key_path)

        # Underlying seestar-api client (created lazily in connect()).
        self._seestar: Optional[_SeestarClient] = None

        # Connection coords (used by file-transfer mixin for port 4801).
        self._host: Optional[str] = None
        self._port = self.DEFAULT_PORT

        # Astronomus-flavored status snapshot.
        self._status = SeestarStatus(connected=False, state=SeestarState.DISCONNECTED)
        self._status_callback: Optional[Callable[[SeestarStatus], None]] = None

        # Event subscription state (kept in this layer so we can translate
        # EventMessage → SeestarEvent before firing callbacks).
        self._event_callbacks: Dict[EventType, List[Callable[[SeestarEvent], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._all_events_callbacks: List[Callable[[SeestarEvent], None]] = []
        self._progress_callbacks: List[Callable[[float, Dict[str, Any]], None]] = []

        # Operation state tracking (used by mixins).
        self._operation_states: Dict[str, str] = {}
        self._observer_location: Optional[tuple] = None

    # ── Properties ─────────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return self._seestar is not None and self._seestar.connected

    @property
    def _connected(self) -> bool:
        # Backward-compat: some code reads the private attr directly.
        return self.connected

    @property
    def status(self) -> SeestarStatus:
        return self._status

    @property
    def host(self) -> Optional[str]:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    # ── Subscription API ───────────────────────────────────────────

    def set_status_callback(self, callback: Callable[[SeestarStatus], None]) -> None:
        self._status_callback = callback

    def subscribe_event(self, event_type: EventType, callback: Callable[[SeestarEvent], None]) -> None:
        if callback not in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].append(callback)

    def unsubscribe_event(self, event_type: EventType, callback: Callable[[SeestarEvent], None]) -> None:
        if callback in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].remove(callback)

    def subscribe_all_events(self, callback: Callable[[SeestarEvent], None]) -> None:
        if callback not in self._all_events_callbacks:
            self._all_events_callbacks.append(callback)

    def unsubscribe_all_events(self, callback: Callable[[SeestarEvent], None]) -> None:
        if callback in self._all_events_callbacks:
            self._all_events_callbacks.remove(callback)

    def subscribe_progress(self, callback: Callable[[float, Dict[str, Any]], None]) -> None:
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)

    def unsubscribe_progress(self, callback: Callable[[float, Dict[str, Any]], None]) -> None:
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    # ── Status update (called by mixins) ───────────────────────────

    def _update_status(self, **kwargs) -> None:
        """Update internal status and trigger callback."""
        if kwargs:
            self.logger.info(f"[TELESCOPE STATUS UPDATE] {kwargs}")

        for key, value in kwargs.items():
            if hasattr(self._status, key):
                setattr(self._status, key, value)

        self._status.last_update = datetime.now()

        if self._status_callback:
            try:
                self._status_callback(self._status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")

    # ── Connection lifecycle ───────────────────────────────────────

    async def connect(self, host: str, port: int = DEFAULT_PORT) -> bool:
        """Connect to Seestar S50 telescope."""
        if self.connected:
            self.logger.warning("Already connected")
            return True

        self._host = host
        self._port = port

        self._seestar = _SeestarClient(
            host=host,
            port=port,
            timeout=self.COMMAND_TIMEOUT,
        )

        try:
            await self._seestar.connect()
        except Exception as exc:
            self._seestar = None
            self._update_status(
                connected=False,
                state=SeestarState.ERROR,
                last_error=str(exc),
            )
            raise ConnectionError(f"Connection failed: {exc}") from exc

        # Wire the seestar-api event router to our translation layer.
        self._seestar.events.on_all(self._forward_event)

        self._update_status(connected=True, state=SeestarState.CONNECTED)
        fw = self._seestar.firmware_version
        if fw is not None:
            self._update_status(firmware_version=str(fw))
        self.logger.info(f"Connected to {host}:{port} (firmware {fw or 'unknown'})")
        return True

    async def disconnect(self) -> None:
        """Disconnect from Seestar."""
        if self._seestar is not None:
            try:
                await self._seestar.disconnect()
            except Exception as exc:
                self.logger.debug(f"Error during disconnect: {exc}")
            self._seestar = None

        self._update_status(connected=False, state=SeestarState.DISCONNECTED)

    # ── Command send ───────────────────────────────────────────────

    async def _send_command(
        self,
        method: str,
        params: Any = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Send a command and return the parsed response as a dict.

        Preserves the pre-migration return shape expected by the mixins
        and scripts: `{id, method, code, result, error}`.
        """
        if self._seestar is None:
            raise ConnectionError("Not connected")

        try:
            resp = await self._seestar.send_command(method, params, timeout=timeout or self.COMMAND_TIMEOUT)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"Command {method!r} timed out") from exc
        except BaseException as exc:
            if isinstance(exc, (ConnectionError, TimeoutError, CommandError)):
                raise
            raise CommandError(f"Command {method!r} failed: {exc}") from exc

        return {
            "id": resp.id,
            "method": resp.method,
            "code": resp.code,
            "result": resp.result,
            "error": resp.error,
        }

    # ── Event translation ──────────────────────────────────────────

    def _forward_event(self, msg: EventMessage) -> None:
        """Translate a seestar-api EventMessage into an astronomus SeestarEvent
        and dispatch to all registered callbacks.
        """
        event = self._translate_event(msg)
        if event is None:
            return

        # Catch-all
        for cb in self._all_events_callbacks:
            try:
                cb(event)
            except Exception as e:
                self.logger.error(f"Error in all-events callback: {e}")

        # Type-specific
        for cb in self._event_callbacks.get(event.event_type, []):
            try:
                cb(event)
            except Exception as e:
                self.logger.error(f"Error in {event.event_type.value} callback: {e}")

        # Progress convenience
        if event.event_type == EventType.PROGRESS_UPDATE:
            percent = event.data.get("percent", 0)
            for pcb in self._progress_callbacks:
                try:
                    pcb(percent, event.data)
                except Exception as e:
                    self.logger.error(f"Error in progress callback: {e}")

    def _translate_event(self, msg: EventMessage) -> Optional[SeestarEvent]:
        """Convert seestar-api EventMessage to astronomus SeestarEvent.

        Uses the same type-routing heuristics as the pre-migration
        `_parse_event` method, applied to the EventMessage payload
        (treated as `result` for parsing purposes).
        """
        data = msg.model_dump(exclude={"Event"}, exclude_none=True)
        event_name = getattr(msg, "Event", "")

        # Route to an astronomus EventType based on payload shape.
        event_type = EventType.UNKNOWN
        event_data: Dict[str, Any] = {}

        if "progress" in data or "percent" in data:
            event_type = EventType.PROGRESS_UPDATE
            event_data = {
                "progress": data.get("progress", 0),
                "percent": data.get("percent", 0),
                "frame": data.get("frame", 0),
                "total_frames": data.get("total_frames", 0),
            }
        elif "state" in data:
            event_type = EventType.STATE_CHANGE
            event_data = {"state": data.get("state"), "stage": data.get("stage")}
        elif "error" in data or data.get("code", 0) != 0:
            event_type = EventType.ERROR
            event_data = {
                "error": data.get("error", "Unknown error"),
                "code": data.get("code", 0),
            }
        elif "stacked" in data or "image_ready" in data:
            event_type = EventType.IMAGE_READY
            event_data = {"filename": data.get("filename"), "path": data.get("path")}
        elif data.get("stage") == "Idle" or data.get("complete"):
            event_type = EventType.OPERATION_COMPLETE
            event_data = {
                "operation": data.get("operation"),
                "success": data.get("success", True),
            }
        else:
            event_data = data

        return SeestarEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            data=event_data,
            source_command=event_name,
        )

    # ── Higher-level wait helpers (unchanged from pre-migration) ───

    async def wait_for_goto_complete(self, timeout: float = 180.0) -> bool:
        """Wait for slew/goto to complete via STATE_CHANGE events."""
        completion_event = asyncio.Event()
        success = False

        def state_callback(event: SeestarEvent):
            nonlocal success
            state = event.data.get("state")
            if state == SeestarState.TRACKING.value or state == "tracking":
                success = True
                completion_event.set()
            elif state in (
                SeestarState.CONNECTED.value,
                "connected",
                SeestarState.PARKED.value,
                "parked",
            ):
                success = False
                completion_event.set()

        self.subscribe_event(EventType.STATE_CHANGE, state_callback)
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Goto operation timed out after {timeout}s")
            success = False
        finally:
            self.unsubscribe_event(EventType.STATE_CHANGE, state_callback)
        return success

    async def wait_for_focus_complete(self, timeout: float = 120.0) -> tuple[bool, Optional[float]]:
        """Wait for autofocus to complete via OPERATION_COMPLETE events."""
        completion_event = asyncio.Event()
        success = False
        focus_position: Optional[float] = None

        def operation_callback(event: SeestarEvent):
            nonlocal success, focus_position
            operation = event.data.get("operation", "")
            if operation and "focus" in str(operation).lower():
                success = bool(event.data.get("success", True))
                pos = event.data.get("position") or event.data.get("focus_position")
                if pos is not None:
                    try:
                        focus_position = float(pos)
                    except (TypeError, ValueError):
                        pass
                completion_event.set()

        self.subscribe_event(EventType.OPERATION_COMPLETE, operation_callback)
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Focus operation timed out after {timeout}s")
            success = False
        finally:
            self.unsubscribe_event(EventType.OPERATION_COMPLETE, operation_callback)
        return success, focus_position

    async def wait_for_imaging_complete(
        self,
        total_frames: Optional[int] = None,
        timeout: float = 600.0,
    ) -> bool:
        """Wait for imaging to complete via OPERATION_COMPLETE or frame-count events."""
        completion_event = asyncio.Event()
        success = False

        def operation_callback(event: SeestarEvent):
            nonlocal success
            operation = event.data.get("operation", "")
            if operation and any(k in str(operation).lower() for k in ("imag", "stack", "expos")):
                success = bool(event.data.get("success", True))
                completion_event.set()

        def progress_callback(event: SeestarEvent):
            nonlocal success
            if total_frames is None:
                return
            frame = event.data.get("frame") or 0
            if frame and int(frame) >= int(total_frames):
                success = True
                completion_event.set()

        self.subscribe_event(EventType.OPERATION_COMPLETE, operation_callback)
        self.subscribe_event(EventType.PROGRESS_UPDATE, progress_callback)
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Imaging operation timed out after {timeout}s")
            success = False
        finally:
            self.unsubscribe_event(EventType.OPERATION_COMPLETE, operation_callback)
            self.unsubscribe_event(EventType.PROGRESS_UPDATE, progress_callback)
        return success
