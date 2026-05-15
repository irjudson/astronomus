# Astronomus Roadmap

**Last Updated**: 2026-05-15

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

### Horizon UX, Comet Planner, Live Tracking, Catalog Enrichment (2026-05 — PR #12)
- Horizon scanner binary/steps mode with live SVG update and cancel button
- Comet targets in plan — `PlanRequest.comet_targets`; CometService ephemeris injected as DSOTarget pseudo-objects
- "Currently visible comets" card in Tonight view with one-click plan toggle
- Live now-marker advances from `executionStore.nowTime` (polled from backend)
- Frame progress bar in NowPlayingPanel — "Frame X of Y" with time remaining
- `active_plan_id` in telescope progress response
- Nearby objects in catalog cards — expandable "within 2°" list via `/api/targets/near`
- Caldwell seeder — 109 Caldwell objects seeded on startup; C{n} IDs resolve

### Live Tracking Polish, Comet Toggle, Arp/Sharpless, Custom Target Images (2026-05 — PR #13)
- Auto-advance when frames complete — NowPlayingPanel skips to next target automatically
- "Done →" primary green button; tooltip added
- "Include visible comets" plan toggle in PlanningControls
- Arp Atlas catalog — 50 Arp peculiar galaxies, `arp_number` column, ARP{n} IDs, idempotent seeder
- Sharpless HII catalog — 50 Sharpless regions, `sharpless_number` column, SH2-{n}/SH{n} IDs
- Custom target `image_url` — optional field: migration, model, API models, create endpoint, form + thumbnail

### Unmanned Capture Automation (2026-05 — PR #14)
- Auto-execute at dusk — Celery Beat 3pm task computes astronomical twilight, queues plan via `apply_async(eta=...)`
- Scope connectivity retries — TCP-ping every 5 min, up to 6 configurable attempts before giving up
- Weather watchdog — every 10 min during astronomical night; aborts on rain, excess wind, or high humidity
- Session webhooks — scope unreachable, session started, session completed/aborted
- Auto-save before "Send to Scope" — no manual save required
- Automation settings tab — auto-execute toggle, retry count, weather abort thresholds

---

## 🚧 Next (Prioritized)

### 1. Post-Capture Processing Pipeline
The processing backend (auto-stretch, TIFF export, Celery jobs) exists and is wired. The Archive tab UI is functional. What's missing:
- File ingest from `$SEESTAR_FITS_PATH` mount showing captured sessions
- Job queue visibility in the Archive tab (submit, status, cancel)
- 16-bit TIFF export pipeline end-to-end (backend exists, UI wiring needed)
- Batch processing multiple sessions

### 2. Unmanned Capture Reliability Improvements
Now that the automation layer exists, a few gaps remain:
- Webhook delivery confirmation / retry visibility in UI
- "Session dry run" — validate plan and scope reachability without actually starting
- Notification when daily plan generation fails (no targets for tonight)
- Manual trigger button in UI for "run plan now" (bypasses dusk timer)

### 3. Horizon Scanner UX Polish
The scanner works. Remaining minor gaps:
- Auto-save prompt on scan completion (currently user must manually save)
- Scan quality indicator — flag azimuths with ambiguous brightness ratio

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
