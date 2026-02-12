#!/usr/bin/env python3
"""Simple alt/az movement test script."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.clients.seestar_client import SeestarClient


async def get_scope_state(client):
    """Get scope state with alt/az and ra/dec."""
    response = await client._send_command("scope_get_state", {})
    result = response.get("result", {})
    return {
        "alt": result.get("alt", 0),
        "az": result.get("az", 0),
        "ra": result.get("ra", 0),
        "dec": result.get("dec", 0),
    }


async def wait_for_move_complete(client, timeout=30):
    """Wait for telescope to finish moving."""
    print("Waiting for move to complete...", end="", flush=True)
    start_time = asyncio.get_event_loop().time()

    while True:
        # Check if timeout
        if asyncio.get_event_loop().time() - start_time > timeout:
            print(" TIMEOUT!")
            return False

        # Get device state
        device_state = await client.get_device_state()
        mount = device_state.get("mount", {})
        move_type = mount.get("move_type", "none")

        # Check if idle
        if move_type == "none":
            print(" ✓ Done!")
            return True

        # Still moving
        print(".", end="", flush=True)
        await asyncio.sleep(0.5)


async def test_movement(client, direction, speed, description):
    """Test a single movement."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"Direction: {direction}, Speed: {speed}x")
    print("=" * 60)

    # Get position before
    state_before = await get_scope_state(client)
    print(f"Before:  Alt={state_before['alt']:.2f}°, Az={state_before['az']:.2f}°")
    print(f"         RA={state_before['ra']:.4f}h, Dec={state_before['dec']:.2f}°")

    # Execute move
    try:
        success = await client.move_scope(action=direction, speed=speed)
        if success:
            print("✓ Move command sent successfully")
        else:
            print("✗ Move command failed")
            return
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return

    # Wait for telescope to finish moving
    if not await wait_for_move_complete(client):
        print("Move did not complete in time")
        return

    # Get position after
    state_after = await get_scope_state(client)
    print(f"After:   Alt={state_after['alt']:.2f}°, Az={state_after['az']:.2f}°")
    print(f"         RA={state_after['ra']:.4f}h, Dec={state_after['dec']:.2f}°")

    # Calculate change
    alt_change = state_after["alt"] - state_before["alt"]
    az_change = state_after["az"] - state_before["az"]
    ra_change = (state_after["ra"] - state_before["ra"]) * 15.0
    dec_change = state_after["dec"] - state_before["dec"]
    print(f"Change:  ΔAlt={alt_change:.3f}°, ΔAz={az_change:.3f}°")
    print(f"         ΔRA={ra_change:.3f}°, ΔDec={dec_change:.3f}°")

    # Check if movement was significant
    expected_movement = 0.5 * speed  # Base offset * speed multiplier
    total_change = abs(alt_change) + abs(az_change)

    if total_change < 0.1:  # Less than 0.1° total change
        print("\n❌ PROBLEM DETECTED!")
        print(f"Expected movement: ~{expected_movement:.1f}°")
        print(f"Actual movement: {total_change:.3f}°")
        print("\nDEBUGGING INFO:")
        print(f"  scope_get_state returns Az={state_before['az']:.2f}° (always 0 - invalid!)")
        print(f"  RA/Dec ARE changing slightly: ΔRA={ra_change:.3f}°, ΔDec={dec_change:.3f}°")
        print("  This suggests:")
        print("    1. scope_get_state doesn't return valid Az in alt/az mode, OR")
        print("    2. Telescope is moving but not to the calculated alt/az position")
        print("\nStopping test to investigate...")
        return False

    return True


async def main():
    """Run movement tests."""

    print("Connecting to telescope at 192.168.2.47:4700...")
    client = SeestarClient()
    await client.connect(host="192.168.2.47", port=4700)
    print("✓ Connected!\n")

    # Check mode
    device_state = await client.get_device_state()
    mount = device_state.get("mount", {})
    is_equ = mount.get("equ_mode", False)
    print(f"Telescope mode: {'EQUATORIAL' if is_equ else 'ALT/AZ'}")

    if is_equ:
        print("\n⚠️  ERROR: Telescope is in equatorial mode!")
        print("Please switch to alt/az mode first:")
        print("  1. Park in alt/az mode: client.park(equ_mode=False)")
        print("  2. Unpark: client.unpark()")
        await client.disconnect()
        return

    print(f"Mount state: {mount}\n")

    print("⚠️  LARGE MOVEMENTS - Watch the telescope!")
    print("Starting in 3 seconds...")
    await asyncio.sleep(3)

    # Run tests - larger movements for visibility
    tests = [
        ("up", 10.0, "TEST 1: Move UP (5° altitude increase - LARGE)"),
        ("down", 10.0, "TEST 2: Move DOWN (5° altitude decrease - LARGE)"),
        ("left", 10.0, "TEST 3: Move LEFT (5° azimuth decrease - LARGE)"),
        ("right", 10.0, "TEST 4: Move RIGHT (5° azimuth increase - LARGE)"),
        ("up", 20.0, "TEST 5: Move UP VERY LARGE (10° altitude, 20x speed)"),
        ("right", 5.0, "TEST 6: Move RIGHT MEDIUM (2.5° azimuth, 5x speed)"),
    ]

    for direction, speed, description in tests:
        success = await test_movement(client, direction, speed, description)
        if success is False:
            print("\n⚠️  Test stopped due to problem detected.")
            break
        await asyncio.sleep(1)  # Brief pause between tests

    # Disconnect
    print(f"\n{'='*60}")
    print("Disconnecting...")
    await client.disconnect()
    print("✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
