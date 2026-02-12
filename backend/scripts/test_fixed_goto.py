#!/usr/bin/env python3
"""Test the fixed goto_target method that automatically handles mount mode."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import MountMode, SeestarClient


async def test_fixed_goto():
    """Test goto with automatic mount mode handling."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TESTING FIXED GOTO_TARGET METHOD")
        print("(Should automatically clear polar alignment if needed)")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Set to alt/az mode (default)
        print("[2] Setting client to alt/az mode...")
        client._update_status(mount_mode=MountMode.ALTAZ, equatorial_initialized=False)
        print(f"✓ Client mount mode: {client.status.mount_mode.value}\n")

        # Target: Somewhere visible in the sky
        print("[3] Testing goto_target() with automatic mode handling...")
        print("    Target: Arbitrary sky position (RA=6h, Dec=10°)")
        print("    ** WATCH THE TELESCOPE - IT SHOULD MOVE **\n")

        # This should automatically call clear_polar_align if needed
        success = await client.goto_target(ra_hours=6.0, dec_degrees=10.0, target_name="Test Target")

        if success:
            print("\n✓ goto_target() succeeded!")
            print("Monitoring position for 15 seconds...\n")

            initial = await client.get_current_coordinates()
            print(f"Initial: RA={initial['ra']:.4f}h, Dec={initial['dec']:.3f}°")

            max_ra_change = 0
            max_dec_change = 0

            for i in range(15):
                await asyncio.sleep(1)
                coords = await client.get_current_coordinates()
                ra_change = abs(coords["ra"] - initial["ra"])
                dec_change = abs(coords["dec"] - initial["dec"])
                max_ra_change = max(max_ra_change, ra_change)
                max_dec_change = max(max_dec_change, dec_change)

                if i % 3 == 0:
                    status = "MOVING" if (ra_change > 0.1 or dec_change > 1.0) else "tracking"
                    print(f"{i+1}s: RA={coords['ra']:.4f}h, Dec={coords['dec']:.3f}° - {status}")

            final = await client.get_current_coordinates()
            print(f"\nFinal: RA={final['ra']:.4f}h, Dec={final['dec']:.3f}°")
            print(f"Max changes: ΔRA={max_ra_change:.4f}h, ΔDec={max_dec_change:.3f}°")

            if max_ra_change > 0.1 or max_dec_change > 1.0:
                print("\n✓✓✓ SUCCESS - TELESCOPE MOVED! ✓✓✓")
                print("The automatic mount mode handling is working!")
            else:
                print("\n⚠️  Small or no movement detected")
        else:
            print("\n✗ goto_target() failed")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_fixed_goto())
