#!/usr/bin/env python3
"""Test unified search functionality across stars, planets, and DSOs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker

from app.models.catalog_models import DSOCatalog, StarCatalog
from app.services.planet_service import PlanetService


def test_unified_search():
    """Test unified search for stars, planets, and DSOs."""

    # Connect to database
    DATABASE_URL = "postgresql://pg:buffalo-jump@localhost:5432/astronomus"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("=" * 70)
        print("UNIFIED SEARCH TEST")
        print("=" * 70)

        # Test queries
        test_queries = [
            "vega",
            "orion",
            "jupiter",
            "sirius",
            "andromeda",
            "polaris",
        ]

        for query in test_queries:
            print(f"\n{'=' * 70}")
            print(f"SEARCHING FOR: {query}")
            print("=" * 70)

            search_pattern = f"%{query}%"

            # Search DSOs
            print(f"\n--- DSOs matching '{query}' ---")
            dso_query = db.query(DSOCatalog).filter(
                or_(
                    DSOCatalog.common_name.ilike(search_pattern),
                    func.concat(DSOCatalog.catalog_name, DSOCatalog.catalog_number).ilike(search_pattern),
                )
            )
            dso_query = dso_query.order_by(DSOCatalog.magnitude.asc().nullslast())
            dsos = dso_query.limit(5).all()

            if dsos:
                for dso in dsos:
                    name = dso.common_name or f"{dso.catalog_name}{dso.catalog_number}"
                    mag_str = f"{dso.magnitude:.1f}" if dso.magnitude is not None else "N/A"
                    print(f"  {name:30} | {dso.object_type:15} | Mag: {mag_str:>6} | {dso.constellation}")
            else:
                print("  No DSOs found")

            # Search Stars
            print(f"\n--- Stars matching '{query}' ---")
            star_query = db.query(StarCatalog).filter(
                or_(
                    StarCatalog.common_name.ilike(search_pattern),
                    StarCatalog.bayer_designation.ilike(search_pattern),
                    func.concat(StarCatalog.catalog_name, StarCatalog.catalog_number).ilike(search_pattern),
                )
            )
            star_query = star_query.order_by(StarCatalog.magnitude.asc().nullslast())
            stars = star_query.limit(5).all()

            if stars:
                for star in stars:
                    name = star.common_name or star.bayer_designation or f"{star.catalog_name}{star.catalog_number}"
                    mag_str = f"{star.magnitude:.2f}" if star.magnitude is not None else "N/A"
                    print(f"  {name:30} | {star.spectral_type or 'N/A':10} | Mag: {mag_str:>6} | {star.constellation}")
            else:
                print("  No stars found")

            # Search Planets
            print(f"\n--- Planets matching '{query}' ---")
            planet_service = PlanetService()
            all_planets = planet_service.get_all_planets()
            matching_planets = [p for p in all_planets if query.lower() in p.name.lower()]

            if matching_planets:
                for planet in matching_planets:
                    print(f"  {planet.name:30} | {planet.planet_type:15} | Diameter: {planet.diameter_km:,.0f} km")
            else:
                print("  No planets found")

        print(f"\n{'=' * 70}")
        print("TEST COMPLETE")
        print("=" * 70)

        # Summary statistics
        print("\nCatalog Statistics:")
        total_dsos = db.query(DSOCatalog).count()
        total_stars = db.query(StarCatalog).count()
        total_planets = len(planet_service.get_all_planets())

        print(f"  DSO Catalog:    {total_dsos:>6} objects")
        print(f"  Star Catalog:   {total_stars:>6} stars")
        print(f"  Planets/Sun:    {total_planets:>6} bodies")
        print(f"  Total:          {total_dsos + total_stars + total_planets:>6} celestial objects")

        return True

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    result = test_unified_search()
    sys.exit(0 if result else 1)
