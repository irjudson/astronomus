# Star Capture Guide

## Overview

The Astronomus system now supports capturing images of stars using the Seestar S50 telescope. This includes a catalog of 94 bright named stars and full workflow automation.

## Quick Start

### Automatic Star Selection (Recommended)

Let the system automatically select the brightest visible star:

```bash
cd backend
python3 scripts/capture_star.py
```

This will:
1. Search the star catalog for bright stars (magnitude < 2.0)
2. Calculate which ones are currently visible above 30° altitude
3. Automatically select the highest/brightest visible star
4. Slew to the star
5. Capture 10 stacked frames (default)

### Capture Specific Star

To capture a specific star by name:

```bash
# Capture Vega
python3 scripts/capture_star.py Vega

# Capture Arcturus
python3 scripts/capture_star.py Arcturus

# Capture Sirius
python3 scripts/capture_star.py Sirius

# Capture with more frames
python3 scripts/capture_star.py Vega --frames 20
```

## Available Stars

The catalog includes 94 bright named stars covering 44 constellations:

### Brightest Stars (Magnitude < 0.5)
- **Sirius** (α CMa) - Mag -1.46 - Brightest star in night sky
- **Canopus** (α Car) - Mag -0.72 - Second brightest
- **Rigil Kentaurus** (α Cen) - Mag -0.27 - Alpha Centauri
- **Arcturus** (α Boo) - Mag -0.05 - Brightest in northern sky
- **Vega** (α Lyr) - Mag 0.03 - Summer Triangle
- **Capella** (α Aur) - Mag 0.08 - Winter star
- **Rigel** (β Ori) - Mag 0.13 - Orion's foot
- **Procyon** (α CMi) - Mag 0.38 - Little Dog
- **Achernar** (α Eri) - Mag 0.46 - End of the River
- **Betelgeuse** (α Ori) - Mag 0.50 - Orion's shoulder

### Navigation Stars
- **Polaris** (α UMi) - North Star
- **Deneb** (α Cyg) - Summer Triangle
- **Altair** (α Aql) - Summer Triangle

### Constellation Patterns
- **Big Dipper**: Dubhe, Merak, Phecda, Megrez, Alioth, Mizar, Alkaid
- **Orion**: Rigel, Betelgeuse, Bellatrix, Alnilam, Alnitak, Mintaka, Saiph
- **Southern Cross**: Acrux, Mimosa, Gacrux, Imai

### Seasonal Highlights
- **Spring**: Arcturus, Spica, Regulus
- **Summer**: Vega, Altair, Deneb
- **Fall**: Fomalhaut, Aldebaran
- **Winter**: Sirius, Capella, Rigel, Betelgeuse

Full list: See database query or `/api/catalog/search?type=star`

## Workflow Details

The capture script performs these steps:

1. **Search Catalog**
   - Queries star_catalog table for matching star
   - Retrieves RA, Dec, magnitude, and other data

2. **Calculate Visibility**
   - Computes current Alt/Az coordinates for your location
   - Checks if star is above minimum altitude (30°)
   - Selects best target if multiple candidates

3. **Connect to Telescope**
   - Establishes connection to Seestar S50 at 192.168.2.47:4700
   - Verifies connection and retrieves current status

4. **Slew to Target**
   - Uses `goto_target()` with Alt/Az mode (default)
   - Converts RA/Dec → Alt/Az coordinates
   - Commands telescope to move to target
   - Waits for slew completion (~15 seconds)

5. **Start Imaging**
   - Starts stacking mode with `start_imaging(restart=True)`
   - Captures specified number of frames
   - Monitors progress every 10 seconds

6. **Stop & Save**
   - Stops imaging when complete
   - Images saved to telescope storage:
     - `/mnt/seestar/stack/` - Stacked images
     - `/mnt/seestar/IMG/` - Individual frames

## Mount Modes

The system supports two mount modes:

### Alt/Az Mode (Default)
- No initialization required
- Quick and simple
- Good for bright star captures
- Coordinates drift over time due to Earth's rotation

**Best for**: Quick star captures, testing, bright star imaging

### Equatorial Mode (Advanced)
- Requires initialization: `await client.initialize_equatorial_mode()`
- Provides continuous tracking
- More accurate long-term positioning
- Takes 30-60 seconds to initialize

**Best for**: Long exposures, precise tracking, fainter targets

See `docs/MOUNT_MODES.md` for complete details.

## API Integration

The unified search API includes stars:

```bash
# Search for a star
curl "http://localhost:9247/search/unified?query=vega"

# Returns:
{
  "query": "vega",
  "total_results": 1,
  "results": {
    "dsos": [],
    "stars": [
      {
        "type": "star",
        "name": "Vega",
        "catalog_id": "HIP91262",
        "bayer_designation": "α Lyr",
        "ra_hours": 18.615,
        "dec_degrees": 38.783,
        "magnitude": 0.03,
        "spectral_type": "A0V",
        "constellation": "Lyr",
        "distance_ly": 25.0
      }
    ],
    "planets": []
  }
}
```

## Programmatic Usage

```python
from app.clients.seestar_client import SeestarClient
from app.models.catalog_models import StarCatalog

# Get star from database
star = db.query(StarCatalog).filter(
    StarCatalog.common_name == "Vega"
).first()

# Connect and capture
client = SeestarClient()
await client.connect("192.168.2.47", 4700)

# Slew to star
await client.goto_target(
    ra_hours=star.ra_hours,
    dec_degrees=star.dec_degrees,
    target_name=star.common_name
)

# Start imaging
await client.start_imaging(restart=True)

# Wait for capture
await asyncio.sleep(60)  # Capture for 1 minute

# Stop imaging
await client.stop_imaging()

await client.disconnect()
```

## Troubleshooting

### "No bright stars currently visible"
- Check time of day - need stars above 30° altitude
- Try different time (early morning or evening)
- Verify location coordinates in script (Montana default: 45.729°N, 111.4857°W)

### "Connection failed"
- Verify telescope is powered on
- Check telescope is on same network (192.168.2.47)
- Ensure no other clients connected to telescope

### "Goto failed"
- Telescope may be in wrong state
- Try stopping any active view/imaging first
- Check mount mode status

### "Large pointing error"
- Expected in Alt/Az mode (coordinates drift)
- Star should still be in field of view
- Use Equatorial mode for better accuracy

## Next Steps

- **Add More Stars**: Integrate full Hipparcos/Tycho-2 catalog (2.5M stars)
- **Planetary Capture**: Capture planets using same workflow
- **Auto-focus**: Add auto-focus before imaging
- **Plate Solving**: Verify actual pointing with plate solving

## Reference

- Star catalog: `/home/irjudson/Projects/astronomus/backend/app/models/catalog_models.py`
- Client API: `/home/irjudson/Projects/astronomus/backend/app/clients/seestar_client.py`
- Capture script: `/home/irjudson/Projects/astronomus/backend/scripts/capture_star.py`
- Mount modes doc: `/home/irjudson/Projects/astronomus/backend/docs/MOUNT_MODES.md`
