#!/usr/bin/env python3
"""Test goto after syncing mount."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from app.clients.seestar_client import SeestarClient


async def test_with_sync():
    """Test goto after syncing mount to current position."""
    client = SeestarClient()

    # Montana location
    lat = 45.729
    lon = -111.4857
    elevation = 1300

    try:
        print("=" * 70)
        print("TEST: Goto with Mount Sync")
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

        # Get current position
        print("\n3. Getting current position...")
        coords = await client.get_current_coordinates()
        current_ra = coords["ra"]
        current_dec = coords["dec"]
        print(f"   Current: RA={current_ra:.3f}h, Dec={current_dec:.3f}°")

        # SYNC mount to current position
        print("\n4. Syncing mount to current position...")
        print(f"   This tells the mount: 'I am currently at RA={current_ra:.3f}h, Dec={current_dec:.3f}°'")
        sync_response = await client._send_command("scope_sync", [current_ra, current_dec])
        print(f"   Sync response: result={sync_response.get('result')}, code={sync_response.get('code')}")

        if sync_response.get("code") == 0:
            print("   ✓ Mount synced successfully!")
        else:
            print(f"   ✗ Sync failed: {sync_response}")
            return False

        # Now try scope_goto
        print("\n5. Testing scope_goto after sync...")
        vega_coord = SkyCoord(ra=279.23 * u.deg, dec=38.783 * u.deg, frame="icrs")
        ra_hours = vega_coord.ra.hour
        dec_degrees = vega_coord.dec.deg

        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())
        altaz_frame = AltAz(obstime=obs_time, location=location)
        altaz_coord = vega_coord.transform_to(altaz_frame)

        print("   Target: Vega")
        print(f"   RA: {ra_hours:.3f}h, Dec: {dec_degrees:.3f}°")
        print(f"   Alt: {altaz_coord.alt.deg:.2f}°, Az: {altaz_coord.az.deg:.2f}°")

        try:
            goto_response = await client._send_command("scope_goto", [ra_hours, dec_degrees])
            print(f"   Goto response: result={goto_response.get('result')}, code={goto_response.get('code')}")

            if goto_response.get("code") == 0:
                print("   ✓ scope_goto command ACCEPTED!")

                # Wait for movement
                print("\n6. Waiting 30 seconds for slew...")
                await asyncio.sleep(30)

                # Check position
                print("\n7. Checking final position...")
                final_coords = await client.get_current_coordinates()
                print(f"   Final: RA={final_coords['ra']:.3f}h, Dec={final_coords['dec']:.3f}°")

                # Calculate error
                ra_error = abs(final_coords["ra"] - ra_hours)
                dec_error = abs(final_coords["dec"] - dec_degrees)

                print("\n8. Results:")
                print(f"   Expected: RA={ra_hours:.3f}h, Dec={dec_degrees:.3f}°")
                print(f"   Actual:   RA={final_coords['ra']:.3f}h, Dec={final_coords['dec']:.3f}°")
                print(f"   Error:    ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

                if ra_error < 0.1 and dec_error < 1.0:
                    print("\n   ✓✓✓ SLEW SUCCESSFUL!")
                    return True
                elif final_coords["ra"] != current_ra or final_coords["dec"] != current_dec:
                    print("\n   ✓ Telescope MOVED but not at target")
                    return True
                else:
                    print("\n   ✗ Telescope did not move")
                    return False

            elif goto_response.get("code") == 207:
                print("   ✗ Still getting error 207 even after sync")
                print("   There may be another requirement we're missing")
                return False
            else:
                print(f"   ✗ Goto failed: {goto_response}")
                return False

        except Exception as e:
            print(f"   ✗ Exception during goto: {e}")
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
    result = asyncio.run(test_with_sync())
    print("\n" + "=" * 70)
    sys.exit(0 if result else 1)
