#!/usr/bin/env python3
"""Test goto with longer wait and position monitoring."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def test_long_slew():
    """Test goto with position monitoring."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TEST: Long Slew with Position Monitoring")
        print("=" * 70)

        print("\n1. Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("   ✓ Connected")

        # Get initial position
        print("\n2. Initial position:")
        coords_initial = await client.get_current_coordinates()
        print(f"   RA: {coords_initial['ra']:.3f}h, Dec: {coords_initial['dec']:.3f}°")

        # Target: Vega
        target_ra = 18.615
        target_dec = 38.783

        # Slew to Vega
        print(f"\n3. Slewing to Vega (RA={target_ra}h, Dec={target_dec}°)")
        success = await client.goto_target(
            ra_hours=target_ra, dec_degrees=target_dec, target_name="Vega", use_altaz=True
        )

        if not success:
            print("   ✗ Goto command failed")
            return False

        print("   ✓ Goto command succeeded!")

        # Monitor position every 10 seconds
        print("\n4. Monitoring position (checking every 10 seconds for 2 minutes)...")
        prev_ra = coords_initial["ra"]
        prev_dec = coords_initial["dec"]

        for i in range(12):  # 12 checks over 2 minutes
            await asyncio.sleep(10)

            coords = await client.get_current_coordinates()
            ra = coords["ra"]
            dec = coords["dec"]

            # Calculate movement since last check
            ra_moved = abs(ra - prev_ra)
            dec_moved = abs(dec - prev_dec)

            # Calculate error from target
            ra_error = abs(ra - target_ra)
            dec_error = abs(dec - target_dec)

            print(f"\n   {(i+1)*10}s: RA={ra:.3f}h, Dec={dec:.3f}°")
            print(f"       Moved: ΔRA={ra_moved:.4f}h ({ra_moved*15:.2f}°), ΔDec={dec_moved:.3f}°")
            print(f"       Error: ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

            # Check if we've reached target
            if ra_error < 0.1 and dec_error < 1.0:
                print(f"\n   ✓✓✓ REACHED TARGET at {(i+1)*10}s!")
                print(f"   Final position: RA={ra:.3f}h, Dec={dec:.3f}°")
                return True

            # Check if still moving
            if ra_moved < 0.001 and dec_moved < 0.1:
                print("\n   Movement stopped. Final position:")
                print(f"   RA={ra:.3f}h, Dec={dec:.3f}°")
                print(f"   Error: ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

                if ra_error > 1.0 or dec_error > 5.0:
                    print("\n   ✗ Did not reach target - stopped too far away")
                    return False
                else:
                    print("\n   ✓ Close enough to target!")
                    return True

            prev_ra = ra
            prev_dec = dec

        # Timeout after 2 minutes
        print("\n   ⚠ Timeout after 2 minutes")
        coords_final = await client.get_current_coordinates()
        ra_final_error = abs(coords_final["ra"] - target_ra)
        dec_final_error = abs(coords_final["dec"] - target_dec)

        print(f"   Final: RA={coords_final['ra']:.3f}h, Dec={coords_final['dec']:.3f}°")
        print(f"   Error: ΔRA={ra_final_error:.3f}h ({ra_final_error*15:.1f}°), ΔDec={dec_final_error:.3f}°")

        if ra_final_error < 0.1 and dec_final_error < 1.0:
            print("\n   ✓ Within acceptable error range")
            return True
        else:
            print("\n   ✗ Not at target after 2 minutes")
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
    result = asyncio.run(test_long_slew())
    print("\n" + "=" * 70)
    sys.exit(0 if result else 1)
