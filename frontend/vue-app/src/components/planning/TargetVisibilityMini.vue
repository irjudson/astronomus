<template>
  <svg
    ref="svgRef"
    :viewBox="`0 0 ${W} ${H}`"
    preserveAspectRatio="xMidYMid meet"
    class="w-full rounded"
    style="display: block; background: #0a0a14"
  >
    <defs>
      <clipPath :id="clipId">
        <rect :x="0" :y="0" :width="W" :height="H" />
      </clipPath>
    </defs>

    <!-- Scheduled window highlight + drag handles -->
    <g v-if="windowWidth > 0">
      <!-- Visual window (non-interactive) -->
      <rect
        :x="windowX" :y="0"
        :width="windowWidth" :height="H"
        :fill="scoreColor + '30'"
        :stroke="scoreColor"
        stroke-width="1"
        style="pointer-events: none"
      />

      <!-- Drag handles (only when index is set) -->
      <template v-if="index != null">
        <!-- Left resize handle -->
        <rect
          :x="windowX" :y="0"
          :width="Math.min(6, windowWidth / 4)" :height="H"
          fill="transparent" style="cursor: ew-resize"
          @mousedown.stop="startDrag($event, 'left')"
        />
        <!-- Interior move handle -->
        <rect
          :x="windowX + Math.min(6, windowWidth / 4)" :y="0"
          :width="Math.max(0, windowWidth - 2 * Math.min(6, windowWidth / 4))" :height="H"
          fill="transparent"
          :style="{ cursor: dragState?.mode === 'move' ? 'grabbing' : 'grab' }"
          @mousedown.stop="startDrag($event, 'move')"
        />
        <!-- Right resize handle -->
        <rect
          :x="windowX + windowWidth - Math.min(6, windowWidth / 4)" :y="0"
          :width="Math.min(6, windowWidth / 4)" :height="H"
          fill="transparent" style="cursor: ew-resize"
          @mousedown.stop="startDrag($event, 'right')"
        />
      </template>
    </g>

    <!-- Min altitude threshold line -->
    <line
      :x1="0" :x2="W"
      :y1="ay(minAlt)" :y2="ay(minAlt)"
      stroke="#f59e0b" stroke-width="0.75" stroke-dasharray="3,2" opacity="0.5"
    />

    <!-- Altitude curve: full-session fetch (preferred) OR fallback to altitude_points while loading -->
    <path
      :d="displayCurvePath"
      fill="none"
      :stroke="fetchedPoints ? 'rgba(255,255,255,0.8)' : 'rgba(255,255,255,0.35)'"
      :stroke-width="fetchedPoints ? 1.5 : 1"
      stroke-linejoin="round"
      :clip-path="`url(#${clipId})`"
    />

    <!-- Start dot (visual, non-interactive) + large hit area for drag -->
    <g v-if="windowWidth > 0 && startDotY !== null">
      <circle :cx="windowX" :cy="startDotY" r="2.5" :fill="scoreColor" style="pointer-events: none" />
      <circle
        v-if="index != null"
        :cx="windowX" :cy="startDotY" r="7"
        fill="transparent" style="cursor: ew-resize"
        @mousedown.stop="startDrag($event, 'left')"
      />
    </g>

    <!-- End dot (visual, non-interactive) + large hit area for drag -->
    <g v-if="windowWidth > 0 && endDotY !== null">
      <circle :cx="windowX + windowWidth" :cy="endDotY" r="2.5" :fill="scoreColor" style="pointer-events: none" />
      <circle
        v-if="index != null"
        :cx="windowX + windowWidth" :cy="endDotY" r="7"
        fill="transparent" style="cursor: ew-resize"
        @mousedown.stop="startDrag($event, 'right')"
      />
    </g>

    <!-- Scheduled time label inside window -->
    <text
      v-if="windowWidth > 28"
      :x="windowX + windowWidth / 2"
      :y="H - 3"
      text-anchor="middle"
      fill="rgba(255,255,255,0.55)"
      font-size="7"
      font-family="ui-sans-serif,system-ui,sans-serif"
    >{{ scheduledLabel }}</text>
  </svg>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { usePlanningStore } from '@/stores/planning'

// Module-level cache shared across all instances: key = `${catalogId}|${imagingStart}`
const _cache = new Map()

const props = defineProps({
  target:   { type: Object, required: true },  // scheduled target or solar system object
  session:  { type: Object, required: true },  // plan.session
  location: { type: Object, default: null },   // plan.location (lat/lon for API)
  minAlt:   { type: Number, default: 20 },
  bodyName: { type: String, default: null },   // solar system body name (overrides ra/dec fetch)
  index:    { type: Number, default: null },   // null = read-only (discovery/solar system cards)
})

const planningStore = usePlanningStore()
const svgRef = ref(null)
const dragState = ref(null)
// { mode: 'move'|'left'|'right', startClientX, origStartMs, origEndMs }
const MIN_DUR_MS = 5 * 60 * 1000

const W = 300
const H = 52

const clipId = `tvm-${Math.random().toString(36).slice(2, 8)}`

const sessionStart = computed(() => new Date(props.session.imaging_start).getTime())
const sessionEnd   = computed(() => new Date(props.session.imaging_end).getTime())
const sessionDur   = computed(() => sessionEnd.value - sessionStart.value)

const tx = (isoStr) => {
  if (!isoStr || !sessionDur.value) return 0
  const frac = (new Date(isoStr).getTime() - sessionStart.value) / sessionDur.value
  return Math.max(0, Math.min(1, frac)) * W
}

const ay = (alt) => H - (Math.max(0, Math.min(90, alt)) / 90) * H

const ptsToPath = (pts) => {
  if (!pts?.length) return ''
  return pts.map(([t, alt], i) =>
    `${i === 0 ? 'M' : 'L'}${tx(t).toFixed(1)},${ay(alt).toFixed(1)}`
  ).join(' ')
}

// Full-session curve fetched from API
const fetchedPoints = ref(null)

const cacheKey = computed(() => {
  const id  = props.bodyName ?? props.target.target?.catalog_id ?? props.target.name
  const t0  = props.session?.imaging_start
  return id && t0 ? `${id}|${t0}` : null
})

async function fetchFullCurve() {
  const key = cacheKey.value
  if (!key) return

  if (_cache.has(key)) {
    fetchedPoints.value = _cache.get(key)
    return
  }

  const lat = props.location?.latitude
  const lon = props.location?.longitude
  if (lat == null || lon == null) return

  const ra  = props.target.target?.ra_hours
  const dec = props.target.target?.dec_degrees
  if (!props.bodyName && (ra == null || dec == null)) return

  try {
    const params = {
      lat,
      lon,
      imaging_start: props.session.imaging_start,
      imaging_end:   props.session.imaging_end,
    }
    if (props.bodyName) {
      params.body_name = props.bodyName
    } else {
      params.ra_hours = ra
      params.dec_degrees = dec
    }
    const res = await axios.get('/api/altitude-curve', { params })
    const pts = res.data.points ?? []
    _cache.set(key, pts)
    fetchedPoints.value = pts
  } catch {
    // fall back to altitude_points
  }
}

onMounted(fetchFullCurve)
// Re-fetch if session changes (new plan generated)
watch(() => props.session?.imaging_start, fetchFullCurve)

// Show full-session curve when fetched; fall back to altitude_points during loading
const displayCurvePath = computed(() =>
  fetchedPoints.value
    ? ptsToPath(fetchedPoints.value)
    : ptsToPath(props.target.altitude_points ?? [])
)

// Scheduled window geometry
const windowX     = computed(() => tx(props.target.start_time))
const windowEnd_x = computed(() => tx(props.target.end_time))
const windowWidth = computed(() => Math.max(0, windowEnd_x.value - windowX.value))

// Dots: interpolate altitude from fetchedPoints at window start/end if possible
const interpAlt = (isoStr, pts) => {
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

const startDotY = computed(() => {
  const pts = fetchedPoints.value ?? props.target.altitude_points
  const alt = interpAlt(props.target.start_time, pts) ?? props.target.start_altitude
  return alt != null ? ay(alt) : null
})
const endDotY = computed(() => {
  const pts = fetchedPoints.value ?? props.target.altitude_points
  const alt = interpAlt(props.target.end_time, pts) ?? props.target.end_altitude
  return alt != null ? ay(alt) : null
})

// Score → stroke color
const scoreColor = computed(() => {
  const s = props.target.score?.total_score
  if (s == null) return '#6b7280'
  return s >= 0.7 ? '#22c55e' : s >= 0.4 ? '#f59e0b' : '#ef4444'
})

// "10:30 PM – 11:45 PM" label
const scheduledLabel = computed(() => {
  const fmt = (iso) => iso
    ? new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
    : ''
  return `${fmt(props.target.start_time)} – ${fmt(props.target.end_time)}`
})

function startDrag(e, mode) {
  if (props.index == null) return
  if (!props.target.start_time || !props.target.end_time) return
  e.preventDefault()
  dragState.value = {
    mode,
    startClientX: e.clientX,
    origStartMs: new Date(props.target.start_time).getTime(),
    origEndMs:   new Date(props.target.end_time).getTime(),
  }
}

function onDocMousemove(e) {
  if (!dragState.value || !svgRef.value || props.index == null) return
  e.preventDefault()
  const { mode, startClientX, origStartMs, origEndMs } = dragState.value

  const rect    = svgRef.value.getBoundingClientRect()
  const pxDelta = e.clientX - startClientX
  // Full SVG width maps to full session duration (simpler than PlanTimeline)
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
    ne = Math.min(sessionEnd.value, Math.max(origEndMs + msDelta, origStartMs + MIN_DUR_MS))
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
</script>
