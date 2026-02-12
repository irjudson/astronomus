#!/usr/bin/env python3
"""Add bright named stars catalog."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func

from app.database import SessionLocal
from app.models.catalog_models import StarCatalog

# Bright named stars data
# Format: (common_name, catalog_name, catalog_number, ra_hours, dec_degrees, magnitude,
#          spectral_type, bayer_designation, constellation, distance_ly)
BRIGHT_STARS = [
    # Brightest stars in the sky
    ("Sirius", "HIP", "32349", 6.752, -16.716, -1.46, "A1V", "α CMa", "CMa", 8.6),
    ("Canopus", "HIP", "30438", 6.399, -52.696, -0.72, "A9II", "α Car", "Car", 310),
    ("Rigil Kentaurus", "HIP", "71683", 14.661, -60.834, -0.27, "G2V", "α Cen", "Cen", 4.4),
    ("Arcturus", "HIP", "69673", 14.261, 19.182, -0.05, "K0III", "α Boo", "Boo", 37),
    ("Vega", "HIP", "91262", 18.615, 38.783, 0.03, "A0V", "α Lyr", "Lyr", 25),
    ("Capella", "HIP", "24608", 5.278, 45.998, 0.08, "G5III", "α Aur", "Aur", 43),
    ("Rigel", "HIP", "24436", 5.242, -8.202, 0.13, "B8Ia", "β Ori", "Ori", 860),
    ("Procyon", "HIP", "37279", 7.655, 5.225, 0.38, "F5IV", "α CMi", "CMi", 11.5),
    ("Betelgeuse", "HIP", "27989", 5.919, 7.407, 0.50, "M1Ia", "α Ori", "Ori", 640),
    ("Achernar", "HIP", "7588", 1.628, -57.237, 0.46, "B6V", "α Eri", "Eri", 139),
    # Navigation stars
    ("Polaris", "HIP", "11767", 2.530, 89.264, 1.98, "F7Ib", "α UMi", "UMi", 433),
    ("Altair", "HIP", "97649", 19.846, 8.868, 0.77, "A7V", "α Aql", "Aql", 17),
    ("Deneb", "HIP", "102098", 20.690, 45.280, 1.25, "A2Ia", "α Cyg", "Cyg", 2615),
    ("Antares", "HIP", "80763", 16.490, -26.432, 0.96, "M1.5Iab", "α Sco", "Sco", 550),
    ("Spica", "HIP", "65474", 13.420, -11.161, 0.98, "B1V", "α Vir", "Vir", 250),
    ("Pollux", "HIP", "37826", 7.755, 28.026, 1.14, "K0III", "β Gem", "Gem", 34),
    ("Fomalhaut", "HIP", "113368", 22.961, -29.622, 1.16, "A3V", "α PsA", "PsA", 25),
    ("Aldebaran", "HIP", "21421", 4.599, 16.509, 0.85, "K5III", "α Tau", "Tau", 65),
    ("Regulus", "HIP", "49669", 10.140, 11.967, 1.35, "B7V", "α Leo", "Leo", 77),
    # Orion constellation
    ("Bellatrix", "HIP", "25336", 5.418, 6.350, 1.64, "B2III", "γ Ori", "Ori", 250),
    ("Alnilam", "HIP", "26311", 5.604, -1.202, 1.69, "B0Ia", "ε Ori", "Ori", 2000),
    ("Alnitak", "HIP", "26727", 5.679, -1.943, 1.77, "O9Ib", "ζ Ori", "Ori", 820),
    ("Saiph", "HIP", "27366", 5.796, -9.669, 2.06, "B0.5Ia", "κ Ori", "Ori", 720),
    ("Mintaka", "HIP", "25930", 5.533, -0.299, 2.23, "O9.5II", "δ Ori", "Ori", 900),
    # Big Dipper / Ursa Major
    ("Dubhe", "HIP", "54061", 11.062, 61.751, 1.79, "K0III", "α UMa", "UMa", 124),
    ("Merak", "HIP", "53910", 11.031, 56.382, 2.37, "A1V", "β UMa", "UMa", 79),
    ("Phecda", "HIP", "58001", 11.897, 53.695, 2.44, "A0V", "γ UMa", "UMa", 84),
    ("Megrez", "HIP", "59774", 12.257, 57.032, 3.31, "A3V", "δ UMa", "UMa", 81),
    ("Alioth", "HIP", "62956", 12.900, 55.960, 1.77, "A0pCr", "ε UMa", "UMa", 81),
    ("Mizar", "HIP", "65378", 13.399, 54.925, 2.27, "A1V", "ζ UMa", "UMa", 78),
    ("Alkaid", "HIP", "67301", 13.792, 49.313, 1.86, "B3V", "η UMa", "UMa", 104),
    # Summer Triangle
    ("Sadr", "HIP", "100453", 20.371, 40.257, 2.20, "F8Ib", "γ Cyg", "Cyg", 1800),
    ("Albireo", "HIP", "95947", 19.512, 27.960, 3.18, "K3II", "β Cyg", "Cyg", 380),
    # Southern Cross
    ("Acrux", "HIP", "60718", 12.443, -63.099, 0.77, "B0.5IV", "α Cru", "Cru", 320),
    ("Mimosa", "HIP", "62434", 12.795, -59.689, 1.25, "B0.5III", "β Cru", "Cru", 280),
    ("Gacrux", "HIP", "61084", 12.519, -57.113, 1.63, "M3.5III", "γ Cru", "Cru", 88),
    # Cassiopeia
    ("Schedar", "HIP", "3179", 0.675, 56.537, 2.23, "K0IIIa", "α Cas", "Cas", 228),
    ("Caph", "HIP", "746", 0.153, 59.150, 2.27, "F2III", "β Cas", "Cas", 54),
    ("Navi", "HIP", "4427", 0.945, 60.717, 2.47, "B0IV", "γ Cas", "Cas", 550),
    # Centaurus
    ("Hadar", "HIP", "68702", 14.064, -60.373, 0.61, "B1III", "β Cen", "Cen", 390),
    ("Menkent", "HIP", "68933", 14.111, -36.370, 2.06, "K0III", "θ Cen", "Cen", 61),
    # Taurus
    ("Elnath", "HIP", "25428", 5.438, 28.608, 1.65, "B7III", "β Tau", "Tau", 131),
    # Gemini
    ("Castor", "HIP", "36850", 7.577, 31.888, 1.58, "A1V", "α Gem", "Gem", 52),
    ("Alhena", "HIP", "31681", 6.628, 16.399, 1.93, "A0IV", "γ Gem", "Gem", 109),
    # Leo
    ("Denebola", "HIP", "57632", 11.818, 14.572, 2.14, "A3V", "β Leo", "Leo", 36),
    ("Algieba", "HIP", "50583", 10.333, 19.842, 2.08, "K0III", "γ Leo", "Leo", 126),
    # Virgo
    ("Porrima", "HIP", "61941", 12.694, -1.450, 2.74, "F0V", "γ Vir", "Vir", 39),
    # Scorpius
    ("Shaula", "HIP", "85927", 17.560, -37.104, 1.63, "B1.5IV", "λ Sco", "Sco", 570),
    ("Sargas", "HIP", "86228", 17.621, -42.998, 1.87, "F0II", "θ Sco", "Sco", 270),
    # Ophiuchus
    ("Rasalhague", "HIP", "86032", 17.582, 12.560, 2.08, "A5III", "α Oph", "Oph", 47),
    # Aquila
    ("Tarazed", "HIP", "97278", 19.771, 10.613, 2.72, "K3II", "γ Aql", "Aql", 460),
    # Cygnus
    ("Gienah", "HIP", "102488", 20.770, 33.970, 2.46, "K0III", "ε Cyg", "Cyg", 72),
    # Pegasus
    ("Enif", "HIP", "107315", 21.736, 9.875, 2.39, "K2Ib", "ε Peg", "Peg", 670),
    ("Markab", "HIP", "113963", 23.079, 15.205, 2.49, "B9III", "α Peg", "Peg", 140),
    ("Scheat", "HIP", "113881", 23.063, 28.083, 2.42, "M2.5II", "β Peg", "Peg", 200),
    ("Algenib", "HIP", "1067", 0.220, 15.184, 2.83, "B2IV", "γ Peg", "Peg", 390),
    # Andromeda
    ("Alpheratz", "HIP", "677", 0.140, 29.091, 2.06, "B8IV", "α And", "And", 97),
    ("Mirach", "HIP", "5447", 1.162, 35.620, 2.06, "M0III", "β And", "And", 200),
    ("Almach", "HIP", "9640", 2.065, 42.330, 2.26, "K3IIb", "γ And", "And", 350),
    # Aries
    ("Hamal", "HIP", "9884", 2.120, 23.462, 2.00, "K2III", "α Ari", "Ari", 66),
    ("Sheratan", "HIP", "8903", 1.911, 20.808, 2.64, "A5V", "β Ari", "Ari", 60),
    # Pisces
    ("Alrescha", "HIP", "9487", 2.034, 2.764, 3.82, "A2V", "α Psc", "Psc", 139),
    # Aquarius
    ("Sadalsuud", "HIP", "106278", 21.526, -5.571, 2.87, "G0Ib", "β Aqr", "Aqr", 540),
    ("Sadalmelik", "HIP", "109074", 22.096, -0.320, 2.96, "G2Ib", "α Aqr", "Aqr", 520),
    # Capricornus
    ("Deneb Algedi", "HIP", "107556", 21.784, -16.128, 2.87, "A7IV", "δ Cap", "Cap", 39),
    # Sagittarius
    ("Kaus Australis", "HIP", "90185", 18.403, -34.385, 1.85, "B9.5III", "ε Sgr", "Sgr", 143),
    ("Nunki", "HIP", "92855", 18.921, -26.297, 2.02, "B2.5V", "σ Sgr", "Sgr", 224),
    # Libra
    ("Zubenelgenubi", "HIP", "74785", 15.284, -16.042, 2.75, "A3IV", "α Lib", "Lib", 77),
    ("Zubeneschamali", "HIP", "74785", 15.284, -9.383, 2.61, "B8V", "β Lib", "Lib", 185),
    # Corona Borealis
    ("Alphecca", "HIP", "76267", 15.578, 26.715, 2.23, "A0V", "α CrB", "CrB", 75),
    # Hercules
    ("Rasalgethi", "HIP", "84345", 17.244, 14.390, 3.48, "M5Ib", "α Her", "Her", 360),
    ("Kornephoros", "HIP", "80816", 16.503, 21.490, 2.77, "G7III", "β Her", "Her", 139),
    # Bootes
    ("Izar", "HIP", "72105", 14.750, 27.074, 2.37, "K0II", "ε Boo", "Boo", 202),
    ("Nekkar", "HIP", "68702", 14.064, 40.391, 3.50, "G8III", "β Boo", "Boo", 219),
    # Draco
    ("Eltanin", "HIP", "87833", 17.943, 51.489, 2.23, "K5III", "γ Dra", "Dra", 154),
    ("Rastaban", "HIP", "85670", 17.507, 52.301, 2.79, "G2Ib", "β Dra", "Dra", 380),
    ("Thuban", "HIP", "68756", 14.073, 64.376, 3.65, "A0III", "α Dra", "Dra", 303),
    # Cepheus
    ("Alderamin", "HIP", "105199", 21.309, 62.585, 2.44, "A7IV", "α Cep", "Cep", 49),
    # Lyra
    ("Sheliak", "HIP", "91971", 18.835, 33.363, 3.52, "B7II", "β Lyr", "Lyr", 960),
    ("Sulafat", "HIP", "91926", 18.827, 32.690, 3.24, "B9III", "γ Lyr", "Lyr", 635),
    # Delphinus
    ("Rotanev", "HIP", "101769", 20.625, 14.595, 3.63, "F5IV", "β Del", "Del", 97),
    ("Sualocin", "HIP", "101958", 20.661, 15.912, 3.77, "B9IV", "α Del", "Del", 241),
    # Corvus
    ("Gienah", "HIP", "59803", 12.263, -17.542, 2.59, "B8III", "γ Crv", "Crv", 165),
    ("Algorab", "HIP", "59199", 12.498, -16.515, 2.95, "A0IV", "δ Crv", "Crv", 88),
    # Crater
    ("Labrum", "HIP", "55705", 11.411, -14.779, 3.56, "K0III", "δ Crt", "Crt", 195),
    # Hydra
    ("Alphard", "HIP", "46390", 9.460, -8.658, 1.98, "K3II", "α Hya", "Hya", 177),
    # Puppis
    ("Naos", "HIP", "39429", 8.060, -40.003, 2.25, "O5Ia", "ζ Pup", "Pup", 1080),
    # Vela
    ("Suhail", "HIP", "44816", 9.134, -43.433, 1.96, "K5Ib", "λ Vel", "Vel", 545),
    ("Regor", "HIP", "39953", 8.158, -47.337, 1.75, "WC8", "γ Vel", "Vel", 840),
    # Carina
    ("Miaplacidus", "HIP", "45238", 9.220, -69.717, 1.68, "A2IV", "β Car", "Car", 111),
    ("Avior", "HIP", "41037", 8.375, -59.510, 1.86, "K3II", "ε Car", "Car", 630),
    # Phoenix
    ("Ankaa", "HIP", "2081", 0.438, -42.306, 2.39, "K0III", "α Phe", "Phe", 77),
    # Grus
    ("Alnair", "HIP", "109268", 22.137, -46.961, 1.74, "B7IV", "α Gru", "Gru", 101),
    # Tucana
    ("Al Dhanab", "HIP", "110130", 22.309, -60.260, 2.86, "K3III", "α Tuc", "Tuc", 200),
    # Pavo
    ("Peacock", "HIP", "100751", 20.428, -56.735, 1.94, "B2IV", "α Pav", "Pav", 183),
]


def add_bright_stars():
    """Add bright named stars to catalog."""
    db = SessionLocal()

    try:
        print(f"Adding {len(BRIGHT_STARS)} bright named stars...")

        added = 0
        skipped = 0

        for star_data in BRIGHT_STARS:
            (
                common_name,
                catalog_name,
                catalog_number,
                ra_hours,
                dec_degrees,
                magnitude,
                spectral_type,
                bayer_designation,
                constellation,
                distance_ly,
            ) = star_data

            # Check if star already exists
            existing = (
                db.query(StarCatalog)
                .filter(StarCatalog.catalog_name == catalog_name, StarCatalog.catalog_number == catalog_number)
                .first()
            )

            if existing:
                print(f"  Skipping {common_name} ({bayer_designation}) - already exists")
                skipped += 1
                continue

            # Create new star entry
            star = StarCatalog(
                catalog_name=catalog_name,
                catalog_number=catalog_number,
                common_name=common_name,
                bayer_designation=bayer_designation,
                ra_hours=ra_hours,
                dec_degrees=dec_degrees,
                magnitude=magnitude,
                spectral_type=spectral_type,
                constellation=constellation,
                distance_ly=distance_ly,
            )

            db.add(star)
            added += 1

            if added % 20 == 0:
                db.commit()
                print(f"  Added {added} stars...")

        db.commit()

        # Print statistics
        print("\n" + "=" * 60)
        print("BRIGHT STARS CATALOG ADDITION COMPLETE")
        print("=" * 60)
        print(f"Added: {added}")
        print(f"Skipped: {skipped}")

        # Show star count
        total_stars = db.query(func.count(StarCatalog.id)).scalar()
        print(f"\nTotal stars in catalog: {total_stars}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_bright_stars()
