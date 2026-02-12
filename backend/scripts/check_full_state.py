#!/usr/bin/env python3
"""Check full telescope state."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def check_state():
    """Check full state."""
    client = SeestarClient()

    try:
        print("Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print("Connected.\n")

        # Check app state
        print("=== APP STATE ===")
        response = await client._send_command("iscope_get_app_state", {})
        app_state = response.get("result", {})
        print(json.dumps(app_state, indent=2))

        print("\n=== MOUNT MODE ===")
        mode_response = await client._send_command("scope_get_mode", {})
        print(f"Mount mode: {mode_response.get('result', 'unknown')}")

        print("\n=== TRACKING ===")
        track_response = await client._send_command("scope_get_track_state", {})
        print(f"Tracking: {track_response.get('result', False)}")

        print("\n=== VIEW STATE ===")
        view_response = await client._send_command("get_view_state", {})
        view_state = view_response.get("result", {}).get("View", {})
        print(f"View state: {view_state.get('state', 'unknown')}")
        print(f"View stage: {view_state.get('stage', 'none')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(check_state())
