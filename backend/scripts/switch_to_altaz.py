#!/usr/bin/env python3
"""Switch mount to alt/az mode using scope_park."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def switch_to_altaz():
    """Switch to alt/az mode."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("SWITCH MOUNT TO ALT/AZ MODE")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Check current state
        print("[2] Current mount state...")
        device_state = await client.get_device_state()
        mount = device_state.get("mount", {})
        print(f"  equ_mode: {mount.get('equ_mode')}")
        print(f"  tracking: {mount.get('tracking')}")
        print(f"  close: {mount.get('close')}\n")

        # Cancel any active view
        print("[3] Canceling active view...")
        try:
            await client._send_command("iscope_cancel_view", {})
            print("✓ View canceled")
            await asyncio.sleep(2)
        except:
            print("  (No active view)")

        # Use scope_park with equ_mode=false to switch to alt/az
        print("\n[4] Switching to alt/az mode using scope_park...")
        print("    (scope_park with equ_mode=false)")
        response = await client._send_command("scope_park", {"equ_mode": False})
        print(f"    Response: code={response.get('code')}, result={response.get('result')}")

        if response.get("code") != 0:
            print(f"    ✗ Failed with code {response.get('code')}")
            return

        print("    ✓ Park command accepted!")
        print("    Waiting 10 seconds for park to complete...\n")

        for i in range(10):
            await asyncio.sleep(1)
            if i % 2 == 0:
                device_state = await client.get_device_state()
                mount = device_state.get("mount", {})
                print(
                    f"    {i+1}s: equ_mode={mount.get('equ_mode')}, "
                    f"close={mount.get('close')}, tracking={mount.get('tracking')}"
                )

        # Check final state
        print("\n[5] Final mount state...")
        device_state = await client.get_device_state()
        mount = device_state.get("mount", {})
        print(f"  equ_mode: {mount.get('equ_mode')}")
        print(f"  tracking: {mount.get('tracking')}")
        print(f"  close: {mount.get('close')}\n")

        if mount.get("equ_mode") == False:
            print("✓✓✓ SUCCESS - Mount switched to alt/az mode!")

            # Now unpark if needed
            if mount.get("close") == True:
                print("\n[6] Mount is parked. Unparking...")
                # Try to unpark by starting a view
                response = await client._send_command(
                    "iscope_start_view",
                    {
                        "mode": "star",
                        "target_ra_dec": [6.0, 10.0],  # Arbitrary target
                        "target_name": "Test",
                        "lp_filter": False,
                    },
                )
                print(f"    Response: code={response.get('code')}")
                await asyncio.sleep(3)

                device_state = await client.get_device_state()
                mount = device_state.get("mount", {})
                print(f"    Mount close: {mount.get('close')}")

            # Test movement
            print("\n[7] Testing movement in alt/az mode...")
            print("    Target: Az=180°, Alt=45°")

            response = await client._send_command("scope_move_to_horizon", [180.0, 45.0])
            print(f"    Response: code={response.get('code')}")

            if response.get("code") == 0:
                print("    ✓ Command accepted!")
                print("    ** WATCH THE TELESCOPE **")
                print("    Monitoring for 15 seconds...\n")

                initial = await client.get_current_coordinates()
                max_change = 0

                for i in range(15):
                    await asyncio.sleep(1)
                    coords = await client.get_current_coordinates()
                    ra_change = abs(coords["ra"] - initial["ra"])
                    dec_change = abs(coords["dec"] - initial["dec"])
                    max_change = max(max_change, ra_change, dec_change)

                    if i % 3 == 0:
                        status = "MOVING" if (ra_change > 0.01 or dec_change > 0.1) else "drift"
                        print(f"    {i+1}s: RA={coords['ra']:.4f}h, Dec={coords['dec']:.3f}° - {status}")

                print(f"\n    Max change observed: {max_change:.4f}")

                if max_change > 0.1:
                    print("    ✓✓✓ TELESCOPE MOVED! ✓✓✓")
                else:
                    print("    ✗ Still no movement")
        else:
            print("✗ Mount still in equatorial mode")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(switch_to_altaz())
