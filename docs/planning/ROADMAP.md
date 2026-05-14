# Astronomus Roadmap

**Last Updated**: 2026-05-14

---

## ✅ Shipped (Chronological)

### Infrastructure & Core (2025-11)
- PostgreSQL + Alembic migration (from SQLite)
- S50 test harness — 41 passing, 18 skipped (firmware)
- 7Timer astronomy forecasts (seeing, transparency) + local Ambient Weather WS-2902
- OpenNGC catalog import (12,394 objects)

### Catalog, Layout, Processing Backend (2025-12)
- Catalog browser: score sort, visible-tonight filter, per-card score breakdown
- Gap-filling optimizer + wishlist `preferred_gap_fillers`
- GPU-accelerated FITS stacking (CuPy, auto-stretch)
- Capture history tracking

### Vue 3 SPA + Wishlist + Tier 1 Telescope Features (2026-02)
- Vite + Vue 3 + Pinia + Vue Router; FastAPI serves SPA at `/app/`
- Settings Scope tab: leveling, compass calibration, polar alignment wizard
- MJPEG live preview (`/api/telescope/preview/stream`)
- Solar System tab: planets/moons with real-time altitude, add to plan/wishlist
- Save/load plans; daily auto-planning with Celery Beat

### IA Redesign + Interactive Timeline (2026-03)
- Navigation: Tonight / Sky / Plan / Observe / Archive
- Interactive timeline drag-editing with conflict detection
- Plan timeline color-coding (altitude bands)
- Sky view defaults (score sort + visible-tonight on load)

### Planet Scheduling, Satellite Avoidance, Horizon Scanner & Profile (2026-04 — PR #10)
- Planet/moon wishlist items injected as real time-blocks in observing plan
- Planet magnitudes via Meeus Table 33.a with Saturn ring tilt
- `avoid_satellites` constraint: Celestrak visual TLEs, blocked-interval scheduling
- Horizon scanner: telescope sweep with brightness-ratio sky/terrain detection
- Per-azimuth horizon profile stored and used by scheduler (linear interpolation)
- Settings → Horizon tab with SVG chart, scan button, import/export

### Multi-Day Weather, Custom Targets, S50 Plan Upload (2026-05 — PR #11)
- Open-Meteo 7-day forecast; `DailyWeatherStrip` in Tonight view
- User-defined custom catalog targets (`user_targets` table, CRUD API, My Targets tab in Sky)
- S50 plan upload: `set_plan`/`list_plan`/`delete_plan` via seestar-api; "Send to Scope" button in Plan view

---

## 🚧 Next (Prioritized)

### 1. Horizon Autoscan UX Polish
The scanner works but requires careful setup (telescope connected, daytime, clear sky). Remaining gaps:
- Progress modal with live SVG update while scanning
- Auto-save prompt on scan completion
- Scan from fixed alt steps (not binary search) option for faster results

### 2. Post-Capture Processing Pipeline
The processing backend (auto-stretch, TIFF export, Celery jobs) exists and is wired. The Archive tab UI is functional. What's missing:
- File ingest from `$SEESTAR_FITS_PATH` mount
- Job queue visibility in the Archive tab
- 16-bit TIFF export pipeline (backend exists, UI wiring needed)
- Batch processing multiple sessions

### 3. Comet / Asteroid Ephemeris
MPC integration for comet catalog refresh is implemented (`POST /comets/refresh`). Still needed:
- Live position computation at session time (RA/Dec from orbital elements)
- Comet targets injected into scheduler (same pattern as planet pseudo-targets)
- "Currently visible comets" indicator in Sky view

### 4. Live Session Tracking
WebSocket or polling link between Observe view and the currently-executing plan on the telescope:
- Auto-advance now-marker when telescope reports target change
- Remaining frames / time estimate from S50 status

### 5. Catalog Enrichment
- Caldwell, Arp, Sharpless catalog import (sources and schema ready)
- Image thumbnails for custom targets
- "Objects near X" angular proximity search

---

## 📋 Backlog (No ETA)

- Mosaic planning (multi-panel FOV, overlap calculator)
- Multi-telescope support / equipment profiles
- Mobile PWA / offline favorites
- Interactive sky map (planetarium overlay)
- Satellite imagery for cloud forecasting
- PixInsight / Siril export integration
- Kubernetes deployment / horizontal scaling

---

## 🚫 Explicitly Deferred

**Processing UI completeness** — deferred until capture reliability (horizon scan, plan upload, live tracking) is solid. No point optimizing post-processing before sessions reliably execute.

---

*Architecture and API docs: `docs/architecture/`*
*Configuration reference: `docs/CONFIGURATION.md`*
