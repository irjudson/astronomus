"""Public types for the Seestar S50 client.

Enums, dataclasses, and exceptions shared across all seestar submodules.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class SeestarState(Enum):
    """Telescope operation states."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"  # Auto-reconnect in progress
    SLEWING = "slewing"
    TRACKING = "tracking"
    FOCUSING = "focusing"
    IMAGING = "imaging"
    PARKING = "parking"
    PARKED = "parked"
    ERROR = "error"


class MountMode(Enum):
    """Mount coordinate system mode."""

    ALTAZ = "altaz"  # Alt/Az mode (default, no equatorial init needed)
    EQUATORIAL = "equatorial"  # Equatorial mode (requires initialization)
    UNKNOWN = "unknown"


@dataclass
class SeestarStatus:
    """Current telescope status."""

    connected: bool
    state: SeestarState
    current_ra_hours: Optional[float] = None
    current_dec_degrees: Optional[float] = None
    current_target: Optional[str] = None
    firmware_version: Optional[str] = None
    is_tracking: bool = False
    mount_mode: MountMode = MountMode.ALTAZ  # Default to alt/az
    equatorial_initialized: bool = False  # Whether equatorial system is aligned/homed
    last_error: Optional[str] = None
    last_update: Optional[datetime] = None


class SeestarClientError(Exception):
    """Base exception for Seestar client errors."""

    pass


class ConnectionError(SeestarClientError):
    """Raised when connection to telescope fails."""

    pass


class CommandError(SeestarClientError):
    """Raised when a telescope command fails."""

    pass


class TimeoutError(SeestarClientError):
    """Raised when a command times out."""

    pass


class EventType(Enum):
    """Known event types from S50."""

    PROGRESS_UPDATE = "progress"  # Frame count, percentage updates
    STATE_CHANGE = "state"  # Device state transitions
    ERROR = "error"  # Operation errors
    IMAGE_READY = "image"  # Stacking complete, image available
    OPERATION_COMPLETE = "complete"  # Goto/focus/imaging done
    UNKNOWN = "unknown"  # Unrecognized event type


@dataclass
class SeestarEvent:
    """Represents unsolicited event from telescope."""

    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source_command: Optional[str] = None
