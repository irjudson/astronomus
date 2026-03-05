<template>
  <svg :viewBox="`0 0 ${W} ${W}`" :width="size" :height="size" xmlns="http://www.w3.org/2000/svg">
    <!-- Outer ring border -->
    <circle :cx="C" :cy="C" :r="R2 + 2" fill="none" stroke="#374151" stroke-width="1" />

    <!-- Coverage segments: 36 × 10° arcs in donut ring -->
    <path
      v-for="i in 36"
      :key="i"
      :d="segPath(i - 1)"
      :fill="covered[i - 1] ? '#3b82f6' : '#1f2937'"
      stroke="#111827"
      stroke-width="0.8"
    />

    <!-- Inner circle (covers center of donut) -->
    <circle :cx="C" :cy="C" :r="R1 - 1" fill="#1a1f2e" />

    <!-- Cardinal labels -->
    <text :x="C"     :y="6"     text-anchor="middle" :font-size="FS" fill="#6b7280" font-family="monospace">N</text>
    <text :x="C"     :y="W - 1" text-anchor="middle" :font-size="FS" fill="#6b7280" font-family="monospace">S</text>
    <text :x="W - 2" :y="C + 3" text-anchor="middle" :font-size="FS" fill="#6b7280" font-family="monospace">E</text>
    <text :x="2"     :y="C + 3" text-anchor="middle" :font-size="FS" fill="#6b7280" font-family="monospace">W</text>

    <!-- Compass needle — rotates to heading (0° = North = up) -->
    <g :transform="`rotate(${heading ?? 0}, ${C}, ${C})`">
      <!-- North half: red -->
      <polygon
        :points="`${C},${C - needleLen} ${C - 4},${C} ${C + 4},${C}`"
        fill="#ef4444"
        opacity="0.95"
      />
      <!-- South half: gray -->
      <polygon
        :points="`${C},${C + needleLen} ${C - 4},${C} ${C + 4},${C}`"
        fill="#4b5563"
        opacity="0.9"
      />
      <!-- Center pivot -->
      <circle :cx="C" :cy="C" r="3" fill="#9ca3af" />
    </g>

    <!-- Heading text (center top) -->
    <text
      :x="C" :y="C - 4"
      text-anchor="middle"
      fill="white"
      :font-size="FS + 3"
      font-family="monospace"
      font-weight="bold"
    >{{ heading !== null ? heading + '°' : '--°' }}</text>

    <!-- Progress text (center bottom) -->
    <text
      :x="C" :y="C + 10"
      text-anchor="middle"
      :fill="progress >= 100 ? '#22c55e' : '#6b7280'"
      :font-size="FS + 1"
      font-family="monospace"
    >{{ Math.round(progress) }}%</text>

    <!-- Done ring: green outer glow when complete -->
    <circle
      v-if="progress >= 100"
      :cx="C" :cy="C" :r="R2 + 2"
      fill="none"
      stroke="#22c55e"
      stroke-width="2"
      opacity="0.6"
    />
  </svg>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  heading: { type: Number, default: null },
  active:  { type: Boolean, default: false },
  size:    { type: Number, default: 140 }
})

// SVG geometry constants
const W = 100        // viewBox width & height
const C = 50         // center x & y
const R1 = 32        // inner donut radius
const R2 = 44        // outer donut radius
const FS = 7         // base font size
const needleLen = 22 // needle length from center

// 36 booleans, one per 10° bucket
const covered = ref(new Array(36).fill(false))

// Reset when a new calibration starts
watch(() => props.active, (active) => {
  if (active) covered.value = new Array(36).fill(false)
})

// Mark bucket visited whenever heading changes during calibration
watch(() => props.heading, (h) => {
  if (h === null || !props.active) return
  const bucket = Math.floor(((h % 360) + 360) % 360 / 10)
  if (!covered.value[bucket]) {
    const next = [...covered.value]
    next[bucket] = true
    covered.value = next
  }
})

const progress = computed(() => covered.value.filter(Boolean).length / 36 * 100)

// Build SVG arc path for one 10° segment in the donut ring
const toRad = d => d * Math.PI / 180
const segPath = (i) => {
  const gap    = 1.5                        // gap between segments in degrees
  const start  = i * 10 - 90 + gap / 2     // -90 rotates 0° to 12-o'clock (North)
  const end    = start + 10 - gap
  const s = toRad(start), e = toRad(end)

  const x1 = C + R2 * Math.cos(s), y1 = C + R2 * Math.sin(s)
  const x2 = C + R2 * Math.cos(e), y2 = C + R2 * Math.sin(e)
  const x3 = C + R1 * Math.cos(e), y3 = C + R1 * Math.sin(e)
  const x4 = C + R1 * Math.cos(s), y4 = C + R1 * Math.sin(s)

  const fmt = n => n.toFixed(2)
  return `M ${fmt(x1)} ${fmt(y1)} A ${R2} ${R2} 0 0 1 ${fmt(x2)} ${fmt(y2)} ` +
         `L ${fmt(x3)} ${fmt(y3)} A ${R1} ${R1} 0 0 0 ${fmt(x4)} ${fmt(y4)} Z`
}
</script>
