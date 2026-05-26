#!/usr/bin/env python3
"""Test scope_move with RA/Dec in alt/az mode."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.clients.seestar_client import SeestarClient


async def get_scope_state(client):
    """Get scope state with all coordinates."""
    response = await client._send_command("scope_get_state", {})
    result = response.get("result", {})
    return {
        "alt": result.get("alt", 0),
        "az": result.get("az", 0),
        "ra": result.get("ra", 0),
        "dec": result.get("dec", 0),
    }


async def main():
    """Test RA/Dec movement in alt/az mode."""

    print("Connecting...")
    client = SeestarClient()
    await client.connect(host="192.168.2.47", port=4700)
    print("✓ Connected!\n")

    # Check mode
    device_state = await client.get_device_state()
    mount = device_state.get("mount", {})
    is_equ = mount.get("equ_mode", False)
    print(f"Mode: {'EQUATORIAL' if is_equ else 'ALT/AZ'}\n")

    # Get current position
    state = await get_scope_state(client)
    current_ra = state["ra"]
    current_dec = state["dec"]
    print("Current position:")
    print(f"  RA={current_ra:.4f}h ({current_ra*15:.2f}°)")
    print(f"  Dec={current_dec:.2f}°")
    print(f"  Alt={state['alt']:.2f}°")
    print(f"  Az={state['az']:.2f}°\n")

    # Test 1: Move UP in Dec by 5°
    print("=" * 60)
    print("TEST 1: Move UP (increase Dec by 5°)")
    print("=" * 60)
    target_ra = current_ra
    target_dec = current_dec + 5.0
    print(f"Target: RA={target_ra:.4f}h, Dec={target_dec:.2f}°")

    # Use scope_move with RA/Dec
    params = {"action": "slew", "ra": target_ra, "dec": target_dec}
    response = await client._send_command("scope_move", params)
    print(f"Response: code={response.get('code')}, result={response.get('result')}")

    if response.get("code") == 0:
        print("✓ Command accepted, waiting for movement...")

        # Wait for idle
        while True:
            device_state = await client.get_device_state()
            mount = device_state.get("mount", {})
            if mount.get("move_type") == "none":
                print("✓ Movement complete!")
                break
            print(".", end="", flush=True)
            await asyncio.sleep(0.5)

        # Check new position
        state_after = await get_scope_state(client)
        print("\nNew position:")
        print(f"  RA={state_after['ra']:.4f}h ({state_after['ra']*15:.2f}°)")
        print(f"  Dec={state_after['dec']:.2f}°")
        print(f"  Alt={state_after['alt']:.2f}°")
        print(f"  Az={state_after['az']:.2f}°")

        dec_change = state_after["dec"] - current_dec
        print(f"\nChange: ΔDec={dec_change:.3f}° (expected ~5.0°)")

        if abs(dec_change - 5.0) < 0.5:
            print("✓ SUCCESS! Movement worked as expected!")
        else:
            print("✗ Problem: Dec didn't change by expected amount")
    else:
        print(f"✗ Command failed with code {response.get('code')}")

    print("\nDisconnecting...")
    await client.disconnect()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
