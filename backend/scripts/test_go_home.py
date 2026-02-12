#!/usr/bin/env python3
"""Test goto after homing the mount."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def test_go_home():
    """Test homing the mount first, then goto."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TEST: Mount Go Home + Goto")
        print("=" * 70)

        print("\n1. Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("   ✓ Connected")

        # Stop any active view
        print("\n2. Stopping any active view...")
        try:
            await client._send_command("iscope_stop_view", {})
            await asyncio.sleep(2)
            print("   ✓ View stopped")
        except:
            print("   (No active view)")

        # Execute mount_go_home
        print("\n3. Sending mount_go_home command...")
        print("   This initializes the mount's equatorial coordinate system")

        try:
            home_response = await client._send_command("mount_go_home", {})
            print(f"   Response: result={home_response.get('result')}, code={home_response.get('code')}")

            if home_response.get("code") == 0:
                print("   ✓ Go home command accepted!")

                # Wait for homing to complete
                print("\n4. Waiting for homing to complete (may take 30-60 seconds)...")
                await asyncio.sleep(45)

                # Check position after homing
                coords_after_home = await client.get_current_coordinates()
                print(
                    f"   Position after homing: RA={coords_after_home['ra']:.3f}h, Dec={coords_after_home['dec']:.3f}°"
                )

                # Now try scope_goto
                print("\n5. Testing scope_goto after homing...")
                print("   Target: RA=18.615h, Dec=38.783° (Vega)")

                goto_response = await client._send_command("scope_goto", [18.615, 38.783])
                print(f"   Goto response: result={goto_response.get('result')}, code={goto_response.get('code')}")

                if goto_response.get("code") == 0:
                    print("   ✓✓✓ scope_goto ACCEPTED after homing!")

                    # Wait for slew
                    print("\n6. Waiting 30 seconds for slew...")
                    await asyncio.sleep(30)

                    # Check final position
                    coords_final = await client.get_current_coordinates()
                    print(f"   Final position: RA={coords_final['ra']:.3f}h, Dec={coords_final['dec']:.3f}°")

                    ra_error = abs(coords_final["ra"] - 18.615)
                    dec_error = abs(coords_final["dec"] - 38.783)
                    print(f"   Error: ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

                    if ra_error < 0.1 and dec_error < 1.0:
                        print("\n   ✓✓✓ SLEW SUCCESSFUL!")
                        print("\n   === SOLUTION FOUND ===")
                        print("   Mount needs to be homed before equatorial goto works!")
                        return True
                    elif (
                        coords_after_home["ra"] != coords_final["ra"] or coords_after_home["dec"] != coords_final["dec"]
                    ):
                        print("\n   ✓ Telescope MOVED - closer but not exact")
                        return True
                    else:
                        print("\n   ✗ Telescope did not move")
                        return False
                elif goto_response.get("code") == 207:
                    print("   ✗ Still error 207 even after homing")
                    print("   May need additional initialization...")
                    return False
                else:
                    print(f"   ✗ Goto failed: {goto_response}")
                    return False

            else:
                print(f"   ✗ Go home command failed: {home_response}")
                return False

        except Exception as e:
            print(f"   ✗ Exception during go_home: {e}")
            import traceback

            traceback.print_exc()
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
    result = asyncio.run(test_go_home())
    print("\n" + "=" * 70)
    sys.exit(0 if result else 1)
