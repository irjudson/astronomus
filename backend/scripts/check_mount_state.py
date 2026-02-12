#!/usr/bin/env python3
"""Check telescope mount state to diagnose motion issues."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def check_mount_state():
    """Check mount state."""
    client = SeestarClient()

    try:
        print("Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Get app state
        print("Getting app state...")
        response = await client._send_command("iscope_get_app_state", {})
        print(f"App state: {response}\n")

        # Get mount state
        print("Getting mount state...")
        response = await client._send_command("get_mount_state", {})
        print(f"Mount state: {response}\n")

        # Check if mount is closed/parked
        if response.get("state", {}).get("close"):
            print("⚠️  MOUNT IS CLOSED/PARKED!")
            print("   This prevents movement. Try opening/unparking the mount.\n")

        # Get device state
        print("Getting device state...")
        response = await client._send_command("get_device_state", {})
        print(f"Device state: {response}\n")

        # Try a small test movement
        print("Testing small movement (5° in azimuth)...")
        current_coords = await client.get_current_coordinates()
        print(f"Current: RA={current_coords['ra']:.3f}h, Dec={current_coords['dec']:.3f}°")

        # Try move_to_horizon with a position 5 degrees away
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

        test_az = current_altaz.az.deg + 5  # 5 degrees east
        test_alt = current_altaz.alt.deg

        print(f"Sending move_to_horizon: Az={test_az:.1f}°, Alt={test_alt:.1f}°")
        response = await client._send_command("scope_move_to_horizon", [test_az, test_alt])
        print(f"Response: {response}")

        if response.get("code") == 0:
            print("✓ Command accepted - wait 5 seconds...")
            await asyncio.sleep(5)

            # Check if position changed
            new_coords = await client.get_current_coordinates()
            print(f"New position: RA={new_coords['ra']:.3f}h, Dec={new_coords['dec']:.3f}°")

            if new_coords["ra"] != current_coords["ra"] or new_coords["dec"] != current_coords["dec"]:
                print("✓✓✓ TELESCOPE MOVED!")
            else:
                print("✗ Position unchanged - telescope did not move")
                print("\nPossible causes:")
                print("  1. Mount is in closed/parked state")
                print("  2. Mount motors are disabled")
                print("  3. Physical obstruction")
                print("  4. Mount calibration needed")
        else:
            print(f"✗ Command rejected: code={response.get('code')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(check_mount_state())
