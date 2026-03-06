"""Transport layer: connection, auth, event system, command dispatch."""

import asyncio
import base64
import json
import logging
import socket
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.core.config import get_settings

from .types import (
    CommandError,
    ConnectionError,
    EventType,
    MountMode,
    SeestarClientError,
    SeestarEvent,
    SeestarState,
    SeestarStatus,
    TimeoutError,
)


class SeestarTransport:
    """TCP transport for Seestar S50 smart telescope.

    Provides low-level communication with the Seestar S50 using its native
    JSON-over-TCP protocol. Handles message formatting, ID tracking, and
    response matching.

    Example usage:
        client = SeestarClient()
        await client.connect("seestar.local")
        await client.goto_target(12.5, 45.3, "M31")
        await client.start_imaging()
        # ... image for some time ...
        await client.stop_imaging()
        await client.disconnect()
    """

    DEFAULT_PORT = 4700  # Port 4700 for firmware v6.x JSON-RPC
    UDP_DISCOVERY_PORT = 4720
    FILE_TRANSFER_PORT = 4801  # Port 4801 for file downloads
    CONNECTION_TIMEOUT = 10.0
    COMMAND_TIMEOUT = 30.0  # Increased from 10s - telescope can be slow to respond
    RECEIVE_BUFFER_SIZE = 4096

    def __init__(self, logger: Optional[logging.Logger] = None, private_key_path: Optional[str] = None):
        """Initialize Seestar client.

        Args:
            logger: Optional logger instance. If None, creates default logger.
            private_key_path: Optional path to RSA private key file. If None, uses config setting.
        """
        self.logger = logger or logging.getLogger(__name__)

        # Store key path for lazy loading (only load when actually connecting)
        settings = get_settings()
        self._private_key_path = Path(private_key_path or settings.seestar_private_key_path)
        if not self._private_key_path.is_absolute():
            # Make relative paths relative to backend directory
            self._private_key_path = Path(__file__).parent.parent.parent / self._private_key_path

        self._private_key_pem: Optional[bytes] = None

        # Connection state
        self._socket: Optional[socket.socket] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._host: Optional[str] = None
        self._port = self.DEFAULT_PORT

        # Message handling
        self._command_id = 10000  # Start at 10000 like seestar_alp
        self._pending_responses: Dict[int, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # State tracking
        self._status = SeestarStatus(connected=False, state=SeestarState.DISCONNECTED)
        self._operation_states: Dict[str, str] = {}

        # Cached observer location (lat, lon, elevation) — populated on first goto
        self._observer_location: Optional[tuple] = None

        # Reconnection tracking (Android app style)
        self._miss_time = 0  # Number of consecutive disconnects
        self._last_miss_time = 0.0  # Timestamp of last disconnect
        self._reconnect_delay = 0.3  # 300ms like Android app
        self._max_retries = 3  # Up to 3 retries
        self._reconnect_timeout = 60.0  # Reset counter after 60 seconds

        # Callbacks
        self._status_callback: Optional[Callable[[SeestarStatus], None]] = None

        # Event streaming
        self._event_callbacks: Dict[EventType, List[Callable[[SeestarEvent], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._all_events_callbacks: List[Callable[[SeestarEvent], None]] = []
        self._progress_callbacks: List[Callable[[float, Dict[str, Any]], None]] = []

    @property
    def connected(self) -> bool:
        """Check if connected to telescope."""
        return self._connected

    @property
    def status(self) -> SeestarStatus:
        """Get current telescope status."""
        return self._status

    @property
    def host(self) -> Optional[str]:
        """Get connected host."""
        return self._host

    @property
    def port(self) -> int:
        """Get connected port."""
        return self._port

    def set_status_callback(self, callback: Callable[[SeestarStatus], None]) -> None:
        """Set callback function for status updates.

        Args:
            callback: Function to call when status changes
        """
        self._status_callback = callback

    def subscribe_event(self, event_type: EventType, callback: Callable[[SeestarEvent], None]) -> None:
        """Register callback for specific event type.

        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if callback not in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].append(callback)
            self.logger.debug(f"Subscribed to {event_type.value} events")

    def unsubscribe_event(self, event_type: EventType, callback: Callable[[SeestarEvent], None]) -> None:
        """Remove event callback.

        Args:
            event_type: Type of event to stop listening for
            callback: Function to remove
        """
        if callback in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from {event_type.value} events")

    def subscribe_all_events(self, callback: Callable[[SeestarEvent], None]) -> None:
        """Receive all telescope events.

        Args:
            callback: Function to call for any event
        """
        if callback not in self._all_events_callbacks:
            self._all_events_callbacks.append(callback)
            self.logger.debug("Subscribed to all events")

    def unsubscribe_all_events(self, callback: Callable[[SeestarEvent], None]) -> None:
        """Stop receiving all events.

        Args:
            callback: Function to remove
        """
        if callback in self._all_events_callbacks:
            self._all_events_callbacks.remove(callback)
            self.logger.debug("Unsubscribed from all events")

    def subscribe_progress(self, callback: Callable[[float, Dict[str, Any]], None]) -> None:
        """Convenience method for progress updates only.

        Callback signature: (percent_complete: float, details: dict)

        Args:
            callback: Function to call with progress updates
        """
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)
            self.logger.debug("Subscribed to progress updates")

    def unsubscribe_progress(self, callback: Callable[[float, Dict[str, Any]], None]) -> None:
        """Stop receiving progress updates.

        Args:
            callback: Function to remove
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
            self.logger.debug("Unsubscribed from progress updates")

    def _update_status(self, **kwargs) -> None:
        """Update internal status and trigger callback."""
        # Log status changes to console for debugging
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

    def _load_private_key(self) -> None:
        """Load RSA private key for authentication.

        Only called when actually connecting to telescope.

        Raises:
            ConnectionError: If key file not found
        """
        if self._private_key_pem is not None:
            return  # Already loaded

        try:
            with open(self._private_key_path, "rb") as f:
                self._private_key_pem = f.read()
            self.logger.debug(f"Loaded Seestar private key from {self._private_key_path}")
        except FileNotFoundError:
            self.logger.error(f"Seestar private key not found at {self._private_key_path}")
            raise ConnectionError(
                f"Seestar authentication key not found at {self._private_key_path}. "
                "Please ensure the key file exists or set SEESTAR_PRIVATE_KEY_PATH environment variable."
            )

    def _sign_challenge(self, challenge_str: str) -> str:
        """Sign authentication challenge using RSA private key.

        This implements the authentication mechanism required by firmware 6.45+.
        The challenge is signed (not encrypted) using RSA-SHA1.

        Args:
            challenge_str: Challenge string from get_verify_str

        Returns:
            Base64-encoded signature
        """
        # Load the private key
        private_key = serialization.load_pem_private_key(
            self._private_key_pem, password=None, backend=default_backend()
        )

        # Sign the challenge using RSA-SHA1 (required by Seestar firmware protocol)
        # SHA1 used for RSA signing (not password hashing), required by hardware
        signature = private_key.sign(challenge_str.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1())  # nosec B303

        # Return base64-encoded signature
        return base64.b64encode(signature).decode("utf-8")

    async def _authenticate(self) -> None:
        """Perform 2-step authentication for firmware 6.45+.

        Step 1: Request challenge string via get_verify_str
        Step 2: Sign challenge and send via verify_client

        Raises:
            ConnectionError: If authentication fails
        """
        try:
            # Step 1: Get challenge string
            self.logger.info("Requesting authentication challenge...")
            challenge_response = await self._send_command("get_verify_str")

            challenge_str = challenge_response.get("result", {}).get("str", "")
            if not challenge_str:
                raise ConnectionError(f"No challenge string in response: {challenge_response}")

            self.logger.debug(f"Received challenge: {challenge_str}")

            # Step 2: Sign challenge and send verification
            self.logger.info("Signing challenge and authenticating...")
            signed_challenge = self._sign_challenge(challenge_str)

            verify_params = {"sign": signed_challenge, "data": challenge_str}

            verify_response = await self._send_command("verify_client", verify_params)

            # Check result
            result_code = verify_response.get("result", verify_response.get("code", -1))
            if result_code != 0:
                error = verify_response.get("error", "unknown error")
                raise ConnectionError(f"Authentication failed: {error} (code {result_code})")

            self.logger.info("Authentication successful")

        except Exception as e:
            raise ConnectionError(f"Authentication error: {e}")

    async def _send_udp_discovery(self) -> None:
        """Send UDP discovery broadcast for guest mode."""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)

            # Send discovery message with app version for firmware 6.45 compatibility
            message = {
                "id": 1,
                "method": "scan_iscope",
                "params": "",
                "app_version": "3.0.0",  # Pretend to be latest app version
                "protocol_version": "6.45",  # Match firmware version exactly
            }
            message_bytes = json.dumps(message).encode()

            addr = (self._host, self.UDP_DISCOVERY_PORT)
            self.logger.info(f"Sending UDP discovery to {addr}")
            sock.sendto(message_bytes, addr)

            # Try to receive response (optional)
            try:
                data, addr = sock.recvfrom(1024)
                self.logger.info(f"Received UDP response from {addr}: {data.decode()}")
            except socket.timeout:
                self.logger.debug("No UDP response (this is normal)")

            sock.close()

        except Exception as e:
            self.logger.warning(f"UDP discovery failed (non-critical): {e}")

    async def connect(self, host: str, port: int = DEFAULT_PORT) -> bool:
        """Connect to Seestar S50 telescope.

        Args:
            host: Hostname or IP address (e.g., "seestar.local" or "192.168.1.100")
            port: TCP port (default: 4700 for firmware v5.x)

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        if self._connected:
            self.logger.warning("Already connected")
            return True

        self._host = host
        self._port = port

        try:
            # Send UDP discovery first (for guest mode)
            await self._send_udp_discovery()

            # Establish TCP connection
            self.logger.info(f"Connecting to Seestar at {host}:{port}")

            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=self.CONNECTION_TIMEOUT
            )

            self._connected = True
            self._update_status(connected=True, state=SeestarState.CONNECTED)

            # Start receive task
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Start heartbeat task (keeps connection alive)
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self.logger.info("Connected to Seestar S50")

            # Load private key and authenticate for firmware 6.45+
            try:
                self._load_private_key()
                await self._authenticate()
            except Exception as e:
                await self.disconnect()
                raise ConnectionError(f"Authentication failed: {e}")

            # Query initial status
            try:
                await self.get_device_state()
            except Exception as e:
                self.logger.warning(f"Failed to get initial device state: {e}")

            return True

        except asyncio.TimeoutError:
            raise ConnectionError(f"Connection timeout to {host}:{port}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")

    async def disconnect(self) -> None:
        """Disconnect from telescope."""
        if not self._connected:
            return

        self.logger.info("Disconnecting from Seestar")

        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close writer
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

        self._connected = False
        self._reader = None
        self._writer = None
        self._pending_responses.clear()

        self._update_status(connected=False, state=SeestarState.DISCONNECTED)

        self.logger.info("Disconnected from Seestar")

    async def _heartbeat_loop(self) -> None:
        """Background task to send heartbeat (test_connection) every 2 seconds.

        Implements Android app's keepalive mechanism to prevent telescope from
        timing out and closing the connection.
        """
        try:
            while self._connected:
                await asyncio.sleep(2.0)  # Every 2 seconds like Android app

                if not self._connected:
                    break

                try:
                    # Send test_connection command (no params needed)
                    await self._send_command("test_connection", timeout=5.0)
                    self.logger.debug("Heartbeat sent successfully")
                except Exception as e:
                    self.logger.warning(f"Heartbeat failed: {e}")
                    # Don't break - let receive loop handle disconnect

        except asyncio.CancelledError:
            self.logger.debug("Heartbeat loop cancelled")
        except Exception as e:
            self.logger.error(f"Heartbeat loop error: {e}")

    async def _receive_loop(self) -> None:
        """Background task to receive and process messages from telescope."""
        try:
            while self._connected:
                # Read until newline
                line = await self._reader.readline()
                if not line:
                    self.logger.error("Connection closed by telescope")
                    break

                # Parse message
                try:
                    message = json.loads(line.decode().strip())
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {line}, error: {e}")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")

        except asyncio.CancelledError:
            self.logger.debug("Receive loop cancelled")
        except Exception as e:
            self.logger.error(f"Receive loop error: {e}")
            self._update_status(state=SeestarState.ERROR, last_error=str(e))
        finally:
            if self._connected:
                # Connection dropped - attempt auto-reconnect (Android app style)
                await self._handle_disconnect_and_reconnect()

    async def _handle_disconnect_and_reconnect(self) -> None:
        """Handle disconnection and attempt auto-reconnect.

        Implements Android app's reconnection logic:
        - Up to 3 retries if within 60 seconds of last disconnect
        - 300ms delay between retries
        - Reset counter if > 60 seconds since last disconnect
        """
        import time

        current_time = time.time()

        # Check if > 60 seconds since last disconnect (reset counter)
        if current_time - self._last_miss_time > self._reconnect_timeout:
            self._miss_time = 0

        self._last_miss_time = current_time

        # Check if we should attempt reconnect
        if self._miss_time >= self._max_retries:
            self.logger.error(f"Max reconnection attempts ({self._max_retries}) reached")
            await self.disconnect()
            self._update_status(state=SeestarState.ERROR, last_error="Connection lost - max retries exceeded")
            return

        # Increment retry counter
        self._miss_time += 1

        self.logger.info(f"Attempting auto-reconnect ({self._miss_time}/{self._max_retries})...")
        self._update_status(state=SeestarState.RECONNECTING)

        # Disconnect cleanly first
        await self.disconnect()

        # Wait before reconnecting (300ms like Android app)
        await asyncio.sleep(self._reconnect_delay)

        # Attempt to reconnect
        try:
            if self._host:
                await self.connect(self._host, self._port)
                self.logger.info("Auto-reconnect successful!")
                # Reset counter on successful reconnect
                self._miss_time = 0
        except Exception as e:
            self.logger.error(f"Auto-reconnect failed: {e}")
            # Don't reset miss_time - will retry on next disconnect if < max

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Process received message from telescope.

        Args:
            message: Parsed JSON message
        """
        # Log message
        method = message.get("method", "unknown")
        msg_id = message.get("id")

        if method == "scope_get_equ_coord":
            self.logger.debug(f"Received: {message}")
        else:
            self.logger.info(f"Received: {message}")

        # Check if this is a response to a pending command
        if msg_id is not None and msg_id in self._pending_responses:
            future = self._pending_responses.pop(msg_id)
            if not future.done():
                future.set_result(message)
            return  # This was a command response, not an event

        # Parse and dispatch as unsolicited event
        event = self._parse_event(message)
        if event:
            await self._dispatch_event(event)

    def _parse_event(self, message: Dict[str, Any]) -> Optional[SeestarEvent]:
        """Parse message as telescope event.

        Args:
            message: Raw message dict from telescope

        Returns:
            SeestarEvent if recognized, None otherwise
        """
        # Determine event type based on message structure
        method = message.get("method", "")
        result = message.get("result", {})

        event_type = EventType.UNKNOWN
        event_data = {}

        # Parse different event types
        if "progress" in result or "percent" in result:
            event_type = EventType.PROGRESS_UPDATE
            event_data = {
                "progress": result.get("progress", 0),
                "percent": result.get("percent", 0),
                "frame": result.get("frame", 0),
                "total_frames": result.get("total_frames", 0),
            }

        elif "state" in result:
            event_type = EventType.STATE_CHANGE
            event_data = {"state": result.get("state"), "stage": result.get("stage")}

        elif "error" in message or message.get("code", 0) != 0:
            event_type = EventType.ERROR
            event_data = {
                "error": message.get("error", "Unknown error"),
                "code": message.get("code", 0),
            }

        elif "stacked" in result or "image_ready" in result:
            event_type = EventType.IMAGE_READY
            event_data = {"filename": result.get("filename"), "path": result.get("path")}

        elif result.get("stage") == "Idle" or result.get("complete"):
            event_type = EventType.OPERATION_COMPLETE
            event_data = {"operation": result.get("operation"), "success": result.get("success", True)}

        # Create event
        return SeestarEvent(event_type=event_type, timestamp=datetime.now(), data=event_data, source_command=method)

    async def _dispatch_event(self, event: SeestarEvent) -> None:
        """Dispatch event to registered callbacks.

        Args:
            event: Event to dispatch
        """
        # Call all-events callbacks
        for callback in self._all_events_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in all-events callback: {e}")

        # Call event-type-specific callbacks
        for callback in self._event_callbacks.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in {event.event_type.value} callback: {e}")

        # Handle progress events specially for progress callbacks
        if event.event_type == EventType.PROGRESS_UPDATE:
            percent = event.data.get("percent", 0)
            details = event.data
            for progress_cb in self._progress_callbacks:
                try:
                    progress_cb(percent, details)
                except Exception as e:
                    self.logger.error(f"Error in progress callback: {e}")

    async def wait_for_goto_complete(self, timeout: float = 180.0) -> bool:
        """Wait for slew/goto operation to complete using events (not polling).

        Subscribes to STATE_CHANGE events and waits for telescope to enter
        TRACKING state, indicating the goto is complete.

        Args:
            timeout: Maximum time to wait in seconds (default: 3 minutes)

        Returns:
            True if goto completed successfully, False on timeout

        Example:
            await client.goto_target(10.0, 45.0, "M31")
            success = await client.wait_for_goto_complete(timeout=120.0)
            if success:
                print("Goto completed, telescope is tracking")
        """
        completion_event = asyncio.Event()
        success = False

        def state_callback(event: SeestarEvent):
            nonlocal success
            state = event.data.get("state")
            if state == SeestarState.TRACKING.value or state == "tracking":
                success = True
                completion_event.set()
            elif state in (SeestarState.CONNECTED.value, "connected", SeestarState.PARKED.value, "parked"):
                # Goto failed or was stopped
                success = False
                completion_event.set()

        # Subscribe to state change events
        self.subscribe_event(EventType.STATE_CHANGE, state_callback)

        try:
            # Wait for completion or timeout
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Goto operation timed out after {timeout}s")
            success = False
        finally:
            # Clean up subscription
            self.unsubscribe_event(EventType.STATE_CHANGE, state_callback)

        return success

    async def wait_for_focus_complete(self, timeout: float = 120.0) -> tuple[bool, Optional[float]]:
        """Wait for autofocus operation to complete using events.

        Subscribes to OPERATION_COMPLETE events and waits for autofocus to finish.

        Args:
            timeout: Maximum time to wait in seconds (default: 2 minutes)

        Returns:
            Tuple of (success: bool, focus_position: Optional[float])
            - success: True if autofocus completed successfully
            - focus_position: Final focus position if available, None otherwise

        Example:
            await client.auto_focus()
            success, position = await client.wait_for_focus_complete(timeout=90.0)
            if success:
                print(f"Autofocus complete at position {position}")
        """
        completion_event = asyncio.Event()
        success = False
        focus_position = None

        def operation_callback(event: SeestarEvent):
            nonlocal success, focus_position
            operation = event.data.get("operation", "")
            if "focus" in operation.lower() or event.source_command == "auto_focus":
                success = event.data.get("success", True)
                focus_position = event.data.get("position")
                completion_event.set()

        # Subscribe to operation complete events
        self.subscribe_event(EventType.OPERATION_COMPLETE, operation_callback)

        try:
            # Wait for completion or timeout
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Autofocus operation timed out after {timeout}s")
            success = False
        finally:
            # Clean up subscription
            self.unsubscribe_event(EventType.OPERATION_COMPLETE, operation_callback)

        return success, focus_position

    async def wait_for_imaging_complete(
        self,
        expected_frames: int,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        timeout: float = 3600.0,
    ) -> bool:
        """Wait for imaging session to reach expected frame count.

        Subscribes to PROGRESS_UPDATE events and tracks frame completion.
        Optionally calls progress_callback after each frame.

        Args:
            expected_frames: Number of frames to wait for
            progress_callback: Optional callback(frame_num, total_frames, percent)
                called after each frame is stacked
            timeout: Maximum time to wait in seconds (default: 1 hour)

        Returns:
            True if expected frames reached, False on timeout or error

        Example:
            def on_progress(current, total, percent):
                print(f"Stacked {current}/{total} frames ({percent:.1f}%)")

            await client.start_imaging(restart=True)
            success = await client.wait_for_imaging_complete(
                expected_frames=50,
                progress_callback=on_progress,
                timeout=1800.0
            )
        """
        completion_event = asyncio.Event()
        success = False
        current_frame = 0

        def imaging_progress_callback(event: SeestarEvent):
            nonlocal success, current_frame
            frame = event.data.get("frame", 0)
            total = event.data.get("total_frames", expected_frames)
            percent = event.data.get("percent", 0)

            current_frame = frame

            # Call user's progress callback if provided
            if progress_callback:
                try:
                    progress_callback(frame, total, percent)
                except Exception as e:
                    self.logger.error(f"Error in user progress callback: {e}")

            # Check if we've reached expected frames
            if frame >= expected_frames:
                success = True
                completion_event.set()

        # Subscribe to progress events
        self.subscribe_event(EventType.PROGRESS_UPDATE, imaging_progress_callback)

        try:
            # Wait for completion or timeout
            await asyncio.wait_for(completion_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Imaging session timed out after {timeout}s " f"(reached {current_frame}/{expected_frames} frames)"
            )
            success = False
        finally:
            # Clean up subscription
            self.unsubscribe_event(EventType.PROGRESS_UPDATE, imaging_progress_callback)

        return success

    async def _send_command(self, method: str, params: Any = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Send command to telescope and wait for response.

        Args:
            method: Command method name
            params: Command parameters (dict, list, or None)
            timeout: Command timeout in seconds (default: COMMAND_TIMEOUT)

        Returns:
            Response message dict

        Raises:
            ConnectionError: If not connected
            TimeoutError: If command times out
            CommandError: If command returns error
        """
        if not self._connected:
            raise ConnectionError("Not connected to telescope")

        # Generate command ID
        cmd_id = self._command_id
        self._command_id += 1

        # Build message with version info for firmware 6.x compatibility
        message = {"method": method, "id": cmd_id, "jsonrpc": "2.0"}  # Add JSON-RPC version
        if params is not None:
            message["params"] = params

        # Create future for response
        future = asyncio.Future()
        self._pending_responses[cmd_id] = future

        # Send message
        message_json = json.dumps(message) + "\r\n"

        if method == "scope_get_equ_coord":
            self.logger.debug(f"Sending: {message_json.strip()}")
        else:
            self.logger.info(f"Sending: {message_json.strip()}")

        try:
            self._writer.write(message_json.encode())
            await self._writer.drain()
        except Exception as e:
            self._pending_responses.pop(cmd_id, None)
            raise ConnectionError(f"Failed to send command: {e}")

        # Wait for response
        try:
            response = await asyncio.wait_for(future, timeout=timeout or self.COMMAND_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending_responses.pop(cmd_id, None)
            raise TimeoutError(f"Command timeout: {method}")

        # Check for error in response
        if "error" in response:
            error_msg = response.get("error", "Unknown error")
            error_code = response.get("code", 0)
            raise CommandError(f"Command failed: {error_msg} (code {error_code})")

        return response
