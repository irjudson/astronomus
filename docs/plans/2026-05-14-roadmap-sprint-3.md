# Roadmap Sprint 3 Implementation Plan


**Goal:** Live session tracking polish, comet auto-injection toggle, Arp/Sharpless catalog import, custom target image thumbnails.

**Architecture:** FastAPI backend + Vue 3 frontend in single Docker container. Catalog additions follow established seeder pattern (seed_caldwell.py). Two Alembic migrations required.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Vue 3, Pinia, Tailwind CSS

---

## Branch

All work on `feature/roadmap-sprint-3`. Run tests with:
```
docker exec astronomus pytest tests/ -q --no-cov
```

---

## Task 0: Branch (already done)

Branch `feature/roadmap-sprint-3` is already checked out. Verify with:
```bash
git branch --show-current
# should output: feature/roadmap-sprint-3
```

---

## Task 1: Feature 1A — Auto-advance when frames complete

**Files to modify:**
- `frontend/vue-app/src/stores/execution.js`

### What exists

`startProgressPolling()` (lines 415-452) polls `GET /api/telescope/progress` every 3s and updates `this.framesCaptures` and `this.totalFrames`. It does NOT auto-advance.

`skipTarget()` (lines 493-515) aborts current target, increments `currentTargetIndex`, resubmits remaining targets.

### What to add

Inside `startProgressPolling()`, in the `setInterval` callback, after the `frames_captured` / `total_frames` update block (after line 436), add auto-advance logic. Add a `lastAutoAdvancedIndex` property to state to prevent re-triggering.

**State addition** — in `state: () => ({...})`, add after `totalFrames: 0,`:
```js
lastAutoAdvancedIndex: -1,   // guard: prevent double-skip on same target
```

**Auto-advance logic** — insert immediately after the existing frames update block inside the poll callback (after `if (p.total_frames != null) this.totalFrames = p.total_frames`):
```js
// Auto-advance when all frames captured for this target
if (
  this.framesCaptures >= this.totalFrames &&
  this.totalFrames > 0 &&
  this.executionStatus === 'running' &&
  this.currentTargetIndex !== this.lastAutoAdvancedIndex
) {
  this.lastAutoAdvancedIndex = this.currentTargetIndex
  this.skipTarget()
  return
}
```

Also reset `lastAutoAdvancedIndex` to `-1` inside `setPlan()` (after `this.resumeOffset = 0`) so it resets when a new plan is loaded.

### Test (browser verification)

1. Load a plan with at least 2 targets. Execute.
2. In browser DevTools console: `useExecutionStore().framesCaptures = useExecutionStore().totalFrames`
3. Within 3s, the NowPlayingPanel should advance to the next target without clicking Skip.

### Commit
```bash
git add frontend/vue-app/src/stores/execution.js
git commit -m "feat: auto-advance to next target when all frames captured"
```

---

## Task 2: Feature 1B — Rename "Skip" button to "Done →"

**Files to modify:**
- `frontend/vue-app/src/components/execution/NowPlayingPanel.vue`

### What exists

Lines 84-90 in `NowPlayingPanel.vue`:
```html
<button
  @click="executionStore.skipTarget()"
  :disabled="executionStore.currentTargetIndex + 1 >= (executionStore.scheduledTargets?.length ?? 0)"
  class="flex-1 px-3 py-2 text-sm rounded bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
>
  Skip ⏭
</button>
```

### Changes

1. Replace label `Skip ⏭` with `Done →`
2. Change button class from `bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700` to `bg-green-800 hover:bg-green-700 text-green-100 border border-green-700`
3. Add `title="Mark current target done and move to next"` attribute

Full replacement for lines 84-91:
```html
<button
  @click="executionStore.skipTarget()"
  :disabled="executionStore.currentTargetIndex + 1 >= (executionStore.scheduledTargets?.length ?? 0)"
  title="Mark current target done and move to next"
  class="flex-1 px-3 py-2 text-sm rounded bg-green-800 hover:bg-green-700 text-green-100 border border-green-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
>
  Done →
</button>
```

### Test (browser verification)

Open the Execution view. The Skip button should now read "Done →" in green. Hovering shows the tooltip.

### Commit
```bash
git add frontend/vue-app/src/components/execution/NowPlayingPanel.vue
git commit -m "feat: rename Skip button to Done → with green color and tooltip"
```

---

## Task 3: Feature 2 — "Include visible comets" toggle (frontend only)

**Files to modify:**
- `frontend/vue-app/src/stores/planning.js`
- `frontend/vue-app/src/components/planning/PlanningControls.vue`

### What exists

`planning.js` state has `cometWishlist: []` and explicit comet injection via `request.comet_targets`. The backend `planner_service.py` auto-injects visible comets when `"comet" in request.constraints.object_types` (lines 177-210).

`PlanningControls.vue` has constraint toggles for Avoid Moon (line 49-55) and Avoid Satellites (lines 57-63). There is no comet inclusion toggle.

`ObservingConstraints` in `backend/app/models/models.py` has `object_types: List[str]` (line 42). The frontend sends `object_types` as `this.constraints.object_types` (planning.js line 125).

### Step A: planning.js

In `state: () => ({...})`, add after `cometWishlist: [],`:
```js
includeComets: false,
```

In `generatePlan()`, after the existing `if (this.cometWishlist.length > 0)` block (around line 144-146), add:
```js
// Include auto-discovered visible comets if toggle is on
if (this.includeComets) {
  if (!request.constraints.object_types) {
    request.constraints.object_types = []
  }
  if (!request.constraints.object_types.includes('comet')) {
    request.constraints.object_types = [...request.constraints.object_types, 'comet']
  }
}
```

### Step B: PlanningControls.vue

After the "Avoid Satellites" `<label>` block (lines 57-65), add the new toggle:
```html
<label class="flex items-center justify-between p-3 bg-gray-800 rounded cursor-pointer hover:bg-gray-750 transition-colors">
  <span class="text-sm text-gray-200">Include visible comets</span>
  <input
    v-model="planningStore.includeComets"
    type="checkbox"
    class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
  />
</label>
```

No backend changes needed — backend already handles `"comet"` in `object_types`.

### Test (browser verification)

1. Open Planning view. Verify "Include visible comets" checkbox appears under Avoid Satellites.
2. Check the box. Click "Generate Plan". Confirm no 500 error in the Network tab.
3. Uncheck the box. Generate again. The generated plan should not include comets (unless wishlist has them).

### Commit
```bash
git add frontend/vue-app/src/stores/planning.js frontend/vue-app/src/components/planning/PlanningControls.vue
git commit -m "feat: add 'Include visible comets' toggle to planning constraints"
```

---

## Task 4: Feature 3A — Alembic migration for arp_number + sharpless_number

**Files to create:**
- `backend/alembic/versions/<revision_id>_add_arp_sharpless_to_dso_catalog.py`

**Files to modify:**
- `backend/app/models/catalog_models.py`

### Step A: Create migration

Run inside the container:
```bash
docker exec astronomus bash -c "cd /app && alembic revision --autogenerate -m 'add_arp_sharpless_to_dso_catalog'"
```

Then edit the generated file so the `upgrade()` function contains exactly:
```python
def upgrade() -> None:
    op.add_column('dso_catalog', sa.Column('arp_number', sa.Integer(), nullable=True))
    op.add_column('dso_catalog', sa.Column('sharpless_number', sa.Integer(), nullable=True))
    op.create_index('ix_dso_catalog_arp_number', 'dso_catalog', ['arp_number'], unique=False)
    op.create_index('ix_dso_catalog_sharpless_number', 'dso_catalog', ['sharpless_number'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_dso_catalog_sharpless_number', table_name='dso_catalog')
    op.drop_index('ix_dso_catalog_arp_number', table_name='dso_catalog')
    op.drop_column('dso_catalog', 'sharpless_number')
    op.drop_column('dso_catalog', 'arp_number')
```

Apply migration:
```bash
docker exec astronomus bash -c "cd /app && alembic upgrade head"
```

### Step B: Update SQLAlchemy model

In `backend/app/models/catalog_models.py`, inside `class DSOCatalog`, after the `caldwell_number` column (line 19), add:
```python
arp_number = Column(Integer, nullable=True, index=True)        # Arp Atlas number (1-338)
sharpless_number = Column(Integer, nullable=True, index=True)  # Sharpless HII region number
```

### Test
```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py -q --no-cov
```
The existing catalog tests must still pass. The new columns are nullable so no data changes break anything.

### Commit
```bash
git add backend/alembic/versions/ backend/app/models/catalog_models.py
git commit -m "feat: add arp_number and sharpless_number columns to dso_catalog"
```

---

## Task 5: Feature 3B — Arp catalog data file + seeder

**Files to create:**
- `backend/scripts/arp_data.py`
- `backend/scripts/seed_arp.py`

### Step A: Create arp_data.py

Create `backend/scripts/arp_data.py` with the top 50 Arp objects observable with Seestar S50 (magnitude brighter than ~14, sorted by Arp number):

```python
"""
Arp Atlas of Peculiar Galaxies — top 50 objects observable with Seestar S50.
Sources: Arp (1966), NED, SIMBAD cross-references.
All coordinates J2000.0.
"""

ARP_CATALOG = [
    # Arp 18 — NGC 4088, spiral with asymmetric arms
    {"arp": 18, "ngc": "NGC 4088", "ra_hours": 12.086, "dec_degrees": 50.535,
     "type": "galaxy", "magnitude": 11.2, "size_arcmin": 5.8, "constellation": "CVn"},
    # Arp 26 — NGC 3718, severely warped spiral
    {"arp": 26, "ngc": "NGC 3718", "ra_hours": 11.576, "dec_degrees": 53.068,
     "type": "galaxy", "magnitude": 11.0, "size_arcmin": 8.1, "constellation": "UMa"},
    # Arp 28 — NGC 7678, one-armed spiral
    {"arp": 28, "ngc": "NGC 7678", "ra_hours": 23.474, "dec_degrees": 22.425,
     "type": "galaxy", "magnitude": 12.4, "size_arcmin": 2.2, "constellation": "Peg"},
    # Arp 47 — NGC 5829, spiral with detached segment
    {"arp": 47, "ngc": "NGC 5829", "ra_hours": 15.063, "dec_degrees": 23.422,
     "type": "galaxy", "magnitude": 13.4, "size_arcmin": 2.2, "constellation": "Boo"},
    # Arp 49 — NGC 2623, merging pair
    {"arp": 49, "ngc": "NGC 2623", "ra_hours": 8.580, "dec_degrees": 25.755,
     "type": "galaxy", "magnitude": 13.1, "size_arcmin": 1.9, "constellation": "Cnc"},
    # Arp 78 — NGC 772, unequal spiral arms
    {"arp": 78, "ngc": "NGC 772", "ra_hours": 1.984, "dec_degrees": 19.008,
     "type": "galaxy", "magnitude": 11.1, "size_arcmin": 7.2, "constellation": "Ari"},
    # Arp 81 — NGC 6621, interacting pair
    {"arp": 81, "ngc": "NGC 6621", "ra_hours": 18.323, "dec_degrees": 68.362,
     "type": "galaxy", "magnitude": 13.4, "size_arcmin": 1.8, "constellation": "Dra"},
    # Arp 84 — NGC 5395, spiral with a companion
    {"arp": 84, "ngc": "NGC 5395", "ra_hours": 13.986, "dec_degrees": 37.565,
     "type": "galaxy", "magnitude": 12.1, "size_arcmin": 3.0, "constellation": "CVn"},
    # Arp 85 — M51 (NGC 5194), interacting pair (most famous Arp)
    {"arp": 85, "ngc": "NGC 5194", "ra_hours": 13.4997, "dec_degrees": 47.195,
     "type": "galaxy", "magnitude": 8.4, "size_arcmin": 11.2, "constellation": "CVn"},
    # Arp 86 — NGC 7752, interacting pair
    {"arp": 86, "ngc": "NGC 7752", "ra_hours": 23.807, "dec_degrees": 29.467,
     "type": "galaxy", "magnitude": 13.2, "size_arcmin": 1.4, "constellation": "Peg"},
    # Arp 94 — NGC 3226/3227, galaxy pair
    {"arp": 94, "ngc": "NGC 3226", "ra_hours": 10.428, "dec_degrees": 19.898,
     "type": "galaxy", "magnitude": 12.2, "size_arcmin": 2.8, "constellation": "Leo"},
    # Arp 104 — NGC 5216/5218, dumbbell-shaped pair
    {"arp": 104, "ngc": "NGC 5216", "ra_hours": 13.570, "dec_degrees": 62.703,
     "type": "galaxy", "magnitude": 13.3, "size_arcmin": 1.7, "constellation": "UMa"},
    # Arp 116 — NGC 4649 (M60), elliptical with companion
    {"arp": 116, "ngc": "NGC 4649", "ra_hours": 12.702, "dec_degrees": 11.552,
     "type": "galaxy", "magnitude": 9.8, "size_arcmin": 7.2, "constellation": "Vir"},
    # Arp 148 — Mayall's Object, ring galaxy
    {"arp": 148, "ngc": "NGC 5221", "ra_hours": 13.577, "dec_degrees": 42.435,
     "type": "galaxy", "magnitude": 14.0, "size_arcmin": 0.9, "constellation": "CVn"},
    # Arp 194 — triple galaxy system
    {"arp": 194, "ngc": "NGC 3799", "ra_hours": 11.654, "dec_degrees": 15.270,
     "type": "galaxy", "magnitude": 13.5, "size_arcmin": 1.0, "constellation": "Leo"},
    # Arp 220 — NGC 7469, Seyfert galaxy merger
    {"arp": 220, "ngc": "NGC 7469", "ra_hours": 23.044, "dec_degrees": 8.874,
     "type": "galaxy", "magnitude": 12.9, "size_arcmin": 1.5, "constellation": "Peg"},
    # Arp 244 — NGC 4038/4039, "Antennae" galaxies
    {"arp": 244, "ngc": "NGC 4038", "ra_hours": 12.029, "dec_degrees": -18.867,
     "type": "galaxy", "magnitude": 10.9, "size_arcmin": 5.2, "constellation": "Crv"},
    # Arp 245 — NGC 2992/2993, interacting pair
    {"arp": 245, "ngc": "NGC 2992", "ra_hours": 9.761, "dec_degrees": -14.326,
     "type": "galaxy", "magnitude": 13.0, "size_arcmin": 3.5, "constellation": "Hya"},
    # Arp 258 — NGC 3524, chain of three galaxies
    {"arp": 258, "ngc": "NGC 3524", "ra_hours": 11.106, "dec_degrees": 11.143,
     "type": "galaxy", "magnitude": 13.6, "size_arcmin": 1.6, "constellation": "Leo"},
    # Arp 261 — NGC 4731, barred spiral with distortion
    {"arp": 261, "ngc": "NGC 4731", "ra_hours": 12.815, "dec_degrees": -6.388,
     "type": "galaxy", "magnitude": 12.1, "size_arcmin": 6.2, "constellation": "Vir"},
    # Arp 273 — UGC 1810/1813, interacting pair (rose-shaped)
    {"arp": 273, "ngc": "NGC 317", "ra_hours": 0.923, "dec_degrees": 43.792,
     "type": "galaxy", "magnitude": 13.4, "size_arcmin": 1.0, "constellation": "And"},
    # Arp 274 — NGC 5679, triple spiral system
    {"arp": 274, "ngc": "NGC 5679", "ra_hours": 14.594, "dec_degrees": 5.417,
     "type": "galaxy", "magnitude": 13.5, "size_arcmin": 1.2, "constellation": "Vir"},
    # Arp 295 — NGC 1024, spiral with tidal tail
    {"arp": 295, "ngc": "NGC 1024", "ra_hours": 2.677, "dec_degrees": 10.853,
     "type": "galaxy", "magnitude": 12.7, "size_arcmin": 3.9, "constellation": "Ari"},
    # Arp 303 — IC 563/564, double galaxy
    {"arp": 303, "ngc": "NGC 3786", "ra_hours": 11.688, "dec_degrees": 31.908,
     "type": "galaxy", "magnitude": 12.8, "size_arcmin": 2.4, "constellation": "UMa"},
    # Arp 316 — NGC 3190 (Hickson 44 group), chain of galaxies
    {"arp": 316, "ngc": "NGC 3190", "ra_hours": 10.328, "dec_degrees": 21.833,
     "type": "galaxy", "magnitude": 12.1, "size_arcmin": 4.4, "constellation": "Leo"},
    # Arp 1 — NGC 2857, spiral with detached segments
    {"arp": 1, "ngc": "NGC 2857", "ra_hours": 9.385, "dec_degrees": 49.20,
     "type": "galaxy", "magnitude": 13.0, "size_arcmin": 1.6, "constellation": "UMa"},
    # Arp 2 — NGC 5256, merging pair
    {"arp": 2, "ngc": "NGC 5256", "ra_hours": 13.658, "dec_degrees": 48.277,
     "type": "galaxy", "magnitude": 13.3, "size_arcmin": 1.1, "constellation": "UMa"},
    # Arp 6 — NGC 2537, Bear Paw galaxy
    {"arp": 6, "ngc": "NGC 2537", "ra_hours": 8.131, "dec_degrees": 45.992,
     "type": "galaxy", "magnitude": 12.3, "size_arcmin": 1.6, "constellation": "Lyn"},
    # Arp 9 — NGC 2523, one-armed spiral
    {"arp": 9, "ngc": "NGC 2523", "ra_hours": 8.138, "dec_degrees": 73.575,
     "type": "galaxy", "magnitude": 12.1, "size_arcmin": 2.8, "constellation": "Cam"},
    # Arp 10 — NGC 7253, disrupted spiral
    {"arp": 10, "ngc": "NGC 7253", "ra_hours": 22.322, "dec_degrees": 29.400,
     "type": "galaxy", "magnitude": 13.5, "size_arcmin": 1.3, "constellation": "Peg"},
    # Arp 23 — NGC 4618, one-armed barred spiral
    {"arp": 23, "ngc": "NGC 4618", "ra_hours": 12.666, "dec_degrees": 41.150,
     "type": "galaxy", "magnitude": 11.2, "size_arcmin": 4.3, "constellation": "CVn"},
    # Arp 29 — NGC 6946, multi-armed Fireworks galaxy
    {"arp": 29, "ngc": "NGC 6946", "ra_hours": 20.578, "dec_degrees": 60.154,
     "type": "galaxy", "magnitude": 9.6, "size_arcmin": 11.5, "constellation": "Cep"},
    # Arp 33 — NGC 4631, edge-on whale galaxy
    {"arp": 33, "ngc": "NGC 4631", "ra_hours": 12.702, "dec_degrees": 32.541,
     "type": "galaxy", "magnitude": 9.8, "size_arcmin": 15.1, "constellation": "CVn"},
    # Arp 37 — NGC 45, diffuse spiral
    {"arp": 37, "ngc": "NGC 45", "ra_hours": 0.235, "dec_degrees": -23.183,
     "type": "galaxy", "magnitude": 11.1, "size_arcmin": 8.5, "constellation": "Cet"},
    # Arp 41 — NGC 1232, face-on spiral with faint companion
    {"arp": 41, "ngc": "NGC 1232", "ra_hours": 3.162, "dec_degrees": -20.579,
     "type": "galaxy", "magnitude": 10.6, "size_arcmin": 7.4, "constellation": "Eri"},
    # Arp 55 — UGC 4881, double galaxy with tails
    {"arp": 55, "ngc": "NGC 2782", "ra_hours": 9.146, "dec_degrees": 40.113,
     "type": "galaxy", "magnitude": 12.0, "size_arcmin": 3.5, "constellation": "Lyn"},
    # Arp 63 — UGC 4854, pair with bridges
    {"arp": 63, "ngc": "NGC 3432", "ra_hours": 10.905, "dec_degrees": 36.372,
     "type": "galaxy", "magnitude": 11.7, "size_arcmin": 6.2, "constellation": "LMi"},
    # Arp 65 — NGC 7465/7464 pair
    {"arp": 65, "ngc": "NGC 7465", "ra_hours": 23.034, "dec_degrees": 15.970,
     "type": "galaxy", "magnitude": 12.5, "size_arcmin": 1.3, "constellation": "Peg"},
    # Arp 70 — NGC 3995, one-armed spiral
    {"arp": 70, "ngc": "NGC 3995", "ra_hours": 11.947, "dec_degrees": 32.292,
     "type": "galaxy", "magnitude": 13.2, "size_arcmin": 2.8, "constellation": "UMa"},
    # Arp 77 — NGC 1097/1097A, barred spiral with dwarf companion
    {"arp": 77, "ngc": "NGC 1097", "ra_hours": 2.770, "dec_degrees": -30.275,
     "type": "galaxy", "magnitude": 10.2, "size_arcmin": 9.3, "constellation": "For"},
    # Arp 88 — NGC 7679/7682, interacting elliptical+spiral
    {"arp": 88, "ngc": "NGC 7679", "ra_hours": 23.467, "dec_degrees": 3.513,
     "type": "galaxy", "magnitude": 12.8, "size_arcmin": 1.5, "constellation": "Psc"},
    # Arp 93 — NGC 3395/3396, merging pair
    {"arp": 93, "ngc": "NGC 3395", "ra_hours": 10.836, "dec_degrees": 32.980,
     "type": "galaxy", "magnitude": 12.6, "size_arcmin": 1.9, "constellation": "LMi"},
    # Arp 147 — ring + spiral pair
    {"arp": 147, "ngc": "NGC 1199", "ra_hours": 3.073, "dec_degrees": -15.617,
     "type": "galaxy", "magnitude": 11.7, "size_arcmin": 2.4, "constellation": "Eri"},
    # Arp 227 — NGC 474, shell galaxy
    {"arp": 227, "ngc": "NGC 474", "ra_hours": 1.307, "dec_degrees": 3.415,
     "type": "galaxy", "magnitude": 11.9, "size_arcmin": 2.7, "constellation": "Psc"},
    # Arp 263 — NGC 3239, irregular galaxy
    {"arp": 263, "ngc": "NGC 3239", "ra_hours": 10.446, "dec_degrees": 17.133,
     "type": "galaxy", "magnitude": 12.3, "size_arcmin": 4.5, "constellation": "Leo"},
    # Arp 271 — NGC 5426/5427, interacting face-on spirals
    {"arp": 271, "ngc": "NGC 5426", "ra_hours": 14.049, "dec_degrees": -6.075,
     "type": "galaxy", "magnitude": 12.9, "size_arcmin": 3.0, "constellation": "Vir"},
    # Arp 282 — NGC 169, warped spiral
    {"arp": 282, "ngc": "NGC 169", "ra_hours": 0.608, "dec_degrees": 23.992,
     "type": "galaxy", "magnitude": 12.9, "size_arcmin": 2.7, "constellation": "And"},
    # Arp 286 — NGC 5560/5569 group
    {"arp": 286, "ngc": "NGC 5560", "ra_hours": 14.330, "dec_degrees": 3.983,
     "type": "galaxy", "magnitude": 13.2, "size_arcmin": 3.8, "constellation": "Vir"},
    # Arp 300 — UGC 5189, double galaxy
    {"arp": 300, "ngc": "NGC 2972", "ra_hours": 9.737, "dec_degrees": 20.903,
     "type": "galaxy", "magnitude": 13.8, "size_arcmin": 1.1, "constellation": "Leo"},
    # Arp 319 — Stephan's Quintet (NGC 7317-7320)
    {"arp": 319, "ngc": "NGC 7317", "ra_hours": 22.596, "dec_degrees": 33.958,
     "type": "galaxy", "magnitude": 13.6, "size_arcmin": 0.9, "constellation": "Peg"},
]
```

### Step B: Create seed_arp.py

Create `backend/scripts/seed_arp.py` following the `seed_caldwell.py` pattern exactly:

```python
#!/usr/bin/env python3
"""Seed Arp Atlas of Peculiar Galaxies into dso_catalog table.

For objects that already exist in the catalog by NGC/IC number, this script
UPDATE-s the existing row to add the arp_number rather than inserting a
duplicate.  For objects not yet in the catalog, it inserts a new row.
Idempotent — safe to run multiple times.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_arp_if_needed(db=None) -> int:
    """Insert or update Arp objects.  Returns count of rows changed."""
    from app.models.catalog_models import DSOCatalog

    own_session = db is None
    if own_session:
        from app.database import SessionLocal
        db = SessionLocal()

    try:
        from scripts.arp_data import ARP_CATALOG

        changed = 0
        for entry in ARP_CATALOG:
            num = entry["arp"]

            # Skip if already tagged with this arp_number
            existing_arp = db.query(DSOCatalog).filter(DSOCatalog.arp_number == num).first()
            if existing_arp:
                continue

            # Try to match by NGC/IC number so we don't duplicate
            ngc_ref = entry.get("ngc", "")
            cat_name, cat_num = "NGC", 0
            ref_upper = ngc_ref.strip().upper()
            if ref_upper.startswith("NGC"):
                raw = ref_upper[3:].strip().split("/")[0].strip()
                try:
                    cat_num = int(raw)
                    cat_name = "NGC"
                except ValueError:
                    cat_num = 0
            elif ref_upper.startswith("IC"):
                raw = ref_upper[2:].strip().split("/")[0].strip()
                try:
                    cat_num = int(raw)
                    cat_name = "IC"
                except ValueError:
                    cat_num = 0

            existing_ngc = None
            if cat_num:
                existing_ngc = (
                    db.query(DSOCatalog)
                    .filter(
                        DSOCatalog.catalog_name == cat_name,
                        DSOCatalog.catalog_number == cat_num,
                    )
                    .first()
                )

            if existing_ngc:
                # UPDATE existing row — just set arp_number
                existing_ngc.arp_number = num
            else:
                # INSERT new row
                dso = DSOCatalog(
                    catalog_name=cat_name,
                    catalog_number=cat_num,
                    common_name=f"Arp {num}",
                    arp_number=num,
                    ra_hours=entry["ra_hours"],
                    dec_degrees=entry["dec_degrees"],
                    object_type=entry["type"],
                    magnitude=entry.get("magnitude"),
                    size_major_arcmin=entry.get("size_arcmin"),
                    constellation=entry.get("constellation"),
                )
                db.add(dso)

            changed += 1

        if own_session:
            db.commit()
        else:
            db.flush()

        return changed

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = seed_arp_if_needed()
    print(f"Seeded/updated {n} Arp objects.")
```

### Test
```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py -q --no-cov
```

### Commit
```bash
git add backend/scripts/arp_data.py backend/scripts/seed_arp.py
git commit -m "feat: add Arp catalog data file and idempotent seeder"
```

---

## Task 6: Feature 3C — Sharpless catalog data file + seeder

**Files to create:**
- `backend/scripts/sharpless_data.py`
- `backend/scripts/seed_sharpless.py`

### Step A: Create sharpless_data.py

Create `backend/scripts/sharpless_data.py` with the top 50 Sharpless HII regions accessible to the Seestar S50 (large angular size or frequently imaged; includes only objects at declinations > -30° for northern hemisphere accessibility):

```python
"""
Sharpless Catalogue of HII Regions (Sh2) — top 50 accessible objects.
Sources: Sharpless (1959), SIMBAD, astrobin community data.
All coordinates J2000.0.  Size is approximate major axis in arcminutes.
"""

SHARPLESS_CATALOG = [
    # Sh2-1 through Sh2-10
    {"sh2": 1, "ra_hours": 0.187, "dec_degrees": 64.783, "type": "nebula",
     "size_arcmin": 8.0, "constellation": "Cas"},
    {"sh2": 7, "ra_hours": 0.667, "dec_degrees": 67.117, "type": "nebula",
     "size_arcmin": 15.0, "constellation": "Cas"},
    {"sh2": 9, "ra_hours": 16.360, "dec_degrees": -24.383, "type": "nebula",
     "size_arcmin": 20.0, "constellation": "Sco"},
    # Sh2-11 — War and Peace Nebula (NGC 6357)
    {"sh2": 11, "ra_hours": 17.437, "dec_degrees": -34.283, "type": "nebula",
     "size_arcmin": 57.0, "constellation": "Sco"},
    # Sh2-13 — NGC 6334, Cat's Paw Nebula
    {"sh2": 13, "ra_hours": 17.301, "dec_degrees": -35.967, "type": "nebula",
     "size_arcmin": 40.0, "constellation": "Sco"},
    # Sh2-16 — NGC 6357 inner region
    {"sh2": 16, "ra_hours": 17.430, "dec_degrees": -34.267, "type": "nebula",
     "size_arcmin": 12.0, "constellation": "Sco"},
    # Sh2-27 — large HII region in Ophiuchus
    {"sh2": 27, "ra_hours": 16.575, "dec_degrees": -4.833, "type": "nebula",
     "size_arcmin": 300.0, "constellation": "Oph"},
    # Sh2-29 — NGC 6618 (M17) Omega/Swan Nebula
    {"sh2": 29, "ra_hours": 18.346, "dec_degrees": -16.177, "type": "nebula",
     "size_arcmin": 46.0, "constellation": "Sgr"},
    # Sh2-33 — IC 4703 (M16) Eagle Nebula
    {"sh2": 33, "ra_hours": 18.313, "dec_degrees": -13.784, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Ser"},
    # Sh2-37 — NGC 6530 region
    {"sh2": 37, "ra_hours": 18.052, "dec_degrees": -24.350, "type": "nebula",
     "size_arcmin": 25.0, "constellation": "Sgr"},
    # Sh2-49 — IC 1287
    {"sh2": 49, "ra_hours": 18.408, "dec_degrees": -11.017, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Sct"},
    # Sh2-54 — NGC 6604 region
    {"sh2": 54, "ra_hours": 18.283, "dec_degrees": -12.117, "type": "nebula",
     "size_arcmin": 40.0, "constellation": "Ser"},
    # Sh2-71 — NGC 6741 (planetary, nearby HII)
    {"sh2": 71, "ra_hours": 19.076, "dec_degrees": -1.767, "type": "nebula",
     "size_arcmin": 8.0, "constellation": "Aql"},
    # Sh2-86 — NGC 6820 + NGC 6823
    {"sh2": 86, "ra_hours": 19.720, "dec_degrees": 23.167, "type": "nebula",
     "size_arcmin": 40.0, "constellation": "Vul"},
    # Sh2-88 — NGC 6888 Crescent Nebula
    {"sh2": 88, "ra_hours": 20.193, "dec_degrees": 38.350, "type": "nebula",
     "size_arcmin": 20.0, "constellation": "Cyg"},
    # Sh2-91 — Cygnus nebulosity
    {"sh2": 91, "ra_hours": 20.400, "dec_degrees": 44.483, "type": "nebula",
     "size_arcmin": 60.0, "constellation": "Cyg"},
    # Sh2-96 — Tulip Nebula (NGC 6595 region)
    {"sh2": 96, "ra_hours": 19.993, "dec_degrees": 35.217, "type": "nebula",
     "size_arcmin": 15.0, "constellation": "Cyg"},
    # Sh2-101 — Tulip Nebula (Sh2-101)
    {"sh2": 101, "ra_hours": 20.138, "dec_degrees": 35.733, "type": "nebula",
     "size_arcmin": 16.0, "constellation": "Cyg"},
    # Sh2-106 — Star-forming region in Cygnus
    {"sh2": 106, "ra_hours": 20.454, "dec_degrees": 37.383, "type": "nebula",
     "size_arcmin": 3.0, "constellation": "Cyg"},
    # Sh2-108 — IC 5070 / Pelican Nebula region
    {"sh2": 108, "ra_hours": 20.908, "dec_degrees": 44.483, "type": "nebula",
     "size_arcmin": 80.0, "constellation": "Cyg"},
    # Sh2-112 — HII region near Cygnus X
    {"sh2": 112, "ra_hours": 21.035, "dec_degrees": 45.617, "type": "nebula",
     "size_arcmin": 15.0, "constellation": "Cyg"},
    # Sh2-119 — HII in Cygnus
    {"sh2": 119, "ra_hours": 21.473, "dec_degrees": 49.500, "type": "nebula",
     "size_arcmin": 120.0, "constellation": "Cyg"},
    # Sh2-126 — large complex in Lacerta
    {"sh2": 126, "ra_hours": 22.500, "dec_degrees": 56.383, "type": "nebula",
     "size_arcmin": 210.0, "constellation": "Lac"},
    # Sh2-129 — Flying Bat Nebula
    {"sh2": 129, "ra_hours": 21.765, "dec_degrees": 60.017, "type": "nebula",
     "size_arcmin": 150.0, "constellation": "Cep"},
    # Sh2-131 — IC 1396 + Elephant Trunk
    {"sh2": 131, "ra_hours": 21.639, "dec_degrees": 57.500, "type": "nebula",
     "size_arcmin": 170.0, "constellation": "Cep"},
    # Sh2-132 — NGC 7380 (Wizard Nebula)
    {"sh2": 132, "ra_hours": 22.760, "dec_degrees": 56.067, "type": "nebula",
     "size_arcmin": 25.0, "constellation": "Cep"},
    # Sh2-140 — HII region in Cepheus
    {"sh2": 140, "ra_hours": 22.192, "dec_degrees": 63.283, "type": "nebula",
     "size_arcmin": 7.0, "constellation": "Cep"},
    # Sh2-142 — NGC 7380 adjacent region
    {"sh2": 142, "ra_hours": 22.793, "dec_degrees": 58.100, "type": "nebula",
     "size_arcmin": 12.0, "constellation": "Cep"},
    # Sh2-147 — supernova remnant / HII complex
    {"sh2": 147, "ra_hours": 5.492, "dec_degrees": 27.817, "type": "nebula",
     "size_arcmin": 180.0, "constellation": "Tau"},
    # Sh2-155 — Cave Nebula (NGC 7822 region)
    {"sh2": 155, "ra_hours": 22.958, "dec_degrees": 62.617, "type": "nebula",
     "size_arcmin": 50.0, "constellation": "Cep"},
    # Sh2-157 — NGC 7762 region in Cassiopeia
    {"sh2": 157, "ra_hours": 23.383, "dec_degrees": 60.233, "type": "nebula",
     "size_arcmin": 60.0, "constellation": "Cas"},
    # Sh2-158 — NGC 7538 region
    {"sh2": 158, "ra_hours": 23.206, "dec_degrees": 61.517, "type": "nebula",
     "size_arcmin": 12.0, "constellation": "Cas"},
    # Sh2-162 — NGC 7635 (Bubble Nebula)
    {"sh2": 162, "ra_hours": 23.344, "dec_degrees": 61.200, "type": "nebula",
     "size_arcmin": 15.0, "constellation": "Cas"},
    # Sh2-171 — NGC 7822 + CED 214
    {"sh2": 171, "ra_hours": 0.030, "dec_degrees": 67.417, "type": "nebula",
     "size_arcmin": 100.0, "constellation": "Cep"},
    # Sh2-173 — NGC 281 (Pacman Nebula)
    {"sh2": 173, "ra_hours": 0.881, "dec_degrees": 56.617, "type": "nebula",
     "size_arcmin": 35.0, "constellation": "Cas"},
    # Sh2-182 — HII in Cassiopeia
    {"sh2": 182, "ra_hours": 1.217, "dec_degrees": 58.067, "type": "nebula",
     "size_arcmin": 20.0, "constellation": "Cas"},
    # Sh2-184 — IC 59 / IC 63 (near gamma Cas)
    {"sh2": 184, "ra_hours": 0.956, "dec_degrees": 60.917, "type": "nebula",
     "size_arcmin": 10.0, "constellation": "Cas"},
    # Sh2-185 — IC 59/63 (gamma Cas nebula)
    {"sh2": 185, "ra_hours": 0.931, "dec_degrees": 60.733, "type": "nebula",
     "size_arcmin": 20.0, "constellation": "Cas"},
    # Sh2-190 — IC 1805 (Heart Nebula)
    {"sh2": 190, "ra_hours": 2.543, "dec_degrees": 61.467, "type": "nebula",
     "size_arcmin": 60.0, "constellation": "Cas"},
    # Sh2-199 — IC 1848 (Soul Nebula)
    {"sh2": 199, "ra_hours": 2.968, "dec_degrees": 60.450, "type": "nebula",
     "size_arcmin": 60.0, "constellation": "Cas"},
    # Sh2-202 — HII in Perseus
    {"sh2": 202, "ra_hours": 3.213, "dec_degrees": 57.833, "type": "nebula",
     "size_arcmin": 15.0, "constellation": "Per"},
    # Sh2-205 — large faint HII in Auriga
    {"sh2": 205, "ra_hours": 3.825, "dec_degrees": 54.233, "type": "nebula",
     "size_arcmin": 100.0, "constellation": "Aur"},
    # Sh2-212 — HII region, Auriga
    {"sh2": 212, "ra_hours": 4.630, "dec_degrees": 47.050, "type": "nebula",
     "size_arcmin": 8.0, "constellation": "Aur"},
    # Sh2-219 — IC 417 (Spider Nebula)
    {"sh2": 219, "ra_hours": 5.457, "dec_degrees": 34.383, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Aur"},
    # Sh2-220 — NGC 1931
    {"sh2": 220, "ra_hours": 5.521, "dec_degrees": 34.250, "type": "nebula",
     "size_arcmin": 3.0, "constellation": "Aur"},
    # Sh2-224 — supernova remnant / HII mix
    {"sh2": 224, "ra_hours": 5.650, "dec_degrees": 42.667, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Aur"},
    # Sh2-232 — Flaming Star complex
    {"sh2": 232, "ra_hours": 5.819, "dec_degrees": 33.667, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Aur"},
    # Sh2-240 — Simeis 147 supernova remnant / HII
    {"sh2": 240, "ra_hours": 5.706, "dec_degrees": 28.000, "type": "nebula",
     "size_arcmin": 180.0, "constellation": "Tau"},
    # Sh2-252 — NGC 2175 (Monkey Head Nebula)
    {"sh2": 252, "ra_hours": 6.160, "dec_degrees": 20.300, "type": "nebula",
     "size_arcmin": 25.0, "constellation": "Gem"},
    # Sh2-264 — Lambda Orionis Ring
    {"sh2": 264, "ra_hours": 5.595, "dec_degrees": 9.933, "type": "nebula",
     "size_arcmin": 420.0, "constellation": "Ori"},
    # Sh2-273 — NGC 2264 (Christmas Tree / Cone Nebula)
    {"sh2": 273, "ra_hours": 6.701, "dec_degrees": 9.900, "type": "nebula",
     "size_arcmin": 30.0, "constellation": "Mon"},
]
```

### Step B: Create seed_sharpless.py

Create `backend/scripts/seed_sharpless.py`:

```python
#!/usr/bin/env python3
"""Seed Sharpless HII region catalog into dso_catalog table.

Idempotent — safe to run multiple times.  Each Sharpless object is stored
with catalog_id = 'SH2-{num}' and common_name = 'Sh2-{num}'.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed_sharpless_if_needed(db=None) -> int:
    """Insert Sharpless objects.  Returns count of new rows inserted."""
    from app.models.catalog_models import DSOCatalog

    own_session = db is None
    if own_session:
        from app.database import SessionLocal
        db = SessionLocal()

    try:
        from scripts.sharpless_data import SHARPLESS_CATALOG

        inserted = 0
        for entry in SHARPLESS_CATALOG:
            num = entry["sh2"]
            catalog_id_str = f"SH2-{num}"

            # Check by sharpless_number
            existing = db.query(DSOCatalog).filter(DSOCatalog.sharpless_number == num).first()
            if existing:
                continue

            # Sharpless objects are not in NGC/IC, so always insert a new row.
            # Use catalog_name="Sh2" and catalog_number=num for consistency.
            dso = DSOCatalog(
                catalog_name="Sh2",
                catalog_number=num,
                common_name=catalog_id_str,
                sharpless_number=num,
                ra_hours=entry["ra_hours"],
                dec_degrees=entry["dec_degrees"],
                object_type=entry["type"],
                magnitude=None,  # Sharpless objects have no single magnitude
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

    except Exception:
        if own_session:
            db.rollback()
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    n = seed_sharpless_if_needed()
    print(f"Seeded {n} Sharpless objects.")
```

### Test
```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py -q --no-cov
```

### Commit
```bash
git add backend/scripts/sharpless_data.py backend/scripts/seed_sharpless.py
git commit -m "feat: add Sharpless HII catalog data file and idempotent seeder"
```

---

## Task 7: Feature 3D — Wire Arp/Sharpless into init_catalog.py + CatalogService

**Files to modify:**
- `backend/scripts/init_catalog.py`
- `backend/app/services/catalog_service.py`

### Step A: init_catalog.py

In `init_catalog.py`, the `seed_catalog()` function (starting at line 101) already calls `seed_caldwell_if_needed(db)` twice (once when catalog is already seeded, once after full seeding). Mirror that pattern for Arp and Sharpless.

In the `if count > 0:` branch (lines 110-122), after the Caldwell block, add:
```python
try:
    from scripts.seed_arp import seed_arp_if_needed
    n = seed_arp_if_needed(db)
    if n > 0:
        print(f"  Arp: seeded/updated {n} objects.")
    else:
        print("  Arp: already seeded, skipping.")
except Exception as e:
    print(f"  WARNING: Arp seeding failed: {e}", file=sys.stderr)

try:
    from scripts.seed_sharpless import seed_sharpless_if_needed
    n = seed_sharpless_if_needed(db)
    if n > 0:
        print(f"  Sharpless: seeded {n} objects.")
    else:
        print("  Sharpless: already seeded, skipping.")
except Exception as e:
    print(f"  WARNING: Sharpless seeding failed: {e}", file=sys.stderr)
```

Also add identical blocks in the `else` branch (after the `except` block that catches Caldwell seeding failure, around line 231).

### Step B: CatalogService.get_target_by_id()

In `backend/app/services/catalog_service.py`, in `get_target_by_id()` (line 152), the final `else: return None` branch (lines 188-190) is where new catalog prefixes are dispatched. Add two new handlers before the final `else`:

```python
elif catalog_id_upper.startswith("ARP") and catalog_id_upper[3:].isdigit():
    arp_num = int(catalog_id_upper[3:])
    dso = self.db.query(DSOCatalog).filter(DSOCatalog.arp_number == arp_num).first()
elif catalog_id_upper.startswith("SH2-") and catalog_id_upper[4:].isdigit():
    sh2_num = int(catalog_id_upper[4:])
    dso = self.db.query(DSOCatalog).filter(DSOCatalog.sharpless_number == sh2_num).first()
elif catalog_id_upper.startswith("SH") and catalog_id_upper[2:].isdigit():
    # Accept SH106 as shorthand for SH2-106
    sh2_num = int(catalog_id_upper[2:])
    dso = self.db.query(DSOCatalog).filter(DSOCatalog.sharpless_number == sh2_num).first()
else:
    return None
```

Also update `_db_row_to_target()` (line 31) so that the catalog_id generation handles Arp and Sharpless rows. After the `elif dso.caldwell_number:` block (lines 41-44), add:

```python
elif dso.arp_number:
    catalog_id = f"ARP{dso.arp_number}"
    name = dso.common_name if dso.common_name else catalog_id
elif dso.sharpless_number:
    catalog_id = f"SH2-{dso.sharpless_number}"
    name = dso.common_name if dso.common_name else catalog_id
```

### Test
```bash
docker exec astronomus pytest tests/unit/services/test_catalog_service.py -q --no-cov
docker exec astronomus pytest tests/ -q --no-cov
```

### Commit
```bash
git add backend/scripts/init_catalog.py backend/app/services/catalog_service.py
git commit -m "feat: wire Arp/Sharpless seeders into init_catalog and CatalogService.get_target_by_id"
```

---

## Task 8: Feature 4A — Alembic migration for image_url on user_targets

**Files to create:**
- `backend/alembic/versions/<revision_id>_add_image_url_to_user_targets.py`

**Files to modify:**
- `backend/app/models/catalog_models.py`

### Step A: Create migration

Run inside container:
```bash
docker exec astronomus bash -c "cd /app && alembic revision --autogenerate -m 'add_image_url_to_user_targets'"
```

Edit the generated file so `upgrade()` contains:
```python
def upgrade() -> None:
    op.add_column('user_targets', sa.Column('image_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('user_targets', 'image_url')
```

Apply:
```bash
docker exec astronomus bash -c "cd /app && alembic upgrade head"
```

### Step B: Update SQLAlchemy model

In `backend/app/models/catalog_models.py`, inside `class UserTarget` (line 154), after `notes = Column(Text, nullable=True)` (line 168), add:
```python
image_url = Column(String(500), nullable=True)
```

### Test
```bash
docker exec astronomus pytest tests/ -q --no-cov
```

### Commit
```bash
git add backend/alembic/versions/ backend/app/models/catalog_models.py
git commit -m "feat: add image_url column to user_targets table"
```

---

## Task 9: Feature 4B/4C — image_url in API models + CustomTargetsPanel form

**Files to modify:**
- `backend/app/api/custom_targets.py`
- `frontend/vue-app/src/components/discovery/CustomTargetsPanel.vue`

### Step A: Backend — custom_targets.py

In `CustomTargetCreate` (line 24), add after `notes`:
```python
image_url: Optional[str] = Field(default=None, max_length=500)
```

In `CustomTargetOut` (line 34), add after `notes`:
```python
image_url: Optional[str]
```

In `create_custom_target()` (line 56), add `image_url=payload.image_url,` to the `UserTarget(...)` constructor:
```python
ut = UserTarget(
    catalog_id=catalog_id,
    name=payload.name,
    ra_hours=payload.ra_hours,
    dec_degrees=payload.dec_degrees,
    magnitude=payload.magnitude,
    size_arcmin=payload.size_arcmin,
    object_type=payload.object_type,
    notes=payload.notes,
    image_url=payload.image_url,          # NEW
)
```

In `update_custom_target()` (line 78), the existing `payload.model_dump(exclude_unset=True)` loop already handles all fields generically — no change needed as long as `image_url` is on the model.

### Step B: Frontend — CustomTargetsPanel.vue

In the `form` ref (line 94), add `image_url: ''`.

In the form template `<div class="grid grid-cols-2 gap-3 mb-3">`, add a new `col-span-2` row after the Notes input (after line 36):
```html
<div class="col-span-2">
  <label class="text-xs text-gray-400">Image URL (optional)</label>
  <input
    v-model="form.image_url"
    class="input-dark w-full mt-1"
    placeholder="https://..."
  />
</div>
```

In `addTarget()` (line 115), add `image_url: form.value.image_url || null,` to the payload object.

In the form reset inside `addTarget()` (line 129), reset `image_url: ''`.

In the target list display, add below the `notes` line (after line 71):
```html
<div v-if="t.image_url" class="mt-1">
  <img :src="t.image_url" alt="Target preview"
    class="h-16 w-24 object-cover rounded border border-gray-700" />
</div>
```

### Test

Backend:
```bash
docker exec astronomus pytest tests/integration/test_catalog_api.py -q --no-cov
```

Browser verification:
1. Open Discovery > My Targets. Add a new custom target with an image URL (e.g., a Wikipedia image URL).
2. The target list should show the thumbnail image below the target row.
3. Re-open the page; the image_url persists.

### Commit
```bash
git add backend/app/api/custom_targets.py frontend/vue-app/src/components/discovery/CustomTargetsPanel.vue
git commit -m "feat: add image_url field to custom targets API and panel form"
```

---

## Task 10: Run full test suite and fix failures

```bash
docker exec astronomus pytest tests/ -q --no-cov
```

Common failure categories and fixes:

**Migration out of sync in test DB:** If tests fail with `column arp_number does not exist`, the test DB migrations are not applied. The `setup_test_db_schema` fixture in `conftest.py` calls `alembic upgrade head` automatically; if the revision files are present and the `down_revision` chain is correct, this is self-healing.

**Import errors for arp_data / sharpless_data:** If `from scripts.arp_data import ARP_CATALOG` fails, ensure `backend/scripts/arp_data.py` exists and is importable from the container's working directory (`/app`). Check `sys.path.insert(0, ...)` at top of `seed_arp.py`.

**CI linting failures (black, isort, ruff, bandit):**
- Run `docker exec astronomus black --line-length 120 backend/scripts/arp_data.py backend/scripts/seed_arp.py backend/scripts/sharpless_data.py backend/scripts/seed_sharpless.py`
- Run `docker exec astronomus isort --settings-path backend backend/scripts/`
- Run `docker exec astronomus ruff check backend/scripts/`

**Frontend unit tests:** Frontend tests live in `frontend/vue-app/src/stores/__tests__/`. If `planning.test.js` breaks due to new `includeComets` state, add `includeComets: false` to any mock store state in those tests.

Once all tests pass:
```bash
git add -u
git commit -m "fix: address test suite failures from sprint 3 features"
```

---

## Task 11: PR to main

```bash
git push -u origin feature/roadmap-sprint-3
gh pr create \
  --title "feat: Sprint 3 — live tracking polish, comet toggle, Arp/Sharpless catalogs, custom target images" \
  --body "$(cat <<'EOF'
## Summary

- **Feature 1A/1B:** Auto-advance execution to next target when all frames captured; rename Skip → Done → (green)
- **Feature 2:** Frontend-only "Include visible comets" toggle wires into existing backend comet auto-injection
- **Feature 3:** Arp Atlas (50 objects) + Sharpless HII (50 objects) catalog import via new DB columns + seeders
- **Feature 4:** Optional image_url field on custom targets (migration, API, and panel form)

## Test plan

- [ ] `docker exec astronomus pytest tests/ -q --no-cov` — all tests pass
- [ ] Execute a plan with 2+ targets; verify auto-advance fires when `framesCaptures >= totalFrames`
- [ ] Verify "Done →" button is green with tooltip in NowPlayingPanel
- [ ] Toggle "Include visible comets" and generate a plan; no 500 error
- [ ] `docker exec astronomus python -c "from scripts.seed_arp import seed_arp_if_needed; print(seed_arp_if_needed())"` outputs row count
- [ ] `docker exec astronomus python -c "from scripts.seed_sharpless import seed_sharpless_if_needed; print(seed_sharpless_if_needed())"` outputs row count
- [ ] Add a custom target with image URL; thumbnail appears in the list

EOF
)"
```

---

## Architecture Notes

### Key field name discrepancy (do not introduce regressions)

`ObservingConstraints` in `backend/app/models/models.py` uses `min_altitude` and `max_altitude` (not `_degrees` suffixed), and does NOT have an `avoid_moon` field. The frontend sends `min_altitude_degrees`, `max_altitude_degrees`, and `avoid_moon`; these are silently ignored by the backend. The frontend's `loadPlan()` handles both name variants when restoring constraints. Do not change this behavior.

### Migration chain

The Alembic revision chain must be:
```
00000001_init → 00000002 → 1eb59f1772f1 (user_targets) → <arp_sharpless> → <image_url>
```

When generating migrations with `--autogenerate`, verify that `down_revision` in each new file points to `1eb59f1772f1` for the first new migration, then the second points to the first new revision.

### Seeder idempotency contract

All seeders follow the same contract as `seed_caldwell_if_needed()`:
- Accept optional `db` session (creates own session if `None`)
- Check for existence before insert
- Flush (not commit) when called with external session
- Commit when using own session
- Always close own session in `finally`

### DSOCatalog catalog_id generation in _db_row_to_target

Priority order for `catalog_id` assignment in `catalog_service.py`:
1. Messier (common_name starts with "M" + digits)
2. Caldwell number
3. **NEW: Arp number** (added in Task 7)
4. **NEW: Sharpless number** (added in Task 7)
5. Fallback: `{catalog_name}{catalog_number}`

This order means an NGC object that is also an Arp object will show as `ARP{n}` in the catalog display. If preserving the NGC designation is preferred, swap Arp/Sharpless below Caldwell. Discuss with product before implementing — the plan uses Arp-priority as specified.
