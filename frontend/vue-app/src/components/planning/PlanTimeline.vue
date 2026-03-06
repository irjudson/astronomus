<template>
  <div class="plan-timeline">
    <!-- Summary bar -->
    <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400 px-3 py-2 bg-gray-900/80 border border-gray-800 border-b-0 rounded-t-lg">
      <span class="text-gray-300">● {{ targets.length }} target{{ targets.length !== 1 ? 's' : '' }}</span>
      <span>● {{ totalImagingHours }} imaging / {{ totalDarkHours }} dark = {{ efficiency }}% efficient</span>
      <span>● Avg score: {{ avgScore }}</span>
      <span v-if="gaps.length > 0" class="text-orange-400">
        ● {{ gaps.length }} gap{{ gaps.length > 1 ? 's' : '' }} ({{ totalGapMinutes }} min wasted)
      </span>
    </div>

    <!-- SVG chart -->
    <svg
      ref="svgRef"
      :viewBox="`0 0 ${W} ${H}`"
      preserveAspectRatio="xMidYMid meet"
      class="w-full border border-gray-800 rounded-b-lg"
      style="background: #070710; display: block"
    >
      <defs>
        <clipPath :id="clipId">
          <rect :x="ML" :y="MT" :width="CW" :height="CH" />
        </clipPath>
      </defs>

      <!-- 1. Twilight bands -->
      <g :clip-path="`url(#${clipId})`">
        <rect
          v-if="hasTwilight('civil_twilight_end', 'nautical_twilight_end')"
          :x="tx(session.civil_twilight_end)" :y="MT"
          :width="Math.max(0, tx(session.nautical_twilight_end) - tx(session.civil_twilight_end))"
          :height="CH" fill="rgba(146, 64, 14, 0.3)"
        />
        <rect
          v-if="hasTwilight('nautical_twilight_end', 'astronomical_twilight_end')"
          :x="tx(session.nautical_twilight_end)" :y="MT"
          :width="Math.max(0, tx(session.astronomical_twilight_end) - tx(session.nautical_twilight_end))"
          :height="CH" fill="rgba(100, 40, 10, 0.4)"
        />
        <rect
          v-if="hasTwilight('astronomical_twilight_start', 'nautical_twilight_start')"
          :x="tx(session.astronomical_twilight_start)" :y="MT"
          :width="Math.max(0, tx(session.nautical_twilight_start) - tx(session.astronomical_twilight_start))"
          :height="CH" fill="rgba(100, 40, 10, 0.4)"
        />
        <rect
          v-if="hasTwilight('nautical_twilight_start', 'civil_twilight_start')"
          :x="tx(session.nautical_twilight_start)" :y="MT"
          :width="Math.max(0, tx(session.civil_twilight_start) - tx(session.nautical_twilight_start))"
          :height="CH" fill="rgba(146, 64, 14, 0.3)"
        />
      </g>

      <!-- 2. Y-axis grid lines + labels -->
      <g>
        <template v-for="alt in yTicks" :key="'ygrid' + alt">
          <line
            :x1="ML" :x2="ML + CW" :y1="ay(alt)" :y2="ay(alt)"
            stroke="#1f2937" stroke-width="0.5"
          />
          <line
            :x1="ML - 3" :x2="ML" :y1="ay(alt)" :y2="ay(alt)"
            stroke="#374151" stroke-width="1"
          />
          <text
            :x="ML - 5" :y="ay(alt) + 3"
            text-anchor="end" fill="#6b7280" font-size="9"
            font-family="ui-sans-serif,system-ui,sans-serif"
          >{{ alt }}°</text>
        </template>

        <!-- Threshold lines -->
        <line
          :x1="ML" :x2="ML + CW" :y1="ay(minAlt)" :y2="ay(minAlt)"
          stroke="#f59e0b" stroke-width="1" stroke-dasharray="4,3" opacity="0.5"
        />
        <line
          :x1="ML" :x2="ML + CW" :y1="ay(85)" :y2="ay(85)"
          stroke="#4b5563" stroke-width="1" stroke-dasharray="4,3" opacity="0.35"
        />
      </g>

      <!-- 3. Gap markers -->
      <g :clip-path="`url(#${clipId})`">
        <rect
          v-for="(gap, i) in gaps" :key="'gap' + i"
          :x="tx(gap.start)" :y="MT"
          :width="Math.max(1, tx(gap.end) - tx(gap.start))"
          :height="CH"
          fill="rgba(239, 68, 68, 0.1)"
        />
      </g>

      <!-- 4. Target window rects + drag handles -->
      <g :clip-path="`url(#${clipId})`">
        <!-- Visual window (pointer-events: none — handled by transparent overlay rects below) -->
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
            :width="edgePx(i)" :height="CH"
            fill="transparent" style="cursor: ew-resize"
            @mousedown.stop="onWindowMousedown($event, i, 'left')"
          />
          <!-- Interior move handle -->
          <rect
            :x="tx(target.start_time) + edgePx(i)" :y="MT"
            :width="Math.max(0, tx(target.end_time) - tx(target.start_time) - 2 * edgePx(i))"
            :height="CH"
            fill="transparent"
            :style="{ cursor: dragState?.index === i ? 'grabbing' : 'grab' }"
            @mousedown.stop="onWindowMousedown($event, i, 'move')"
          />
          <!-- Right resize handle -->
          <rect
            :x="tx(target.end_time) - edgePx(i)" :y="MT"
            :width="edgePx(i)" :height="CH"
            fill="transparent" style="cursor: ew-resize"
            @mousedown.stop="onWindowMousedown($event, i, 'right')"
          />
        </template>
      </g>

      <!-- 5. Field rotation stripe (bottom of window) -->
      <g :clip-path="`url(#${clipId})`">
        <template v-for="(target, i) in targets" :key="'rot' + i">
          <rect
            v-if="(target.field_rotation_rate || 0) > 0.8"
            :x="tx(target.start_time)"
            :y="MT + CH - 4"
            :width="Math.max(2, tx(target.end_time) - tx(target.start_time))"
            height="4"
            fill="rgba(239, 68, 68, 0.75)"
          />
        </template>
      </g>

      <!-- 6. Altitude curves (full-session from API when available, fallback to altitude_points) -->
      <g :clip-path="`url(#${clipId})`">
        <path
          v-for="(target, i) in targets" :key="'curve' + (target.target?.catalog_id || i)"
          :d="pointsToPath(fullCurves[target.target?.catalog_id] ?? target.altitude_points)"
          fill="none"
          :stroke="fullCurves[target.target?.catalog_id] ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.35)'"
          stroke-width="1.5"
          stroke-linejoin="round"
          style="pointer-events: none"
        />
      </g>

      <!-- 7. "Now" indicator -->
      <line
        v-if="nowX !== null"
        :x1="nowX" :x2="nowX"
        :y1="MT" :y2="MT + CH"
        stroke="#3b82f6" stroke-width="1.5" opacity="0.85"
      />

      <!-- 8. Target name labels (below each window) -->
      <g>
        <text
          v-for="(target, i) in targets" :key="'lbl' + i"
          :x="(tx(target.start_time) + tx(target.end_time)) / 2"
          :y="MT + CH + 13"
          text-anchor="middle"
          fill="#9ca3af"
          font-size="8"
          font-family="ui-sans-serif,system-ui,sans-serif"
          style="pointer-events: none"
        >{{ shortName(target) }}</text>
      </g>

      <!-- 9. X-axis hour ticks + labels -->
      <g>
        <template v-for="tick in hourTicks" :key="tick.label">
          <line
            :x1="tick.x" :x2="tick.x"
            :y1="MT + CH" :y2="MT + CH + 4"
            stroke="#374151" stroke-width="1"
          />
          <text
            :x="tick.x" :y="MT + CH + 23"
            text-anchor="middle" fill="#6b7280" font-size="9"
            font-family="ui-sans-serif,system-ui,sans-serif"
          >{{ tick.label }}</text>
        </template>
      </g>

      <!-- Chart border -->
      <rect :x="ML" :y="MT" :width="CW" :height="CH" fill="none" stroke="#1f2937" stroke-width="1" />
    </svg>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { usePlanningStore } from '@/stores/planning'

const props = defineProps({
  plan: { type: Object, required: true }
})
const emit = defineEmits(['select-target'])

const planningStore = usePlanningStore()
const svgRef = ref(null)
const dragState = ref(null)
// dragState shape: { index, mode: 'move'|'left'|'right', startClientX, origStartMs, origEndMs }

const EDGE_PX = 8        // viewBox pixels for left/right drag handle zones
const MIN_DUR_MS = 5 * 60 * 1000

// Module-level cache shared across all PlanTimeline instances
const _tlCache = new Map()

// Full-session curves fetched from API, keyed by catalog_id
const fullCurves = ref({})

async function fetchAllCurves() {
  const plan = props.plan
  if (!plan?.session || !plan?.location) return
  const lat = plan.location.latitude
  const lon = plan.location.longitude
  if (lat == null || lon == null) return
  const { imaging_start, imaging_end } = plan.session

  const updated = {}
  for (const target of (plan.scheduled_targets ?? [])) {
    const id  = target.target?.catalog_id
    const ra  = target.target?.ra_hours
    const dec = target.target?.dec_degrees
    if (!id || ra == null || dec == null) continue

    const key = `${id}|${imaging_start}`
    if (_tlCache.has(key)) {
      updated[id] = _tlCache.get(key)
      continue
    }
    try {
      const res = await axios.get('/api/altitude-curve', {
        params: { lat, lon, imaging_start, imaging_end, ra_hours: ra, dec_degrees: dec }
      })
      const pts = res.data.points ?? []
      _tlCache.set(key, pts)
      updated[id] = pts
    } catch {
      // fall back to altitude_points
    }
  }
  fullCurves.value = { ...fullCurves.value, ...updated }
}

onMounted(() => {
  fetchAllCurves()
  document.addEventListener('mousemove', onDocMousemove)
  document.addEventListener('mouseup',   onDocMouseup)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMousemove)
  document.removeEventListener('mouseup',   onDocMouseup)
})
watch(() => props.plan?.session?.imaging_start, fetchAllCurves)

// SVG dimensions & margins
const W = 640
const H = 230
const ML = 32   // margin left (Y-axis labels)
const MR = 8    // margin right
const MT = 10   // margin top
const MB = 42   // margin bottom (X-axis labels + target names)
const CW = W - ML - MR   // chart width  = 600
const CH = H - MT - MB   // chart height = 178

const yTicks = [0, 20, 45, 70, 85]

// Unique clip-path id per instance
const clipId = `chart-clip-${Math.random().toString(36).slice(2, 8)}`

const session  = computed(() => props.plan?.session ?? {})
const targets  = computed(() => props.plan?.scheduled_targets ?? [])
const minAlt   = computed(() => props.plan?.constraints?.min_altitude_degrees ?? 20)

const sessionStart = computed(() => {
  const v = session.value.imaging_start
  return v ? new Date(v).getTime() : 0
})
const sessionEnd = computed(() => {
  const v = session.value.imaging_end
  return v ? new Date(v).getTime() : 0
})
const sessionDur = computed(() => sessionEnd.value - sessionStart.value)

// Time ISO string → X pixel within chart area
const tx = (isoStr) => {
  if (!isoStr || !sessionDur.value) return ML
  const frac = (new Date(isoStr).getTime() - sessionStart.value) / sessionDur.value
  return ML + Math.max(0, Math.min(1, frac)) * CW
}

// Altitude (0–90°) → Y pixel, 0° at bottom
const ay = (alt) => MT + CH - (Math.max(0, Math.min(90, alt)) / 90) * CH

// [[iso, alt], ...] → SVG path d string
const pointsToPath = (pts) => {
  if (!pts?.length) return ''
  return pts
    .map(([t, alt], i) => `${i === 0 ? 'M' : 'L'}${tx(t).toFixed(1)},${ay(alt).toFixed(1)}`)
    .join(' ')
}

function interpAlt(tMs, pts) {
  if (!pts?.length || tMs == null) return null
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

const SLEW_GAP_MS = 5 * 60 * 1000  // 5-minute minimum slew gap

const conflictMap = computed(() => {
  const ts = targets.value
  const result = {}
  // Only process targets with valid times
  const validIndices = new Set(
    ts.map((t, i) => (t.start_time && t.end_time ? i : null)).filter(i => i !== null)
  )

  // 1. Low-altitude check — sample at start, middle, end of each window
  for (let i = 0; i < ts.length; i++) {
    if (!validIndices.has(i)) continue
    const curve = fullCurves.value[ts[i].target?.catalog_id] ?? ts[i].altitude_points
    if (!curve?.length) continue
    const sMs = new Date(ts[i].start_time).getTime()
    const eMs = new Date(ts[i].end_time).getTime()
    for (const ms of [sMs, (sMs + eMs) / 2, eMs]) {
      const alt = interpAlt(ms, curve)
      if (alt != null && alt < minAlt.value) {
        result[i] = 'lowalt'
        break
      }
    }
  }

  // 2. True overlap — any two windows that share time (overrides lowalt)
  for (let i = 0; i < ts.length; i++) {
    if (!validIndices.has(i)) continue
    for (let j = i + 1; j < ts.length; j++) {
      if (!validIndices.has(j)) continue
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

  // 3. Insufficient slew gap between consecutive targets (only if not already overlap)
  const sorted = ts
    .map((t, origIndex) => ({
      origIndex,
      startMs: new Date(t.start_time).getTime(),
      endMs: new Date(t.end_time).getTime(),
    }))
    .filter((_, i) => validIndices.has(i))
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

function windowColor(i) {
  const c = conflictMap.value[i]
  if (c === 'overlap') return '#ef4444'  // red
  if (c === 'gap')     return '#f97316'  // orange
  if (c === 'lowalt')  return '#eab308'  // yellow
  return scoreColor(targets.value[i].score?.total_score)
}

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

function onDocMousemove(e) {
  if (!dragState.value || !svgRef.value) return
  e.preventDefault()
  const { index, mode, startClientX, origStartMs, origEndMs } = dragState.value

  const rect    = svgRef.value.getBoundingClientRect()
  const pxDelta = e.clientX - startClientX
  // Convert rendered-px delta → ms: (W/rect.width) maps to viewBox px, (sessionDur/CW) maps to time
  const msDelta = pxDelta * sessionDur.value * W / (CW * rect.width)

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
  } else { // right
    ne = Math.min(sessionEnd.value, Math.max(origEndMs + msDelta, origStartMs + MIN_DUR_MS))
  }

  planningStore.setTargetWindow(index, new Date(ns).toISOString(), new Date(ne).toISOString())
}

function onDocMouseup() { dragState.value = null }

const edgePx = (i) => {
  const w = tx(targets.value[i].end_time) - tx(targets.value[i].start_time)
  return Math.min(EDGE_PX, Math.floor(w / 3))
}

const scoreColor = (score) =>
  score == null ? '#6b7280' : score >= 0.7 ? '#22c55e' : score >= 0.4 ? '#f59e0b' : '#ef4444'

const shortName = (target) => {
  const n = target.target?.common_name || target.target?.catalog_id || ''
  return n.length > 9 ? n.slice(0, 8) + '…' : n
}

// Check both twilight fields exist and first < second
const hasTwilight = (f1, f2) => {
  const v1 = session.value[f1]
  const v2 = session.value[f2]
  return !!(v1 && v2 && new Date(v1).getTime() < new Date(v2).getTime())
}

// Gaps between consecutive target windows (> 1 min)
const gaps = computed(() => {
  const ts = targets.value
  if (ts.length < 2) return []
  const result = []
  for (let i = 0; i < ts.length - 1; i++) {
    const endMs   = new Date(ts[i].end_time).getTime()
    const startMs = new Date(ts[i + 1].start_time).getTime()
    const gapMin  = (startMs - endMs) / 60000
    if (gapMin > 1) result.push({ start: ts[i].end_time, end: ts[i + 1].start_time, minutes: Math.round(gapMin) })
  }
  return result
})

// Blue "now" line if current time is within the session window
const nowX = computed(() => {
  if (!sessionDur.value) return null
  const now = Date.now()
  if (now < sessionStart.value || now > sessionEnd.value) return null
  return ML + ((now - sessionStart.value) / sessionDur.value) * CW
})

// Hour tick marks on X-axis
const hourTicks = computed(() => {
  if (!sessionDur.value) return []
  const ticks = []
  const startHour = Math.ceil(sessionStart.value / 3600000) * 3600000
  for (let t = startHour; t <= sessionEnd.value; t += 3600000) {
    const frac = (t - sessionStart.value) / sessionDur.value
    if (frac < 0 || frac > 1) continue
    const x = ML + frac * CW
    const d = new Date(t)
    const h = d.getHours()
    const label = h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h - 12}p`
    ticks.push({ x, label })
  }
  return ticks
})

// Summary bar stats
const totalImagingMin = computed(() =>
  targets.value.reduce((sum, t) => sum + (t.duration_minutes || 0), 0)
)
const totalDarkMin  = computed(() => sessionDur.value / 60000)

const formatHM = (min) => {
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

const totalImagingHours = computed(() => formatHM(totalImagingMin.value))
const totalDarkHours    = computed(() => formatHM(totalDarkMin.value))

const efficiency = computed(() =>
  totalDarkMin.value > 0 ? Math.round((totalImagingMin.value / totalDarkMin.value) * 100) : 0
)

const avgScore = computed(() => {
  const scores = targets.value.map(t => t.score?.total_score).filter(s => s != null)
  if (!scores.length) return 'N/A'
  return (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2)
})

const totalGapMinutes = computed(() => gaps.value.reduce((sum, g) => sum + g.minutes, 0))
</script>
