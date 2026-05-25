# Interactive Timeline Drag-Editing Implementation Plan


**Goal:** Make the planning timeline and per-card mini-charts fully interactive — drag to reposition or resize target observation windows, with real-time conflict highlighting when windows overlap, have insufficient slew gaps, or fall outside a target's good-altitude range.

**Architecture:** Three-layer approach: (1) store action `setTargetWindow` mutates a single target's times without cascade; (2) `PlanTimeline.vue` gets drag handles (three transparent overlay rects per target: left-edge/interior/right-edge) plus a `conflictMap` computed that drives color overrides; (3) `TargetVisibilityMini.vue` gets draggable rect and dot handles, calling the same store action. Both components use document-level `mousemove`/`mouseup` listeners so drags survive cursor leaving the SVG element.

**Tech Stack:** Vue 3 Composition API (`ref`, `computed`, `watch`, `onMounted`, `onUnmounted`), Pinia, SVG mouse events, no additional libraries.

---

## Context You Must Know

### Coordinate systems

**PlanTimeline.vue** (`W=640`, `H=230`, `ML=32`, `MR=8`, `MT=10`, `MB=42`, `CW=600`, `CH=178`):
- `tx(isoStr)` → X pixel in viewBox (ML to ML+CW)
- `ay(alt)` → Y pixel in viewBox (inverted)
- Screen pixel delta → ms: `pxDelta * sessionDur * W / (CW * rect.width)` where `rect` = `svgRef.getBoundingClientRect()`

**TargetVisibilityMini.vue** (`W=300`, `H=52`):
- `tx(isoStr)` → X pixel 0..W (full viewBox = full session)
- Screen pixel delta → ms: `pxDelta * sessionDur / rect.width` (simpler — full width = full session)

### Current `_recalcTimes()` behavior
This action recalculates ALL targets sequentially from `imaging_start`. Do NOT call it from drag actions — it would cascade and shift other targets. The new `setTargetWindow` action is independent.

### altitude_points vs fullCurves
`altitude_points` from the scheduler span only the originally scheduled window. `fullCurves` is a `ref({})` in PlanTimeline keyed by `catalog_id`, populated from `/api/altitude-curve` — this is what conflict detection should use for altitude checks.

### interpAlt helper (used in TargetVisibilityMini — needs duplicating in PlanTimeline)
```javascript
function interpAlt(isoStr, pts) {
  if (!pts?.length || !isoStr) return null
  const tMs = new Date(isoStr).getTime()
  for (let i = 0; i < pts.length - 1; i++) {
    const t0 = new Date(pts[i][0]).getTime()
    const t1 = new Date(pts[i + 1][0]).getTime()
    if (tMs >= t0 && tMs <= t1) {
      const frac = (tMs - t0) / (t1 - t0)
      return pts[i][1] + frac * (pts[i + 1][1] - pts[i][1])
    }
  }
  return null
}
```

---

## Task 1: Store — `setTargetWindow` action

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js` (add to `actions` object, after `_recalcTimes`)

**Step 1: Add the action**

```javascript
setTargetWindow(index, startIso, endIso) {
  const ts = this.currentPlan?.scheduled_targets
  if (!ts?.[index]) return
  const startMs = new Date(startIso).getTime()
  const endMs   = new Date(endIso).getTime()
  ts[index].start_time      = startIso
  ts[index].end_time        = endIso
  ts[index].duration_minutes = Math.round((endMs - startMs) / 60000)
  // Update coverage percent
  const s = this.currentPlan.session
  if (s) {
    const totalDarkMs    = new Date(s.imaging_end).getTime() - new Date(s.imaging_start).getTime()
    const totalImagingMs = ts.reduce((sum, t) => sum + t.duration_minutes * 60000, 0)
    this.currentPlan.coverage_percent = Math.round((totalImagingMs / totalDarkMs) * 100)
  }
},
```

**Step 2: Verify manually**
Open browser devtools → Pinia devtools → trigger `setTargetWindow(0, '...', '...')` → confirm `start_time`, `end_time`, `duration_minutes`, and `coverage_percent` all update without shifting other targets.

**Step 3: Commit**
```bash
git add frontend/vue-app/src/stores/planning.js
git commit -m "feat: add setTargetWindow store action for independent target window editing"
```

---

## Task 2: PlanTimeline — drag handles + cursor rects

**Files:**
- Modify: `frontend/vue-app/src/components/planning/PlanTimeline.vue`

### Step 1: Update imports and add drag state refs

Replace the `<script setup>` import line and add after the existing `const emit`:

```javascript
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { usePlanningStore } from '@/stores/planning'

// (after existing defineProps/defineEmits)
const planningStore = usePlanningStore()
const svgRef = ref(null)
const dragState = ref(null)
// { index, mode: 'move'|'left'|'right', startClientX, origStartMs, origEndMs }

const EDGE_PX = 8   // viewBox pixels for left/right drag handle zones
const MIN_DUR_MS = 5 * 60 * 1000
```

### Step 2: Add `onWindowMousedown` handler

```javascript
function onWindowMousedown(e, i, mode) {
  e.preventDefault()
  emit('select-target', i)
  const t = targets.value[i]
  dragState.value = {
    index: i,
    mode,
    startClientX: e.clientX,
    origStartMs: new Date(t.start_time).getTime(),
    origEndMs:   new Date(t.end_time).getTime(),
  }
}
```

### Step 3: Add document-level mousemove/mouseup handlers

```javascript
function onDocMousemove(e) {
  if (!dragState.value) return
  const { index, mode, startClientX, origStartMs, origEndMs } = dragState.value

  const rect     = svgRef.value.getBoundingClientRect()
  const pxDelta  = e.clientX - startClientX
  // Convert screen pixel delta to milliseconds (chart area CW out of total viewBox width W)
  const msDelta  = pxDelta * sessionDur.value * W / (CW * rect.width)

  let ns = origStartMs
  let ne = origEndMs

  if (mode === 'move') {
    ns = origStartMs + msDelta
    ne = origEndMs   + msDelta
    // Clamp within session, preserving duration
    if (ns < sessionStart.value) { ne += sessionStart.value - ns; ns = sessionStart.value }
    if (ne > sessionEnd.value)   { ns -= ne - sessionEnd.value;   ne = sessionEnd.value   }
  } else if (mode === 'left') {
    ns = Math.max(sessionStart.value, Math.min(origStartMs + msDelta, origEndMs - MIN_DUR_MS))
  } else {
    ne = Math.min(sessionEnd.value,   Math.max(origEndMs   + msDelta, origStartMs + MIN_DUR_MS))
  }

  planningStore.setTargetWindow(index, new Date(ns).toISOString(), new Date(ne).toISOString())
}

function onDocMouseup() { dragState.value = null }

onMounted(() => {
  document.addEventListener('mousemove', onDocMousemove)
  document.addEventListener('mouseup',   onDocMouseup)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMousemove)
  document.removeEventListener('mouseup',   onDocMouseup)
})
```

### Step 4: Replace the window rect SVG layer (layer 4) with three-rect handle system

Find the existing `<!-- 4. Target window rects -->` group and replace it entirely:

```html
<!-- 4. Target window rects + drag handles -->
<g :clip-path="`url(#${clipId})`">
  <!-- Filled, score/conflict-colored window -->
  <rect
    v-for="(target, i) in targets" :key="'win' + (target.target?.catalog_id || i)"
    :x="tx(target.start_time)" :y="MT"
    :width="Math.max(2, tx(target.end_time) - tx(target.start_time))"
    :height="CH"
    :fill="windowColor(i) + '26'"
    :stroke="windowColor(i)"
    stroke-width="1.5"
    style="pointer-events: none"
  />

  <!-- Per-target drag handles: left edge / interior / right edge -->
  <template v-for="(target, i) in targets" :key="'drag' + i">
    <!-- Left resize handle -->
    <rect
      :x="tx(target.start_time)" :y="MT"
      :width="EDGE_PX" :height="CH"
      fill="transparent" style="cursor: ew-resize"
      @mousedown.stop="onWindowMousedown($event, i, 'left')"
    />
    <!-- Interior move handle -->
    <rect
      :x="tx(target.start_time) + EDGE_PX" :y="MT"
      :width="Math.max(0, tx(target.end_time) - tx(target.start_time) - 2 * EDGE_PX)"
      :height="CH"
      fill="transparent"
      :style="{ cursor: dragState?.index === i ? 'grabbing' : 'grab' }"
      @mousedown.stop="onWindowMousedown($event, i, 'move')"
    />
    <!-- Right resize handle -->
    <rect
      :x="tx(target.end_time) - EDGE_PX" :y="MT"
      :width="EDGE_PX" :height="CH"
      fill="transparent" style="cursor: ew-resize"
      @mousedown.stop="onWindowMousedown($event, i, 'right')"
    />
  </template>
</g>
```

Also add `ref="svgRef"` to the `<svg>` element:
```html
<svg ref="svgRef" :viewBox="`0 0 ${W} ${H}`" ...>
```

### Step 5: Verify drag works

Rebuild and `docker cp` dist, open browser. Click and drag a target window in the top chart — it should move. Drag the left/right 8px edge zones — window should resize. The card mini-charts should update reactively (since they read `target.start_time`/`target.end_time` from the same Pinia state).

### Step 6: Commit
```bash
git add frontend/vue-app/src/components/planning/PlanTimeline.vue
git commit -m "feat: add drag-to-move and drag-to-resize on PlanTimeline target windows"
```

---

## Task 3: PlanTimeline — conflict detection + color overrides

**Files:**
- Modify: `frontend/vue-app/src/components/planning/PlanTimeline.vue`

### Step 1: Add `interpAlt` helper (after `pointsToPath`)

```javascript
function interpAlt(isoStr, pts) {
  if (!pts?.length || !isoStr) return null
  const tMs = new Date(isoStr).getTime()
  for (let i = 0; i < pts.length - 1; i++) {
    const t0 = new Date(pts[i][0]).getTime()
    const t1 = new Date(pts[i + 1][0]).getTime()
    if (tMs >= t0 && tMs <= t1) {
      const frac = (tMs - t0) / (t1 - t0)
      return pts[i][1] + frac * (pts[i + 1][1] - pts[i][1])
    }
  }
  return null
}
```

### Step 2: Add `conflictMap` computed

```javascript
const SLEW_GAP_MS = 5 * 60 * 1000   // 5-minute minimum between consecutive targets

const conflictMap = computed(() => {
  const ts = targets.value
  const result = {}

  // 1. Low-altitude check — sample altitude at start, middle, end of each window
  for (let i = 0; i < ts.length; i++) {
    const curve = fullCurves.value[ts[i].target?.catalog_id] ?? ts[i].altitude_points
    if (!curve?.length) continue
    const sMs = new Date(ts[i].start_time).getTime()
    const eMs = new Date(ts[i].end_time).getTime()
    const checkPoints = [sMs, (sMs + eMs) / 2, eMs]
    for (const ms of checkPoints) {
      const alt = interpAlt(new Date(ms).toISOString(), curve)
      if (alt != null && alt < minAlt.value) {
        result[i] = 'lowalt'
        break
      }
    }
  }

  // 2. True overlap — any two windows that share time
  for (let i = 0; i < ts.length; i++) {
    for (let j = i + 1; j < ts.length; j++) {
      const sI = new Date(ts[i].start_time).getTime()
      const eI = new Date(ts[i].end_time).getTime()
      const sJ = new Date(ts[j].start_time).getTime()
      const eJ = new Date(ts[j].end_time).getTime()
      if (sI < eJ && eI > sJ) {
        result[i] = 'overlap'
        result[j] = 'overlap'
      }
    }
  }

  // 3. Slew gap — consecutive by time with gap < 5 min
  const sorted = ts
    .map((t, origIndex) => ({ origIndex, startMs: new Date(t.start_time).getTime(), endMs: new Date(t.end_time).getTime() }))
    .sort((a, b) => a.startMs - b.startMs)

  for (let i = 0; i < sorted.length - 1; i++) {
    const gap = sorted[i + 1].startMs - sorted[i].endMs
    if (gap >= 0 && gap < SLEW_GAP_MS) {
      if (result[sorted[i].origIndex] !== 'overlap')     result[sorted[i].origIndex]     = 'gap'
      if (result[sorted[i + 1].origIndex] !== 'overlap') result[sorted[i + 1].origIndex] = 'gap'
    }
  }

  return result
})
```

### Step 3: Add `windowColor` helper

```javascript
function windowColor(i) {
  const c = conflictMap.value[i]
  if (c === 'overlap') return '#ef4444'  // red
  if (c === 'gap')     return '#f97316'  // orange
  if (c === 'lowalt')  return '#eab308'  // yellow
  return scoreColor(targets.value[i].score?.total_score)
}
```

### Step 4: Verify conflict colors

Drag a target to overlap another — both should turn red. Drag two targets to within 5 minutes of each other — both should turn orange. Drag a target window to a time when the object is below 30° (the dashed line) — should turn yellow.

### Step 5: Commit
```bash
git add frontend/vue-app/src/components/planning/PlanTimeline.vue
git commit -m "feat: real-time conflict detection (overlap/gap/low-altitude) in PlanTimeline"
```

---

## Task 4: TargetVisibilityMini — draggable rect and dot handles

**Files:**
- Modify: `frontend/vue-app/src/components/planning/TargetVisibilityMini.vue`
- Modify: `frontend/vue-app/src/views/PlanningView.vue` (add `:index` prop)

### Step 1: Add `index` prop and planningStore import

```javascript
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { usePlanningStore } from '@/stores/planning'

const planningStore = usePlanningStore()

const props = defineProps({
  target:   { type: Object, required: true },
  session:  { type: Object, required: true },
  location: { type: Object, default: null },
  minAlt:   { type: Number, default: 20 },
  bodyName: { type: String, default: null },
  index:    { type: Number, default: null },   // null = read-only (discovery cards)
})
```

### Step 2: Add drag state and SVG ref

```javascript
const svgRef  = ref(null)
const dragState = ref(null)
// { mode: 'move'|'left'|'right', startClientX, origStartMs, origEndMs }
const MIN_DUR_MS = 5 * 60 * 1000
```

### Step 3: Add document-level handlers

```javascript
function onDocMousemove(e) {
  if (!dragState.value || props.index == null) return
  const { mode, startClientX, origStartMs, origEndMs } = dragState.value

  const rect    = svgRef.value.getBoundingClientRect()
  const pxDelta = e.clientX - startClientX
  // Full SVG width = full session duration (viewBox W maps 1:1 to session)
  const msDelta = (pxDelta / rect.width) * sessionDur.value

  let ns = origStartMs
  let ne = origEndMs

  if (mode === 'move') {
    ns = origStartMs + msDelta
    ne = origEndMs   + msDelta
    if (ns < sessionStart.value) { ne += sessionStart.value - ns; ns = sessionStart.value }
    if (ne > sessionEnd.value)   { ns -= ne - sessionEnd.value;   ne = sessionEnd.value   }
  } else if (mode === 'left') {
    ns = Math.max(sessionStart.value, Math.min(origStartMs + msDelta, origEndMs - MIN_DUR_MS))
  } else {
    ne = Math.min(sessionEnd.value,   Math.max(origEndMs   + msDelta, origStartMs + MIN_DUR_MS))
  }

  planningStore.setTargetWindow(props.index, new Date(ns).toISOString(), new Date(ne).toISOString())
}

function onDocMouseup() { dragState.value = null }

onMounted(() => {
  document.addEventListener('mousemove', onDocMousemove)
  document.addEventListener('mouseup',   onDocMouseup)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMousemove)
  document.removeEventListener('mouseup',   onDocMouseup)
})

function startDrag(e, mode) {
  if (props.index == null) return
  e.preventDefault()
  dragState.value = {
    mode,
    startClientX: e.clientX,
    origStartMs:  new Date(props.target.start_time).getTime(),
    origEndMs:    new Date(props.target.end_time).getTime(),
  }
}
```

### Step 4: Update the SVG template

Add `ref="svgRef"` to the `<svg>` element.

Replace the scheduled window rect section and dot section:

```html
<!-- Scheduled window highlight — draggable when index is set -->
<g v-if="windowWidth > 0">
  <!-- Colored window fill + border (non-interactive, pointer-events none so handles work) -->
  <rect
    :x="windowX" :y="0"
    :width="windowWidth" :height="H"
    :fill="scoreColor + '30'"
    :stroke="scoreColor"
    stroke-width="1"
    style="pointer-events: none"
  />

  <!-- Left resize handle (6px wide) -->
  <rect
    v-if="index != null"
    :x="windowX" :y="0"
    :width="Math.min(6, windowWidth / 4)" :height="H"
    fill="transparent" style="cursor: ew-resize"
    @mousedown.stop="startDrag($event, 'left')"
  />
  <!-- Interior move handle -->
  <rect
    v-if="index != null"
    :x="windowX + Math.min(6, windowWidth / 4)" :y="0"
    :width="Math.max(0, windowWidth - 2 * Math.min(6, windowWidth / 4))" :height="H"
    fill="transparent"
    :style="{ cursor: dragState?.mode === 'move' ? 'grabbing' : 'grab' }"
    @mousedown.stop="startDrag($event, 'move')"
  />
  <!-- Right resize handle (6px wide) -->
  <rect
    v-if="index != null"
    :x="windowX + windowWidth - Math.min(6, windowWidth / 4)" :y="0"
    :width="Math.min(6, windowWidth / 4)" :height="H"
    fill="transparent" style="cursor: ew-resize"
    @mousedown.stop="startDrag($event, 'right')"
  />
</g>

<!-- Window start dot + invisible larger hit target for drag -->
<g v-if="windowWidth > 0 && startDotY !== null">
  <circle :cx="windowX" :cy="startDotY" r="2.5" :fill="scoreColor" style="pointer-events: none" />
  <circle
    v-if="index != null"
    :cx="windowX" :cy="startDotY" r="7"
    fill="transparent" style="cursor: ew-resize"
    @mousedown.stop="startDrag($event, 'left')"
  />
</g>

<!-- Window end dot + invisible larger hit target -->
<g v-if="windowWidth > 0 && endDotY !== null">
  <circle :cx="windowX + windowWidth" :cy="endDotY" r="2.5" :fill="scoreColor" style="pointer-events: none" />
  <circle
    v-if="index != null"
    :cx="windowX + windowWidth" :cy="endDotY" r="7"
    fill="transparent" style="cursor: ew-resize"
    @mousedown.stop="startDrag($event, 'right')"
  />
</g>
```

### Step 5: Pass `index` from PlanningView.vue

In `PlanningView.vue`, find the `<TargetVisibilityMini>` inside the `v-for="(target, index)"` loop and add `:index="index"`:

```html
<TargetVisibilityMini
  :target="target"
  :session="planningStore.currentPlan.session"
  :location="planningStore.currentPlan.location"
  :min-alt="planningStore.constraints.min_altitude_degrees"
  :index="index"
/>
```

The solar system `<TargetVisibilityMini>` (with `:body-name`) does NOT get an index — it stays read-only.

### Step 6: Verify

Drag the green window on a card mini-chart left/right — the window should slide and the PlanTimeline above should update. Drag a dot — window should shrink/expand. Both charts stay in sync because they both read reactive Pinia state.

### Step 7: Commit
```bash
git add frontend/vue-app/src/components/planning/TargetVisibilityMini.vue
git add frontend/vue-app/src/views/PlanningView.vue
git commit -m "feat: draggable windows and resize dots on per-card visibility mini charts"
```

---

## Task 5: Build and deploy

```bash
cd frontend/vue-app
npm run build
docker cp dist/. astronomus:/app/frontend/vue-app/dist/
```

Verify in browser:
1. Drag window in top timeline → moves, adjacent target stays put, coverage% in header updates
2. Drag edge in top timeline → resizes, duration input in card updates
3. Drag green rect on card mini-chart → same effect as top timeline, both charts update
4. Drag end dot on card mini-chart → window expands/shrinks
5. Overlap two windows → both turn red in top timeline
6. Put two windows within 5 min of each other → both turn orange
7. Drag a window into a low-altitude time range → turns yellow

---

## Deployment reminder

After verifying manually, final commit for build artifacts is optional (dist/ is typically gitignored). The source commits above are sufficient.

---

## What was intentionally NOT built

- Touch/mobile drag (PointerEvents API instead of MouseEvents) — can add later if iPad use is confirmed
- Snap-to-minute or snap-to-other-target's-edge during drag — could add as a UX polish
- Gantt-push behavior (auto-shifting subsequent targets) — user explicitly chose "warn on conflict"
- "Undo" for drag operations — future enhancement
