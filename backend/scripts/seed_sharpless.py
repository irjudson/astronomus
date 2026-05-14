#!/usr/bin/env python3
"""Seed Sharpless HII regions into dso_catalog."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_sharpless_if_needed(db=None) -> int:
    """Insert Sharpless HII region objects. Returns count of rows inserted."""
    from app.models.catalog_models import DSOCatalog
    from scripts.sharpless_data import SHARPLESS_CATALOG

    own_session = db is None
    if own_session:
        from app.database import SessionLocal

        db = SessionLocal()

    try:
        inserted = 0
        for entry in SHARPLESS_CATALOG:
            num = entry["sh2"]
            # Idempotent: skip if already present
            if db.query(DSOCatalog).filter(DSOCatalog.sharpless_number == num).first():
                continue

            dso = DSOCatalog(
                catalog_name="Sharpless",
                catalog_number=num,
                common_name=f"Sh2-{num}",
                sharpless_number=num,
                ra_hours=entry["ra_hours"],
                dec_degrees=entry["dec_degrees"],
                object_type="nebula",
                size_major_arcmin=entry.get("size_arcmin"),
                constellation=entry.get("constellation"),
            )
            db.add(dso)
            inserted += 1

        if own_session:
            db.commit()
        else:
            db.flush()

        return inserted

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = seed_sharpless_if_needed()
    print(f"Seeded {n} Sharpless objects.")
