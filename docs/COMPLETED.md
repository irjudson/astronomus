# Completed Work

Chronological record of shipped features. Plans are archived in `docs/archive/`.

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
