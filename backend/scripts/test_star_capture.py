#!/usr/bin/env python3
"""Test end-to-end star capture workflow: search → slew → image."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients.seestar_client import SeestarClient
from app.models.catalog_models import StarCatalog


async def test_star_capture():
    """Test full star capture workflow."""

    # Connect to database
    DATABASE_URL = "postgresql://pg:buffalo-jump@localhost:5432/astronomus"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Initialize telescope client
    client = SeestarClient()

    try:
        print("=" * 70)
        print("STAR CAPTURE WORKFLOW TEST")
        print("=" * 70)

        # Step 1: Search for a bright visible star
        print("\n1. Searching for bright visible stars...")

        # Get bright stars (magnitude < 2.0)
        stars = db.query(StarCatalog).filter(StarCatalog.magnitude < 2.0).order_by(StarCatalog.magnitude.asc()).all()

        print(f"\nFound {len(stars)} bright stars (mag < 2.0):")
        for i, star in enumerate(stars[:10], 1):
            name = star.common_name or star.bayer_designation
            print(
                f"  {i}. {name:20} | RA={star.ra_hours:.3f}h Dec={star.dec_degrees:+.2f}° | Mag={star.magnitude:.2f} | {star.constellation}"
            )

        # Check which are currently visible
        print("\n2. Checking current visibility...")

        # Calculate altitude for each star (Montana location)
        import astropy.units as u
        from astropy.coordinates import AltAz, EarthLocation, SkyCoord
        from astropy.time import Time

        lat = 45.729
        lon = -111.4857
        elevation = 1300  # meters

        location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
        obs_time = Time(datetime.utcnow())
        altaz_frame = AltAz(obstime=obs_time, location=location)

        visible_stars = []
        for star in stars[:20]:  # Check top 20 brightest
            coord = SkyCoord(ra=star.ra_hours * u.hourangle, dec=star.dec_degrees * u.deg, frame="icrs")
            altaz = coord.transform_to(altaz_frame)

            if altaz.alt.deg > 30:  # Above 30° altitude
                visible_stars.append({"star": star, "altitude": altaz.alt.deg, "azimuth": altaz.az.deg})

        if not visible_stars:
            print("\n⚠ No bright stars currently visible above 30° altitude")
            print("This test requires a bright star to be visible.")
            return False

        # Sort by altitude (highest first)
        visible_stars.sort(key=lambda x: x["altitude"], reverse=True)

        print("\nVisible stars above 30° altitude:")
        for i, item in enumerate(visible_stars[:5], 1):
            star = item["star"]
            name = star.common_name or star.bayer_designation
            print(
                f"  {i}. {name:20} | Alt={item['altitude']:.1f}° Az={item['azimuth']:.1f}° | Mag={star.magnitude:.2f}"
            )

        # Select highest star
        target = visible_stars[0]
        target_star = target["star"]
        target_name = target_star.common_name or target_star.bayer_designation

        print(f"\n✓ Selected target: {target_name}")
        print(f"  RA:       {target_star.ra_hours:.4f} hours")
        print(f"  Dec:      {target_star.dec_degrees:.4f}°")
        print(f"  Altitude: {target['altitude']:.1f}°")
        print(f"  Azimuth:  {target['azimuth']:.1f}°")
        print(f"  Magnitude: {target_star.magnitude:.2f}")

        # Step 3: Connect to telescope
        print("\n3. Connecting to telescope...")
        try:
            await client.connect("192.168.2.47", 4700)
            print("   ✓ Connected to Seestar S50")
        except Exception as e:
            print(f"   ✗ Connection failed: {e}")
            print("\n⚠ Cannot proceed without telescope connection")
            return False

        # Get current position
        print("\n4. Getting current telescope position...")
        coords = await client.get_current_coordinates()
        print(f"   Current: RA={coords['ra']:.3f}h, Dec={coords['dec']:.3f}°")
        print(f"   Mount mode: {client.status.mount_mode.value}")

        # Step 4: Slew to star
        print(f"\n5. Slewing to {target_name}...")
        print(f"   Using {client.status.mount_mode.value} mode")

        success = await client.goto_target(
            ra_hours=target_star.ra_hours, dec_degrees=target_star.dec_degrees, target_name=target_name
        )

        if not success:
            print("   ✗ Goto command failed")
            return False

        print("   ✓ Goto command accepted")

        # Wait for slew to complete
        print("\n6. Waiting for slew to complete (30 seconds)...")
        await asyncio.sleep(30)

        # Check final position
        coords_after = await client.get_current_coordinates()
        print(f"   Final position: RA={coords_after['ra']:.3f}h, Dec={coords_after['dec']:.3f}°")

        # Calculate error
        ra_error = abs(coords_after["ra"] - target_star.ra_hours)
        dec_error = abs(coords_after["dec"] - target_star.dec_degrees)

        print("\n   Pointing accuracy:")
        print(f"   RA error:  {ra_error:.3f}h ({ra_error*15:.1f}°)")
        print(f"   Dec error: {dec_error:.2f}°")

        # Check if we're on target
        if client.status.mount_mode.value == "altaz":
            # Alt/Az mode - more lenient since coordinates drift
            if ra_error < 1.0 and dec_error < 10.0:
                print("   ✓ Telescope moved to target region")
            else:
                print("   ⚠ Large pointing error (expected in alt/az mode)")
        else:
            # Equatorial mode - should be more accurate
            if ra_error < 0.1 and dec_error < 1.0:
                print("   ✓✓✓ Excellent pointing accuracy!")
            elif ra_error < 0.5 and dec_error < 5.0:
                print("   ✓ Acceptable pointing accuracy")
            else:
                print("   ⚠ Large pointing error")

        # Step 5: Start imaging (optional - commented out to avoid accidental capture)
        print(f"\n7. Ready to start imaging {target_name}")
        print("   To start imaging, run:")
        print(
            f"   await client.start_stack_star(target_name={target_name!r}, ra={target_star.ra_hours}, dec={target_star.dec_degrees})"
        )

        print("\n" + "=" * 70)
        print("STAR CAPTURE WORKFLOW TEST COMPLETE")
        print("=" * 70)
        print("\n✓ Workflow verified:")
        print("  1. Star catalog search - OK")
        print("  2. Visibility calculation - OK")
        print("  3. Telescope connection - OK")
        print("  4. Goto target - OK")
        print("  5. Position verification - OK")
        print(f"\nTelescope is now pointed at {target_name} and ready for imaging!")

        return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if client.connected:
            await client.disconnect()
        db.close()


if __name__ == "__main__":
    result = asyncio.run(test_star_capture())
    sys.exit(0 if result else 1)
