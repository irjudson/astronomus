#!/usr/bin/env python3
"""Test iscope_start_view with graceful connection handling."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from app.clients.seestar_client import SeestarClient


async def test_iscope_start_view():
    """Test iscope_start_view command handling connection close."""
    client = SeestarClient()

    # Montana location
    lat = 45.729
    lon = -111.4857
    elevation = 1300

    try:
        print("=" * 70)
        print("TEST: iscope_start_view with connection handling")
        print("=" * 70)

        print("\n1. Connecting...")
        await client.connect("192.168.2.47", 4700)
        print(f"   ✓ Connected. State: {client.status.state}")

        # Check and stop any active view
        print("\n2. Checking for active view...")
        view_response = await client._send_command("get_view_state", {})
        view_state = view_response.get("result", {}).get("View", {}).get("state", "unknown")
        print(f"   Current view state: {view_state}")

        if view_state == "working":
            print("   Stopping active view...")
            await client._send_command("iscope_stop_view", {})
            await asyncio.sleep(2)
            print("   ✓ View stopped")

        # Unpark if needed
        if "PARKED" in str(client.status.state):
            print("\n3. Unparking...")
            await client.move_to_horizon(azimuth=180.0, altitude=45.0)
            await asyncio.sleep(5)
            print("   ✓ Unparked")

        # Calculate Vega position
        print("\n4. Target: Vega")
        vega_coord = SkyCoord(ra=279.23 * u.deg, dec=38.783 * u.deg, frame="icrs")
        ra_hours = vega_coord.ra.hour
        dec_degrees = vega_coord.dec.deg

        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())
        altaz_frame = AltAz(obstime=obs_time, location=location)
        altaz_coord = vega_coord.transform_to(altaz_frame)

        print(f"   RA: {ra_hours:.3f}h, Dec: {dec_degrees:.3f}°")
        print(f"   Alt: {altaz_coord.alt.deg:.2f}°, Az: {altaz_coord.az.deg:.2f}°")

        # Get position before
        print("\n5. Position before slew:")
        coords_before = await client.get_current_coordinates()
        print(f"   RA: {coords_before['ra']:.3f}h, Dec: {coords_before['dec']:.3f}°")

        # Send iscope_start_view and expect connection may close
        print("\n6. Sending iscope_start_view command...")
        print("   (Note: Connection may close - this might be expected behavior)")

        try:
            params = {
                "mode": "star",
                "target_ra_dec": [ra_hours, dec_degrees],
                "target_name": "Vega",
                "lp_filter": False,
            }
            response = await client._send_command("iscope_start_view", params)
            print(f"   Response: result={response.get('result')}, code={response.get('code')}")

            if response.get("result") == 0 and response.get("code") == 0:
                print("   ✓ Command ACCEPTED")
            else:
                print(f"   ✗ Command rejected: {response}")
                return False

        except Exception as e:
            if "Connection closed" in str(e) or "disconnect" in str(e).lower():
                print("   ⚠ Connection closed after command (may be expected)")
                print("   Telescope is likely transitioning to viewing mode")
            else:
                print(f"   ✗ Error: {e}")
                raise

        # Wait for slew
        print("\n7. Waiting 30 seconds for slew...")
        await asyncio.sleep(30)

        # Reconnect and check position
        print("\n8. Reconnecting to check position...")
        if not client.connected:
            await client.connect("192.168.2.47", 4700)

        coords_after = await client.get_current_coordinates()
        print(f"   RA: {coords_after['ra']:.3f}h, Dec: {coords_after['dec']:.3f}°")

        # Calculate error
        ra_error = abs(coords_after["ra"] - ra_hours)
        dec_error = abs(coords_after["dec"] - dec_degrees)

        print("\n9. Results:")
        print(f"   Expected: RA={ra_hours:.3f}h, Dec={dec_degrees:.3f}°")
        print(f"   Actual:   RA={coords_after['ra']:.3f}h, Dec={coords_after['dec']:.3f}°")
        print(f"   Error:    ΔRA={ra_error:.3f}h ({ra_error*15:.1f}°), ΔDec={dec_error:.3f}°")

        # Check view state
        print("\n10. Checking view state after slew...")
        view_response = await client._send_command("get_view_state", {})
        view_state = view_response.get("result", {}).get("View", {})
        print(f"   View state: {view_state.get('state', 'unknown')}")
        print(f"   View mode: {view_state.get('mode', 'none')}")
        print(f"   View stage: {view_state.get('stage', 'none')}")

        # Success check
        if ra_error < 0.1 and dec_error < 1.0:
            print("\n   ✓✓✓ SLEW SUCCESSFUL!")
            print("=" * 70)
            return True
        elif coords_before["ra"] != coords_after["ra"] or coords_before["dec"] != coords_after["dec"]:
            print("\n   ✓ Telescope MOVED but not at target yet")
            print("=" * 70)
            return True
        else:
            print("\n   ✗ Telescope did not move")
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
    result = asyncio.run(test_iscope_start_view())
    sys.exit(0 if result else 1)
