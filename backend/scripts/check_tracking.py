#!/usr/bin/env python3
"""Check telescope tracking state."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def check_tracking():
    """Check tracking state."""
    client = SeestarClient()

    try:
        print("Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print(f"Connected. State: {client.status.state}\n")

        # Check tracking state
        print("Checking tracking state...")
        response = await client._send_command("scope_get_track_state", {})
        print(f"Track state response: {response}")

        is_tracking = response.get("result", False)
        track_code = response.get("track_code")
        track_error = response.get("track_error")

        print(f"\nTracking: {is_tracking}")
        if track_code:
            print(f"Track code: {track_code}")
        if track_error:
            print(f"Track error: {track_error}")

        # If not tracking, try to enable it
        if not is_tracking:
            print("\n--- Tracking is OFF. Attempting to enable tracking... ---")
            enable_response = await client._send_command("scope_set_track_state", [True])
            print(f"Enable tracking response: {enable_response}")

            # Check again
            await asyncio.sleep(2)
            check_response = await client._send_command("scope_get_track_state", {})
            print(f"Track state after enable: {check_response}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(check_tracking())
