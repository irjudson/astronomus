#!/usr/bin/env python3
"""Test telescope slew after reboot."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from app.clients.seestar_client import SeestarClient


async def test_slew():
    """Test slewing to Vega."""
    client = SeestarClient()

    # Montana location (from user preferences)
    lat = 45.729
    lon = -111.4857
    elevation = 1300  # meters

    try:
        print("=" * 70)
        print("TELESCOPE SLEW TEST - POST REBOOT")
        print("=" * 70)

        print("\n1. Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print(f"   ✓ Connected. Current state: {client.status.state}")

        # Unpark if needed
        if "PARKED" in str(client.status.state):
            print("\n2. Telescope is parked. Unparking...")
            # Unpark by moving to horizon position (south, 45° altitude)
            await client.move_to_horizon(azimuth=180.0, altitude=45.0)
            await asyncio.sleep(5)  # Wait for unpark to complete
            print(f"   ✓ Unpark command sent. State: {client.status.state}")

        # Calculate current position of Vega
        print("\n3. Calculating Vega position...")
        vega_coord = SkyCoord(ra=279.23 * u.deg, dec=38.783 * u.deg, frame="icrs")
        ra_hours = vega_coord.ra.hour
        dec_degrees = vega_coord.dec.deg

        # Calculate altitude
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())
        altaz_frame = AltAz(obstime=obs_time, location=location)
        altaz_coord = vega_coord.transform_to(altaz_frame)

        print("   Target: Vega")
        print(f"   RA: {ra_hours:.3f}h ({vega_coord.ra.deg:.2f}°)")
        print(f"   Dec: {dec_degrees:.3f}°")
        print(f"   Alt: {altaz_coord.alt.deg:.2f}°")
        print(f"   Az: {altaz_coord.az.deg:.2f}°")

        if altaz_coord.alt.deg < 20:
            print(f"   ⚠ WARNING: Vega is low (alt={altaz_coord.alt.deg:.1f}°). May not be visible.")

        # Get current position before slew
        print("\n4. Current telescope position:")
        coords_before = await client.get_current_coordinates()
        current_ra = coords_before.get("ra", 0)
        current_dec = coords_before.get("dec", 0)
        print(f"   RA: {current_ra:.3f}h")
        print(f"   Dec: {current_dec:.3f}°")

        # Slew to Vega using low-level scope_goto (no viewing mode activation)
        print("\n5. Sending slew command to Vega (using scope_goto)...")
        success = await client.scope_goto(ra_hours, dec_degrees)
        print(f"   Command result: {'ACCEPTED' if success else 'FAILED'}")

        if not success:
            print("\n   ✗ Slew command failed!")
            return False

        # Wait for slew to complete
        print("\n6. Waiting 30 seconds for slew to complete...")
        await asyncio.sleep(30)

        # Check final position
        print("\n7. Checking final position...")
        coords_after = await client.get_current_coordinates()
        final_ra = coords_after.get("ra", 0)
        final_dec = coords_after.get("dec", 0)
        print(f"   RA: {final_ra:.3f}h")
        print(f"   Dec: {final_dec:.3f}°")

        # Calculate error
        ra_error = abs(final_ra - ra_hours)
        dec_error = abs(final_dec - dec_degrees)

        print("\n8. Results:")
        print(f"   Expected: RA={ra_hours:.3f}h, Dec={dec_degrees:.3f}°")
        print(f"   Actual:   RA={final_ra:.3f}h, Dec={final_dec:.3f}°")
        print(f"   Error:    ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

        # Success threshold: within 0.1 hours (1.5°) for RA and 1° for Dec
        if ra_error < 0.1 and dec_error < 1.0:
            print("\n   ✓✓✓ SLEW SUCCESSFUL! Telescope moved to target!")
            print("=" * 70)
            return True
        elif current_ra == final_ra and current_dec == final_dec:
            print("\n   ✗✗✗ SLEW FAILED! Telescope did not move at all!")
            print("=" * 70)
            return False
        else:
            print("\n   ⚠ PARTIAL SUCCESS: Telescope moved but didn't reach target")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    result = asyncio.run(test_slew())
    sys.exit(0 if result else 1)
