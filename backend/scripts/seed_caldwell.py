#!/usr/bin/env python3
"""Seed Caldwell catalog objects into dso_catalog table."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_caldwell_if_needed(db=None) -> int:
    """Insert Caldwell objects. Returns count of new rows inserted."""
    from app.models.catalog_models import DSOCatalog

    own_session = db is None
    if own_session:
        from app.database import SessionLocal

        db = SessionLocal()

    try:
        from scripts.caldwell_data import CALDWELL_CATALOG

        inserted = 0
        for entry in CALDWELL_CATALOG:
            num = entry["caldwell"]
            catalog_id_str = f"C{num}"

            # Check by caldwell_number first (may have been seeded via init_catalog), then by common_name
            existing = db.query(DSOCatalog).filter(DSOCatalog.caldwell_number == num).first()
            if existing:
                continue

            ngc_ref = entry.get("ngc", "")
            cat_name = "NGC"
            cat_num = 0
            ref_upper = ngc_ref.strip().upper()
            if ref_upper.startswith("NGC"):
                # Handle compound refs like "NGC 869/884" — use first number
                raw = ref_upper[3:].strip().split("/")[0].strip()
                try:
                    cat_num = int(raw)
                except ValueError:
                    cat_num = 0
                cat_name = "NGC"
            elif ref_upper.startswith("IC"):
                raw = ref_upper[2:].strip().split("/")[0].strip()
                try:
                    cat_num = int(raw)
                except ValueError:
                    cat_num = 0
                cat_name = "IC"

            dso = DSOCatalog(
                catalog_name=cat_name,
                catalog_number=cat_num,
                common_name=catalog_id_str,
                caldwell_number=num,
                ra_hours=entry["ra_hours"],
                dec_degrees=entry["dec_degrees"],
                object_type=entry["type"],
                magnitude=entry.get("magnitude"),
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
    n = seed_caldwell_if_needed()
    print(f"Seeded {n} Caldwell objects.")
