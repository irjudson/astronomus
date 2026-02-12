#!/usr/bin/env python3
"""Test goto with alt/az coordinate conversion."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def test_altaz_goto():
    """Test goto using alt/az conversion."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TEST: Goto with Alt/Az Conversion")
        print("=" * 70)

        print("\n1. Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("   ✓ Connected")

        # Get initial position
        print("\n2. Current position:")
        coords_before = await client.get_current_coordinates()
        print(f"   RA: {coords_before['ra']:.3f}h, Dec: {coords_before['dec']:.3f}°")

        # Slew to Vega using alt/az mode (default)
        print("\n3. Slewing to Vega (RA=18.615h, Dec=38.783°)")
        print("   Using alt/az coordinate conversion...")

        success = await client.goto_target(
            ra_hours=18.615, dec_degrees=38.783, target_name="Vega", use_altaz=True  # Use alt/az mode (default)
        )

        if success:
            print("   ✓ Goto command succeeded!")

            # Wait for movement
            print("\n4. Waiting 30 seconds for slew...")
            await asyncio.sleep(30)

            # Check final position
            print("\n5. Final position:")
            coords_after = await client.get_current_coordinates()
            print(f"   RA: {coords_after['ra']:.3f}h, Dec: {coords_after['dec']:.3f}°")

            # Check if it moved
            if coords_before["ra"] != coords_after["ra"] or coords_before["dec"] != coords_after["dec"]:
                ra_diff = abs(coords_after["ra"] - coords_before["ra"])
                dec_diff = abs(coords_after["dec"] - coords_before["dec"])

                print("\n   ✓✓✓ TELESCOPE MOVED!")
                print(f"   Movement: ΔRA={ra_diff:.3f}h ({ra_diff*15:.1f}°), ΔDec={dec_diff:.3f}°")

                # Check accuracy
                ra_error = abs(coords_after["ra"] - 18.615)
                dec_error = abs(coords_after["dec"] - 38.783)
                print("\n   Target accuracy:")
                print("   Expected: RA=18.615h, Dec=38.783°")
                print(f"   Actual:   RA={coords_after['ra']:.3f}h, Dec={coords_after['dec']:.3f}°")
                print(f"   Error:    ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

                return True
            else:
                print("\n   ✗ Telescope did not move")
                return False
        else:
            print("   ✗ Goto command failed")
            return False

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_altaz_goto())
    print("\n" + "=" * 70)
    if result:
        print("SUCCESS: Slew works with alt/az coordinate conversion!")
    else:
        print("FAILED: Still investigating...")
    print("=" * 70)
    sys.exit(0 if result else 1)
