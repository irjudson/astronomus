#!/usr/bin/env python3
"""Recover telescope from locked state and test movement.

This script:
1. Cancels any active ViewPlan/operation
2. Explicitly sets mount to Alt/Az mode
3. Tests movement with detailed coordinate monitoring
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import MountMode, SeestarClient


async def recover_and_test():
    """Recover telescope state and test movement."""
    client = SeestarClient()

    try:
        print("=" * 60)
        print("TELESCOPE STATE RECOVERY & MOVEMENT TEST")
        print("=" * 60)

        # Connect
        print("\n[1] Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Get current state
        print("[2] Getting current state...")
        device_state = await client._send_command("get_device_state", {})
        view_state = await client._send_command("get_view_state", {})

        print("Device state summary:")
        print(f"  - equ_mode: {device_state.get('result', {}).get('equ_mode')}")
        print(f"  - Mount tracking: {device_state.get('result', {}).get('mount', {}).get('tracking')}")
        print(f"  - Mount closed: {device_state.get('result', {}).get('mount', {}).get('close')}")

        print("\nView state summary:")
        print(f"  - State: {view_state.get('result', {}).get('View', {}).get('state')}")
        print(f"  - Stage: {view_state.get('result', {}).get('View', {}).get('stage')}")
        print()

        # Cancel any active operation
        print("[3] Canceling any active operations...")
        try:
            cancel_response = await client._send_command("iscope_cancel_view", {})
            print(f"  Cancel view response: {cancel_response}")
        except Exception as e:
            print(f"  Cancel view error (may be expected): {e}")

        # Stop any active plan
        try:
            stop_plan_response = await client._send_command("stop_view_plan", {})
            print(f"  Stop plan response: {stop_plan_response}")
        except Exception as e:
            print(f"  Stop plan error (may be expected): {e}")

        # Stop any imaging
        try:
            stop_imaging_response = await client._send_command("scope_imaging_stop", {})
            print(f"  Stop imaging response: {stop_imaging_response}")
        except Exception as e:
            print(f"  Stop imaging error (may be expected): {e}")

        print("✓ Cleanup commands sent\n")

        # Wait for operations to settle
        print("[4] Waiting 3 seconds for operations to settle...")
        await asyncio.sleep(3)

        # Explicitly set mount mode to Alt/Az
        print("[5] Setting mount mode to Alt/Az...")
        client._update_status(mount_mode=MountMode.ALTAZ, equatorial_initialized=False)
        print("✓ Mount mode set to Alt/Az (no initialization needed)\n")

        # Get current coordinates
        print("[6] Getting current coordinates...")
        current_coords = await client.get_current_coordinates()
        print("Current position:")
        print(f"  RA: {current_coords['ra']:.4f} hours")
        print(f"  Dec: {current_coords['dec']:.4f}°\n")

        # Calculate test position (10 degrees in azimuth from current)
        from datetime import datetime

        import astropy.units as u
        from astropy.coordinates import AltAz, EarthLocation, SkyCoord
        from astropy.time import Time

        lat = 45.729
        lon = -111.4857
        elevation = 1300

        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())

        # Current position to Alt/Az
        coord = SkyCoord(ra=current_coords["ra"] * u.hourangle, dec=current_coords["dec"] * u.deg, frame="icrs")
        altaz_frame = AltAz(obstime=obs_time, location=location)
        current_altaz = coord.transform_to(altaz_frame)

        print("Current Alt/Az position:")
        print(f"  Azimuth: {current_altaz.az.deg:.2f}°")
        print(f"  Altitude: {current_altaz.alt.deg:.2f}°\n")

        # Test position: 10 degrees east in azimuth
        test_az = current_altaz.az.deg + 10
        test_alt = current_altaz.alt.deg

        print("[7] Testing movement to:")
        print(f"  Target Azimuth: {test_az:.2f}°")
        print(f"  Target Altitude: {test_alt:.2f}°")
        print("  (Movement: +10° in azimuth)\n")

        # Send movement command
        print("Sending move_to_horizon command...")
        response = await client._send_command("scope_move_to_horizon", [test_az, test_alt])
        print(f"Response: {response}\n")

        if response.get("code") != 0:
            print(f"✗ Command rejected with code {response.get('code')}")
            print("Possible reasons:")
            print("  - Telescope in protected state")
            print("  - Mount motors disabled")
            print("  - Physical obstruction")
            return

        print("✓ Command accepted!")
        print("\n[8] Monitoring coordinates for 15 seconds...")
        print("Time | RA (hours) | Dec (°) | Az (°) | Alt (°) | Status")
        print("-" * 70)

        # Monitor for 15 seconds
        moved = False
        for i in range(15):
            await asyncio.sleep(1)

            # Get new coordinates
            new_coords = await client.get_current_coordinates()
            new_coord = SkyCoord(ra=new_coords["ra"] * u.hourangle, dec=new_coords["dec"] * u.deg, frame="icrs")
            new_obs_time = Time(datetime.utcnow())
            new_altaz_frame = AltAz(obstime=new_obs_time, location=location)
            new_altaz = new_coord.transform_to(new_altaz_frame)

            # Check if coordinates changed
            ra_diff = abs(new_coords["ra"] - current_coords["ra"])
            dec_diff = abs(new_coords["dec"] - current_coords["dec"])
            az_diff = abs(new_altaz.az.deg - current_altaz.az.deg)
            alt_diff = abs(new_altaz.alt.deg - current_altaz.alt.deg)

            status = (
                "MOVING!" if (ra_diff > 0.001 or dec_diff > 0.01 or az_diff > 0.1 or alt_diff > 0.1) else "No change"
            )
            if status == "MOVING!" and not moved:
                moved = True
                print(
                    f"{i+1:2d}s  | {new_coords['ra']:9.4f} | {new_coords['dec']:7.3f} | "
                    f"{new_altaz.az.deg:6.2f} | {new_altaz.alt.deg:6.2f} | *** {status} ***"
                )
            elif i % 3 == 0:  # Print every 3 seconds
                print(
                    f"{i+1:2d}s  | {new_coords['ra']:9.4f} | {new_coords['dec']:7.3f} | "
                    f"{new_altaz.az.deg:6.2f} | {new_altaz.alt.deg:6.2f} | {status}"
                )

        print()

        # Final check
        final_coords = await client.get_current_coordinates()
        final_coord = SkyCoord(ra=final_coords["ra"] * u.hourangle, dec=final_coords["dec"] * u.deg, frame="icrs")
        final_obs_time = Time(datetime.utcnow())
        final_altaz_frame = AltAz(obstime=final_obs_time, location=location)
        final_altaz = final_coord.transform_to(final_altaz_frame)

        ra_change = abs(final_coords["ra"] - current_coords["ra"])
        dec_change = abs(final_coords["dec"] - current_coords["dec"])
        az_change = abs(final_altaz.az.deg - current_altaz.az.deg)
        alt_change = abs(final_altaz.alt.deg - current_altaz.alt.deg)

        print("=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(f"Initial RA:  {current_coords['ra']:.4f}h → Final RA:  {final_coords['ra']:.4f}h (Δ {ra_change:.4f}h)")
        print(
            f"Initial Dec: {current_coords['dec']:.3f}° → Final Dec: {final_coords['dec']:.3f}° (Δ {dec_change:.3f}°)"
        )
        print(f"Initial Az:  {current_altaz.az.deg:.2f}° → Final Az:  {final_altaz.az.deg:.2f}° (Δ {az_change:.2f}°)")
        print(
            f"Initial Alt: {current_altaz.alt.deg:.2f}° → Final Alt: {final_altaz.alt.deg:.2f}° (Δ {alt_change:.2f}°)"
        )
        print()

        if ra_change > 0.01 or dec_change > 0.1 or az_change > 0.5 or alt_change > 0.5:
            print("✓✓✓ TELESCOPE MOVED! ✓✓✓")
            print("Coordinates changed - telescope is responding to commands.")
        else:
            print("✗✗✗ NO MOVEMENT DETECTED ✗✗✗")
            print("\nTelescope accepts commands but does not physically move.")
            print("\nPOSSIBLE CAUSES:")
            print("1. ViewPlan still active (needs official app to fully cancel)")
            print("2. Mount motors disabled or in protective state")
            print("3. Physical obstruction or safety interlock")
            print("4. Telescope needs restart to clear internal state")
            print("5. Mount calibration lost (needs homing)")
            print("\nRECOMMENDED NEXT STEPS:")
            print("A. Try official Seestar app to see if it can move the telescope")
            print("B. If official app works, compare our command sequence")
            print("C. If official app doesn't work, restart telescope hardware")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected from telescope")


if __name__ == "__main__":
    asyncio.run(recover_and_test())
