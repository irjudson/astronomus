#!/usr/bin/env python3
"""Test movement using the proper high-level goto command sequence."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from app.clients.seestar_client import MountMode, SeestarClient


async def test_proper_goto():
    """Test using iscope_start_view which is what the official app uses."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TESTING PROPER GOTO COMMAND SEQUENCE")
        print("(Using iscope_start_view like official Seestar app)")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Cancel any active operations first
        print("[2] Canceling any active operations...")
        try:
            await client._send_command("iscope_cancel_view", {})
            print("✓ Canceled view")
        except:
            print("  (No active view to cancel)")

        await asyncio.sleep(2)

        # Set mount mode to Alt/Az (no equatorial initialization)
        print("\n[3] Setting mount mode to Alt/Az...")
        client._update_status(mount_mode=MountMode.ALTAZ, equatorial_initialized=False)
        print("✓ Mount mode: Alt/Az (no equatorial init needed)\n")

        # Get current position
        print("[4] Current position...")
        current_coords = await client.get_current_coordinates()

        lat = 45.729
        lon = -111.4857
        elevation = 1300
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())

        coord = SkyCoord(ra=current_coords["ra"] * u.hourangle, dec=current_coords["dec"] * u.deg, frame="icrs")
        altaz_frame = AltAz(obstime=obs_time, location=location)
        current_altaz = coord.transform_to(altaz_frame)

        print(f"  RA: {current_coords['ra']:.4f}h, Dec: {current_coords['dec']:.3f}°")
        print(f"  Az: {current_altaz.az.deg:.2f}°, Alt: {current_altaz.alt.deg:.2f}°\n")

        # Pick a target with visible coordinates
        # Betelgeuse (should be visible from Montana in winter evening)
        print("[5] Target: Betelgeuse (α Ori)")
        target_ra = 5.92  # hours
        target_dec = 7.4  # degrees
        target_name = "Betelgeuse"

        # Calculate its current Alt/Az
        target_coord = SkyCoord(ra=target_ra * u.hourangle, dec=target_dec * u.deg, frame="icrs")
        target_altaz = target_coord.transform_to(altaz_frame)

        print(f"  RA: {target_ra:.4f}h, Dec: {target_dec:.3f}°")
        print(f"  Az: {target_altaz.az.deg:.2f}°, Alt: {target_altaz.alt.deg:.2f}°")

        if target_altaz.alt.deg < 0:
            print(f"  ⚠️  Warning: Target is below horizon (Alt={target_altaz.alt.deg:.1f}°)")
            print("  Will still command - telescope should reject or do nothing")
        else:
            print("  ✓ Target is above horizon")
        print()

        # Test 1: Use iscope_start_view with mode="star" (what official app uses)
        print("[6] TEST 1: Using iscope_start_view (official app method)")
        print("    Command: iscope_start_view with mode='star'")

        params = {
            "mode": "star",
            "target_ra_dec": [target_ra, target_dec],
            "target_name": target_name,
            "lp_filter": False,
        }

        print(f"    Params: {params}")
        response = await client._send_command("iscope_start_view", params)
        print(f"    Response: code={response.get('code')}, result={response.get('result')}")

        if response.get("code") != 0:
            print("\n    ✗ Command rejected!")
            print(f"    Error code: {response.get('code')}")

            # Check if it's the mount state issue
            device_state = await client.get_device_state()
            mount = device_state.get("mount", {})
            view_state = await client._send_command("get_view_state", {})

            print("\n    Device diagnostics:")
            print(f"      mount.close: {mount.get('close')}")
            print(f"      mount.tracking: {mount.get('tracking')}")
            print(f"      View.state: {view_state.get('result', {}).get('View', {}).get('state')}")
            return

        print("\n    ✓ Command accepted!")
        print("\n[7] Monitoring for 20 seconds...")
        print("    ** WATCH THE TELESCOPE **\n")

        print("Time | RA (h) | Dec (°) | Az (°)  | Alt (°) | Change")
        print("-" * 70)

        initial_ra = current_coords["ra"]
        initial_dec = current_coords["dec"]
        initial_az = current_altaz.az.deg
        initial_alt = current_altaz.alt.deg

        max_ra_change = 0
        max_dec_change = 0
        max_az_change = 0
        max_alt_change = 0

        for i in range(20):
            await asyncio.sleep(1)

            # Get new position
            new_coords = await client.get_current_coordinates()
            new_coord = SkyCoord(ra=new_coords["ra"] * u.hourangle, dec=new_coords["dec"] * u.deg, frame="icrs")
            new_obs_time = Time(datetime.utcnow())
            new_altaz_frame = AltAz(obstime=new_obs_time, location=location)
            new_altaz = new_coord.transform_to(new_altaz_frame)

            # Calculate changes from initial
            ra_change = abs(new_coords["ra"] - initial_ra)
            dec_change = abs(new_coords["dec"] - initial_dec)
            az_change = abs(new_altaz.az.deg - initial_az)
            alt_change = abs(new_altaz.alt.deg - initial_alt)

            max_ra_change = max(max_ra_change, ra_change)
            max_dec_change = max(max_dec_change, dec_change)
            max_az_change = max(max_az_change, az_change)
            max_alt_change = max(max_alt_change, alt_change)

            # Status
            if ra_change > 0.05 or dec_change > 0.5 or az_change > 2.0 or alt_change > 2.0:
                status = "*** MOVING ***"
            elif ra_change > 0.001 or az_change > 0.1:
                status = "drift"
            else:
                status = "no change"

            if i % 2 == 0 or status == "*** MOVING ***":
                print(
                    f"{i+1:2d}s  | {new_coords['ra']:6.3f} | {new_coords['dec']:7.3f} | "
                    f"{new_altaz.az.deg:7.2f} | {new_altaz.alt.deg:7.2f} | {status}"
                )

        print("\n" + "=" * 70)
        print("RESULTS:")
        print("=" * 70)

        final_coords = await client.get_current_coordinates()
        final_coord = SkyCoord(ra=final_coords["ra"] * u.hourangle, dec=final_coords["dec"] * u.deg, frame="icrs")
        final_obs_time = Time(datetime.utcnow())
        final_altaz_frame = AltAz(obstime=final_obs_time, location=location)
        final_altaz = final_coord.transform_to(final_altaz_frame)

        print(f"Target:  {target_name}")
        print(f"  Commanded: RA={target_ra:.4f}h, Dec={target_dec:.3f}°")
        print(f"  Current Az/Alt: Az={target_altaz.az.deg:.2f}°, Alt={target_altaz.alt.deg:.2f}°\n")

        print("Initial position:")
        print(f"  RA={initial_ra:.4f}h, Dec={initial_dec:.3f}°")
        print(f"  Az={initial_az:.2f}°, Alt={initial_alt:.2f}°\n")

        print("Final position:")
        print(f"  RA={final_coords['ra']:.4f}h, Dec={final_coords['dec']:.3f}°")
        print(f"  Az={final_altaz.az.deg:.2f}°, Alt={final_altaz.alt.deg:.2f}°\n")

        print("Maximum changes observed:")
        print(f"  ΔRA={max_ra_change:.4f}h, ΔDec={max_dec_change:.3f}°")
        print(f"  ΔAz={max_az_change:.2f}°, ΔAlt={max_alt_change:.2f}°\n")

        if max_az_change > 5.0 or max_alt_change > 5.0:
            print("✓✓✓ SUCCESS - TELESCOPE MOVED! ✓✓✓")
        elif max_az_change > 0.5 or max_alt_change > 0.5:
            print("⚠️  PARTIAL - Small movement detected")
            print("   Telescope may be moving but blocked or limited")
        else:
            print("✗✗✗ NO MOVEMENT ✗✗✗")
            print("\nNext steps:")
            print("1. Try goto_target() method (handles mode conversion automatically)")
            print("2. Check if mount needs initialization sequence")
            print("3. May need to send 'actionScope_Start' first")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_proper_goto())
