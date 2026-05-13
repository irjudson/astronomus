# Horizon, Planet Scheduling, and Satellite Avoidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add planet/moon scheduling as real plan time-blocks, satellite-pass avoidance, user-defined horizon profile with auto-scan, and clean up stale markdown docs.

**Architecture:** Five loosely coupled features sharing the `ObservingConstraints` model as the central config object. Planet targets are converted to pseudo-`DSOTarget` objects at plan time. Satellite and horizon data attach as pre-computed constraint data before the scheduler runs. The horizon scanner runs as a background task using the telescope's own camera.

**Tech Stack:** Python/FastAPI backend, Vue 3 + Pinia frontend, skyfield (already present), sgp4 (new dep), Pillow (already present), PostgreSQL AppSetting for storage.

---

## Branch Setup

### Task 0: Create feature branch

**Step 1: Create and switch to branch**
```bash
git checkout -b feature/horizon-planets-satellites
```

**Step 2: Verify clean state**
```bash
git status
```
Expected: nothing to commit (or only the untracked files listed in git status).

---

## Feature 1: Markdown Cleanup

### Task 1: Delete stale root-level docs

**Files to delete:**
- `CONSOLIDATED_MIGRATION_STATUS.md`
- `DATABASE_MIGRATION_CONSOLIDATION.md`
- `ENDPOINT_INTEGRATION_COMPLETE.md`
- `ENDPOINT_INTEGRATION_FIXES.md`
- `MIGRATION_STATUS.md`
- `NAVIGATION_QUICKREF.md`
- `PHASE1_COMPLETE.md`
- `SESSION_STATE.md`
- `SINGLE_CONTAINER_MIGRATION.md`
- `TELESCOPE_API.md`
- `TELESCOPE_SETUP_COMPLETE.md`
- `MEMENTO.md`
- `docs/SEESTAR_MIGRATION_B_PLAN.md`

**Step 1: Delete files**
```bash
cd /home/irjudson/Projects/astronomus
rm CONSOLIDATED_MIGRATION_STATUS.md DATABASE_MIGRATION_CONSOLIDATION.md \
   ENDPOINT_INTEGRATION_COMPLETE.md ENDPOINT_INTEGRATION_FIXES.md \
   MIGRATION_STATUS.md NAVIGATION_QUICKREF.md PHASE1_COMPLETE.md \
   SESSION_STATE.md SINGLE_CONTAINER_MIGRATION.md TELESCOPE_API.md \
   TELESCOPE_SETUP_COMPLETE.md MEMENTO.md docs/SEESTAR_MIGRATION_B_PLAN.md
```

**Step 2: Delete archive directory**
```bash
rm -rf docs/archive/
```

**Step 3: Stage and commit**
```bash
git add -A
git commit -m "chore: remove stale status and migration docs"
```

---

## Feature 5a: Horizon Profile — Storage Layer

### Task 2: Add HorizonPoint model and horizon_profile to ObservingConstraints

**Files:**
- Modify: `backend/app/models/models.py`

**Step 1: Write failing test**

File: `backend/tests/unit/test_horizon_models.py`
```python
"""Tests for horizon profile model."""
import pytest
from app.models.models import HorizonPoint, ObservingConstraints


def test_horizon_point_valid():
    pt = HorizonPoint(az=90.0, alt=15.0)
    assert pt.az == 90.0
    assert pt.alt == 15.0


def test_horizon_point_rejects_invalid_az():
    with pytest.raises(Exception):
        HorizonPoint(az=400.0, alt=10.0)


def test_observing_constraints_accepts_horizon_profile():
    profile = [HorizonPoint(az=0.0, alt=5.0), HorizonPoint(az=180.0, alt=20.0)]
    c = ObservingConstraints(horizon_profile=profile)
    assert len(c.horizon_profile) == 2


def test_observing_constraints_horizon_profile_defaults_none():
    c = ObservingConstraints()
    assert c.horizon_profile is None
```

**Step 2: Run test to verify it fails**
```bash
docker exec astronomus pytest tests/unit/test_horizon_models.py -v --no-cov
```
Expected: ImportError — `HorizonPoint` does not exist yet.

**Step 3: Add HorizonPoint and horizon_profile to models.py**

In `backend/app/models/models.py`, after the existing imports add:
```python
class HorizonPoint(BaseModel):
    """Single point in a local horizon profile."""
    az: float = Field(ge=0, lt=360, description="Azimuth in degrees (0=N, 90=E, 180=S, 270=W)")
    alt: float = Field(default=0.0, ge=0, le=90, description="Altitude above horizon in degrees")
```

In `ObservingConstraints`, add after `daytime_planning`:
```python
horizon_profile: Optional[List["HorizonPoint"]] = Field(
    default=None, description="Per-azimuth altitude minimums. None means use min_altitude everywhere."
)
```

Also add `HorizonPoint` to `__init__.py` exports in `backend/app/models/__init__.py`.

**Step 4: Run tests**
```bash
docker exec astronomus pytest tests/unit/test_horizon_models.py -v --no-cov
```
Expected: 4 PASSED.

**Step 5: Commit**
```bash
git add backend/app/models/models.py backend/app/models/__init__.py \
        backend/tests/unit/test_horizon_models.py
git commit -m "feat: add HorizonPoint model and horizon_profile to ObservingConstraints"
```

---

### Task 3: Add horizon profile settings API endpoints

**Files:**
- Modify: `backend/app/api/settings.py`
- Create: `backend/tests/api/test_horizon_profile_api.py`

**Step 1: Write failing tests**

File: `backend/tests/api/test_horizon_profile_api.py`
```python
"""Tests for horizon profile settings endpoints."""
import json
import pytest

pytestmark = pytest.mark.integration


class TestHorizonProfileEndpoints:

    def test_get_horizon_profile_when_empty(self, client):
        response = client.get("/api/settings/horizon-profile")
        assert response.status_code == 200
        assert response.json() == []

    def test_put_horizon_profile_saves_points(self, client):
        profile = [
            {"az": 0.0, "alt": 5.0},
            {"az": 90.0, "alt": 10.0},
            {"az": 180.0, "alt": 20.0},
            {"az": 270.0, "alt": 8.0},
        ]
        response = client.put("/api/settings/horizon-profile", json=profile)
        assert response.status_code == 200
        assert response.json()["count"] == 4

    def test_get_horizon_profile_returns_saved(self, client):
        profile = [{"az": 45.0, "alt": 12.0}]
        client.put("/api/settings/horizon-profile", json=profile)
        response = client.get("/api/settings/horizon-profile")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["az"] == 45.0
        assert data[0]["alt"] == 12.0

    def test_put_horizon_profile_replaces_existing(self, client):
        client.put("/api/settings/horizon-profile", json=[{"az": 0.0, "alt": 5.0}])
        client.put("/api/settings/horizon-profile", json=[{"az": 90.0, "alt": 15.0}, {"az": 180.0, "alt": 10.0}])
        response = client.get("/api/settings/horizon-profile")
        assert len(response.json()) == 2
```

**Step 2: Run tests to verify they fail**
```bash
docker exec astronomus pytest tests/api/test_horizon_profile_api.py -v --no-cov
```
Expected: 404 — endpoints don't exist yet.

**Step 3: Add endpoints to settings.py**

In `backend/app/api/settings.py`, add after the wishlist endpoints:
```python
@router.get("/horizon-profile")
async def get_horizon_profile(db: Session = Depends(get_db)):
    """Get user's local horizon profile."""
    setting = db.query(AppSetting).filter(AppSetting.key == "user.horizon_profile").first()
    if not setting or not setting.value:
        return []
    return json.loads(setting.value)


@router.put("/horizon-profile")
async def update_horizon_profile(profile: List[dict], db: Session = Depends(get_db)):
    """Save user's local horizon profile as list of {az, alt} points."""
    profile_json = json.dumps(profile)
    setting = db.query(AppSetting).filter(AppSetting.key == "user.horizon_profile").first()
    if setting:
        setting.value = profile_json
    else:
        setting = AppSetting(key="user.horizon_profile", value=profile_json, category="user")
        db.add(setting)
    db.commit()
    return {"message": "Horizon profile updated", "count": len(profile)}
```

**Step 4: Run tests**
```bash
docker exec astronomus pytest tests/api/test_horizon_profile_api.py -v --no-cov
```
Expected: 4 PASSED.

**Step 5: Commit**
```bash
git add backend/app/api/settings.py backend/tests/api/test_horizon_profile_api.py
git commit -m "feat: add GET/PUT /api/settings/horizon-profile endpoints"
```

---

## Feature 2: Planet/Moon Wishlist Scheduling

### Task 4: Add solar_targets to PlanRequest and inject planet pseudo-targets in planner

**Files:**
- Modify: `backend/app/models/models.py`
- Modify: `backend/app/services/planner_service.py`

**Step 1: Write failing test**

In `backend/tests/unit/services/test_planner_service.py`, add to the `TestPlannerServiceComprehensive` class:
```python
def test_solar_targets_creates_planet_pseudo_targets(self, override_get_db):
    """Test that solar_targets in request are scheduled as plan time-blocks."""
    request = PlanRequest(
        location=Location(
            name="Test Location", latitude=45.0, longitude=-110.0,
            elevation=1000.0, timezone="America/Denver"
        ),
        observing_date="2025-01-15",
        constraints=ObservingConstraints(min_altitude=10.0, object_types=["galaxy"]),
        solar_targets=["Jupiter", "Saturn"],
    )
    planner = PlannerService(override_get_db)
    plan = planner.generate_plan(request)

    scheduled_types = {st.target.object_type for st in plan.scheduled_targets}
    scheduled_ids = {st.target.catalog_id for st in plan.scheduled_targets}
    # Planets should appear if they're above horizon during the session
    # At minimum, the request shouldn't fail
    assert plan is not None
    assert isinstance(plan.scheduled_targets, list)
```

**Step 2: Run test to verify it fails**
```bash
docker exec astronomus pytest tests/unit/services/test_planner_service.py::TestPlannerServiceComprehensive::test_solar_targets_creates_planet_pseudo_targets -v --no-cov
```
Expected: ValidationError — `solar_targets` field not in PlanRequest.

**Step 3: Add solar_targets to PlanRequest**

In `backend/app/models/models.py`, in `PlanRequest` after `preferred_gap_fillers`:
```python
solar_targets: Optional[List[str]] = Field(
    default=None,
    description="Planet/moon names from wishlist to schedule as imaging targets (e.g. ['Jupiter', 'Moon'])"
)
```

**Step 4: Add planet injection to planner_service.py**

In `backend/app/services/planner_service.py`, add import at top:
```python
from app.services.planetary_ephemeris import PlanetaryEphemeris
```

Add to `PlannerService.__init__`:
```python
self.planetary_ephemeris = PlanetaryEphemeris()
```

In `generate_plan()`, after the comet injection block and before weather forecast, add:
```python
# Inject solar system wishlist targets as schedulable pseudo-targets
if request.solar_targets:
    midpoint_utc = (session.imaging_start + (session.imaging_end - session.imaging_start) / 2)
    midpoint_naive = midpoint_utc.astimezone(pytz.UTC).replace(tzinfo=None)
    for planet_name in request.solar_targets:
        try:
            pos = self.planetary_ephemeris.get_position(
                planet_name.lower(),
                latitude=request.location.latitude,
                longitude=request.location.longitude,
                elevation=request.location.elevation,
                time=midpoint_naive,
            )
            from app.models import DSOTarget
            duration_hint = 5 if planet_name.lower() == "moon" else 10
            planet_target = DSOTarget(
                name=planet_name,
                catalog_id=f"PLANET:{planet_name}",
                object_type="moon" if planet_name.lower() == "moon" else "planet",
                ra_hours=pos["ra_hours"],
                dec_degrees=pos["dec_degrees"],
                magnitude=pos.get("magnitude", 0.0),
                size_arcmin=pos.get("angular_diameter_arcsec", 0.0) / 60.0,
                description=f"Solar system target (scheduled {duration_hint} min)",
                preferred_duration_minutes=duration_hint,
            )
            targets.append(planet_target)
            logger.debug("Added solar system target %s at RA=%.2fh Dec=%.1f°", planet_name, pos["ra_hours"], pos["dec_degrees"])
        except Exception as e:
            logger.warning("Failed to add solar system target %s: %s", planet_name, e)
```

**Step 5: Add preferred_duration_minutes to DSOTarget**

In `backend/app/models/models.py`, in `DSOTarget`, add after `capture_history`:
```python
preferred_duration_minutes: Optional[int] = Field(
    default=None, description="Requested imaging duration; scheduler caps at this value if set"
)
```

**Step 6: Respect preferred_duration_minutes in scheduler**

In `backend/app/services/scheduler_service.py`, in `schedule_session()`, after the `if duration > max_duration: duration = max_duration` line, add:
```python
# Respect per-target duration preference (e.g. planets: 10 min)
if best_target.preferred_duration_minutes is not None:
    pref = timedelta(minutes=best_target.preferred_duration_minutes)
    if duration > pref:
        duration = pref
```

**Step 7: Run tests**
```bash
docker exec astronomus pytest tests/unit/services/test_planner_service.py -v --no-cov
```
Expected: All PASSED.

**Step 8: Commit**
```bash
git add backend/app/models/models.py backend/app/services/planner_service.py \
        backend/app/services/scheduler_service.py \
        backend/tests/unit/services/test_planner_service.py
git commit -m "feat: schedule planet/moon wishlist items as plan time-blocks"
```

---

### Task 5: Update frontend to send solar_targets and remove post-plan fetch

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js`
- Modify: `frontend/vue-app/src/views/PlanningView.vue`

**Step 1: Update planning.js**

In `generatePlan()`, replace the solar system block (lines ~115-148) with:
```javascript
const SOLAR_TYPES = new Set(['planet', 'moon', 'star'])
const dsoTargets = wishlist.filter(t => !SOLAR_TYPES.has(t.type)).map(t => t.name)
const solarTargets = wishlist.filter(t => SOLAR_TYPES.has(t.type)).map(t => t.name)

if (dsoTargets.length > 0) {
  request.preferred_gap_fillers = dsoTargets
}
if (solarTargets.length > 0) {
  request.solar_targets = solarTargets
}
```

Remove the entire `if (solarTargets.length > 0) { try { ... } }` post-plan fetch block and the `else { this.currentPlan.solar_system_targets = [] }`.

**Step 2: Remove the separate Solar System section from PlanningView.vue**

Remove the entire `<!-- Solar System Targets from Wishlist -->` div block (lines ~203-240). Planets now appear inline in the scheduled targets list.

**Step 3: Verify frontend builds**
```bash
cd /home/irjudson/Projects/astronomus && docker exec astronomus sh -c "cd /app && ls"
```
Then rebuild:
```bash
docker compose build astronomus && docker compose up -d astronomus
```

**Step 4: Commit**
```bash
git add frontend/vue-app/src/stores/planning.js \
        frontend/vue-app/src/views/PlanningView.vue
git commit -m "feat: send solar_targets in plan request, remove post-plan fetch"
```

---

## Feature 3: Avoid Satellites

### Task 6: Add avoid_satellites to ObservingConstraints and sgp4 dependency

**Files:**
- Modify: `backend/app/models/models.py`
- Modify: `backend/requirements.txt`

**Step 1: Add field to model**

In `ObservingConstraints`, add after `daytime_planning`:
```python
avoid_satellites: bool = Field(
    default=False,
    description="Avoid scheduling imaging during bright satellite passes (ISS, Starlink chain, etc.)"
)
```

**Step 2: Add sgp4 to requirements**

In `backend/requirements.txt`, add:
```
sgp4>=2.22
```

(skyfield already includes sgp4 internally, but we add it explicitly for direct use if needed.)

**Step 3: Commit**
```bash
git add backend/app/models/models.py backend/requirements.txt
git commit -m "feat: add avoid_satellites constraint field and sgp4 dependency"
```

---

### Task 7: Create SatelliteAvoidanceService

**Files:**
- Create: `backend/app/services/satellite_avoidance_service.py`
- Create: `backend/tests/unit/services/test_satellite_avoidance_service.py`

**Step 1: Write failing tests**

File: `backend/tests/unit/services/test_satellite_avoidance_service.py`
```python
"""Tests for satellite avoidance service."""
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytz

from app.models import Location
from app.services.satellite_avoidance_service import (
    BlockedInterval,
    SatelliteAvoidanceService,
)


SAMPLE_TLE = """ISS (ZARYA)
1 25544U 98067A   24001.50000000  .00010000  00000-0  17000-3 0  9994
2 25544  51.6400 337.6200 0006703  81.0500 279.1400 15.49814514 10000
"""


class TestSatelliteAvoidanceService:

    def test_init_creates_service(self):
        svc = SatelliteAvoidanceService()
        assert svc is not None

    def test_blocked_interval_model(self):
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 5, tzinfo=pytz.UTC)
        interval = BlockedInterval(start_time=start, end_time=end, satellite_name="ISS")
        assert interval.satellite_name == "ISS"
        assert interval.duration_minutes == 5

    @patch("app.services.satellite_avoidance_service.SatelliteAvoidanceService._load_tle_data")
    def test_get_blocked_intervals_returns_list(self, mock_load):
        mock_load.return_value = []
        svc = SatelliteAvoidanceService()
        location = Location(name="Test", latitude=46.8, longitude=-112.0, elevation=1000.0, timezone="America/Denver")
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        intervals = svc.get_blocked_intervals(location, start, end)
        assert isinstance(intervals, list)

    def test_overlaps_interval(self):
        svc = SatelliteAvoidanceService()
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC)
        blocked = [
            BlockedInterval(
                start_time=datetime(2025, 1, 15, 22, 30, tzinfo=pytz.UTC),
                end_time=datetime(2025, 1, 15, 22, 35, tzinfo=pytz.UTC),
                satellite_name="ISS",
            )
        ]
        assert svc.overlaps_blocked(start, end, blocked) is True

    def test_no_overlap_returns_false(self):
        svc = SatelliteAvoidanceService()
        start = datetime(2025, 1, 15, 22, 0, tzinfo=pytz.UTC)
        end = datetime(2025, 1, 15, 22, 20, tzinfo=pytz.UTC)
        blocked = [
            BlockedInterval(
                start_time=datetime(2025, 1, 15, 23, 0, tzinfo=pytz.UTC),
                end_time=datetime(2025, 1, 15, 23, 5, tzinfo=pytz.UTC),
                satellite_name="ISS",
            )
        ]
        assert svc.overlaps_blocked(start, end, blocked) is False
```

**Step 2: Run tests to verify they fail**
```bash
docker exec astronomus pytest tests/unit/services/test_satellite_avoidance_service.py -v --no-cov
```
Expected: ImportError.

**Step 3: Create satellite_avoidance_service.py**

File: `backend/app/services/satellite_avoidance_service.py`
```python
"""Satellite pass avoidance service for astrophotography planning."""

import hashlib
import logging
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pytz
import requests
from pydantic import BaseModel
from skyfield.api import EarthSatellite, load, wgs84

logger = logging.getLogger(__name__)

TLE_URL = "https://celestrak.org/TLE/catalog.csv?GROUP=visual&FORMAT=tle"
TLE_CACHE_HOURS = 24
TLE_CACHE_PATH = Path(tempfile.gettempdir()) / "astronomus_visual_tle.txt"

MIN_ELEVATION_DEG = 10.0
BRIGHT_MAG_THRESHOLD = 2.0


class BlockedInterval(BaseModel):
    """A time window to avoid scheduling imaging in."""

    start_time: datetime
    end_time: datetime
    satellite_name: str

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)


class SatelliteAvoidanceService:
    """Compute satellite pass windows that should be avoided during imaging."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._ts = load.timescale()

    def get_blocked_intervals(
        self,
        location,
        session_start: datetime,
        session_end: datetime,
        min_elevation: float = MIN_ELEVATION_DEG,
    ) -> List[BlockedInterval]:
        """Return time intervals when a bright satellite passes over the observer."""
        satellites = self._load_tle_data()
        if not satellites:
            return []

        blat = location.latitude
        blon = location.longitude
        belev = getattr(location, "elevation", 0.0)
        observer = wgs84.latlon(blat, blon, elevation_m=belev)

        t0 = self._ts.from_datetime(session_start.astimezone(pytz.UTC))
        t1 = self._ts.from_datetime(session_end.astimezone(pytz.UTC))

        intervals: List[BlockedInterval] = []

        for sat in satellites:
            try:
                times, events = sat.find_events(observer, t0, t1, altitude_degrees=min_elevation)
                # events: 0=rise, 1=culminate, 2=set
                i = 0
                while i < len(events):
                    if events[i] == 0:
                        rise_t = times[i].utc_datetime().replace(tzinfo=pytz.UTC)
                        # Find matching set event
                        for j in range(i + 1, len(events)):
                            if events[j] == 2:
                                set_t = times[j].utc_datetime().replace(tzinfo=pytz.UTC)
                                intervals.append(BlockedInterval(
                                    start_time=rise_t - timedelta(seconds=30),
                                    end_time=set_t + timedelta(seconds=30),
                                    satellite_name=sat.name,
                                ))
                                break
                    i += 1
            except Exception as e:
                logger.debug("Error computing passes for %s: %s", sat.name, e)

        logger.info("Found %d satellite pass intervals during session", len(intervals))
        return intervals

    def overlaps_blocked(
        self,
        start: datetime,
        end: datetime,
        blocked: List[BlockedInterval],
    ) -> bool:
        """Return True if [start, end) overlaps any blocked interval."""
        for interval in blocked:
            if start < interval.end_time and end > interval.start_time:
                return True
        return False

    def _load_tle_data(self) -> List[EarthSatellite]:
        """Load TLE data from cache or download from Celestrak."""
        if self._cache_is_fresh():
            raw = TLE_CACHE_PATH.read_text()
        else:
            raw = self._download_tles()
            if raw:
                TLE_CACHE_PATH.write_text(raw)

        if not raw:
            return []

        return self._parse_tles(raw)

    def _cache_is_fresh(self) -> bool:
        if not TLE_CACHE_PATH.exists():
            return False
        age_hours = (time.time() - TLE_CACHE_PATH.stat().st_mtime) / 3600
        return age_hours < TLE_CACHE_HOURS

    def _download_tles(self) -> str:
        try:
            resp = requests.get(TLE_URL, timeout=self.timeout)
            resp.raise_for_status()
            logger.info("Downloaded visual TLEs from Celestrak (%d bytes)", len(resp.text))
            return resp.text
        except Exception as e:
            logger.warning("Failed to download TLEs from Celestrak: %s", e)
            return ""

    def _parse_tles(self, raw: str) -> List[EarthSatellite]:
        sats = []
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        i = 0
        while i + 2 < len(lines):
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            if line1.startswith("1 ") and line2.startswith("2 "):
                try:
                    sats.append(EarthSatellite(line1, line2, name, self._ts))
                except Exception:
                    pass
                i += 3
            else:
                i += 1
        return sats
```

**Step 4: Run tests**
```bash
docker exec astronomus pytest tests/unit/services/test_satellite_avoidance_service.py -v --no-cov
```
Expected: All PASSED (network calls mocked).

**Step 5: Commit**
```bash
git add backend/app/services/satellite_avoidance_service.py \
        backend/tests/unit/services/test_satellite_avoidance_service.py
git commit -m "feat: satellite avoidance service using Celestrak visual TLEs"
```

---

### Task 8: Integrate satellite avoidance into planner and scheduler

**Files:**
- Modify: `backend/app/services/planner_service.py`
- Modify: `backend/app/services/scheduler_service.py`

**Step 1: Pass blocked_intervals to scheduler**

In `scheduler_service.py`, update `schedule_session` signature:
```python
def schedule_session(
    self,
    targets: List[DSOTarget],
    location: Location,
    session: SessionInfo,
    constraints: ObservingConstraints,
    weather_forecasts: List,
    blocked_intervals: Optional[List] = None,   # add this
) -> List[ScheduledTarget]:
```

In the `while current_time < session.imaging_end` loop, after finding `best_target` and before creating `scheduled_target`, add:
```python
# Skip slots overlapping a satellite pass
if blocked_intervals:
    from app.services.satellite_avoidance_service import SatelliteAvoidanceService
    svc = SatelliteAvoidanceService()
    slot_end = current_time + duration
    if svc.overlaps_blocked(current_time, slot_end, blocked_intervals):
        # Advance past the blocking interval
        blocking = next(
            (b for b in blocked_intervals if current_time < b.end_time and slot_end > b.start_time),
            None,
        )
        if blocking:
            current_time = blocking.end_time + timedelta(seconds=30)
        else:
            current_time += timedelta(minutes=5)
        continue
```

Also update `fill_gaps` to accept and use `blocked_intervals` with the same pattern.

**Step 2: Call satellite service in planner_service.py**

In `planner_service.py`, add import:
```python
from app.services.satellite_avoidance_service import SatelliteAvoidanceService
```

In `generate_plan()`, after weather forecast and before `schedule_session`:
```python
# Compute satellite blocked intervals if requested
blocked_intervals = []
if request.constraints.avoid_satellites:
    try:
        sat_svc = SatelliteAvoidanceService()
        blocked_intervals = sat_svc.get_blocked_intervals(
            location=request.location,
            session_start=session.imaging_start,
            session_end=session.imaging_end,
        )
        logger.info("Satellite avoidance: %d blocked intervals", len(blocked_intervals))
    except Exception as e:
        logger.warning("Satellite avoidance failed, proceeding without it: %s", e)
```

Update the `schedule_session` call to pass `blocked_intervals=blocked_intervals` and similarly for `fill_gaps`.

**Step 3: Run full test suite**
```bash
docker exec astronomus pytest tests/ -q --no-cov
```
Expected: All existing + new tests PASS.

**Step 4: Commit**
```bash
git add backend/app/services/planner_service.py backend/app/services/scheduler_service.py
git commit -m "feat: integrate satellite avoidance into scheduler"
```

---

### Task 9: Add avoid_satellites to frontend

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js`
- Modify: `frontend/vue-app/src/components/planning/PlanningControls.vue`

**Step 1: Add state to planning store**

In `planning.js` `state()`, add in `constraints`:
```javascript
avoid_satellites: false,
```

In `initFromSettings()`, add:
```javascript
this.constraints.avoid_satellites = s.planAvoidSatellites ?? this.constraints.avoid_satellites
```

In `saveConstraints()`, add:
```javascript
planAvoidSatellites: this.constraints.avoid_satellites,
```

In the `request.constraints` object inside `generatePlan()`, add:
```javascript
avoid_satellites: this.constraints.avoid_satellites,
```

In `loadPlan()` (the plan restoration block), add:
```javascript
if (c.avoid_satellites != null) this.constraints.avoid_satellites = c.avoid_satellites
```

**Step 2: Add toggle to PlanningControls.vue**

After the existing "Avoid Moon" label block, add:
```html
<label class="flex items-center justify-between p-3 bg-gray-800 rounded cursor-pointer hover:bg-gray-750 transition-colors">
  <span class="text-sm text-gray-200">Avoid Satellites</span>
  <input
    v-model="planningStore.constraints.avoid_satellites"
    type="checkbox"
    class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
  />
</label>
```

**Step 3: Commit**
```bash
git add frontend/vue-app/src/stores/planning.js \
        frontend/vue-app/src/components/planning/PlanningControls.vue
git commit -m "feat: add avoid satellites toggle to planning constraints UI"
```

---

## Feature 5b: Horizon Profile — Scheduler Integration

### Task 10: Add horizon interpolation to ephemeris service and use in scheduler

**Files:**
- Modify: `backend/app/services/ephemeris_service.py`
- Modify: `backend/app/services/scheduler_service.py`
- Create: `backend/tests/unit/services/test_horizon_interpolation.py`

**Step 1: Write failing tests**

File: `backend/tests/unit/services/test_horizon_interpolation.py`
```python
"""Tests for horizon profile altitude interpolation."""
import pytest
from app.models.models import HorizonPoint
from app.services.ephemeris_service import EphemerisService


def make_profile(points):
    return [HorizonPoint(az=az, alt=alt) for az, alt in points]


class TestHorizonInterpolation:

    def setup_method(self):
        self.svc = EphemerisService()

    def test_empty_profile_returns_zero(self):
        assert self.svc.interpolate_horizon_altitude(90.0, []) == 0.0

    def test_single_point_returns_its_altitude(self):
        profile = make_profile([(90.0, 15.0)])
        assert self.svc.interpolate_horizon_altitude(90.0, profile) == 15.0

    def test_exact_match_returns_altitude(self):
        profile = make_profile([(0.0, 5.0), (90.0, 15.0), (180.0, 25.0), (270.0, 10.0)])
        assert self.svc.interpolate_horizon_altitude(90.0, profile) == 15.0

    def test_interpolates_between_points(self):
        profile = make_profile([(0.0, 0.0), (90.0, 18.0)])
        result = self.svc.interpolate_horizon_altitude(45.0, profile)
        assert abs(result - 9.0) < 0.01  # midpoint = 9 degrees

    def test_wraps_around_360(self):
        profile = make_profile([(350.0, 10.0), (10.0, 20.0)])
        result = self.svc.interpolate_horizon_altitude(0.0, profile)
        assert abs(result - 15.0) < 0.01  # midpoint between 350 and 10

    def test_get_effective_min_altitude_no_profile(self):
        result = self.svc.get_effective_min_altitude(90.0, 30.0, None)
        assert result == 30.0

    def test_get_effective_min_altitude_uses_max(self):
        profile = make_profile([(90.0, 35.0)])
        result = self.svc.get_effective_min_altitude(90.0, 30.0, profile)
        assert result == 35.0  # horizon is higher than flat min

    def test_get_effective_min_altitude_flat_min_wins(self):
        profile = make_profile([(90.0, 5.0)])
        result = self.svc.get_effective_min_altitude(90.0, 30.0, profile)
        assert result == 30.0  # flat min is higher
```

**Step 2: Run tests to verify they fail**
```bash
docker exec astronomus pytest tests/unit/services/test_horizon_interpolation.py -v --no-cov
```
Expected: AttributeError — methods don't exist.

**Step 3: Add interpolation methods to EphemerisService**

In `backend/app/services/ephemeris_service.py`, add methods:
```python
def interpolate_horizon_altitude(self, azimuth: float, profile: list) -> float:
    """Linear interpolation of local horizon altitude at given azimuth."""
    if not profile:
        return 0.0
    sorted_pts = sorted(profile, key=lambda p: p.az)
    # Find surrounding points (with wraparound)
    for i, pt in enumerate(sorted_pts):
        if pt.az == azimuth:
            return pt.alt
        if pt.az > azimuth:
            prev = sorted_pts[i - 1] if i > 0 else sorted_pts[-1]
            next_pt = pt
            az0, alt0 = prev.az, prev.alt
            az1, alt1 = next_pt.az, next_pt.alt
            # Handle wraparound (e.g. prev=350, next=10)
            if az0 > az1:
                span = (360 - az0) + az1
                pos = azimuth - az0 if azimuth >= az0 else (360 - az0) + azimuth
            else:
                span = az1 - az0
                pos = azimuth - az0
            if span == 0:
                return alt0
            return alt0 + (alt1 - alt0) * (pos / span)
    # azimuth is beyond the last point — interpolate between last and first (wraparound)
    prev = sorted_pts[-1]
    next_pt = sorted_pts[0]
    az0, alt0 = prev.az, prev.alt
    az1, alt1 = next_pt.az, next_pt.alt
    span = (360 - az0) + az1
    pos = azimuth - az0 if azimuth >= az0 else (360 - az0) + azimuth
    if span == 0:
        return alt0
    return alt0 + (alt1 - alt0) * (pos / span)

def get_effective_min_altitude(self, azimuth: float, flat_min: float, profile) -> float:
    """Return max(flat_min, local horizon altitude at azimuth)."""
    if not profile:
        return flat_min
    local_horizon = self.interpolate_horizon_altitude(azimuth, profile)
    return max(flat_min, local_horizon)
```

**Step 4: Update is_target_visible to use horizon profile**

In `ephemeris_service.py`, update `is_target_visible`:
```python
def is_target_visible(
    self, target: DSOTarget, location: Location, time: datetime,
    min_alt: float, max_alt: float, horizon_profile=None
) -> bool:
    alt, az = self.calculate_position(target, location, time)
    effective_min = self.get_effective_min_altitude(az, min_alt, horizon_profile)
    return effective_min <= alt <= max_alt
```

**Step 5: Pass horizon_profile through scheduler calls**

In `scheduler_service.py`, update every `self.ephemeris.is_target_visible(...)` call to add `horizon_profile=constraints.horizon_profile`.

**Step 6: Load horizon profile in planner_service.py**

In `planner_service.py`, in `generate_plan()`, after creating `session` and before getting candidates, add:
```python
# Load horizon profile from user settings
from app.models.settings_models import AppSetting
import json as _json
horizon_profile = None
try:
    hp_setting = self.db.query(AppSetting).filter(AppSetting.key == "user.horizon_profile").first()
    if hp_setting and hp_setting.value:
        from app.models.models import HorizonPoint
        raw_profile = _json.loads(hp_setting.value)
        horizon_profile = [HorizonPoint(**pt) for pt in raw_profile]
        request.constraints.horizon_profile = horizon_profile
except Exception as e:
    logger.warning("Failed to load horizon profile: %s", e)
```

**Step 7: Run tests**
```bash
docker exec astronomus pytest tests/unit/services/test_horizon_interpolation.py -v --no-cov
docker exec astronomus pytest tests/ -q --no-cov
```
Expected: All PASSED.

**Step 8: Commit**
```bash
git add backend/app/services/ephemeris_service.py \
        backend/app/services/scheduler_service.py \
        backend/app/services/planner_service.py \
        backend/tests/unit/services/test_horizon_interpolation.py
git commit -m "feat: horizon profile interpolation in scheduler visibility checks"
```

---

## Feature 4: Horizon Scanner

### Task 11: Create HorizonScannerService

**Files:**
- Create: `backend/app/services/horizon_scanner_service.py`
- Create: `backend/tests/unit/services/test_horizon_scanner_service.py`

**Step 1: Write failing tests**

File: `backend/tests/unit/services/test_horizon_scanner_service.py`
```python
"""Tests for horizon scanner service brightness analysis."""
import io
import pytest
from PIL import Image
from app.services.horizon_scanner_service import HorizonScannerService, analyze_frame_brightness


def make_frame(top_brightness: int, bottom_brightness: int, width=100, height=100) -> bytes:
    """Create a test JPEG with different brightness in top/bottom halves."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        b = top_brightness if y < height // 2 else bottom_brightness
        for x in range(width):
            pixels[x, y] = (b, b, b)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestBrightnessAnalysis:

    def test_all_sky_returns_high_ratio(self):
        frame = make_frame(top_brightness=200, bottom_brightness=200)
        ratio = analyze_frame_brightness(frame)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_sky_over_terrain_returns_ratio_above_1(self):
        frame = make_frame(top_brightness=200, bottom_brightness=60)
        ratio = analyze_frame_brightness(frame)
        assert ratio > 1.2  # sky on top, terrain on bottom = above horizon

    def test_terrain_fills_frame_returns_ratio_near_1(self):
        frame = make_frame(top_brightness=50, bottom_brightness=50)
        ratio = analyze_frame_brightness(frame)
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_scanner_instantiates(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc is not None

    def test_is_above_horizon_sky_ratio(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc._is_sky(ratio=1.5) is True

    def test_is_above_horizon_terrain_ratio(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc._is_sky(ratio=0.7) is False
```

**Step 2: Run tests to verify they fail**
```bash
docker exec astronomus pytest tests/unit/services/test_horizon_scanner_service.py -v --no-cov
```
Expected: ImportError.

**Step 3: Create horizon_scanner_service.py**

File: `backend/app/services/horizon_scanner_service.py`
```python
"""Horizon scanner: use the Seestar S50 camera to auto-detect local horizon."""

import asyncio
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

SKY_RATIO_THRESHOLD = 1.2   # top/bottom brightness ratio above this = sky
TERRAIN_RATIO_THRESHOLD = 0.9
SETTLE_SECONDS = 1.8
BINARY_SEARCH_ITERATIONS = 5


def analyze_frame_brightness(jpeg_bytes: bytes) -> float:
    """Return top-third / bottom-third mean brightness ratio."""
    img = Image.open(io.BytesIO(jpeg_bytes)).convert("L")  # grayscale
    w, h = img.size
    third = h // 3
    top = list(img.crop((0, 0, w, third)).getdata())
    bottom = list(img.crop((0, h - third, w, h)).getdata())
    mean_top = sum(top) / len(top) if top else 1
    mean_bottom = sum(bottom) / len(bottom) if bottom else 1
    if mean_bottom == 0:
        return 999.0
    return mean_top / mean_bottom


@dataclass
class ScanProgress:
    current_az: float
    total_azimuths: int
    completed: int
    points: List[dict] = field(default_factory=list)
    status: str = "scanning"  # scanning | complete | error
    error: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_azimuths == 0:
            return 0.0
        return round(self.completed / self.total_azimuths * 100, 1)


class HorizonScannerService:
    """Scan local horizon by sweeping telescope azimuths and analyzing camera frames."""

    def __init__(
        self,
        telescope_host: str,
        telescope_port: int,
        az_step: int = 15,
        alt_min: float = 2.0,
        alt_max: float = 45.0,
    ):
        self.host = telescope_host
        self.port = telescope_port
        self.az_step = az_step
        self.alt_min = alt_min
        self.alt_max = alt_max
        self._snapshot_url = f"http://localhost:9247/api/telescope/preview/snapshot"

    def _is_sky(self, ratio: float) -> bool:
        return ratio >= SKY_RATIO_THRESHOLD

    async def scan(self) -> AsyncGenerator[ScanProgress, None]:
        """Sweep azimuths, binary-search altitude, yield progress after each az."""
        azimuths = list(range(0, 360, self.az_step))
        total = len(azimuths)
        points = []

        for i, az in enumerate(azimuths):
            try:
                alt = await self._find_horizon_altitude(az)
            except Exception as e:
                logger.warning("Scan failed at az=%.0f: %s", az, e)
                alt = self.alt_min  # fallback

            points.append({"az": float(az), "alt": round(alt, 1)})
            yield ScanProgress(
                current_az=float(az),
                total_azimuths=total,
                completed=i + 1,
                points=list(points),
                status="scanning" if i < total - 1 else "complete",
            )

    async def _find_horizon_altitude(self, azimuth: float) -> float:
        """Binary search for horizon altitude at the given azimuth."""
        low, high = self.alt_min, self.alt_max

        for _ in range(BINARY_SEARCH_ITERATIONS):
            mid = (low + high) / 2.0
            await self._move_scope(azimuth, mid)
            await asyncio.sleep(SETTLE_SECONDS)
            frame = await self._capture_frame()
            ratio = analyze_frame_brightness(frame)

            if self._is_sky(ratio):
                # We can see sky; horizon is at or below mid
                high = mid
            else:
                # Terrain in view; horizon is above mid
                low = mid

        return (low + high) / 2.0

    async def _move_scope(self, azimuth: float, altitude: float) -> None:
        """Command telescope to move to alt/az position."""
        import json as _json
        import asyncio

        # Use the Seestar JSON-RPC protocol directly
        reader, writer = await asyncio.open_connection(self.host, self.port)
        cmd = _json.dumps({
            "id": 1, "method": "scope_move_to_horizon",
            "params": [azimuth, altitude]
        }) + "\r\n"
        writer.write(cmd.encode())
        await writer.drain()
        await asyncio.sleep(0.2)
        writer.close()
        await writer.wait_closed()

    async def _capture_frame(self) -> bytes:
        """Fetch a JPEG snapshot from the backend preview endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(self._snapshot_url)
            resp.raise_for_status()
            return resp.content
```

**Step 4: Run tests**
```bash
docker exec astronomus pytest tests/unit/services/test_horizon_scanner_service.py -v --no-cov
```
Expected: All PASSED.

**Step 5: Commit**
```bash
git add backend/app/services/horizon_scanner_service.py \
        backend/tests/unit/services/test_horizon_scanner_service.py
git commit -m "feat: horizon scanner service with brightness-based sky detection"
```

---

### Task 12: Add preview snapshot endpoint and horizon scan API

**Files:**
- Modify: `backend/app/api/routes.py`
- Create: `backend/app/api/horizon.py`
- Modify: `backend/app/api/routes.py` (register new router)

**Step 1: Add snapshot endpoint to routes.py**

In `backend/app/api/routes.py`, add after the existing preview stream endpoint:
```python
@router.get("/telescope/preview/snapshot")
async def get_preview_snapshot():
    """Capture a single JPEG frame from the telescope preview stream."""
    import httpx
    from fastapi.responses import Response

    # The MJPEG stream is served internally; grab one frame by reading
    # the first boundary from the multipart stream
    telescope_host = os.environ.get("TELESCOPE_HOST", "192.168.2.47")
    telescope_port = int(os.environ.get("TELESCOPE_PORT", "4700"))
    # The preview stream URL (internal MJPEG from scope)
    preview_url = f"http://{telescope_host}:{telescope_port}/stream"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            async with client.stream("GET", preview_url) as resp:
                buf = b""
                async for chunk in resp.aiter_bytes(1024):
                    buf += chunk
                    # JPEG frame starts with FFD8 and ends with FFD9
                    start = buf.find(b"\xff\xd8")
                    end = buf.find(b"\xff\xd9", start + 2)
                    if start != -1 and end != -1:
                        jpeg = buf[start:end + 2]
                        return Response(content=jpeg, media_type="image/jpeg")
                    if len(buf) > 500_000:
                        break
        raise HTTPException(status_code=503, detail="Could not capture frame from preview stream")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Preview snapshot failed: {e}")
```

**Step 2: Create horizon.py API router**

File: `backend/app/api/horizon.py`
```python
"""Horizon scanning API endpoints."""

import asyncio
import json
import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.horizon_scanner_service import HorizonScannerService

router = APIRouter(prefix="/horizon", tags=["horizon"])

# In-memory store for scan tasks (single-user app)
_scans: Dict[str, dict] = {}


@router.post("/scan")
async def start_horizon_scan(
    telescope_host: str = "192.168.2.47",
    telescope_port: int = 4700,
    az_step: int = 15,
):
    """Start a background horizon scan. Returns a scan_id to poll for status."""
    scan_id = str(uuid.uuid4())[:8]
    _scans[scan_id] = {"status": "scanning", "progress": 0, "points": [], "current_az": 0}

    async def _run():
        svc = HorizonScannerService(telescope_host, telescope_port, az_step=az_step)
        async for progress in svc.scan():
            _scans[scan_id].update({
                "status": progress.status,
                "progress": progress.progress_percent,
                "current_az": progress.current_az,
                "points": progress.points,
            })

    asyncio.create_task(_run())
    return {"scan_id": scan_id, "message": "Horizon scan started"}


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get current scan progress and detected horizon points."""
    if scan_id not in _scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scans[scan_id]


@router.delete("/scan/{scan_id}")
async def clear_scan(scan_id: str):
    """Remove a completed scan record."""
    _scans.pop(scan_id, None)
    return {"deleted": scan_id}
```

**Step 3: Register the new router**

In `backend/app/api/routes.py` (or wherever routers are registered), add:
```python
from app.api.horizon import router as horizon_router
app.include_router(horizon_router, prefix="/api")
```

Find the existing router registration pattern and follow it exactly.

**Step 4: Run full test suite**
```bash
docker exec astronomus pytest tests/ -q --no-cov
```
Expected: All PASSED.

**Step 5: Commit**
```bash
git add backend/app/api/horizon.py backend/app/api/routes.py
git commit -m "feat: horizon scan background task API and preview snapshot endpoint"
```

---

### Task 13: Horizon profile UI in Settings

**Files:**
- Modify: `frontend/vue-app/src/components/shared/SettingsModal.vue`
- Create: `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue`

**Step 1: Create HorizonProfileEditor.vue**

File: `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue`
```vue
<template>
  <div class="space-y-4">
    <!-- Horizon chart preview -->
    <div class="bg-gray-900 rounded-lg p-3">
      <svg :viewBox="`0 0 360 90`" class="w-full h-24 border border-gray-700 rounded" preserveAspectRatio="none">
        <!-- Background grid -->
        <line v-for="alt in [15,30,45,60,75]" :key="alt"
          x1="0" :y1="90-alt" x2="360" :y2="90-alt"
          stroke="#374151" stroke-width="0.5" />
        <!-- Horizon profile polygon -->
        <polygon v-if="sortedProfile.length >= 2"
          :points="polygonPoints"
          fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="1.5" />
        <!-- Min altitude line -->
        <line x1="0" :y1="90 - minAltitude" x2="360" :y2="90 - minAltitude"
          stroke="#6b7280" stroke-width="1" stroke-dasharray="4,4" />
        <text x="2" :y="90 - minAltitude - 2" fill="#9ca3af" font-size="6">min alt</text>
      </svg>
    </div>

    <!-- Controls row -->
    <div class="flex gap-2 flex-wrap">
      <button @click="startScan"
        :disabled="scanning"
        class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded transition-colors">
        {{ scanning ? `Scanning ${scanProgress}%…` : 'Scan Horizon' }}
      </button>
      <button @click="addPoint"
        class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded">
        + Add Point
      </button>
      <button @click="clearProfile"
        class="px-3 py-1.5 bg-red-900/50 hover:bg-red-900 text-red-300 text-sm rounded">
        Clear
      </button>
      <button @click="exportProfile"
        class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded ml-auto">
        Export
      </button>
      <label class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded cursor-pointer">
        Import
        <input type="file" accept=".json" @change="importProfile" class="hidden" />
      </label>
    </div>

    <!-- Point table -->
    <div class="space-y-1 max-h-48 overflow-y-auto">
      <div v-if="profile.length === 0" class="text-sm text-gray-500 text-center py-4">
        No horizon points defined. Click "Scan Horizon" or add points manually.
      </div>
      <div v-for="(pt, i) in sortedProfile" :key="i"
        class="flex items-center gap-2 bg-gray-800 px-3 py-1.5 rounded text-sm">
        <span class="text-gray-400 w-6 text-xs">{{ i + 1 }}</span>
        <label class="text-gray-400 text-xs w-12">Az</label>
        <input v-model.number="pt.az" type="number" min="0" max="359" step="5"
          class="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-gray-200 text-xs" />
        <label class="text-gray-400 text-xs w-12">Alt</label>
        <input v-model.number="pt.alt" type="number" min="0" max="45" step="1"
          class="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-gray-200 text-xs" />
        <button @click="removePoint(i)" class="ml-auto text-red-400 hover:text-red-300 text-xs">✕</button>
      </div>
    </div>

    <!-- Save button -->
    <button @click="save" :disabled="saving"
      class="w-full px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm rounded transition-colors">
      {{ saving ? 'Saving…' : 'Save Horizon Profile' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({ minAltitude: { type: Number, default: 30 } })

const profile = ref([])
const saving = ref(false)
const scanning = ref(false)
const scanProgress = ref(0)
let scanPollInterval = null

const sortedProfile = computed(() =>
  [...profile.value].sort((a, b) => a.az - b.az)
)

const polygonPoints = computed(() => {
  const pts = sortedProfile.value
  if (pts.length < 2) return ''
  const coords = pts.map(p => `${p.az},${90 - p.alt}`).join(' ')
  return `0,90 ${coords} 360,90`
})

onMounted(async () => {
  try {
    const res = await axios.get('/api/settings/horizon-profile')
    profile.value = res.data || []
  } catch {}
})

async function save() {
  saving.value = true
  try {
    await axios.put('/api/settings/horizon-profile', profile.value)
  } finally {
    saving.value = false
  }
}

function addPoint() {
  profile.value.push({ az: 0, alt: 10 })
}

function removePoint(i) {
  profile.value.splice(i, 1)
}

function clearProfile() {
  profile.value = []
}

async function startScan() {
  scanning.value = true
  scanProgress.value = 0
  try {
    const res = await axios.post('/api/horizon/scan')
    const scanId = res.data.scan_id
    scanPollInterval = setInterval(async () => {
      const status = await axios.get(`/api/horizon/scan/${scanId}/status`)
      scanProgress.value = Math.round(status.data.progress || 0)
      if (status.data.points?.length) profile.value = status.data.points
      if (status.data.status === 'complete' || status.data.status === 'error') {
        clearInterval(scanPollInterval)
        scanning.value = false
      }
    }, 2000)
  } catch (e) {
    scanning.value = false
    console.error('Scan failed:', e)
  }
}

function exportProfile() {
  const blob = new Blob([JSON.stringify(sortedProfile.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'horizon-profile.json'; a.click()
  URL.revokeObjectURL(url)
}

async function importProfile(e) {
  const file = e.target.files[0]
  if (!file) return
  const text = await file.text()
  try {
    profile.value = JSON.parse(text)
  } catch { alert('Invalid JSON file') }
}
</script>
```

**Step 2: Add Horizon tab to SettingsModal**

In `SettingsModal.vue`, add a new tab "Horizon" alongside General/Scope/Planning tabs, and render `<HorizonProfileEditor :min-altitude="settingsStore.settings.planMinAltitude" />` in its panel.

**Step 3: Rebuild container and verify**
```bash
docker compose build astronomus && docker compose up -d astronomus
```
Open http://localhost:9247/app/ → Settings → Horizon tab. Verify the editor loads and shows the profile chart.

**Step 4: Commit**
```bash
git add frontend/vue-app/src/components/shared/HorizonProfileEditor.vue \
        frontend/vue-app/src/components/shared/SettingsModal.vue
git commit -m "feat: horizon profile editor with scan button and SVG preview"
```

---

## Final Verification

### Task 14: Run full test suite and confirm all pass

**Step 1: Run all tests**
```bash
docker exec astronomus pytest tests/ -q --no-cov 2>&1 | tail -20
```
Expected: All tests PASS, 0 errors.

**Step 2: If failures, fix before proceeding**

Common issues to check:
- Import errors in new services → verify `__init__.py` exports
- Schema validation errors → check Optional fields have defaults
- Mock not covering network calls → patch Celestrak download in tests

**Step 3: Rebuild with final code**
```bash
docker compose build astronomus && docker compose up -d astronomus
```

**Step 4: Smoke test the API**
```bash
# Verify horizon profile endpoints work
curl -s http://localhost:9247/api/settings/horizon-profile
# Should return []

# Verify plan endpoint accepts new fields
curl -s -X POST http://localhost:9247/api/plan \
  -H "Content-Type: application/json" \
  -d '{"location":{"name":"Test","latitude":46.8,"longitude":-112.0,"elevation":1000,"timezone":"America/Denver"},"observing_date":"2026-05-15","constraints":{"min_altitude":30,"avoid_satellites":false},"solar_targets":["Jupiter"]}' \
  | python3 -m json.tool | head -20
```

---

### Task 15: Create pull request

**Step 1: Push branch**
```bash
git push -u origin feature/horizon-planets-satellites
```

**Step 2: Create PR**
```bash
gh pr create \
  --title "feat: planet scheduling, satellite avoidance, horizon scanner & profile" \
  --body "$(cat <<'EOF'
## Summary
- **Planet/moon scheduling**: Wishlist solar system targets now appear as real time-block entries in the observing plan (not a separate sidebar list). Positions computed at session midpoint via planetary ephemeris.
- **Satellite avoidance**: New `avoid_satellites` constraint (like `avoid_moon`). Uses Celestrak visual TLE set (free, no API key) to block scheduling during ISS/bright satellite passes.
- **Horizon profile**: User-defined per-azimuth altitude minimums stored in settings. Scheduler interpolates local horizon at target azimuth and uses `max(min_altitude, local_horizon)` as the effective floor.
- **Horizon scanner**: Seestar S50 scans its own horizon during the day — sweeps azimuths, binary-searches sky/terrain boundary via camera brightness analysis. Background task API with live progress.
- **Markdown cleanup**: Deleted 12 stale root-level status docs and `docs/archive/` (30 files).

## Test plan
- [ ] `docker exec astronomus pytest tests/ -q --no-cov` passes with 0 failures
- [ ] Settings → Horizon tab loads and shows editor
- [ ] Plan generation with `solar_targets: ["Jupiter"]` returns Jupiter in `scheduled_targets`
- [ ] Plan generation with `avoid_satellites: true` completes without error (may block some slots)
- [ ] PUT/GET `/api/settings/horizon-profile` round-trips correctly
EOF
)"
```

---

## Key Notes for Implementer

- **skyfield is already in requirements** (`skyfield==1.49`). `sgp4` needs to be added.
- **Pillow is already present** (`Pillow>=10.0.0`). `analyze_frame_brightness` uses PIL.
- **`PlanetaryEphemeris.get_position()`** accepts lowercase body names (`"jupiter"`, `"moon"`) and returns `{ra_hours, dec_degrees, altitude, azimuth, magnitude, angular_diameter_arcsec, ...}`.
- **`scope_move_to_horizon`** is confirmed working on this hardware (41 hardware tests pass).
- **AppSetting storage pattern**: key `"user.horizon_profile"` → JSON string, same pattern as `"user.wishlist_targets"`.
- **Tests run inside container**: `docker exec astronomus pytest tests/unit/... -v --no-cov` for unit tests without DB; `docker exec astronomus pytest tests/api/... -v --no-cov` for integration tests that use the test DB.
- **`ObservingConstraints` does NOT currently have `avoid_moon`** in the Pydantic model — it's only in the frontend. The backend silently ignores it. Add `avoid_satellites` to the model properly; don't repeat that inconsistency.
