"""Backward-compatible re-export for the Seestar S50 client.

All public symbols are now defined in app.clients.seestar.
This module exists so existing code (``from app.clients.seestar_client import SeestarClient``)
continues to work without modification.
"""

from app.clients.seestar import (  # noqa: F401
    CommandError,
    ConnectionError,
    EventType,
    MountMode,
    SeestarClient,
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
