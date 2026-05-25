# Architecture Documentation

Technical architecture and implementation details for Astronomus — an astrophotography session planner for the Seestar S50 smart telescope.

## Table of Contents
- [System Overview](#system-overview)
- [Container Topology](#container-topology)
- [Backend Services](#backend-services)
- [Frontend Architecture](#frontend-architecture)
- [Data Models](#data-models)
- [Background Task System](#background-task-system)
- [External Integrations](#external-integrations)
- [Key Algorithms](#key-algorithms)
- [API Surface](#api-surface)

---

## System Overview

### Technology Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.100+ with Uvicorn (ASGI) |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Database | PostgreSQL 14 (internal to container) |
| Task queue broker | Redis 7 (internal to container) |
| Background workers | Celery 5 (worker + beat scheduler) |
| Astronomical math | Skyfield (DE421 ephemeris) + Astropy |
| Frontend framework | Vue 3 (Composition API) |
| Frontend build | Vite |
| State management | Pinia |
| Routing | Vue Router 4 |
| CSS | Tailwind CSS |
| HTTP client (frontend) | Axios |
| Python version | 3.11+ |
| Container runtime | Docker (single container, `astronomus`) |

---

## Container Topology

The entire stack runs inside one Docker container (`astronomus`, port 9247). PostgreSQL and Redis run as processes within the same container. An optional `shared-infra` external Docker network connects the container to a `wx-service` sidecar providing Ambient Weather WS-2902 data.

```
+------------------------------------------------------------------+
|  Host machine                                                    |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  Docker container: astronomus  (port 9247)                 |  |
|  |                                                            |  |
|  |  +------------------+    +----------------------------+    |  |
|  |  |  Uvicorn / FastAPI|    |  Celery Worker(s)          |    |  |
|  |  |  app/main.py     |    |  + Celery Beat scheduler    |    |  |
|  |  +--------+---------+    +----------+-----------------+    |  |
|  |           |                         |                       |  |
|  |  +--------v---------+    +----------v-----------+          |  |
|  |  |  PostgreSQL 14   |    |  Redis 7 (broker +   |          |  |
|  |  |  (astronomus DB) |    |  result backend)      |          |  |
|  |  +------------------+    +---------------------+           |  |
|  |                                                            |  |
|  |  Volumes:                                                  |  |
|  |    astronomus-pgdata  ->  /var/lib/postgresql/14/main      |  |
|  |    ./backend/app      ->  /app/app         (live reload)   |  |
|  |    ./frontend         ->  /app/frontend    (built dist)    |  |
|  |    $SEESTAR_FITS_PATH ->  /fits            (FITS files)    |  |
|  |    ./data             ->  /app/data        (cache, ephem.) |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +---------------------+   External network: shared-infra       |
|  |  wx-service         |   (optional; provides local weather)   |
|  |  (Ambient WS-2902)  |                                        |
|  +---------------------+                                        |
|                                                                  |
|  Seestar S50 telescope  <---  TCP/WiFi  192.168.2.47:4700       |
+------------------------------------------------------------------+
```

An optional `flower` container (profile: `monitoring`) can be started to inspect Celery tasks via a web UI on port 5555.

---

## Backend Services

All services live in `backend/app/services/`. The main entry point is `backend/app/main.py`, which creates the FastAPI app, registers CORS middleware, mounts Vue SPA static assets at `/app/`, and registers all API routers under `/api`.

### PlannerService (`planner_service.py`)

Orchestrates the full plan-generation workflow. Called by `POST /api/plan`.

Steps in order:
1. Calculate twilight times via `EphemerisService` (astronomical dusk to astronomical dawn defines the imaging window)
2. Filter DSO candidates from `CatalogService` (up to magnitude 12, matching requested object types)
3. Optionally inject solar system targets from `PlanetaryEphemeris` and comet targets from `CometService`
4. Fetch weather forecast via `WeatherService`
5. Optionally fetch satellite blocked intervals via `SatelliteAvoidanceService`
6. Run the greedy scheduler via `SchedulerService`
7. Detect and fill schedule gaps (preferring wishlist targets)
8. Look up sky quality via `LightPollutionService`
9. Return a complete `ObservingPlan` Pydantic model

### EphemerisService (`ephemeris_service.py`)

Astronomical position calculations using Skyfield with the JPL DE421 ephemeris (`data/ephemeris/de421.bsp`).

Key methods:
- `calculate_twilight_times()` — finds sunset, civil/nautical/astronomical twilight start and end, sunrise using Skyfield `almanac.dark_twilight_day`
- `calculate_position()` — returns (altitude, azimuth) for a target at a given time; results are cached in a module-level dict keyed by (ra, dec, lat, lon, 60s time bucket) with a 1,000-entry eviction cap
- `calculate_field_rotation_rate()` — field rotation rate in degrees/minute for alt-az mounts
- `is_target_visible()` — checks altitude against `min_altitude`/`max_altitude` and, when present, a per-azimuth `horizon_profile` via linear interpolation

### SchedulerService (`scheduler_service.py`)

Greedy scheduling algorithm with urgency-based lookahead. See [Key Algorithms](#key-algorithms) for scoring details.

Planning modes (set by `constraints.planning_mode`):

| Mode | Min duration | Max duration | Min score | Max targets/night |
|---|---|---|---|---|
| quality | 45 min | 180 min | 0.70 | 8 |
| balanced | 20 min | 90 min | 0.60 | 15 |
| quantity | 15 min | 45 min | 0.50 | 20 |

### CatalogService (`catalog_service.py`)

Reads and filters the `dso_catalog` PostgreSQL table. Converts `DSOCatalog` ORM rows to `DSOTarget` Pydantic models. Merges user-defined targets from `user_targets` into the same result set. Also calculates real-time visibility (`TargetVisibility`) by calling `EphemerisService.calculate_position()`.

The catalog currently holds 12,394+ DSO entries across NGC, IC, Messier, Caldwell, Arp, and Sharpless catalogs.

### WeatherService (`weather_service.py`)

Fetches forecast data from two sources and merges them:
- OpenWeatherMap — cloud cover, humidity, temperature, wind (requires `OPENWEATHERMAP_API_KEY`)
- 7Timer (`SevenTimerService`) — astronomy-specific seeing and transparency estimates

Falls back to an optimistic default forecast if both sources fail.

### MultiDayWeatherService (`multi_day_weather_service.py`)

Fetches a 7-day daily forecast from Open-Meteo (no API key required). Used by the Tonight dashboard weather strip. Returns a list of `DailyForecast` objects with `astronomy_score` derived from mean cloud cover.

### LocalWeatherService (`local_weather_service.py`)

Calls `http://wx-service:8000/api/weather/latest` (3-second timeout) to read current conditions from the Ambient Weather WS-2902 station. Returns a `LocalWeatherReading` with temperature, humidity, wind speed, rain rate, UV index, and solar radiation. Used by the weather watchdog Celery task to abort observations on rain or high wind.

### SatelliteAvoidanceService (`satellite_avoidance_service.py`)

Downloads visual-orbit TLEs from Celestrak (`GROUP=visual`) and caches them for 24 hours. Uses Skyfield's `EarthSatellite` to propagate each satellite and find passes above `MIN_ELEVATION_DEG` (10°) during the imaging window. Returns a list of `BlockedInterval` objects. The scheduler skips time slots that overlap any blocked interval.

### HorizonScannerService (`horizon_scanner_service.py`)

Autonomous horizon profiling: sweeps telescope azimuths in configurable steps (default 15°), pointing the scope at each azimuth and binary-searching the altitude where the top-third/bottom-third brightness ratio crosses a threshold (`SKY_RATIO_THRESHOLD = 1.2`). Each azimuth requires `BINARY_SEARCH_ITERATIONS = 5` pointing moves. Results are streamed as server-sent events via `GET /api/horizon/scan/{id}/status`.

### TelescopeService + SeestarClient (`telescope_service.py`, `clients/seestar/`)

The `SeestarClient` is assembled from five mixins over a `SeestarTransport` base:
- `SeestarTransport` — async TCP JSON-RPC over port 4700
- `SeestarMountMixin` — goto, park, speed-move, focuser
- `SeestarObservationMixin` — start/stop stacking, plan upload (`set_plan`), preview
- `SeestarSystemMixin` — device state, location, firmware
- `SeestarFilesMixin` — file listing and retrieval

Plan upload format: `set_plan(name, targets)` where RA is in decimal degrees (hours × 15) and each target carries `{name, ra, dec, lp_filter, gain, exp_time, count}`.

The MJPEG preview stream is served at `/api/telescope/preview/stream` by pulling frames from an RTSP capture service (`rtmp_preview_service.py`) and delivering them as multipart JPEG.

### Other Services

| Service | Purpose |
|---|---|
| `CometService` | CRUD and ephemeris for `comet_catalog` table; Keplerian propagation |
| `AsteroidService` | CRUD and ephemeris for `asteroid_catalog` table |
| `PlanetService` / `PlanetaryEphemeris` | Planet/moon positions via Astropy `get_body()` + single AltAz frame |
| `LightPollutionService` | Bortle class estimation from geographic coordinates |
| `ImagePreviewService` | On-demand DSO preview image fetch from SkyView; cached in `/app/data/previews/` |
| `ExportService` | Converts `ObservingPlan` to JSON, `seestar_alp`, CSV, or plain text |
| `WebhookService` | HTTP POST notifications for plan creation, weather abort, scope unreachable |
| `FileScannerService` | Walks the `/fits` mount to discover capture files |
| `ProcessingService` / `StackingService` | FITS stacking pipeline (requires files in `/fits`) |
| `SettingsService` | Reads/writes `app_settings` key-value table and `observing_locations` |

---

## Frontend Architecture

The Vue 3 SPA is built with Vite and served from `/app/` by FastAPI's static file mount. All routes are caught by a FastAPI catch-all that returns `frontend/vue-app/dist/index.html`.

### Views (Vue Router routes)

| Path | Component | Purpose |
|---|---|---|
| `/` | `TonightView` | Dashboard: conditions, telescope status, active plan, 7-day weather strip |
| `/sky` | `DiscoveryView` | DSO catalog grid, Solar System panel, Custom Targets panel |
| `/plan` | `PlanningView` | Plan generation, drag-editable timeline, wishlist, saved plans |
| `/observe` | `ExecutionView` | Plan Mode (NowPlayingPanel) and Manual Mode (goto/capture/focus controls) |
| `/archive` | `ProcessingView` | FITS file browser, processing pipeline |
| `/execute` | redirect → `/observe` | Legacy URL |
| `/process` | redirect → `/archive` | Legacy URL |

### Pinia Stores

| Store | State managed |
|---|---|
| `app` | Sidebar / right-panel / console collapsed state |
| `settings` | User preferences (location, telescope host, planning defaults); persists to `localStorage` and `PUT /api/settings/user` |
| `catalog` | DSO items, filters, pagination, wishlist, capture map; page-ahead prefetch cache (5 pages) |
| `planning` | `currentPlan`, `savedPlans`, constraints, comet wishlist, execution polling state |
| `execution` | Telescope connection, position, imaging/recording state, plan execution progress, hardware readings |
| `telescope` | Simple connection status and live RA/Dec/Alt/Az (composition API store) |
| `processing` | FITS file list and processing job state |
| `weather` | Current conditions and multi-day forecast |
| `toast` | Transient notification queue |

### Key Component Groups

**Discovery (`components/discovery/`)**
- `CatalogGrid` — paginated DSO card grid; `ResizeObserver` on the grid element calculates dynamic page size from available height (`CARD_ROW_HEIGHT = 346`, `PAGINATION_HEIGHT = 52`)
- `SolarSystemPanel` — planets/moons with live altitude and add-to-plan/wishlist buttons
- `CustomTargetsPanel` — CRUD for user-defined targets
- `SearchFilters` — type, constellation, magnitude, sort, visible-tonight filters

**Planning (`components/planning/`)**
- `PlanningControls` — session parameters, constraints, generate button, tabbed wishlist/saved-plans panel
- `PlanTimeline` — drag-editable scheduled-target timeline with conflict detection and live now-marker

**Execution (`components/execution/`)**
- `NowPlayingPanel` — active target display with skip/extend controls
- `PlanExecutionPanel` — full plan view with live progress
- `LivePreviewPanel` — MJPEG stream from `/api/telescope/preview/stream`
- `ImagingPanel`, `FocuserPanel`, `DirectionalControlPanel` — manual telescope controls

**Shared**
- `SettingsModal` — tabs for General, Planning, Scope settings, and Horizon profile editor
- `HorizonProfileEditor` — SVG chart + scan/import/export controls
- `DailyWeatherStrip` — 7-day color-coded weather cards from Open-Meteo

---

## Data Models

### SQLAlchemy Tables

| Table | Model class | Purpose |
|---|---|---|
| `dso_catalog` | `DSOCatalog` | 12,394+ deep sky objects (NGC, IC, Messier, Caldwell, Arp, Sharpless) |
| `user_targets` | `UserTarget` | User-defined custom observing targets |
| `star_catalog` | `StarCatalog` | Named stars with Bayer/Flamsteed designations |
| `constellation_names` | `ConstellationName` | 3-letter abbreviation → full name lookup |
| `comet_catalog` | `CometCatalog` | Comets with Keplerian orbital elements |
| `asteroid_catalog` | `AsteroidCatalog` | Asteroids with Keplerian orbital elements |
| `saved_plans` | `SavedPlan` | Complete `ObservingPlan` stored as JSON blob |
| `telescope_executions` | `TelescopeExecution` | Execution records with state machine (starting/running/paused/completed/aborted/error) |
| `telescope_execution_targets` | `TelescopeExecutionTarget` | Per-target progress within an execution |
| `capture_history` | `CaptureHistory` | Aggregated capture stats per catalog ID (total frames, exposure, FWHM) |
| `output_files` | `OutputFile` | Individual FITS/image files linked to targets and executions |
| `observing_locations` | `ObservingLocation` | Saved observer locations with Bortle class |
| `seestar_devices` | `SeestarDevice` | Telescope device configurations (control host/port, mount path) |
| `app_settings` | `AppSetting` | Key-value store for all application settings |
| `image_source_stats` | `ImageSourceStats` | Success/failure tracking for preview image sources |

### Key Pydantic Models (`models/models.py`)

- `Location` — name, latitude, longitude, elevation, IANA timezone
- `ObservingConstraints` — min/max altitude, object types, planning mode, horizon profile, `avoid_satellites` flag
- `PlanRequest` — location, date, constraints, optional `preferred_gap_fillers`, `solar_targets`, `comet_targets`
- `DSOTarget` — catalog_id, RA/Dec, object_type, magnitude, size_arcmin, optional capture_history and visibility
- `TargetVisibility` — current altitude/azimuth, status (visible/rising/setting/below_horizon), best time tonight
- `ScheduledTarget` — target + start/end times, altitude points at 15-min intervals, field rotation rate, score
- `TargetScore` — visibility_score (0-1), weather_score (0-1), object_score (0-1), total_score (0-1)
- `ObservingPlan` — session, location, constraints, scheduled_targets, weather_forecast, gap_fill_stats, candidates
- `SessionInfo` — all twilight times plus imaging_start/end and total_imaging_minutes
- `WeatherForecast` / `DailyForecast` — hourly and daily forecast with astronomy-specific fields (seeing, transparency)

---

## Background Task System

Celery uses Redis as both the broker and result backend (`REDIS_URL`, database 1). Beat scheduler timezone defaults to `CELERY_TIMEZONE` env var (default: `America/Denver`).

### Scheduled Tasks (Celery Beat)

| Task name | Schedule | Purpose |
|---|---|---|
| `generate_daily_plan` | Daily 12:00 (local) | Generates and saves tonight's plan using Quality mode; fires optional webhook on completion |
| `schedule_dusk_execution` | Daily 15:00 (local) | Computes tonight's astronomical dusk, schedules `auto_execute_plan` via `apply_async(eta=dusk_time)` |
| `weather_watchdog` | Every 10 minutes | During astronomical night: reads local weather station, aborts active execution on rain/high wind/extreme humidity; fires webhook |
| `cleanup_old_jobs` | Daily 02:00 (local) | Removes old processing job records |

### On-Demand Tasks

| Task | Triggered by | Purpose |
|---|---|---|
| `auto_execute_plan` | `schedule_dusk_execution` at dusk | Connects to S50, uploads plan, starts execution; retries every 5 min (up to 6 times) if telescope unreachable |
| `execute_observation_plan_task` | Manual "Start Execution" or auto-execute | Drives telescope through each scheduled target: goto → focus → image |
| `abort_observation_plan_task` | Weather watchdog or manual abort | Stops current imaging and parks scope |
| `process_fits_task` | `POST /api/processing/jobs` | Runs FITS stacking pipeline |

### Weather Abort Logic (`weather_watchdog_task`)

Configured via `app_settings` keys:
- `weather.abort_on_rain` (default: true)
- `weather.abort_wind_mph` (default: 25.0)
- `weather.abort_humidity_pct` (default: 95)

---

## External Integrations

| System | Protocol | Purpose |
|---|---|---|
| Seestar S50 telescope | TCP JSON-RPC, port 4700 (WiFi) | Goto, focus, imaging control, plan upload, device state |
| Seestar S50 RTSP stream | RTSP port 4554 | Live preview frames, delivered as MJPEG at `/api/telescope/preview/stream` |
| OpenWeatherMap API | HTTPS | Cloud cover, humidity, temperature, wind for weather scoring |
| 7Timer API | HTTPS | Astronomy seeing and transparency forecasts |
| Open-Meteo API | HTTPS | 7-day daily weather forecast for Tonight dashboard (no API key) |
| Celestrak | HTTPS | Visual-orbit TLE catalog for satellite avoidance (cached 24h) |
| JPL DE421 ephemeris | Local file | Twilight calculations, sun/planet positions |
| SkyView (NASA) | HTTPS | On-demand DSO preview image fetch (cached locally) |
| wx-service (Ambient WS-2902) | HTTP, `shared-infra` network | Real-time local weather station readings |
| Webhook endpoint | HTTPS POST | Notifications: plan created, weather abort, scope unreachable |

---

## Key Algorithms

### 1. Target Scoring (composite 0-1 score)

```
total_score = visibility_score * 0.4
            + weather_score    * 0.3
            + object_score     * 0.3
```

**Visibility score** (weighted sum):
- Altitude score (0.5 weight): 1.0 at 45-65°, degrades linearly below or above
- Field rotation score (0.3 weight): 1.0 below 0.5°/min, 0.3 above 2.0°/min
- Duration score (0.2 weight): linear 0→1 up to 120 minutes

**Object score** (weighted sum):
- Brightness score (0.6 weight): 1.0 below magnitude 6, 0.3 above magnitude 10
- Size score (0.4 weight): 1.0 when object is 0.3×–1.2× the S50 FOV diagonal (≈85 arcmin); penalised below 0.1× or above 3×

### 2. Urgency Bonus

After scoring, each target receives a +0.2 bonus if it will set below `min_altitude` within the next 30 minutes (configurable `lookahead_minutes`). This ensures time-critical targets get scheduled before they disappear. Wishlist targets additionally receive a +0.3 priority boost.

### 3. Visibility Duration via Binary Search

`_calculate_visibility_duration()` uses binary search (1-minute precision) rather than stepping through every minute, reducing O(n) scans to O(log n) for each candidate:

```
low = current_time
high = session_end_time
while (high - low) > 1 minute:
    mid = (low + high) / 2
    if target still visible at mid:
        low = mid   # setting time is later
    else:
        high = mid  # setting time is earlier
return low - current_time
```

### 4. Field Rotation Rate

For alt-azimuth mounts, the image field rotates as the telescope tracks a sidereal target:

```
rate (deg/hr) = 15 * cos(latitude) / cos(altitude) * |sin(azimuth)|
```

Where 15°/hr is Earth's rotation rate. The rate approaches infinity near the zenith (`cos(altitude) → 0`) and is zero on the meridian (`sin(azimuth) = 0`). A rate below 0.5°/min scores 1.0; above 2.0°/min scores 0.3.

### 5. Horizon Scanner Binary Search

For each azimuth step the scanner binary-searches altitude between `alt_min` and `alt_max` in `BINARY_SEARCH_ITERATIONS = 5` iterations. At each candidate altitude the telescope is pointed, a JPEG frame is captured, and the top-third/bottom-third brightness ratio is computed. A ratio above `SKY_RATIO_THRESHOLD = 1.2` indicates sky; below `TERRAIN_RATIO_THRESHOLD = 0.9` indicates terrain. The final breakpoint is the lowest altitude that still shows sky.

### 6. Satellite Avoidance

TLEs are propagated with Skyfield's `EarthSatellite.find_events()` for the session window. Any pass with elevation above 10° creates a `BlockedInterval`. The scheduler skips forward to after the interval's end time (plus 30 seconds) when a candidate slot overlaps.

### 7. Gap Filling

After the primary greedy schedule, `PlannerService` detects unfilled time gaps (intervals between scheduled targets, or between the session start and the first target, longer than `min_target_duration_minutes`). Each gap is offered to wishlist targets first, then to any unscheduled candidate. Statistics are returned in `GapFillStats`.

---

## API Surface

The full OpenAPI spec is available at `/api/docs` (Swagger UI) or `/api/redoc`. Key router groups:

| Prefix | Router module | Coverage |
|---|---|---|
| `/api/plan` | `routes.py` | Plan generation, scoring, catalog search, sky quality, shared plan links |
| `/api/plans/` | `plans.py` | CRUD for saved plans |
| `/api/targets/` | `routes.py` | DSO target list, scored targets, nearby targets, single target lookup |
| `/api/catalog/search` | `routes.py` | Paginated catalog search with optional comprehensive scoring |
| `/api/comets/` | `comets.py` | Comet catalog CRUD and ephemeris |
| `/api/asteroids/` | `asteroids.py` | Asteroid catalog CRUD and ephemeris |
| `/api/planets/` | `planets.py` | Planet visibility and ephemeris |
| `/api/solar-system/objects` | `routes.py` | All solar system bodies with current altitude |
| `/api/telescope/` | `telescope.py` | Connect, goto, imaging, focus, plan upload |
| `/api/telescope/features/` | `telescope_features.py` | Higher-level telescope features |
| `/api/telescope/preview/` | `routers/preview.py` | MJPEG frame and SSE stream |
| `/api/horizon/` | `horizon.py` | Horizon profile CRUD and scan control |
| `/api/captures/` | `captures.py` | Capture history read/write |
| `/api/settings/` | `settings.py` | Location, wishlist, and key-value settings |
| `/api/user/` | `user_preferences.py` | Per-user preference storage |
| `/api/processing/` | `processing.py` | FITS file browser and processing jobs |
| `/api/astronomy/` | `astronomy.py` | Twilight, moon phase, miscellaneous calculations |
| `/api/weather/local` | `settings.py` | Current reading from wx-service |
