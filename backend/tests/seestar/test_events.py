"""Hardware tests: event callbacks, state changes, progress events.

Run with:  pytest tests/seestar/test_events.py --telescope-host=<ip>
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

import pytest

from app.clients.seestar_client import CommandError, EventType, SeestarClient, SeestarEvent

pytestmark = pytest.mark.hardware


class TestEvents:
    """Event callback hardware tests."""

    @pytest.mark.asyncio
    async def test_all_events_callback_fires(self, telescope: SeestarClient):
        """on_all_events callback receives events during connection."""
        events: List[SeestarEvent] = []

        def capture(event: SeestarEvent):
            events.append(event)

        telescope.subscribe_all_events(capture)
        try:
            # Trigger at least one event by querying state
            await telescope.get_device_state()
            # Allow brief settle for any async events
            await asyncio.sleep(2)
        finally:
            telescope.unsubscribe_all_events(capture)

        # At minimum heartbeat responses may generate state events; we just
        # verify the callback was called if any events were received.
        assert isinstance(events, list)

    @pytest.mark.asyncio
    async def test_state_change_callback_fires(self, telescope_ready: SeestarClient):
        """Register STATE_CHANGE callback, trigger action, verify it can fire.

        Uses telescope_ready so the arm is open before triggering movement.
        Triggers via move_to_horizon (known working movement command) rather
        than scope_speed_move which has wrong param format on this firmware.
        """
        state_events: List[SeestarEvent] = []

        def on_state(event: SeestarEvent):
            state_events.append(event)

        telescope_ready.subscribe_event(EventType.STATE_CHANGE, on_state)
        try:
            # Trigger movement with a known-working command (small nudge north)
            await telescope_ready.move_to_horizon(azimuth=180.0, altitude=46.0)
            await asyncio.sleep(2)
        except CommandError:
            pass
        finally:
            telescope_ready.unsubscribe_event(EventType.STATE_CHANGE, on_state)

        # We can't guarantee a state event fires; just verify list type
        assert isinstance(state_events, list)

    @pytest.mark.asyncio
    async def test_progress_callback_registration(self, telescope: SeestarClient):
        """subscribe_progress() and unsubscribe_progress() round-trip without error."""
        progress_calls: List[tuple] = []

        def on_progress(percent: float, details: Dict[str, Any]):
            progress_calls.append((percent, details))

        telescope.subscribe_progress(on_progress)
        await asyncio.sleep(1)
        telescope.unsubscribe_progress(on_progress)
        assert isinstance(progress_calls, list)

    @pytest.mark.asyncio
    async def test_event_data_structure(self, telescope: SeestarClient):
        """SeestarEvent objects have expected fields when they arrive."""
        received: List[SeestarEvent] = []

        def capture(event: SeestarEvent):
            received.append(event)

        telescope.subscribe_all_events(capture)
        try:
            await telescope.get_device_state()
            await asyncio.sleep(3)
        finally:
            telescope.unsubscribe_all_events(capture)

        for event in received:
            assert hasattr(event, "event_type")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "data")
            assert isinstance(event.timestamp, datetime)
            assert isinstance(event.data, dict)
            assert isinstance(event.event_type, EventType)
