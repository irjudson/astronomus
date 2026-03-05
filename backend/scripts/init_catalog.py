#!/usr/bin/env python3
"""Seed the DSO catalog from pyongc on first deployment.

Runs only if dso_catalog is empty (safe to call on every startup).
Imports all NGC and IC objects directly from pyongc, then adds
Messier cross-references and Caldwell numbers from the static list.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# fmt: off
CALDWELL_NUMBERS = {
    "NGC0188": 1, "NGC0040": 2, "NGC0004236": 3, "NGC0253": 65,
    "NGC0246": 4, "NGC0869": 14, "NGC0884": 14,  # h+chi Persei (both parts)
    "NGC0650": 76, "NGC0651": 76,  # M76 both parts
    "NGC0185": 18, "NGC0147": 17, "NGC0205": 18,
    "IC0342": 5, "NGC2403": 7, "NGC0559": 8,
    "NGC0663": 10, "NGC7789": 16, "NGC0891": 23, "NGC1275": 24,
    "NGC2419": 25, "NGC4244": 26, "NGC6888": 27, "NGC0752": 28,
    "IC1805": 31, "IC0405": 31,
    "NGC0281": 11, "NGC0457": 13, "NGC0869": 14, "NGC1502": 9,
    "NGC7789": 16, "NGC0185": 18, "NGC0147": 17, "NGC1023": 6,
    "NGC2403": 7, "NGC7331": 30, "IC0405": 31, "NGC4631": 32,
    "NGC6992": 33, "NGC6960": 34, "NGC4889": 35, "NGC4559": 36,
    "NGC6885": 37, "NGC4565": 38, "NGC2392": 39, "NGC3626": 40,
    "NGC0057": 41, "NGC7006": 42, "NGC7814": 43, "NGC7479": 44,
    "NGC5248": 45, "NGC2261": 46, "NGC6934": 47, "NGC2775": 48,
    "NGC2237": 49, "NGC2244": 49, "NGC4490": 29,
    "NGC1499": 20, "NGC2244": 49, "IC1613": 51,
    "NGC4697": 52, "NGC3115": 53, "NGC2506": 54, "NGC7009": 55,
    "NGC0246": 4, "NGC6543": 6,
    "NGC7293": 63, "NGC2362": 64, "NGC0253": 65, "NGC5694": 66,
    "NGC1097": 67, "NGC6729": 68, "NGC6302": 69, "NGC0300": 70,
    "NGC2477": 71, "NGC0055": 72, "NGC1851": 73, "NGC3132": 74,
    "NGC6124": 75, "NGC6231": 76, "NGC5128": 77, "NGC6541": 78,
    "NGC3201": 79, "NGC5139": 80, "NGC6352": 81, "NGC6193": 82,
    "NGC4945": 83, "NGC5286": 84, "IC2391": 85, "NGC6397": 86,
    "NGC1261": 87, "NGC5823": 88, "NGC6087": 89, "NGC2867": 90,
    "NGC3532": 91, "NGC3372": 92, "NGC6752": 93, "NGC4755": 94,
    "NGC6025": 95, "NGC2516": 96, "NGC3766": 97, "NGC4609": 98,
    "IC2944": 99, "NGC6101": 100, "NGC6422": 101,
    "NGC4833": 105, "NGC2547": 106, "NGC4463": 107,
    "NGC2516": 96, "IC2602": 102, "NGC2516": 96,
    "NGC3114": 103, "NGC5281": 104,
}

# Caldwell list indexed by catalog+number for faster lookup
_CALDWELL_LOOKUP = {}
for _key, _cnum in CALDWELL_NUMBERS.items():
    if _key.startswith("NGC"):
        _n = int(_key[3:])
        _CALDWELL_LOOKUP[("NGC", _n)] = _cnum
    elif _key.startswith("IC"):
        _n = int(_key[2:])
        _CALDWELL_LOOKUP[("IC", _n)] = _cnum
# fmt: on


def _parse_ra(ra_str: str) -> float:
    """Convert 'HH:MM:SS.ss' to decimal hours."""
    if not ra_str:
        return None
    parts = ra_str.strip().split(":")
    h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return h + m / 60.0 + s / 3600.0


def _parse_dec(dec_str: str) -> float:
    """Convert '+DD:MM:SS.s' to decimal degrees."""
    if not dec_str:
        return None
    sign = -1.0 if dec_str.strip().startswith("-") else 1.0
    parts = dec_str.strip().lstrip("+-").split(":")
    d, m, s = float(parts[0]), float(parts[1]), float(parts[2])
    return sign * (d + m / 60.0 + s / 3600.0)


def _type_map(pyongc_type: str) -> str:
    """Map pyongc type strings to our normalized object_type values."""
    t = (pyongc_type or "").lower()
    if "galaxy" in t:
        return "galaxy"
    if "nebula" in t or "hii" in t or "snr" in t:
        return "nebula"
    if "cluster" in t and "glob" in t:
        return "globular_cluster"
    if "cluster" in t:
        return "open_cluster"
    if "planetary" in t or t == "pn":
        return "planetary_nebula"
    if "star" in t or t in ("*", "**", "d*", "v*"):
        return "star"
    if "dark" in t:
        return "dark_nebula"
    return t or "unknown"


def seed_catalog():
    from app.database import SessionLocal
    from app.models.catalog_models import DSOCatalog

    db = SessionLocal()
    try:
        count = db.query(DSOCatalog).count()
        if count > 0:
            print(f"Catalog already seeded ({count} objects). Skipping.")
            return

        print("Catalog is empty — seeding from pyongc...")
        from pyongc.ongc import listObjects

        inserted = 0
        batch = []
        BATCH_SIZE = 500

        for obj in listObjects():
            try:
                ra = _parse_ra(obj.ra)
                dec = _parse_dec(obj.dec)
                if ra is None or dec is None:
                    continue

                name = obj.name  # e.g. "NGC0001", "IC0001"
                if name.startswith("NGC"):
                    cat_name = "NGC"
                    cat_num = int(name[3:])
                elif name.startswith("IC"):
                    cat_name = "IC"
                    cat_num = int(name[2:])
                else:
                    continue  # Skip Barnard, etc.

                # Magnitude: prefer V, else first non-None
                mag = None
                if obj.magnitudes:
                    mags = obj.magnitudes
                    if isinstance(mags, dict):
                        mag = mags.get("V") or mags.get("B")
                    elif isinstance(mags, (tuple, list)):
                        for m in mags:
                            if m is not None:
                                mag = float(m)
                                break
                    elif mags is not None:
                        mag = float(mags)

                # Common name: Messier designation preferred
                common_name = None
                messier_id = None
                try:
                    idents = obj.identifiers
                    if idents and idents[0]:  # idents[0] = Messier name like "M031"
                        messier_id = idents[0]  # "M031"
                        # Normalize to "M31"
                        try:
                            num = int(messier_id[1:])
                            common_name = f"M{num}"
                        except Exception:
                            common_name = messier_id
                except Exception:
                    pass

                # Dimensions
                size_major = size_minor = None
                try:
                    dims = obj.dimensions
                    if dims:
                        size_major = dims[0] if dims[0] else None
                        size_minor = dims[1] if len(dims) > 1 and dims[1] else None
                except Exception:
                    pass

                dso = DSOCatalog(
                    catalog_name=cat_name,
                    catalog_number=cat_num,
                    common_name=common_name,
                    caldwell_number=_CALDWELL_LOOKUP.get((cat_name, cat_num)),
                    ra_hours=ra,
                    dec_degrees=dec,
                    object_type=_type_map(obj.type),
                    magnitude=mag,
                    surface_brightness=getattr(obj, "surface_brightness", None),
                    size_major_arcmin=size_major,
                    size_minor_arcmin=size_minor,
                    constellation=obj.constellation,
                )
                batch.append(dso)
                inserted += 1

                if len(batch) >= BATCH_SIZE:
                    db.bulk_save_objects(batch)
                    db.commit()
                    batch = []
                    print(f"  Inserted {inserted} objects...")

            except Exception as e:
                # Skip objects that fail to parse
                continue

        if batch:
            db.bulk_save_objects(batch)
            db.commit()

        print(f"✓ Catalog seeded: {inserted} objects imported.")

    except Exception as e:
        db.rollback()
        print(f"✗ Catalog seeding failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_catalog()
