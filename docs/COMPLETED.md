# Completed Work

Chronological record of shipped features. Plans are archived in `docs/archive/`.

---

## 2026-05 — Unmanned Capture Automation (PR #14)

### Auto-Execute at Dusk
Celery Beat fires `schedule_dusk_execution_task` at 3pm daily. It reads the observer location, computes tonight's astronomical twilight end via `EphemerisService.calculate_twilight_times()`, then queues `auto_execute_plan_task.apply_async(eta=dusk_time)` to fire at the exact moment.
`auto_execute_plan_task` TCP-pings the S50 (`socket.create_connection`); if unreachable it reschedules itself with `countdown=300` up to `autoExecuteRetryCount` attempts (default 6, configurable). On success it dispatches `execute_observation_plan_task` for today's most-recent saved plan.
*PR #14*

### Weather Watchdog
`weather_watchdog_task` runs every 10 minutes (Celery Beat crontab). During astronomical night only. Checks `LocalWeatherService`: aborts the active execution if `is_raining`, `wind_speed_mph > weatherAbortWindMph`, or `humidity_pct >= weatherAbortHumidityPct`. Calls `abort_observation_plan_task.delay(execution_id)` and fires a webhook notification.
*PR #14*

### Session Webhooks
`WebhookService` extended with `send_scope_unreachable_notification`, `send_weather_abort_notification`, `send_session_started_notification`, `send_session_completed_notification`. All use a shared `_post()` retry helper (3 attempts, exponential back-off). Session started/completed hooks fire from `telescope_tasks.py` after state transitions.
*PR #14*

### Auto-Save Before Send to Scope
PlanningView "Send to Scope" button now auto-saves the current plan if not yet saved before uploading, removing the manual save-first requirement.
*PR #14*

### Automation Settings Tab
New "Automation" tab in `SettingsModal.vue`. Two cards: "Auto-Execute at Dusk" (enabled toggle + retry count) and "Weather Abort" (rain toggle + wind mph + humidity % thresholds). All settings persisted via `AppSetting` key-value store with `_PREF_KEYS` / `_PREF_DEFAULTS` pattern.
*PR #14*

---

## 2026-05 — Live Tracking Polish, Comet Toggle, Arp/Sharpless, Custom Target Images (PR #13)

### Auto-Advance and Done Button
`NowPlayingPanel` auto-advances to the next target when all frames for the current target complete (`execution.js` polls frame count). "Skip" button renamed to "Done →" as the primary green action with a tooltip.
*PR #13*

### Include Visible Comets Toggle
`PlanningControls` checkbox appends `"comet"` to `object_types` constraint when checked, causing the scheduler to include tonight's visible comets. Driven by `includeComets` state in `planningStore`.
*PR #13*

### Arp Atlas Catalog
50 Arp peculiar galaxies seeded on startup. `arp_number` column on `CelestialTarget`, `ARP{n}` catalog IDs. Idempotent seeder in `init_catalog.py`.
*PR #13*

### Sharpless HII Catalog
50 Sharpless HII emission regions. `sharpless_number` column on `CelestialTarget`, `SH2-{n}` and `SH{n}` IDs. Idempotent seeder.
*PR #13*

### Custom Target Image URL
Optional `image_url` field (VARCHAR 500) on `UserTarget`. Added to `CustomTargetCreate` / `CustomTargetOut` Pydantic models, create endpoint, and `CustomTargetsPanel.vue` form with thumbnail preview.
*PR #13*

---

## 2026-05 — Horizon UX, Comet Planner, Live Tracking, Catalog Enrichment (PR #12)

### Horizon Scanner UX
Binary (default) and steps scan modes selectable in `HorizonScanModal`. Live SVG chart updates as points arrive. Cancel button wired. Progress bar shows current azimuth.
*PR #12*

### Comet Targets in Plan
`PlanRequest.comet_targets` field. `CometService` fetches ephemeris for requested designations and injects them as `DSOTarget` pseudo-objects (same pattern as planet pseudo-targets). Comets appear in the scheduled timeline.
*PR #12*

### Visible Comets Tonight Card
`TonightView` fetches `GET /api/comets/visible-tonight` and displays a card listing tonight's comets with one-click "Add to Plan" toggle.
*PR #12*

### Live Now-Marker
`PlanTimeline` now-marker `nowX` advances automatically using `executionStore.nowTime`, which is polled from the backend every 30s. Marker moves in real time during an active session.
*PR #12*

### Frame Progress Bar
`NowPlayingPanel` shows "Frame X of Y" with a progress bar and estimated time remaining for the current target.
*PR #12*

### Active Plan ID in Progress
Telescope progress API response includes `active_plan_id` — the saved plan currently running on the S50.
*PR #12*

### Nearby Objects in Catalog Cards
Expandable "Within 2°" section in each catalog card. Fetches `GET /api/targets/near?ra=…&dec=…&radius_deg=2` using haversine distance. Lists up to 10 nearby objects.
*PR #12*

### Caldwell Catalog Seeder
109 Caldwell objects seeded on startup. `C{n}` IDs resolve in `CatalogService`.
*PR #12*

---

## 2026-05 — Multi-Day Weather, Custom Targets, S50 Plan Upload

### Multi-Day Weather Forecast
7-day daily forecast from Open-Meteo (free, no API key). `MultiDayWeatherService` fetches cloud %, temps, wind, precip, and derives an astronomy score (100 − cloud_pct, clamped). `GET /api/weather/multiday` endpoint.
`DailyWeatherStrip.vue` — color-coded 7-column strip (green ≥70, yellow 40–69, red <40) embedded in TonightView between conditions grid and Active Plan card.
Weather store gains `multiDayForecast` state + `fetchMultiDayForecast()` action.
*PR #11*

### Custom Catalog Targets
User-defined observing targets stored in `user_targets` PostgreSQL table (`UserTarget` SQLAlchemy model, Alembic migration).
`CatalogService` merges user targets into `filter_targets()` and `get_all_targets()` — they appear in the Sky tab grid with a purple "Custom" badge.
CRUD API at `/api/targets/custom/`. `CustomTargetsPanel.vue` with add/delete form, plus "My Targets" tab added to `DiscoveryView`.
*PR #11*

### S50 Plan Upload (Send to Scope)
`list_plan()`, `set_plan()`, `delete_plan()` methods added to `SeestarObservationMixin`. Three new endpoints in telescope features API: `GET /api/telescope/features/plan/list`, `POST /api/telescope/features/plan/upload` (converts saved plan to Seestar wire format with RA hours→decimal degrees), `DELETE /api/telescope/features/plan/{name}`.
"Send to Scope" button in PlanningView toolbar (enabled after saving a plan). `planningStore.sendToTelescope(planId)` action.
*PR #11*

---

## 2026-04 — Planet Scheduling, Satellite Avoidance, Horizon Scanner & Profile

### Planet / Moon Wishlist Scheduling
Solar system wishlist items now appear as real time-block entries in the observing plan alongside DSOs (not just a sidebar list). `PlanRequest.solar_targets` field; `planner_service` computes ephemeris at session midpoint, creates `DSOTarget` pseudo-objects (`catalog_id="PLANET:Jupiter"`, `object_type="planet"`). Planets get 10 min, Moon gets 5 min. Planet magnitudes use Meeus Table 33.a with Saturn ring tilt correction.
*PR #10*

### Satellite Avoidance Constraint
`avoid_satellites: bool` added to `ObservingConstraints`. `SatelliteAvoidanceService` downloads Celestrak "visual" TLEs (100 brightest, 24h cache), computes blocked intervals over the imaging window using sgp4/skyfield. Scheduler skips or splits targets that overlap a blocked interval. Frontend toggle in PlanningControls alongside "Avoid moon".
*PR #10*

### Horizon Scanner
`HorizonScannerService` sweeps azimuths (15° steps), binary-searches altitude (5 iterations, 2°–45°) using Pillow top-third/bottom-third brightness ratio (sky:terrain ≥ 1.2 = sky). Telescope moves via `scope_move_to_horizon`, waits 1.8s, captures JPEG from RTSP preview stream.
`POST /api/horizon/scan` starts background scan, `GET /api/horizon/scan/{id}/status` polls progress/points.
`HorizonProfileEditor.vue` in Settings → Horizon tab: SVG preview chart (360×90 viewBox), point table, scan/add/remove/import/export.
*PR #10*

### Horizon Profile in Scheduler
`HorizonPoint(az, alt)` model. `GET/PUT /api/settings/horizon-profile` endpoints (stored as AppSetting). `get_effective_min_altitude(az, profile)` interpolates linearly between breakpoints (wrapping at 0/360). Scheduler uses `max(constraints.min_altitude, effective_min_alt)` per target azimuth.
*PR #10*

---

## 2026-03 — IA Redesign + Execution + Timeline

### IA Redesign: Tonight / Sky / Plan / Observe / Archive
Routes renamed, `TonightView` dashboard added, Archive tab replaces broken Processing stub.
Legacy `/execute` and `/process` redirects preserved.
*Files: `router/index.js`, `AppHeader.vue`, `TonightView.vue`, `ProcessingView.vue`*

### Execution View Redesign
Plan Mode / Manual Mode layout. `NowPlayingPanel` shows current target, next target, skip/extend controls.
Live now-marker ticks in `PlanTimeline`. `skipTarget` / `extendTarget` store actions.
Tier 2 `ControlsDrawer` (gain, exposure, focus, dew heater). Unified left panel with collapsible sections.
*Files: `ExecutionView.vue`, `NowPlayingPanel.vue`, `PlanTimeline.vue`, `stores/execution.js`*

### Interactive Timeline Drag-Editing
Drag-to-move and drag-to-resize on both `PlanTimeline` (session overview) and per-card `TargetVisibilityMini` charts.
Real-time conflict detection: overlap, insufficient slew gap, low-altitude violations.
`setTargetWindow` store action mutates one target without cascading. Card reorder on drag end.
*Files: `PlanTimeline.vue`, `TargetVisibilityMini.vue`, `stores/planning.js`*

### Plan timeline color-coding + planning panel declutter
Color bands on timeline (good/marginal/poor altitude). Planning panel shows only essential controls.
Goto autocomplete in Observe.
*Files: `PlanTimeline.vue`, `PlanningControls.vue`, `GotoPanel.vue`*

### Sky view defaults
Score sort + visible-tonight filter applied on load. Comprehensive scoring algorithm.
*Files: `stores/catalog.js`, `DiscoveryView.vue`*

---

## 2026-02 — Vue 3 SPA + Wishlist + Tier 1 Features

### Vue 3 SPA Migration (Phase 0)
Vite + Vue 3 + Pinia + Vue Router scaffold. FastAPI serves SPA at `/app/`. Root `/` redirects to `/app/`.
Dark scientific color palette (astro-* Tailwind tokens). All vanilla JS functionality ported.
*Plans: `phase0-vue-setup`, `astronomus-modernization`, `lumina-style-redesign`*

### Tier 1 Telescope Features
Settings modal Scope tab: leveling, compass calibration, polar alignment.
MJPEG live preview via `/api/telescope/preview/stream` (threading.Condition, zero-lag).
Alt/Az in header, board temp + battery in Settings → Scope → Hardware Info.
Solar System tab: planets/moons grouped, fast altitude calc (no 144-iteration sweep), add to plan/wishlist.
*Plans: `tier1-features-ux-optimization`*

### Wishlist & Daily Planning
Wishlist API: `GET/PUT /api/settings/wishlist`. Star buttons in CatalogGrid + SolarSystemPanel.
`planningStore.generatePlan()` auto-selects best DSO targets with gap-filling.
DSO wishlist → `preferred_gap_fillers`. Solar system wishlist → `currentPlan.solar_system_targets`.
Save/load plans: `POST /api/plans/`, `GET /api/plans/`, `GET /api/plans/{id}`.
Capture review: `PUT /api/captures/{catalog_id}`, inline review in CatalogGrid expanded cards.
*Plans: `wishlist-daily-plan-design`, `wishlist-daily-plan-implementation`*

---

## 2025-12 — Catalog, Capture History, Layout

### Catalog Browser + Scoring
OpenNGC catalog (12,394 objects), advanced filtering API, score-based sorting.
SearchFilters initialize from store (not hardcoded defaults). Zero-padding fix for catalog IDs.
*Plans: `catalog-browser-enhancement-design`, `catalog-browser-implementation`*

### Capture History Tracking
`CapturedTarget` model. `PUT /api/captures/{catalog_id}`. History displayed in wishlist panel.
*Plans: `capture-history-tracking`, `capture-history-backend-implementation`*

### Gap-Filling Optimizer
Scoring algorithm selects best targets to fill schedule gaps. `preferred_gap_fillers` param.
*Plans: `gap-filling-optimizer-design`*

### File Transfer & Captures API
`GET /api/telescope/files`, file transfer endpoints. Captures linked to plan targets.
*Plans: `file-transfer-captures-api`*

### Unified Layout
Responsive two-panel layout. Discovery/Planning/Execution panels wired to Vue stores.
*Plans: `unified-layout-design`, `unified-layout-implementation`*

### Observe View (pre-Vue migration)
Original observe view redesign before Vue 3 migration.
*Plans: `observe-view-redesign`, `observe-view-implementation`*

---

## 2025-11 — Infrastructure

### PostgreSQL + Alembic Migration
Migrated from SQLite to PostgreSQL. Alembic env.py always reads `DATABASE_URL` env var.
`docker/start.sh` exports `DATABASE_URL` before running migrations.
Test DB (`test_astronomus`) properly migrated via conftest fixture.
*Plans: `catalog-postgres-migration-design`, `pure-alembic-test-fixtures`, `test-fixes-postgres-migration`*

### S50 Test Harness
41 passing tests, 18 skipped (firmware limitations). Mock + hardware + playback test modes.
Wire format fixes for scope_move, scope_speed_move, move_focuser, set_user_location, polar align commands.
*Files: `backend/tests/seestar/`*

### Weather Integration
7Timer astronomy-specific forecasts (seeing, transparency). Local Ambient Weather WS-2902 station.
`wx-service` on `shared-infra` Docker network. WeatherWidget with astronomy suitability score.
