#!/usr/bin/env python3
"""Capture a bright visible star - complete workflow."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.clients.seestar_client import SeestarClient
from app.models.catalog_models import StarCatalog


async def capture_star(star_name: str = None, exposure_count: int = 10):
    """
    Capture a star with full workflow.

    Args:
        star_name: Specific star to capture (e.g., "Vega", "Arcturus")
                   If None, automatically selects highest visible bright star
        exposure_count: Number of frames to capture (default: 10)
    """

    # Connect to database
    DATABASE_URL = "postgresql://pg:buffalo-jump@localhost:5432/astronomus"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Initialize telescope client
    client = SeestarClient()

    try:
        print("=" * 70)
        print("STAR CAPTURE")
        print("=" * 70)

        # Step 1: Find target star
        if star_name:
            print(f"\n1. Searching for '{star_name}'...")
            star = db.query(StarCatalog).filter(StarCatalog.common_name.ilike(f"%{star_name}%")).first()

            if not star:
                print(f"   ✗ Star '{star_name}' not found in catalog")
                return False
        else:
            print("\n1. Finding brightest visible star...")

            # Get bright stars
            stars = (
                db.query(StarCatalog).filter(StarCatalog.magnitude < 2.0).order_by(StarCatalog.magnitude.asc()).all()
            )

            # Check visibility
            import astropy.units as u
            from astropy.coordinates import AltAz, EarthLocation, SkyCoord
            from astropy.time import Time

            lat = 45.729
            lon = -111.4857
            elevation = 1300

            location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
            obs_time = Time(datetime.utcnow())
            altaz_frame = AltAz(obstime=obs_time, location=location)

            visible_stars = []
            for s in stars:
                coord = SkyCoord(ra=s.ra_hours * u.hourangle, dec=s.dec_degrees * u.deg, frame="icrs")
                altaz = coord.transform_to(altaz_frame)
                if altaz.alt.deg > 30:
                    visible_stars.append((s, altaz.alt.deg, altaz.az.deg))

            if not visible_stars:
                print("   ✗ No bright stars currently visible above 30°")
                return False

            visible_stars.sort(key=lambda x: x[1], reverse=True)
            star, altitude, azimuth = visible_stars[0]

            print(f"   ✓ Auto-selected: {star.common_name}")
            print(f"     Altitude: {altitude:.1f}°")

        target_name = star.common_name or star.bayer_designation or f"{star.catalog_name}{star.catalog_number}"

        print(f"\n✓ Target: {target_name}")
        print(f"  RA:  {star.ra_hours:.4f}h")
        print(f"  Dec: {star.dec_degrees:+.4f}°")
        print(f"  Magnitude: {star.magnitude:.2f}")
        print(f"  Spectral type: {star.spectral_type}")

        # Step 2: Connect to telescope
        print("\n2. Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print("   ✓ Connected")

        # Step 3: Slew to target
        print(f"\n3. Slewing to {target_name}...")
        success = await client.goto_target(
            ra_hours=star.ra_hours, dec_degrees=star.dec_degrees, target_name=target_name
        )

        if not success:
            print("   ✗ Goto failed")
            return False

        print("   ✓ Slewing...")

        # Wait for slew
        await asyncio.sleep(15)
        print("   ✓ Slew complete")

        # Step 4: Start imaging
        print(f"\n4. Starting imaging ({exposure_count} frames)...")
        success = await client.start_imaging(restart=True)

        if not success:
            print("   ✗ Failed to start imaging")
            return False

        print("   ✓ Imaging started!")

        # Step 5: Monitor progress
        print("\n5. Capturing frames...")
        print("   (Press Ctrl+C to stop monitoring, imaging will continue)")

        try:
            for i in range(exposure_count + 5):  # Wait a bit longer
                await asyncio.sleep(10)

                # Check status
                status = client.status
                print(f"   [{i*10}s] State: {status.state.value}")

                # If we reach target count, we're done
                if i >= exposure_count:
                    break

        except KeyboardInterrupt:
            print("\n   Monitoring stopped (imaging continues on telescope)")

        # Step 6: Stop imaging
        print("\n6. Stopping imaging...")
        await client.stop_imaging()
        print("   ✓ Imaging stopped")

        print("\n" + "=" * 70)
        print(f"CAPTURE COMPLETE: {target_name}")
        print("=" * 70)
        print("\nImages saved to telescope storage:")
        print("  /mnt/seestar/stack/ - Stacked images")
        print("  /mnt/seestar/IMG/    - Individual frames")
        print("\nTo download images, use:")
        print("  await client.list_images()")
        print("  await client.download_stacked_image(filename)")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if client.connected:
            await client.disconnect()
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Capture a star with the Seestar S50")
    parser.add_argument(
        "star_name",
        nargs="?",
        default=None,
        help="Star name (e.g., 'Vega', 'Arcturus'). If not specified, auto-selects brightest visible star.",
    )
    parser.add_argument("-n", "--frames", type=int, default=10, help="Number of frames to capture (default: 10)")

    args = parser.parse_args()

    result = asyncio.run(capture_star(args.star_name, args.frames))
    sys.exit(0 if result else 1)
