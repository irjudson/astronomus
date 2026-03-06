"""Seestar S50 client package."""

from .types import (
    SeestarState,
    MountMode,
    SeestarStatus,
    SeestarClientError,
    ConnectionError,
    CommandError,
    TimeoutError,
    EventType,
    SeestarEvent,
)
from .client import SeestarClient

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
