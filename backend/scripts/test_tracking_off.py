#!/usr/bin/env python3
"""Test goto with tracking OFF."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def test_tracking_off():
    """Test if turning tracking OFF allows goto to work."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TEST: Goto with Tracking OFF")
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

        # Check current tracking state
        print("\n3. Checking current tracking state...")
        track_response = await client._send_command("scope_get_track_state", {})
        is_tracking = track_response.get("result", False)
        print(f"   Current tracking: {is_tracking}")

        # Turn tracking OFF
        if is_tracking:
            print("\n4. Turning tracking OFF...")
            off_response = await client._send_command("scope_set_track_state", [False])
            print(f"   Response: result={off_response.get('result')}, code={off_response.get('code')}")

            await asyncio.sleep(2)

            # Verify
            verify_response = await client._send_command("scope_get_track_state", {})
            is_tracking_now = verify_response.get("result", False)
            print(f"   Tracking now: {is_tracking_now}")

        # Try scope_goto with tracking OFF
        print("\n5. Testing scope_goto with tracking OFF...")
        print("   Target: RA=18.615h, Dec=38.783° (Vega)")

        try:
            goto_response = await client._send_command("scope_goto", [18.615, 38.783])
            print(f"   Goto response: result={goto_response.get('result')}, code={goto_response.get('code')}")

            if goto_response.get("code") == 0:
                print("   ✓✓✓ scope_goto ACCEPTED with tracking OFF!")
                print("\nThis was the issue - tracking needs to be OFF for goto!")

                # Get initial position
                coords_before = await client.get_current_coordinates()
                print(f"\n   Position before: RA={coords_before['ra']:.3f}h, Dec={coords_before['dec']:.3f}°")

                # Wait for movement
                print("\n6. Waiting 30 seconds for slew...")
                await asyncio.sleep(30)

                # Check final position
                coords_after = await client.get_current_coordinates()
                print(f"   Position after: RA={coords_after['ra']:.3f}h, Dec={coords_after['dec']:.3f}°")

                # Check if moved
                if coords_before["ra"] != coords_after["ra"] or coords_before["dec"] != coords_after["dec"]:
                    ra_error = abs(coords_after["ra"] - 18.615)
                    dec_error = abs(coords_after["dec"] - 38.783)
                    print(f"\n   Error: ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

                    if ra_error < 0.1 and dec_error < 1.0:
                        print("\n   ✓✓✓ SLEW SUCCESSFUL!")
                        return True
                    else:
                        print("\n   ✓ Telescope MOVED but not at exact target")
                        return True
                else:
                    print("\n   ✗ Telescope did not move")
                    return False

            elif goto_response.get("code") == 207:
                print("   ✗ Still error 207 even with tracking OFF")
                print("   There must be another factor...")
                return False
            else:
                print(f"   ✗ Goto failed: {goto_response}")
                return False

        except Exception as e:
            print(f"   ✗ Exception: {e}")
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
    result = asyncio.run(test_tracking_off())
    print("\n" + "=" * 70)
    sys.exit(0 if result else 1)
