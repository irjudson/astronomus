"""Seestar S50 client package."""

from .client import SeestarClient
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

__all__ = [
    "SeestarClient",
    "SeestarState",
    "MountMode",
    "SeestarStatus",
    "SeestarClientError",
    "ConnectionError",
    "CommandError",
    "TimeoutError",
    "EventType",
    "SeestarEvent",
]
