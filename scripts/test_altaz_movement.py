#!/usr/bin/env python3
"""Test script for alt/az telescope movement.

Tests directional movement in alt/az mode with different speeds.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.clients.seestar_client import SeestarClient


async def main():
    """Test alt/az movement."""

    # Connect to telescope
    print("Connecting to telescope...")
    client = SeestarClient()
    await client.connect(host="192.168.2.47", port=4700)
    print("Connected!")

    # Check current mode
    print("\nChecking telescope mode...")
    device_state = await client.get_device_state()
    mount = device_state.get("mount", {})
    is_equ = mount.get("equ_mode", False)
    print(f"Equatorial mode: {is_equ}")

    if is_equ:
        print("\n⚠️  Telescope is in EQUATORIAL mode!")
        response = input("Switch to alt/az mode? (y/n): ")
        if response.lower() == "y":
            print("Parking in alt/az mode...")
            await client.park(equ_mode=False)
            await asyncio.sleep(3)
            print("Unparking...")
            await client.unpark()
            await asyncio.sleep(2)
        else:
            print("Exiting.")
            await client.disconnect()
            return

    # Get current position
    print("\nGetting current position...")
    coords = await client.get_current_coordinates()
    ra = coords.get("ra_hours", 0)
    dec = coords.get("dec_degrees", 0)
    print(f"Current RA/Dec: {ra:.4f}h, {dec:.2f}°")

    # Test movements
    print("\n" + "=" * 60)
    print("MOVEMENT TESTS")
    print("=" * 60)

    movements = [
        ("up", 1.0, "Move UP (0.5° altitude)"),
        ("down", 1.0, "Move DOWN (0.5° altitude)"),
        ("left", 1.0, "Move LEFT (0.5° azimuth)"),
        ("right", 1.0, "Move RIGHT (0.5° azimuth)"),
        ("up", 2.0, "Move UP FAST (1.0° altitude)"),
        ("right", 0.5, "Move RIGHT SLOW (0.25° azimuth)"),
    ]

    for direction, speed, description in movements:
        print(f"\n{description}")
        print(f"Direction: {direction}, Speed: {speed}x")

        # Get position before
        coords_before = await client.get_current_coordinates()
        ra_before = coords_before.get("ra_hours", 0)
        dec_before = coords_before.get("dec_degrees", 0)
        print(f"  Before: RA={ra_before:.4f}h, Dec={dec_before:.2f}°")

        # Execute move
        print("  Executing move...")
        try:
            success = await client.move_scope(action=direction, speed=speed)
            if success:
                print("  ✓ Move command sent")
            else:
                print("  ✗ Move command failed")
                continue
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

        # Wait for move to complete
        await asyncio.sleep(3)

        # Get position after
        coords_after = await client.get_current_coordinates()
        ra_after = coords_after.get("ra_hours", 0)
        dec_after = coords_after.get("dec_degrees", 0)
        print(f"  After:  RA={ra_after:.4f}h, Dec={dec_after:.2f}°")

        # Calculate change
        ra_change = (ra_after - ra_before) * 15.0  # Convert hours to degrees
        dec_change = dec_after - dec_before
        print(f"  Change: ΔRA={ra_change:.3f}°, ΔDec={dec_change:.3f}°")

        # Pause between tests
        response = input("\n  Continue to next test? (y/n): ")
        if response.lower() != "y":
            break

    # Disconnect
    print("\nDisconnecting...")
    await client.disconnect()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
