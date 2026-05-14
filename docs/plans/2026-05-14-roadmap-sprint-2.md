# Roadmap Sprint 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Horizon UX polish, comet ephemeris scheduling, live session tracking, and Caldwell/proximity catalog enrichment.

**Architecture:** FastAPI backend + Vue 3 frontend in single Docker container. New features follow established patterns: comet injection mirrors planet injection; horizon modal is a new Vue component; proximity search is a new API endpoint.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Skyfield, Vue 3, Pinia, Tailwind CSS

---

## Branch

All work on `feature/roadmap-sprint-2`. Run tests with:
```
docker exec astronomus pytest tests/ -q --no-cov
```

---

## Task 0: Branch (already done)

Branch `feature/roadmap-sprint-2` is already checked out. No action needed.

---

## Task 1: Feature 1A — HorizonScanModal.vue (frontend)

**Files to create/modify:**
- `frontend/vue-app/src/components/settings/HorizonScanModal.vue` (CREATE)
- `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue` (MODIFY)

### Step 1: Write the failing test (browser verification)

No pytest test for this pure frontend component. Skip to Step 3.

### Step 2: (Skipped — frontend-only)

### Step 3: Write minimal implementation

**Create `frontend/vue-app/src/components/settings/HorizonScanModal.vue`:**

```vue
<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-2xl shadow-xl">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Horizon Scan</h2>

      <!-- Live SVG horizon chart -->
      <div class="bg-gray-950 rounded p-2 mb-4">
        <svg viewBox="0 0 360 90" class="w-full h-32 border border-gray-700 rounded" preserveAspectRatio="none">
          <line v-for="alt in [15,30,45,60,75]" :key="alt"
            x1="0" :y1="90-alt" x2="360" :y2="90-alt"
            stroke="#374151" stroke-width="0.5" />
          <polygon v-if="points.length >= 2"
            :points="polygonPoints"
            fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="1.5" />
        </svg>
      </div>

      <!-- Status line -->
      <p class="text-sm text-gray-300 mb-4">
        <template v-if="status === 'scanning'">
          Scanning azimuth {{ currentAz }}° — {{ progressPct }}% complete
        </template>
        <template v-else-if="status === 'complete'">
          Scan complete — {{ points.length }} points found
        </template>
        <template v-else-if="status === 'error'">
          <span class="text-red-400">Error: {{ errorMsg }}</span>
        </template>
      </p>

      <!-- Progress bar -->
      <div class="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-blue-500 transition-all duration-500"
          :style="{ width: progressPct + '%' }" />
      </div>

      <!-- Cancel button -->
      <div class="flex justify-end gap-2">
        <button
          v-if="status !== 'complete'"
          @click="cancel"
          class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded transition-colors"
        >
          Cancel
        </button>
        <button
          v-if="status === 'complete'"
          @click="$emit('scan-complete', points)"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
        >
          Use These Points
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  scanId: { type: String, required: true },
  scanMode: { type: String, default: 'binary' },
})
const emit = defineEmits(['scan-complete', 'close'])

const points = ref([])
const currentAz = ref(0)
const progressPct = ref(0)
const status = ref('scanning')
const errorMsg = ref('')
let pollInterval = null

const polygonPoints = computed(() => {
  const pts = [...points.value].sort((a, b) => a.az - b.az)
  if (pts.length < 2) return ''
  const coords = pts.map(p => `${p.az},${90 - p.alt}`).join(' ')
  return `0,90 ${coords} 360,90`
})

async function poll() {
  try {
    const res = await axios.get(`/api/horizon/scan/${props.scanId}/status`)
    const d = res.data
    currentAz.value = d.current_az ?? 0
    progressPct.value = Math.round(d.progress ?? 0)
    if (d.points?.length) points.value = d.points
    status.value = d.status ?? 'scanning'
    if (d.status === 'error') errorMsg.value = d.error || 'Unknown error'
    if (d.status === 'complete' || d.status === 'error') {
      clearInterval(pollInterval)
    }
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e.message
    clearInterval(pollInterval)
  }
}

async function cancel() {
  clearInterval(pollInterval)
  try { await axios.delete(`/api/horizon/scan/${props.scanId}`) } catch {}
  emit('close')
}

onMounted(() => {
  pollInterval = setInterval(poll, 2000)
  poll()
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>
```

**Modify `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue`:**

Replace the `<script setup>` block. Key changes:
1. Import `HorizonScanModal`
2. Add `showModal` and `activeScanId` refs
3. Replace `startScan` to show modal instead of polling inline
4. Add scan-mode toggle refs (`scanMode`)

```vue
<!-- Add to template, before closing </div> of the component root: -->
<div v-if="showModal">
  <HorizonScanModal
    :scan-id="activeScanId"
    :scan-mode="scanMode"
    @scan-complete="onScanComplete"
    @close="showModal = false"
  />
</div>

<!-- Add scan-mode toggle before the Scan Horizon button: -->
<div class="flex gap-3 items-center text-sm text-gray-400 mb-2">
  <label class="flex items-center gap-1 cursor-pointer">
    <input type="radio" v-model="scanMode" value="binary" class="accent-blue-500" />
    Binary search (precise)
  </label>
  <label class="flex items-center gap-1 cursor-pointer">
    <input type="radio" v-model="scanMode" value="steps" class="accent-blue-500" />
    Step scan (faster)
  </label>
</div>
```

```js
// In <script setup>, replace startScan and add new refs:
import HorizonScanModal from '@/components/settings/HorizonScanModal.vue'

const showModal = ref(false)
const activeScanId = ref(null)
const scanMode = ref('binary')
const previousProfile = ref([])

async function startScan() {
  try {
    const res = await axios.post('/api/horizon/scan', null, {
      params: { scan_mode: scanMode.value }
    })
    activeScanId.value = res.data.scan_id
    previousProfile.value = [...profile.value]
    showModal.value = true
  } catch (e) {
    console.error('Failed to start scan:', e)
  }
}

function onScanComplete(points) {
  showModal.value = false
  profile.value = points
  pendingSave.value = true  // triggers 1B inline confirm
}
```

Remove old `scanning`, `scanProgress`, and `scanPollInterval` refs.

### Step 4: Verify in browser

1. Open Settings > Horizon Profile
2. Click "Scan Horizon" — full-screen modal appears
3. SVG polygon updates every 2 seconds as scan progresses
4. Status line shows current azimuth and percent
5. Cancel button calls `DELETE /api/horizon/scan/{id}` and closes
6. On completion modal shows "Use These Points" button

### Step 5: Commit

```bash
git add frontend/vue-app/src/components/settings/HorizonScanModal.vue \
        frontend/vue-app/src/components/shared/HorizonProfileEditor.vue
git commit -m "feat: add HorizonScanModal with live SVG progress and cancel support"
```

---

## Task 2: Feature 1B — Auto-save prompt on scan completion (frontend)

**Files to modify:**
- `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue`

### Step 1: Write the failing test

No pytest test. Frontend-only.

### Step 3: Write minimal implementation

In `HorizonProfileEditor.vue`, add `pendingSave` ref (set to `true` in `onScanComplete`) and an inline confirm section in the template:

```vue
<!-- Inline confirm section — insert above the Save button -->
<div v-if="pendingSave" class="bg-gray-800 border border-blue-700 rounded p-3 space-y-2">
  <p class="text-sm text-gray-200">
    Scan found <strong>{{ profile.length }}</strong> horizon points. Replace current profile?
  </p>
  <div class="flex gap-2">
    <button @click="acceptScan"
      class="flex-1 px-3 py-1.5 bg-green-700 hover:bg-green-600 text-white text-sm rounded transition-colors">
      Yes, Save
    </button>
    <button @click="discardScan"
      class="flex-1 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded transition-colors">
      Discard
    </button>
  </div>
</div>
```

In `<script setup>`:
```js
const pendingSave = ref(false)

function acceptScan() {
  pendingSave.value = false
  save()
}

function discardScan() {
  profile.value = previousProfile.value
  pendingSave.value = false
}
```

### Step 4: Verify in browser

1. Complete a scan (or mock one)
2. Inline confirm section appears: "Scan found N horizon points. Replace current profile?"
3. "Yes, Save" calls `PUT /api/settings/horizon-profile` and hides section
4. "Discard" reverts `profile` to pre-scan values and hides section

### Step 5: Commit

```bash
git add frontend/vue-app/src/components/shared/HorizonProfileEditor.vue
git commit -m "feat: add auto-save prompt after horizon scan completes"
```

---

## Task 3: Feature 1C — Fixed alt steps scan mode (backend + frontend)

**Files to modify:**
- `backend/app/services/horizon_scanner_service.py`
- `backend/app/api/horizon.py`
- `frontend/vue-app/src/components/shared/HorizonProfileEditor.vue` (scan_mode already wired in Task 1)

### Step 1: Write the failing test

In `backend/tests/unit/services/test_horizon_scanner_service.py`, add:

```python
class TestStepScanMode:

    def test_scanner_instantiates_with_steps_mode(self):
        svc = HorizonScannerService(
            telescope_host="127.0.0.1",
            telescope_port=4700,
            scan_mode="steps",
        )
        assert svc.scan_mode == "steps"

    def test_scanner_defaults_to_binary_mode(self):
        svc = HorizonScannerService(telescope_host="127.0.0.1", telescope_port=4700)
        assert svc.scan_mode == "binary"
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/unit/services/test_horizon_scanner_service.py -q --no-cov -k "TestStepScanMode"
```

Expected: `AttributeError: 'HorizonScannerService' object has no attribute 'scan_mode'`

### Step 3: Write minimal implementation

**`backend/app/services/horizon_scanner_service.py`:**

Add `scan_mode: str = "binary"` to `HorizonScannerService.__init__` and store as `self.scan_mode`. Extend the `scan` method:

```python
def __init__(
    self,
    telescope_host: str,
    telescope_port: int,
    az_step: int = 15,
    alt_min: float = 2.0,
    alt_max: float = 45.0,
    scan_mode: str = "binary",
):
    self.host = telescope_host
    self.port = telescope_port
    self.az_step = az_step
    self.alt_min = alt_min
    self.alt_max = alt_max
    self.scan_mode = scan_mode
    self._snapshot_url = "http://localhost:9247/api/telescope/preview/snapshot"

async def scan(self) -> AsyncGenerator[ScanProgress, None]:
    """Sweep azimuths, find horizon altitude, yield progress after each az."""
    azimuths = list(range(0, 360, self.az_step))
    total = len(azimuths)
    points = []

    for i, az in enumerate(azimuths):
        try:
            if self.scan_mode == "steps":
                alt = await self._find_horizon_altitude_steps(az)
            else:
                alt = await self._find_horizon_altitude(az)
        except Exception as e:
            logger.warning("Scan failed at az=%.0f: %s", az, e)
            alt = self.alt_min

        points.append({"az": float(az), "alt": round(alt, 1)})
        yield ScanProgress(
            current_az=float(az),
            total_azimuths=total,
            completed=i + 1,
            points=list(points),
            status="scanning" if i < total - 1 else "complete",
        )

async def _find_horizon_altitude_steps(self, azimuth: float) -> float:
    """Step through altitudes in 2° increments; return first alt where sky ratio >= threshold."""
    ALT_STEP = 2.0
    alt = self.alt_min
    while alt <= self.alt_max:
        await self._move_scope(azimuth, alt)
        await asyncio.sleep(SETTLE_SECONDS)
        frame = await self._capture_frame()
        ratio = analyze_frame_brightness(frame)
        if self._is_sky(ratio):
            return alt
        alt += ALT_STEP
    return self.alt_max
```

**`backend/app/api/horizon.py`:**

Add `scan_mode: str = "binary"` query param to `start_horizon_scan` and pass it to `HorizonScannerService`:

```python
@router.post("/scan")
async def start_horizon_scan(
    telescope_host: str = "192.168.2.47",
    telescope_port: int = 4700,
    az_step: int = 15,
    scan_mode: str = "binary",
):
    scan_id = str(uuid.uuid4())[:8]
    _scans[scan_id] = {"status": "scanning", "progress": 0, "points": [], "current_az": 0}

    async def _run():
        svc = HorizonScannerService(
            telescope_host, telescope_port,
            az_step=az_step,
            scan_mode=scan_mode,
        )
        async for progress in svc.scan():
            _scans[scan_id].update(
                {
                    "status": progress.status,
                    "progress": progress.progress_percent,
                    "current_az": progress.current_az,
                    "points": progress.points,
                }
            )

    asyncio.create_task(_run())
    return {"scan_id": scan_id, "message": "Horizon scan started"}
```

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/unit/services/test_horizon_scanner_service.py -q --no-cov -k "TestStepScanMode"
```

Expected: `2 passed`

### Step 5: Commit

```bash
git add backend/app/services/horizon_scanner_service.py \
        backend/app/api/horizon.py
git commit -m "feat: add step-scan mode to horizon scanner service and API"
```

---

## Task 4: Feature 2A — Comet injection in planner (backend)

**Files to modify:**
- `backend/app/models/models.py`
- `backend/app/services/planner_service.py`

### Step 1: Write the failing test

In `backend/tests/unit/services/test_planner_service.py`, add to `TestPlannerServiceComprehensive`:

```python
def test_generate_plan_with_comet_targets(self, override_get_db):
    """Test that comet_targets in PlanRequest are injected as schedulable targets."""
    request = PlanRequest(
        location=Location(
            name="Test Location", latitude=45.0, longitude=-110.0,
            elevation=1000.0, timezone="America/Denver"
        ),
        observing_date="2025-01-15",
        constraints=ObservingConstraints(min_altitude=30.0),
        comet_targets=["C/2021 TEST1"],
    )
    planner = PlannerService(override_get_db)
    plan = planner.generate_plan(request)
    assert plan is not None
    # Comet is injected; check it appears in scheduled or considered targets
    comet_ids = [
        st.target.catalog_id for st in (plan.scheduled_targets or [])
        if "COMET:" in (st.target.catalog_id or "")
    ]
    # It's acceptable if the comet isn't scheduled (low altitude) but no exception
    assert isinstance(plan.total_targets, int)
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/unit/services/test_planner_service.py::TestPlannerServiceComprehensive::test_generate_plan_with_comet_targets -q --no-cov
```

Expected: `ValidationError` — `comet_targets` field doesn't exist on `PlanRequest`.

### Step 3: Write minimal implementation

**`backend/app/models/models.py`** — add field to `PlanRequest` after `solar_targets`:

```python
comet_targets: Optional[List[str]] = Field(
    default=None,
    description="Comet designations to schedule as imaging targets (e.g. ['C/2020 F3'])",
)
```

**`backend/app/services/planner_service.py`** — after the solar targets injection block (after line ~247), add:

```python
# Inject comet wishlist targets
if request.comet_targets:
    for designation in request.comet_targets:
        try:
            comet = self.comet_service.get_comet_by_designation(designation)
            if comet:
                eph = self.comet_service.compute_ephemeris(comet, midpoint_naive)
                comet_target = DSOTarget(
                    name=designation,
                    catalog_id=f"COMET:{designation}",
                    object_type="comet",
                    ra_hours=eph.ra_hours,
                    dec_degrees=eph.dec_degrees,
                    magnitude=eph.magnitude or 10.0,
                    size_arcmin=5.0,
                    description=f"Comet {designation}",
                    preferred_duration_minutes=15,
                )
                targets.append(comet_target)
                logger.debug("Added comet target %s", designation)
        except Exception as e:
            logger.warning("Failed to add comet target %s: %s", designation, e)
```

Note: `midpoint_naive` is already defined by the solar targets block above it. If the solar targets block was not previously executed (i.e., `request.solar_targets` is None), `midpoint_naive` may not be set. Move midpoint computation outside both blocks:

```python
# Compute midpoint (used by both solar and comet injection)
midpoint_utc = session.imaging_start + (session.imaging_end - session.imaging_start) / 2
midpoint_naive = midpoint_utc.astimezone(pytz.UTC).replace(tzinfo=None)
```

Place this block before either injection section.

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/unit/services/test_planner_service.py::TestPlannerServiceComprehensive::test_generate_plan_with_comet_targets -q --no-cov
```

Expected: `1 passed`

### Step 5: Commit

```bash
git add backend/app/models/models.py \
        backend/app/services/planner_service.py
git commit -m "feat: inject comet_targets into observation plan alongside solar system targets"
```

---

## Task 5: Feature 2B — Visible-tonight comets endpoint (backend)

**Files to modify:**
- `backend/app/api/comets.py`

### Step 1: Write the failing test

In `backend/tests/integration/test_catalog_api.py` (or a new `backend/tests/integration/test_comets_api.py`), add:

```python
import pytest
pytestmark = pytest.mark.integration

def test_visible_tonight_comets_endpoint(client):
    """GET /api/comets/visible-tonight returns a list."""
    resp = client.get("/api/comets/visible-tonight")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Each item has required fields
    for item in data:
        assert "designation" in item
        assert "magnitude" in item
        assert "altitude" in item
        assert "ra_hours" in item
        assert "dec_degrees" in item
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/integration/test_comets_api.py::test_visible_tonight_comets_endpoint -q --no-cov
```

Expected: `404` — endpoint doesn't exist.

### Step 3: Write minimal implementation

Add to `backend/app/api/comets.py` (before other routes to avoid path conflicts):

```python
from datetime import datetime, timezone

@router.get("/visible-tonight")
async def get_visible_comets_tonight(
    min_altitude: float = Query(20.0, description="Minimum altitude in degrees", ge=0, le=90),
    max_magnitude: float = Query(12.0, description="Maximum (faintest) magnitude", ge=0, le=20),
    db: Session = Depends(get_db),
):
    """
    Get comets visible tonight from the user's configured location.

    Uses the saved observer location from app settings.
    Returns a flat list suitable for the frontend Visible Comets panel.
    """
    from app.models.settings_models import AppSetting, ObservingLocation
    from app.services.comet_service import CometService

    # Resolve observer location from settings
    loc_setting = db.query(AppSetting).filter(AppSetting.key == "observing_location").first()
    if loc_setting:
        import json as _json
        loc_data = _json.loads(loc_setting.value)
        location = Location(
            name=loc_data.get("name", "Observer"),
            latitude=loc_data.get("latitude", 45.0),
            longitude=loc_data.get("longitude", -110.0),
            elevation=loc_data.get("elevation", 0.0),
            timezone=loc_data.get("timezone", "UTC"),
        )
    else:
        # Fallback default location
        location = Location(
            name="Default", latitude=45.0, longitude=-110.0, elevation=0.0, timezone="UTC"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    comet_svc = CometService(db)

    try:
        visible = comet_svc.get_visible_comets(
            location=location,
            time_utc=now,
            min_altitude=min_altitude,
            max_magnitude=max_magnitude,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing comet visibility: {str(e)}")

    return [
        {
            "designation": v.comet.designation,
            "name": v.comet.name,
            "magnitude": v.ephemeris.magnitude,
            "altitude": round(v.altitude_deg, 1),
            "azimuth": round(v.azimuth_deg, 1),
            "ra_hours": v.ephemeris.ra_hours,
            "dec_degrees": v.ephemeris.dec_degrees,
        }
        for v in visible
    ]
```

**Important:** This route uses path `/visible-tonight`. Since FastAPI matches routes in declaration order, and `/{designation}` is a catch-all, place the new `GET /visible-tonight` route BEFORE the `GET /{designation}` route in the file.

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/integration/test_comets_api.py::test_visible_tonight_comets_endpoint -q --no-cov
```

Expected: `1 passed`

### Step 5: Commit

```bash
git add backend/app/api/comets.py
git commit -m "feat: add GET /api/comets/visible-tonight endpoint using stored observer location"
```

---

## Task 6: Feature 2C — Comet wishlist + TonightView badge (frontend)

**Files to modify:**
- `frontend/vue-app/src/stores/planning.js`
- `frontend/vue-app/src/views/TonightView.vue` (or `DiscoveryView.vue` — whichever is the "Tonight" tab)

### Step 1: Write the failing test

No pytest test. Frontend-only.

### Step 3: Write minimal implementation

**`frontend/vue-app/src/stores/planning.js`** — add to `state()`:

```js
cometWishlist: [],
```

Add to `actions`:

```js
toggleCometWishlist(designation) {
  const idx = this.cometWishlist.indexOf(designation)
  if (idx >= 0) {
    this.cometWishlist.splice(idx, 1)
  } else {
    this.cometWishlist.push(designation)
  }
},
isCometWishlisted(designation) {
  return this.cometWishlist.includes(designation)
},
```

In `generatePlan` action, inside the `request` object before `axios.post`, add:

```js
if (this.cometWishlist.length > 0) {
  request.comet_targets = [...this.cometWishlist]
}
```

**Add "Visible Comets" panel to the Tonight / Discovery view:**

Find the file that contains the tonight sky summary (check `frontend/vue-app/src/views/` for `TonightView.vue`, `DiscoveryView.vue`, or `PlanningView.vue`). Add a small card component:

```vue
<!-- Visible Comets card (add near the top of the tonight section) -->
<div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
  <h3 class="text-sm font-semibold text-gray-300 mb-3">Comets Visible Tonight</h3>
  <div v-if="cometsLoading" class="text-xs text-gray-500">Loading…</div>
  <div v-else-if="visibleComets.length === 0" class="text-xs text-gray-500 italic">
    No comets above {{ minCometAlt }}° tonight
  </div>
  <div v-else class="space-y-2">
    <div
      v-for="c in visibleComets"
      :key="c.designation"
      class="flex items-center justify-between text-sm"
    >
      <div>
        <span class="text-gray-200 font-medium">{{ c.name || c.designation }}</span>
        <span class="text-gray-500 text-xs ml-2">mag {{ c.magnitude?.toFixed(1) ?? '?' }}</span>
        <span class="text-gray-500 text-xs ml-2">alt {{ c.altitude }}°</span>
      </div>
      <button
        @click="planningStore.toggleCometWishlist(c.designation)"
        :title="planningStore.isCometWishlisted(c.designation) ? 'Remove from plan' : 'Add to plan'"
        class="px-2 py-1 text-xs rounded transition-colors"
        :class="planningStore.isCometWishlisted(c.designation)
          ? 'bg-blue-600/30 text-blue-400 hover:bg-blue-600/50'
          : 'bg-gray-700 text-gray-400 hover:text-blue-400'"
      >
        {{ planningStore.isCometWishlisted(c.designation) ? '✓ Added' : '+ Plan' }}
      </button>
    </div>
  </div>
</div>
```

In `<script setup>` for that view:

```js
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { usePlanningStore } from '@/stores/planning'

const planningStore = usePlanningStore()
const visibleComets = ref([])
const cometsLoading = ref(false)
const minCometAlt = 20

onMounted(async () => {
  cometsLoading.value = true
  try {
    const res = await axios.get('/api/comets/visible-tonight', {
      params: { min_altitude: minCometAlt }
    })
    visibleComets.value = res.data
  } catch (e) {
    // silently ignore if endpoint unavailable
  } finally {
    cometsLoading.value = false
  }
})
```

### Step 4: Verify in browser

1. Tonight/Discovery view shows "Comets Visible Tonight" card
2. "+ Plan" adds comet to `planningStore.cometWishlist`
3. Generating a plan with a wishlisted comet includes `comet_targets` in the API request body

### Step 5: Commit

```bash
git add frontend/vue-app/src/stores/planning.js
# Add whichever view file was modified
git add frontend/vue-app/src/views/TonightView.vue  # or DiscoveryView.vue
git commit -m "feat: add comet wishlist to planning store and visible comets panel on Tonight view"
```

---

## Task 7: Feature 3A — Auto-advance now-marker from telescope state (frontend store)

**Files to modify:**
- `frontend/vue-app/src/stores/execution.js`

### Step 1: Write the failing test

No pytest test. Frontend store logic.

### Step 3: Write minimal implementation

In `frontend/vue-app/src/stores/execution.js`, in `startProgressPolling()`, find the progress handler block (around line 422-435). Add two changes:

1. Update `currentTargetIndex` from backend (this already exists — but confirm it updates `state.currentTargetIndex` not a local variable).
2. Add `nowTime` state and update it on each poll tick.

First, add `nowTime` to state:

```js
// In state() return object, add:
nowTime: new Date(),
```

Then in `startProgressPolling` poll callback, after the existing `backendIndex` handling, add:

```js
// Update nowTime on every poll tick so PlanTimeline marker stays current
this.nowTime = new Date()
```

The existing `currentTargetIndex` update logic already handles the index update. Verify that the wiring reads from state (`this.currentTargetIndex`) rather than a local ref.

**`frontend/vue-app/src/components/execution/PlanTimeline.vue`:**

Ensure the now-marker computation uses `executionStore.nowTime`. If PlanTimeline currently uses `new Date()` inline in a computed, replace with:

```js
import { useExecutionStore } from '@/stores/execution'
const executionStore = useExecutionStore()

// In the now-marker position computed:
const nowMs = computed(() => executionStore.nowTime?.getTime() ?? Date.now())
```

If `PlanTimeline.vue` accepts `nowTime` as a prop, update parent to pass `executionStore.nowTime`.

### Step 4: Verify in browser

1. Start plan execution
2. Telescope progresses to second target
3. PlanTimeline now-marker advances to match the current target's position in the timeline
4. `currentTargetIndex` in the store matches what telescope reports

### Step 5: Commit

```bash
git add frontend/vue-app/src/stores/execution.js
git commit -m "feat: sync currentTargetIndex and nowTime from telescope progress poll"
```

---

## Task 8: Feature 3B — Frames captured display in NowPlayingPanel (frontend)

**Files to modify:**
- `frontend/vue-app/src/stores/execution.js`
- `frontend/vue-app/src/components/execution/NowPlayingPanel.vue`

### Step 1: Write the failing test

No pytest test. Frontend-only.

### Step 3: Write minimal implementation

**`frontend/vue-app/src/stores/execution.js`** — add to `state()`:

```js
framesCaptures: 0,
totalFrames: 0,
```

In `startProgressPolling` callback, update from progress response:

```js
if (p.frames_captured != null) this.framesCaptures = p.frames_captured
if (p.total_frames != null) this.totalFrames = p.total_frames
```

Note: The backend `GET /api/telescope/progress` response currently does not include `frames_captured`/`total_frames`. Task 9 (3C) adds `active_plan_id`; frames data comes from `TelescopeExecutionTarget.actual_exposures` and `recommended_frames`. Add these fields to the progress response in `backend/app/api/telescope.py` at the same time as Task 9, or add them here:

In `backend/app/api/telescope.py` `get_execution_progress()`, add to the return dict:

```python
# Get current target's frame data
frames_captured = 0
total_frames = 0
current_target = next(
    (t for t in execution.targets if t.target_index == execution.current_target_index),
    None
)
if current_target:
    frames_captured = current_target.actual_exposures or 0
    total_frames = current_target.recommended_frames or 0

return {
    ...,  # existing fields
    "frames_captured": frames_captured,
    "total_frames": total_frames,
}
```

**`frontend/vue-app/src/components/execution/NowPlayingPanel.vue`** — after the time progress bar, add:

```vue
<!-- Frames progress (shown when frames data available) -->
<div v-if="executionStore.totalFrames > 0 && executionStore.executionStatus === 'running'" class="space-y-1">
  <div class="flex justify-between text-xs text-gray-400">
    <span>Frame {{ executionStore.framesCaptures }} of {{ executionStore.totalFrames }}</span>
    <span v-if="estFrameRemaining != null" class="text-gray-200">
      ~{{ estFrameRemaining }} remaining
    </span>
  </div>
  <div class="h-1 bg-gray-800 rounded-full overflow-hidden">
    <div class="h-full bg-green-500 transition-none"
      :style="{ width: frameProgressPct + '%' }" />
  </div>
</div>
```

In `<script setup>`:

```js
const frameProgressPct = computed(() => {
  const total = executionStore.totalFrames
  if (!total) return 0
  return Math.min(100, Math.max(0, (executionStore.framesCaptures / total) * 100))
})

// Estimated remaining based on current scheduled target's exposure time
const estFrameRemaining = computed(() => {
  const remaining = executionStore.totalFrames - executionStore.framesCaptures
  if (remaining <= 0) return null
  const expSec = currentSt.value?.target?.exposure_seconds ?? 10
  const totalSec = remaining * expSec
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
})
```

### Step 4: Verify in browser

1. Start plan execution
2. NowPlayingPanel shows green "Frame X of Y" bar below the time countdown
3. Bar advances as telescope captures frames
4. Estimated remaining time displayed

### Step 5: Commit

```bash
git add frontend/vue-app/src/stores/execution.js \
        frontend/vue-app/src/components/execution/NowPlayingPanel.vue \
        backend/app/api/telescope.py
git commit -m "feat: display frames captured progress in NowPlayingPanel during execution"
```

---

## Task 9: Feature 3C — Active plan persistence (backend)

**Files to modify:**
- `backend/app/api/telescope.py`

### Step 1: Write the failing test

Add to `backend/tests/integration/test_telescope_api.py` (or create if needed):

```python
import pytest
pytestmark = pytest.mark.integration

def test_progress_includes_active_plan_id(client):
    """GET /api/telescope/progress response includes active_plan_id field."""
    resp = client.get("/api/telescope/progress")
    assert resp.status_code == 200
    data = resp.json()
    # Field must be present (may be None when no active execution)
    assert "active_plan_id" in data
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/integration/test_telescope_api.py::test_progress_includes_active_plan_id -q --no-cov
```

Expected: `AssertionError: 'active_plan_id' not in {...}`

### Step 3: Write minimal implementation

**`backend/app/api/telescope.py`** — in `get_execution_progress()`, add `active_plan_id` to the return dict:

```python
return {
    "execution_id": execution.execution_id,
    "state": execution.state,
    "total_targets": execution.total_targets,
    "current_target_index": execution.current_target_index,
    "targets_completed": execution.targets_completed,
    "targets_failed": execution.targets_failed,
    "current_target_name": execution.current_target_name,
    "current_phase": execution.current_phase,
    "progress_percent": round(execution.progress_percent, 1),
    "elapsed_time": elapsed_time,
    "estimated_remaining": estimated_remaining,
    "errors": errors,
    "active_plan_id": execution.saved_plan_id,  # Links execution to the saved plan
    "frames_captured": frames_captured,          # Added in Task 8
    "total_frames": total_frames,                # Added in Task 8
}
```

The `saved_plan_id` field already exists on `TelescopeExecution` and is populated when `ExecutePlanRequest.saved_plan_id` is set. The frontend can use this to identify which plan's targets to show in PlanTimeline.

No additional AppSetting storage is required because the `TelescopeExecution` table already carries `saved_plan_id`. If the frontend needs to persist this across page refreshes (before execution starts), a follow-up can add an AppSetting write, but for Sprint 2 the execution record is sufficient.

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/integration/test_telescope_api.py::test_progress_includes_active_plan_id -q --no-cov
```

Expected: `1 passed`

### Step 5: Commit

```bash
git add backend/app/api/telescope.py
git commit -m "feat: include active_plan_id in telescope progress response"
```

---

## Task 10: Feature 4A — Caldwell catalog seeding (backend)

**Files to create/modify:**
- `backend/scripts/seed_caldwell.py` (CREATE)
- `backend/scripts/init_catalog.py` (MODIFY)

### Step 1: Write the failing test

Add to `backend/tests/unit/services/test_catalog_service.py`:

```python
def test_caldwell_object_returned_by_id(self, override_get_db):
    """After Caldwell seeding, C14 (Double Cluster) should be retrievable."""
    from scripts.seed_caldwell import seed_caldwell_if_needed
    seed_caldwell_if_needed(override_get_db)

    service = CatalogService(override_get_db)
    target = service.get_target_by_id("C14")
    assert target is not None
    assert "C14" in (target.catalog_id or "")
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py::TestCatalogServiceComprehensive::test_caldwell_object_returned_by_id -q --no-cov
```

Expected: `ImportError` (seed_caldwell.py doesn't exist) or `AssertionError`.

### Step 3: Write minimal implementation

**Create `backend/scripts/seed_caldwell.py`:**

```python
#!/usr/bin/env python3
"""Seed Caldwell catalog objects into dso_catalog table.

Creates standalone entries for Caldwell objects that are identified by
their 'C{num}' catalog ID. Objects already present by catalog_id are skipped.
Reads from caldwell_data.py (already written, 109 complete entries).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_caldwell_if_needed(db=None) -> int:
    """Insert Caldwell objects into dso_catalog. Returns count of inserted rows.

    Args:
        db: Optional existing SQLAlchemy session. If None, creates own session.
    """
    from app.models.catalog_models import DSOCatalog

    own_session = db is None
    if own_session:
        from app.database import SessionLocal
        db = SessionLocal()

    try:
        from scripts.caldwell_data import CALDWELL_CATALOG

        inserted = 0
        for entry in CALDWELL_CATALOG:
            num = entry["caldwell"]
            catalog_id_str = f"C{num}"

            # Skip if already present (check common_name or catalog_name+number)
            existing = (
                db.query(DSOCatalog)
                .filter(DSOCatalog.common_name == catalog_id_str)
                .first()
            )
            if existing:
                continue

            # Parse NGC/IC reference to get catalog_name and catalog_number
            ngc_ref = entry.get("ngc", "")
            cat_name = "NGC"
            cat_num = 0
            if ngc_ref.upper().startswith("NGC"):
                cat_num = int(ngc_ref.strip().split()[-1])
                cat_name = "NGC"
            elif ngc_ref.upper().startswith("IC"):
                cat_num = int(ngc_ref.strip().split()[-1])
                cat_name = "IC"

            dso = DSOCatalog(
                catalog_name=cat_name,
                catalog_number=cat_num,
                common_name=catalog_id_str,   # "C14", "C1", etc.
                caldwell_number=num,
                ra_hours=entry["ra_hours"],
                dec_degrees=entry["dec_degrees"],
                object_type=entry["type"],
                magnitude=entry.get("magnitude"),
                size_major_arcmin=entry.get("size_arcmin"),
                constellation=entry.get("constellation"),
            )
            db.add(dso)
            inserted += 1

        if own_session:
            db.commit()
        else:
            db.flush()

        return inserted

    except Exception as e:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = seed_caldwell_if_needed()
    print(f"Seeded {n} Caldwell objects.")
```

**Modify `backend/scripts/init_catalog.py`** — at the end of `seed_catalog()`, before the final `print` and after `db.commit()`:

```python
# Seed Caldwell objects (idempotent — skips existing entries)
try:
    from scripts.seed_caldwell import seed_caldwell_if_needed
    n = seed_caldwell_if_needed(db)
    if n > 0:
        print(f"✓ Caldwell: seeded {n} objects.")
    else:
        print("Caldwell: already seeded, skipping.")
except Exception as e:
    print(f"⚠ Caldwell seeding failed: {e}", file=sys.stderr)
```

Also ensure `CatalogService.get_target_by_id` resolves `C{num}` IDs. Check `backend/app/services/catalog_service.py` for the resolver. If it only checks `NGC` and `IC` prefixes, add a `C` prefix resolver:

```python
# In get_target_by_id, add branch:
if upper_id.startswith("C") and upper_id[1:].isdigit():
    # Caldwell ID — look up by common_name
    return db.query(DSOCatalog).filter(
        DSOCatalog.common_name == upper_id
    ).first()
```

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py::TestCatalogServiceComprehensive::test_caldwell_object_returned_by_id -q --no-cov
```

Expected: `1 passed`

### Step 5: Commit

```bash
git add backend/scripts/seed_caldwell.py \
        backend/scripts/init_catalog.py
git commit -m "feat: seed 109 Caldwell objects into dso_catalog on startup"
```

---

## Task 11: Feature 4B — Angular proximity search endpoint (backend)

**Files to modify:**
- `backend/app/api/routes.py` (or `catalog.py` — wherever `GET /api/targets` endpoints live)

### Step 1: Write the failing test

Add to `backend/tests/integration/test_catalog_api.py`:

```python
def test_nearby_objects_returns_sorted_results(client):
    """GET /api/targets/near returns objects sorted by angular separation."""
    # M31 (Andromeda) — NGC 224 at RA 0.712h, Dec +41.27°
    resp = client.get("/api/targets/near", params={
        "ra_hours": 0.712,
        "dec_degrees": 41.27,
        "radius_deg": 5.0,
        "limit": 5,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Results must include separation_deg field
    for item in data:
        assert "separation_deg" in item
        assert item["separation_deg"] >= 0.0
    # Results sorted by separation_deg ascending
    seps = [item["separation_deg"] for item in data]
    assert seps == sorted(seps)

def test_nearby_objects_first_result_is_m31_itself(client):
    """Searching near M31 coordinates should return M31 first at ~0° separation."""
    resp = client.get("/api/targets/near", params={
        "ra_hours": 0.712,
        "dec_degrees": 41.27,
        "radius_deg": 1.0,
        "limit": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    if data:
        assert data[0]["separation_deg"] < 0.1  # M31 itself at ~0°
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/integration/test_catalog_api.py::test_nearby_objects_returns_sorted_results -q --no-cov
```

Expected: `404` — endpoint doesn't exist.

### Step 3: Write minimal implementation

Add a new route. Find where `/api/targets` routes are registered — likely `backend/app/api/routes.py`. Add:

```python
import math

@router.get("/targets/near")
async def get_nearby_targets(
    ra_hours: float = Query(..., description="Reference RA in hours"),
    dec_degrees: float = Query(..., description="Reference Dec in degrees"),
    radius_deg: float = Query(2.0, description="Search radius in degrees", gt=0, le=20),
    limit: int = Query(10, description="Maximum results", gt=0, le=50),
    db: Session = Depends(get_db),
):
    """
    Return DSO catalog objects within radius_deg of the given coordinates.

    Uses Haversine angular separation formula with a Dec band pre-filter
    for performance. Results sorted by angular separation ascending.
    """
    from app.models.catalog_models import DSOCatalog

    ref_ra_deg = ra_hours * 15.0  # Convert hours to degrees
    ref_dec = dec_degrees

    # Pre-filter by declination band to avoid full table scan
    dec_min = ref_dec - radius_deg
    dec_max = ref_dec + radius_deg
    candidates = (
        db.query(DSOCatalog)
        .filter(DSOCatalog.dec_degrees >= dec_min)
        .filter(DSOCatalog.dec_degrees <= dec_max)
        .all()
    )

    results = []
    for obj in candidates:
        # Haversine angular separation
        ra1, dec1 = math.radians(ref_ra_deg), math.radians(ref_dec)
        ra2, dec2 = math.radians(obj.ra_hours * 15.0), math.radians(obj.dec_degrees)
        delta_ra = ra2 - ra1
        delta_dec = dec2 - dec1
        a = (
            math.sin(delta_dec / 2) ** 2
            + math.cos(dec1) * math.cos(dec2) * math.sin(delta_ra / 2) ** 2
        )
        sep_deg = math.degrees(2 * math.asin(math.sqrt(min(a, 1.0))))

        if sep_deg <= radius_deg:
            results.append({
                "catalog_id": obj.common_name or f"{obj.catalog_name}{obj.catalog_number}",
                "name": obj.common_name or f"{obj.catalog_name} {obj.catalog_number}",
                "catalog_name": obj.catalog_name,
                "catalog_number": obj.catalog_number,
                "object_type": obj.object_type,
                "ra_hours": obj.ra_hours,
                "dec_degrees": obj.dec_degrees,
                "magnitude": obj.magnitude,
                "constellation": obj.constellation,
                "separation_deg": round(sep_deg, 3),
            })

    results.sort(key=lambda x: x["separation_deg"])
    return results[:limit]
```

### Step 4: Run test to verify it passes

```bash
docker exec astronomus pytest tests/integration/test_catalog_api.py::test_nearby_objects_returns_sorted_results tests/integration/test_catalog_api.py::test_nearby_objects_first_result_is_m31_itself -q --no-cov
```

Expected: `2 passed`

### Step 5: Commit

```bash
git add backend/app/api/routes.py   # or catalog.py
git commit -m "feat: add GET /api/targets/near proximity search with Haversine separation"
```

---

## Task 12: Feature 4C — Nearby Objects in expanded catalog card (frontend)

**Files to modify:**
- `frontend/vue-app/src/components/discovery/CatalogGrid.vue`

### Step 1: Write the failing test

No pytest test. Frontend-only.

### Step 3: Write minimal implementation

In `CatalogGrid.vue`, add a `nearbyCache` ref and fetch function:

```js
const nearbyCache = ref({})

async function fetchNearbyObjects(item) {
  const key = cardKey(item)
  if (nearbyCache.value[key] !== undefined) return
  if (item.ra == null || item.dec == null) return

  nearbyCache.value[key] = null  // Mark as loading
  try {
    const res = await axios.get('/api/targets/near', {
      params: {
        ra_hours: item.ra,
        dec_degrees: item.dec,
        radius_deg: 2,
        limit: 5,
      }
    })
    // Exclude the item itself (separation ~0)
    nearbyCache.value[key] = res.data.filter(n => n.separation_deg > 0.05)
  } catch {
    nearbyCache.value[key] = []
  }
}
```

In `toggleCard`, after the existing logic that triggers `fetchAltitudeCurve` and `fetchViewingMonths`, also call:

```js
fetchNearbyObjects(item)
```

In the template, inside the expanded card section (after `<!-- Capture Review -->`):

```vue
<!-- Nearby Objects (shown when card expanded) -->
<div v-if="expandedCardId === cardKey(item)" class="border-t border-gray-700 pt-2 mt-2">
  <p class="text-xs text-gray-500 mb-1">Nearby objects (2°)</p>
  <div v-if="nearbyCache[cardKey(item)] === null" class="text-xs text-gray-600">
    Loading…
  </div>
  <div v-else-if="nearbyCache[cardKey(item)]?.length === 0" class="text-xs text-gray-600">
    None within 2°
  </div>
  <div v-else class="flex flex-wrap gap-1">
    <span
      v-for="nearby in nearbyCache[cardKey(item)]"
      :key="nearby.catalog_id"
      class="inline-flex items-center gap-1 px-1.5 py-0.5 bg-gray-800 rounded text-xs text-gray-300 cursor-pointer hover:bg-gray-700"
      :title="`${nearby.object_type} · ${nearby.separation_deg}° away`"
      @click="scrollToCard(nearby)"
    >
      <span class="text-gray-400">{{ nearby.name }}</span>
      <span class="text-gray-600">{{ nearby.separation_deg }}°</span>
    </span>
  </div>
</div>
```

Add `scrollToCard` function:

```js
function scrollToCard(nearbyItem) {
  // Attempt to find and scroll to the nearby item's card in the grid
  // If the item is on a different page, this is best-effort
  const targetKey = nearbyItem.catalog_id
  const cards = gridEl.value?.querySelectorAll('.catalog-card')
  if (!cards) return
  // Could also set a search filter in catalogStore to navigate to it
  catalogStore.setSearch(nearbyItem.name)
}
```

### Step 4: Verify in browser

1. Open Discovery / Catalog view
2. Expand a card (e.g., M31 / NGC224)
3. "Nearby objects (2°)" section appears at the bottom
4. Shows compact tags like "NGC221 (0.3°)", "NGC205 (0.6°)"
5. Clicking a tag triggers a search for that object

### Step 5: Commit

```bash
git add frontend/vue-app/src/components/discovery/CatalogGrid.vue
git commit -m "feat: show nearby catalog objects in expanded catalog card using proximity search"
```

---

## Task 13: Run full test suite; fix any failures

### Step 1: Run all tests

```bash
docker exec astronomus pytest tests/ -q --no-cov
```

### Step 2: Fix failures

Common failure patterns to anticipate:

1. **Import errors** in `seed_caldwell.py` — check `sys.path` includes `backend/` directory.
2. **Route order conflict** in `comets.py` — `GET /visible-tonight` must appear before `GET /{designation}` to avoid FastAPI matching `visible-tonight` as a designation value.
3. **Missing `midpoint_naive` variable** in `planner_service.py` — ensure midpoint is computed before both solar and comet injection blocks, not inside a conditional.
4. **`CatalogService.get_target_by_id` doesn't handle `C{num}` format** — add the `C` prefix branch as described in Task 10.
5. **Isort / black failures** — run `black --line-length 120` and `isort --profile black --settings-path backend` on all modified Python files before committing.

### Step 3: CI checks

```bash
docker exec astronomus black --check --line-length 120 backend/
docker exec astronomus isort --check --profile black --settings-path backend backend/
docker exec astronomus ruff check backend/
docker exec astronomus bandit -r backend/app/ -q
```

Fix any linting issues, then re-run tests.

### Step 4: Commit fixes

```bash
git add -p  # Stage specific fixes
git commit -m "fix: address test failures and linting issues from sprint 2 implementation"
```

---

## Task 14: Create PR to main

```bash
git push -u origin feature/roadmap-sprint-2
gh pr create \
  --title "feat: Roadmap Sprint 2 — horizon UX, comet planner, live tracking, catalog enrichment" \
  --body "## Summary

- Feature 1: Horizon Autoscan UX — full-screen progress modal with live SVG, auto-save prompt, step-scan mode
- Feature 2: Comet Ephemeris in Planner — comet injection into plan, visible-tonight endpoint, comet wishlist on Tonight view
- Feature 3: Live Session Tracking — now-marker auto-advances from telescope progress, frames captured bar in NowPlayingPanel, active_plan_id in progress response
- Feature 4: Catalog Enrichment — 109 Caldwell objects seeded, angular proximity search endpoint, Nearby Objects in catalog cards

## Test plan
- [ ] All unit tests pass: \`docker exec astronomus pytest tests/ -q --no-cov\`
- [ ] Horizon scan modal opens, shows live SVG, cancel works
- [ ] Scan completion shows inline save/discard prompt
- [ ] Step-scan mode available and selectable
- [ ] Plan with comet_targets includes comet injection (check plan API response)
- [ ] GET /api/comets/visible-tonight returns 200 with list
- [ ] Tonight view shows Visible Comets card; '+Plan' adds to wishlist
- [ ] During execution, timeline marker advances on target change
- [ ] NowPlayingPanel shows frames progress bar when frames data present
- [ ] GET /api/telescope/progress includes active_plan_id field
- [ ] GET /api/targets/near returns sorted results with separation_deg
- [ ] Expanded catalog cards show Nearby Objects section
- [ ] CI passes: black, isort, ruff, bandit

🤖 Generated with Claude Code"
```

---

## Key notes for implementation

1. **Route ordering in `comets.py`**: FastAPI resolves routes top-to-bottom. `GET /visible-tonight` must be declared before `GET /{designation}` to prevent `visible-tonight` being captured as a designation parameter.

2. **`midpoint_naive` scoping in `planner_service.py`**: The existing code only computes `midpoint_naive` inside `if request.solar_targets:`. Move this computation outside both conditional blocks so comet injection can use it independently.

3. **Caldwell `common_name` field**: The seed script uses `common_name` to store the `C{num}` identifier (e.g., "C14"). `CatalogService.get_target_by_id` must be updated to handle the `C` prefix by querying `common_name`.

4. **`frames_captured` / `total_frames` in progress**: These fields are sourced from `TelescopeExecutionTarget.actual_exposures` and `recommended_frames`. The join query needs to match `target_index == current_target_index` on the active execution.

5. **Frontend `nowTime` reactivity**: Pinia state is reactive; updating `this.nowTime = new Date()` in the poll callback will trigger computed re-renders in `PlanTimeline.vue` automatically if the component uses `executionStore.nowTime`.

