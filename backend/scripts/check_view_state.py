#!/usr/bin/env python3
"""Check telescope view state."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def check_view_state():
    """Check view state and stop if active."""
    client = SeestarClient()

    try:
        print("Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print(f"Connected. State: {client.status.state}\n")

        # Check view state
        print("Checking view state...")
        response = await client._send_command("get_view_state", {})
        print(f"View state response: {response}\n")

        view_state = response.get("result", {})
        if view_state:
            print(f"View state: {view_state}")

            # Check if viewing is active
            state = view_state.get("state", "unknown")
            print(f"Current state: {state}")

            if state != "idle":
                print("\n--- View is ACTIVE. Attempting to stop view... ---")
                stop_response = await client._send_command("iscope_stop_view", {})
                print(f"Stop view response: {stop_response}")

                await asyncio.sleep(2)
                check_response = await client._send_command("get_view_state", {})
                print(f"View state after stop: {check_response}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(check_view_state())
