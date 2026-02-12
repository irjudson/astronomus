#!/usr/bin/env python3
"""Test simple movement - just move up in altitude."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from app.clients.seestar_client import MountMode, SeestarClient


async def test_simple_movement():
    """Test simple movement."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("SIMPLE MOVEMENT TEST")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Set mount mode
        client._update_status(mount_mode=MountMode.ALTAZ, equatorial_initialized=False)

        # Get current position
        print("[2] Current position...")
        current_coords = await client.get_current_coordinates()

        lat = 45.729
        lon = -111.4857
        elevation = 1300
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())

        coord = SkyCoord(ra=current_coords["ra"] * u.hourangle, dec=current_coords["dec"] * u.deg, frame="icrs")
        altaz_frame = AltAz(obstime=obs_time, location=location)
        current_altaz = coord.transform_to(altaz_frame)

        print(f"  Az: {current_altaz.az.deg:.2f}°, Alt: {current_altaz.alt.deg:.2f}°")

        # Try three different movement commands in sequence

        # Test 1: Move to zenith (straight up)
        print("\n[3] TEST 1: Move to zenith (Az=0°, Alt=85°)")
        print("    (Nearly straight up in the sky)")
        response = await client._send_command("scope_move_to_horizon", [0.0, 85.0])
        print(f"    Response: code={response.get('code')}")

        if response.get("code") == 0:
            print("    ✓ Command accepted - waiting 10 seconds...")
            for i in range(10):
                await asyncio.sleep(1)
                coords = await client.get_current_coordinates()
                c = SkyCoord(ra=coords["ra"] * u.hourangle, dec=coords["dec"] * u.deg, frame="icrs")
                t = Time(datetime.utcnow())
                af = AltAz(obstime=t, location=location)
                aa = c.transform_to(af)
                if i % 2 == 0:
                    print(f"    {i+1}s: Az={aa.az.deg:.2f}°, Alt={aa.alt.deg:.2f}°")

        # Test 2: Move to moderate altitude, south direction
        print("\n[4] TEST 2: Move to moderate altitude (Az=180°, Alt=45°)")
        print("    (Halfway up in southern sky)")
        response = await client._send_command("scope_move_to_horizon", [180.0, 45.0])
        print(f"    Response: code={response.get('code')}")

        if response.get("code") == 0:
            print("    ✓ Command accepted - waiting 10 seconds...")
            for i in range(10):
                await asyncio.sleep(1)
                coords = await client.get_current_coordinates()
                c = SkyCoord(ra=coords["ra"] * u.hourangle, dec=coords["dec"] * u.deg, frame="icrs")
                t = Time(datetime.utcnow())
                af = AltAz(obstime=t, location=location)
                aa = c.transform_to(af)
                if i % 2 == 0:
                    print(f"    {i+1}s: Az={aa.az.deg:.2f}°, Alt={aa.alt.deg:.2f}°")

        # Test 3: Move to low altitude, east
        print("\n[5] TEST 3: Move to low altitude (Az=90°, Alt=30°)")
        print("    (Low in eastern sky)")
        response = await client._send_command("scope_move_to_horizon", [90.0, 30.0])
        print(f"    Response: code={response.get('code')}")

        if response.get("code") == 0:
            print("    ✓ Command accepted - waiting 10 seconds...")
            for i in range(10):
                await asyncio.sleep(1)
                coords = await client.get_current_coordinates()
                c = SkyCoord(ra=coords["ra"] * u.hourangle, dec=coords["dec"] * u.deg, frame="icrs")
                t = Time(datetime.utcnow())
                af = AltAz(obstime=t, location=location)
                aa = c.transform_to(af)
                if i % 2 == 0:
                    print(f"    {i+1}s: Az={aa.az.deg:.2f}°, Alt={aa.alt.deg:.2f}°")

        # Check device state for any clues
        print("\n[6] Checking device state...")
        device_state = await client._send_command("get_device_state", {})
        result = device_state.get("result", {})

        print("  Mount state:")
        mount = result.get("mount", {})
        print(f"    - close: {mount.get('close')}")
        print(f"    - tracking: {mount.get('tracking')}")
        print(f"    - go_home_flag: {mount.get('go_home_flag')}")

        print("\n  Device general:")
        print(f"    - working_state: {result.get('working_state')}")
        print(f"    - equ_mode: {result.get('equ_mode')}")

        # Final position
        print("\n[7] Final position...")
        final_coords = await client.get_current_coordinates()
        c = SkyCoord(ra=final_coords["ra"] * u.hourangle, dec=final_coords["dec"] * u.deg, frame="icrs")
        t = Time(datetime.utcnow())
        af = AltAz(obstime=t, location=location)
        final_altaz = c.transform_to(af)

        print(f"  Az: {final_altaz.az.deg:.2f}°, Alt: {final_altaz.alt.deg:.2f}°")

        print("\n" + "=" * 70)
        print("SUMMARY:")
        print("=" * 70)
        print(f"Initial: Az={current_altaz.az.deg:.2f}°, Alt={current_altaz.alt.deg:.2f}°")
        print(f"Final:   Az={final_altaz.az.deg:.2f}°, Alt={final_altaz.alt.deg:.2f}°")
        print(
            f"Change:  ΔAz={abs(final_altaz.az.deg - current_altaz.az.deg):.2f}°, "
            f"ΔAlt={abs(final_altaz.alt.deg - current_altaz.alt.deg):.2f}°"
        )

        print("\n**Did you see the telescope physically move?**")
        print("\nIf YES → Commands are working, telescope is responding")
        print("If NO → Telescope is locked/disabled - try official Seestar app")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_simple_movement())
