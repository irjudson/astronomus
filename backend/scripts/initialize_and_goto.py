#!/usr/bin/env python3
"""Initialize mount properly and test goto."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def initialize_and_goto():
    """Initialize mount with go_home, then test goto."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("INITIALIZE MOUNT AND TEST GOTO")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Check current mount state
        print("[2] Checking mount state...")
        device_state = await client.get_device_state()
        mount = device_state.get("mount", {})
        print(f"  equ_mode: {mount.get('equ_mode')}")
        print(f"  tracking: {mount.get('tracking')}")
        print(f"  close: {mount.get('close')}")
        print(f"  go_home_flag: {mount.get('go_home_flag')}\n")

        # Initialize equatorial mode with mount_go_home
        print("[3] Initializing mount with mount_go_home...")
        print("    This will move the telescope to home position")
        print("    ** WATCH THE TELESCOPE - IT SHOULD MOVE NOW **")
        print()

        response = await client._send_command("mount_go_home", {})
        print(f"    Response: code={response.get('code')}, result={response.get('result')}")

        if response.get("code") != 0:
            print(f"    ✗ mount_go_home failed with code {response.get('code')}")
            return

        print("    ✓ mount_go_home accepted!")
        print("    Waiting 60 seconds for homing to complete...\n")

        # Monitor during homing
        for i in range(6):
            await asyncio.sleep(10)
            coords = await client.get_current_coordinates()
            device_state = await client.get_device_state()
            mount = device_state.get("mount", {})
            print(
                f"    {(i+1)*10}s: RA={coords['ra']:.4f}h, Dec={coords['dec']:.3f}°, "
                f"mount.go_home_flag={mount.get('go_home_flag')}, "
                f"mount.tracking={mount.get('tracking')}"
            )

        print("\n[4] Homing complete. Checking mount state...")
        device_state = await client.get_device_state()
        mount = device_state.get("mount", {})
        print(f"  equ_mode: {mount.get('equ_mode')}")
        print(f"  tracking: {mount.get('tracking')}")
        print(f"  go_home_flag: {mount.get('go_home_flag')}\n")

        # Now try goto with initialized mount
        print("[5] Testing goto with initialized mount...")
        print("    Target: Az=180°, Alt=45° (South, halfway up)")

        response = await client._send_command("scope_move_to_horizon", [180.0, 45.0])
        print(f"    Response: code={response.get('code')}")

        if response.get("code") == 0:
            print("    ✓ Command accepted!")
            print("    ** WATCH THE TELESCOPE **")
            print("    Monitoring for 15 seconds...\n")

            initial = await client.get_current_coordinates()
            for i in range(15):
                await asyncio.sleep(1)
                coords = await client.get_current_coordinates()
                ra_change = abs(coords["ra"] - initial["ra"])
                dec_change = abs(coords["dec"] - initial["dec"])

                if i % 3 == 0:
                    status = "MOVING" if (ra_change > 0.01 or dec_change > 0.1) else "no change"
                    print(f"    {i+1}s: RA={coords['ra']:.4f}h, Dec={coords['dec']:.3f}° - {status}")

            final = await client.get_current_coordinates()
            ra_change = abs(final["ra"] - initial["ra"])
            dec_change = abs(final["dec"] - initial["dec"])

            print(f"\n    Changes: ΔRA={ra_change:.4f}h, ΔDec={dec_change:.3f}°")

            if ra_change > 0.1 or dec_change > 1.0:
                print("    ✓✓✓ TELESCOPE MOVED! ✓✓✓")
            else:
                print("    ✗ Still no movement")
        else:
            print(f"    ✗ Command rejected with code {response.get('code')}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(initialize_and_goto())
