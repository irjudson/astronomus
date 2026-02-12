#!/usr/bin/env python3
"""Add Messier catalog entries from existing NGC objects."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func

from app.database import SessionLocal
from app.models.catalog_models import DSOCatalog


def extract_messier_number(common_name: str) -> str:
    """Extract Messier number from common name like 'M031' -> '31'."""
    if not common_name or not common_name.startswith("M"):
        return None

    # Remove 'M' prefix and leading zeros
    try:
        num = common_name[1:].lstrip("0")
        return num if num else "0"
    except:
        return None


def add_messier_catalog():
    """Create Messier catalog entries from NGC objects with Messier common names."""
    db = SessionLocal()

    try:
        # Find all NGC objects with Messier common names
        ngc_messier_objects = (
            db.query(DSOCatalog).filter(DSOCatalog.catalog_name == "NGC", DSOCatalog.common_name.like("M0%")).all()
        )

        print(f"Found {len(ngc_messier_objects)} NGC objects with Messier designations")

        added = 0
        skipped = 0

        for ngc_obj in ngc_messier_objects:
            messier_num = extract_messier_number(ngc_obj.common_name)

            if not messier_num:
                print(f"  Skipping {ngc_obj.common_name} - couldn't extract number")
                skipped += 1
                continue

            # Check if Messier entry already exists
            existing = (
                db.query(DSOCatalog)
                .filter(DSOCatalog.catalog_name == "Messier", DSOCatalog.catalog_number == messier_num)
                .first()
            )

            if existing:
                print(f"  Skipping M{messier_num} - already exists")
                skipped += 1
                continue

            # Create new Messier entry
            messier_obj = DSOCatalog(
                catalog_name="Messier",
                catalog_number=messier_num,
                common_name=ngc_obj.common_name,  # Keep M031 format
                ra_hours=ngc_obj.ra_hours,
                dec_degrees=ngc_obj.dec_degrees,
                object_type=ngc_obj.object_type,
                magnitude=ngc_obj.magnitude,
                surface_brightness=ngc_obj.surface_brightness,
                size_major_arcmin=ngc_obj.size_major_arcmin,
                size_minor_arcmin=ngc_obj.size_minor_arcmin,
                constellation=ngc_obj.constellation,
            )

            db.add(messier_obj)
            added += 1

            if added % 10 == 0:
                db.commit()
                print(f"  Added {added} Messier objects...")

        db.commit()

        # Print statistics
        print("\n" + "=" * 60)
        print("MESSIER CATALOG ADDITION COMPLETE")
        print("=" * 60)
        print(f"Added: {added}")
        print(f"Skipped: {skipped}")

        # Show catalog counts
        counts = (
            db.query(DSOCatalog.catalog_name, func.count(DSOCatalog.id))
            .group_by(DSOCatalog.catalog_name)
            .order_by(DSOCatalog.catalog_name)
            .all()
        )

        print("\nCatalog counts:")
        for catalog, count in counts:
            print(f"  {catalog}: {count}")

        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_messier_catalog()
