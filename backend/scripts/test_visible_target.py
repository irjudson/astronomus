#!/usr/bin/env python3
"""Test movement to a visible target above horizon."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_moon
from astropy.time import Time

from app.clients.seestar_client import MountMode, SeestarClient


async def test_visible_target():
    """Test movement to a visible target."""
    client = SeestarClient()

    try:
        print("=" * 70)
        print("TESTING MOVEMENT TO VISIBLE TARGET")
        print("=" * 70)

        # Connect
        print("\n[1] Connecting...")
        await client.connect("192.168.2.47", 4700)
        print("✓ Connected\n")

        # Set mount mode to Alt/Az
        print("[2] Setting mount mode to Alt/Az...")
        client._update_status(mount_mode=MountMode.ALTAZ, equatorial_initialized=False)
        print("✓ Mount mode: Alt/Az\n")

        # Get current coordinates
        print("[3] Getting current coordinates...")
        current_coords = await client.get_current_coordinates()

        # Setup location
        lat = 45.729
        lon = -111.4857
        elevation = 1300
        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())

        # Current position to Alt/Az
        coord = SkyCoord(ra=current_coords["ra"] * u.hourangle, dec=current_coords["dec"] * u.deg, frame="icrs")
        altaz_frame = AltAz(obstime=obs_time, location=location)
        current_altaz = coord.transform_to(altaz_frame)

        print("Current position:")
        print(f"  RA: {current_coords['ra']:.4f}h, Dec: {current_coords['dec']:.3f}°")
        print(f"  Az: {current_altaz.az.deg:.2f}°, Alt: {current_altaz.alt.deg:.2f}°")

        if current_altaz.alt.deg < 0:
            print("  ⚠️  WARNING: Currently pointing BELOW horizon!")
        else:
            print("  ✓ Currently pointing above horizon")
        print()

        # Find a good visible target
        print("[4] Finding visible targets...")

        # Check Moon
        moon = get_moon(obs_time, location)
        moon_altaz = moon.transform_to(altaz_frame)
        print(f"Moon: Az={moon_altaz.az.deg:.2f}°, Alt={moon_altaz.alt.deg:.2f}°")

        # Check some bright stars (approximate coordinates)
        targets = []

        # Sirius (brightest star)
        sirius = SkyCoord(ra=6.75 * u.hourangle, dec=-16.7 * u.deg, frame="icrs")
        sirius_altaz = sirius.transform_to(altaz_frame)
        targets.append(("Sirius", sirius_altaz))
        print(f"Sirius: Az={sirius_altaz.az.deg:.2f}°, Alt={sirius_altaz.alt.deg:.2f}°")

        # Capella
        capella = SkyCoord(ra=5.28 * u.hourangle, dec=45.9 * u.deg, frame="icrs")
        capella_altaz = capella.transform_to(altaz_frame)
        targets.append(("Capella", capella_altaz))
        print(f"Capella: Az={capella_altaz.az.deg:.2f}°, Alt={capella_altaz.alt.deg:.2f}°")

        # Betelgeuse
        betelgeuse = SkyCoord(ra=5.92 * u.hourangle, dec=7.4 * u.deg, frame="icrs")
        betelgeuse_altaz = betelgeuse.transform_to(altaz_frame)
        targets.append(("Betelgeuse", betelgeuse_altaz))
        print(f"Betelgeuse: Az={betelgeuse_altaz.az.deg:.2f}°, Alt={betelgeuse_altaz.alt.deg:.2f}°")

        # Find highest target above 30° altitude
        visible_targets = [(name, altaz) for name, altaz in targets if altaz.alt.deg > 30]

        if moon_altaz.alt.deg > 30:
            visible_targets.append(("Moon", moon_altaz))

        if not visible_targets:
            print("\n✗ No targets above 30° altitude!")
            print("Cannot test - need visible target")
            return

        # Pick highest target
        target_name, target_altaz = max(visible_targets, key=lambda x: x[1].alt.deg)

        print(f"\n[5] Selected target: {target_name}")
        print(f"  Az: {target_altaz.az.deg:.2f}°")
        print(f"  Alt: {target_altaz.alt.deg:.2f}°")
        print("  (Above horizon: ✓)\n")

        # Command movement
        print(f"[6] Commanding telescope to move to {target_name}...")
        response = await client._send_command("scope_move_to_horizon", [target_altaz.az.deg, target_altaz.alt.deg])
        print(f"Response: code={response.get('code')}, result={response.get('result')}")

        if response.get("code") != 0:
            print("\n✗ Command rejected!")
            return

        print("\n✓ Command accepted!")
        print("\n[7] Monitoring telescope for 20 seconds...")
        print(f"     ** WATCH THE TELESCOPE - IT SHOULD BE MOVING TO {target_name} **\n")

        print("Time | RA (h) | Dec (°) | Az (°)  | Alt (°) | Status")
        print("-" * 70)

        initial_ra = current_coords["ra"]
        initial_dec = current_coords["dec"]
        initial_az = current_altaz.az.deg
        initial_alt = current_altaz.alt.deg

        for i in range(20):
            await asyncio.sleep(1)

            # Get new position
            new_coords = await client.get_current_coordinates()
            new_coord = SkyCoord(ra=new_coords["ra"] * u.hourangle, dec=new_coords["dec"] * u.deg, frame="icrs")
            new_obs_time = Time(datetime.utcnow())
            new_altaz_frame = AltAz(obstime=new_obs_time, location=location)
            new_altaz = new_coord.transform_to(new_altaz_frame)

            # Calculate changes
            ra_change = abs(new_coords["ra"] - initial_ra)
            dec_change = abs(new_coords["dec"] - initial_dec)
            az_change = abs(new_altaz.az.deg - initial_az)
            alt_change = abs(new_altaz.alt.deg - initial_alt)

            # Determine status
            if ra_change > 0.01 or dec_change > 0.1 or az_change > 1.0 or alt_change > 1.0:
                status = "*** MOVING ***"
            elif ra_change > 0.001 or dec_change > 0.01 or az_change > 0.1 or alt_change > 0.1:
                status = "drift"
            else:
                status = "no change"

            # Print every 2 seconds or when moving
            if i % 2 == 0 or status == "*** MOVING ***":
                print(
                    f"{i+1:2d}s  | {new_coords['ra']:6.3f} | {new_coords['dec']:7.3f} | "
                    f"{new_altaz.az.deg:7.2f} | {new_altaz.alt.deg:7.2f} | {status}"
                )

        # Final position
        final_coords = await client.get_current_coordinates()
        final_coord = SkyCoord(ra=final_coords["ra"] * u.hourangle, dec=final_coords["dec"] * u.deg, frame="icrs")
        final_obs_time = Time(datetime.utcnow())
        final_altaz_frame = AltAz(obstime=final_obs_time, location=location)
        final_altaz = final_coord.transform_to(final_altaz_frame)

        print("\n" + "=" * 70)
        print("RESULTS:")
        print("=" * 70)
        print(f"Target:  {target_name} at Az={target_altaz.az.deg:.2f}°, Alt={target_altaz.alt.deg:.2f}°\n")

        print(f"Initial: RA={initial_ra:.4f}h, Dec={initial_dec:.3f}°, Az={initial_az:.2f}°, Alt={initial_alt:.2f}°")
        print(
            f"Final:   RA={final_coords['ra']:.4f}h, Dec={final_coords['dec']:.3f}°, "
            f"Az={final_altaz.az.deg:.2f}°, Alt={final_altaz.alt.deg:.2f}°\n"
        )

        ra_change = abs(final_coords["ra"] - initial_ra)
        dec_change = abs(final_coords["dec"] - initial_dec)
        az_change = abs(final_altaz.az.deg - initial_az)
        alt_change = abs(final_altaz.alt.deg - initial_alt)

        print(f"Changes: ΔRA={ra_change:.4f}h, ΔDec={dec_change:.3f}°, ΔAz={az_change:.2f}°, ΔAlt={alt_change:.2f}°\n")

        # Calculate distance from target
        target_az_distance = abs(final_altaz.az.deg - target_altaz.az.deg)
        target_alt_distance = abs(final_altaz.alt.deg - target_altaz.alt.deg)

        print(f"Distance from target: ΔAz={target_az_distance:.2f}°, ΔAlt={target_alt_distance:.2f}°\n")

        if az_change > 5.0 or alt_change > 5.0:
            print("✓✓✓ SIGNIFICANT MOVEMENT DETECTED! ✓✓✓")
            print("Telescope is physically moving in response to commands.")

            if target_az_distance < 5.0 and target_alt_distance < 5.0:
                print(f"✓ Telescope reached target {target_name} successfully!")
            else:
                print("⚠️  Telescope moved but didn't reach target")
                print(f"   (Off by {target_az_distance:.1f}° in Az, {target_alt_distance:.1f}° in Alt)")

        elif az_change > 0.5 or alt_change > 0.5:
            print("⚠️  SMALL MOVEMENT DETECTED")
            print("Telescope moved slightly but may be blocked or limited.")
        else:
            print("✗✗✗ NO MOVEMENT DETECTED ✗✗✗")
            print("\nTelescope did NOT physically move despite:")
            print("  - Command accepted (code 0)")
            print(f"  - Target above horizon (Alt={target_altaz.alt.deg:.1f}°)")
            print(f"  - Clear visible target ({target_name})")
            print("\n**ACTION REQUIRED:**")
            print("1. Try moving telescope with official Seestar app")
            print("2. If official app works → our command sequence is wrong")
            print("3. If official app fails → telescope needs restart/reset")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.connected:
            await client.disconnect()
            print("\n✓ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_visible_target())
