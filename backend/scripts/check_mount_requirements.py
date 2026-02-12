#!/usr/bin/env python3
"""Check mount requirements for scope_goto."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def check_requirements():
    """Check what's needed for scope_goto to work."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("MOUNT REQUIREMENTS CHECK")
        print("=" * 70)

        print("\n1. Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("   ✓ Connected")

        print("\n2. Checking mount mode...")
        mode_response = await client._send_command("scope_get_mode", {})
        mount_mode = mode_response.get("result", "unknown")
        print(f"   Mount mode: {mount_mode}")

        print("\n3. Checking tracking state...")
        track_response = await client._send_command("scope_get_track_state", {})
        is_tracking = track_response.get("result", False)
        track_code = track_response.get("track_code")
        track_error = track_response.get("track_error")
        print(f"   Tracking: {is_tracking}")
        if track_code:
            print(f"   Track code: {track_code}")
        if track_error:
            print(f"   Track error: {track_error}")

        print("\n4. Checking mount capabilities...")
        cap_response = await client._send_command("scope_get_cap", {})
        capabilities = cap_response.get("result", {})
        print(f"   Capabilities: {capabilities}")

        print("\n5. Checking if scope is moving...")
        moving_response = await client._send_command("scope_is_moving", {})
        is_moving = moving_response.get("result", "unknown")
        print(f"   Is moving: {is_moving}")

        print("\n6. Checking view state...")
        view_response = await client._send_command("get_view_state", {})
        view_state = view_response.get("result", {}).get("View", {})
        view_state_str = view_state.get("state", "unknown")
        view_stage = view_state.get("stage", "none")
        print(f"   View state: {view_state_str}")
        print(f"   View stage: {view_stage}")

        print("\n7. Checking mount state...")
        try:
            mount_response = await client._send_command("scope_get_mount_state", {})
            mount_state = mount_response.get("result", {})
            print(f"   Mount state: {mount_state}")
        except Exception as e:
            print(f"   (scope_get_mount_state not available: {e})")

        print("\n8. Checking axis coordinates...")
        axle_response = await client._send_command("scope_get_axle_coord", {})
        axle_coords = axle_response.get("result", [])
        print(f"   Axis coords: {axle_coords}")

        # Attempt scope_goto to see what happens
        print("\n9. Testing scope_goto (RA=18.615h, Dec=38.783°)...")
        try:
            test_response = await client._send_command("scope_goto", [18.615, 38.783])
            print(f"   Response: {test_response}")

            if test_response.get("code") == 207:
                print("\n   ✗ ERROR 207: fail to operate")
                print("   This typically means:")
                print("   - Mount is not ready for goto")
                print("   - Tracking system not initialized")
                print("   - View/imaging mode is active")
                print("   - Mount needs to be homed/aligned first")
        except Exception as e:
            print(f"   Exception: {e}")

        # Check if we need to set tracking mode
        print("\n10. Checking tracking mode...")
        try:
            track_mode_response = await client._send_command("scope_get_track_mode", {})
            track_mode = track_mode_response.get("result", "unknown")
            print(f"   Track mode: {track_mode}")
        except Exception as e:
            print(f"   (scope_get_track_mode not available: {e})")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Mount mode: {mount_mode}")
        print(f"Tracking: {is_tracking}")
        print(f"Is moving: {is_moving}")
        print(f"View state: {view_state_str}")
        print(f"View stage: {view_stage}")

        print("\nRECOMMENDATIONS:")
        if view_state_str == "working":
            print("- Stop active view with iscope_stop_view")
        if not is_tracking:
            print("- Enable tracking with scope_set_track_state")
        if mount_mode == "az":
            print("- Mount in alt/az mode - may need equatorial mode for scope_goto")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(check_requirements())
