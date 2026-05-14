#!/usr/bin/env python3
"""Seed Arp Atlas of Peculiar Galaxies into dso_catalog."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_arp_if_needed(db=None) -> int:
    from app.models.catalog_models import DSOCatalog
    from scripts.arp_data import ARP_CATALOG

    own_session = db is None
    if own_session:
        from app.database import SessionLocal

        db = SessionLocal()

    try:
        inserted = updated = 0
        for entry in ARP_CATALOG:
            num = entry["arp"]
            # Skip if already tagged
            if db.query(DSOCatalog).filter(DSOCatalog.arp_number == num).first():
                continue

            # Try to find existing NGC row to update
            ngc_ref = entry.get("ngc", "")
            existing = None
            if ngc_ref:
                # Try common_name match (e.g., "M51", "NGC 5194")
                existing = db.query(DSOCatalog).filter(DSOCatalog.common_name == ngc_ref).first()
                if not existing and ngc_ref.upper().startswith("NGC"):
                    try:
                        cat_num = int(ngc_ref.split()[-1])
                        existing = (
                            db.query(DSOCatalog)
                            .filter(DSOCatalog.catalog_name == "NGC", DSOCatalog.catalog_number == cat_num)
                            .first()
                        )
                    except ValueError:
                        pass
                if not existing and ngc_ref.upper().startswith("M"):
                    # Messier lookup via common_name (stored as "M042" etc.)
                    try:
                        m_num = int(ngc_ref[1:])
                        padded = f"M{m_num:03d}"
                        existing = db.query(DSOCatalog).filter(DSOCatalog.common_name == padded).first()
                    except ValueError:
                        pass

            if existing:
                existing.arp_number = num
                updated += 1
            else:
                dso = DSOCatalog(
                    catalog_name="Arp",
                    catalog_number=num,
                    common_name=f"Arp {num}",
                    arp_number=num,
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

        return inserted + updated

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = seed_arp_if_needed()
    print(f"Processed {n} Arp objects.")
