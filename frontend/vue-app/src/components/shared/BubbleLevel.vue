<template>
  <svg viewBox="0 0 60 60" :width="size" :height="size" xmlns="http://www.w3.org/2000/svg">
    <!-- Outer ring -->
    <circle cx="30" cy="30" r="28" stroke="#4b5563" fill="none" stroke-width="1.5" />
    <!-- Level target zone (±2°) — bubble inside here = level -->
    <circle cx="30" cy="30" r="8" fill="rgba(34,197,94,0.15)" stroke="#16a34a" stroke-width="1" />
    <!-- Crosshairs -->
    <line x1="30" y1="3" x2="30" y2="57" stroke="#374151" stroke-width="1" />
    <line x1="3" y1="30" x2="57" y2="30" stroke="#374151" stroke-width="1" />
    <!-- Moving bubble -->
    <circle :cx="30 + bubbleX" :cy="30 + bubbleY" r="6" :fill="bubbleColor" opacity="0.9" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  z: { type: Number, default: 0 },
  angle: { type: Number, default: 0 },
  size: { type: Number, default: 80 }
})

// Scale: maps g-force (sin of tilt angle) to pixels.
// sin(2°) ≈ 0.035 → 8px (edge of green zone); sin(10°) ≈ 0.174 → 22px (outer ring edge).
// SCALE = 8 / sin(2°) ≈ 229
const SCALE = 229
const MAX_PX = 22  // outer ring radius minus bubble radius

const bubbleX = computed(() => Math.max(-MAX_PX, Math.min(MAX_PX, props.x * SCALE)))
const bubbleY = computed(() => Math.max(-MAX_PX, Math.min(MAX_PX, -props.y * SCALE)))

const bubbleColor = computed(() => {
  if (props.angle <= 2) return '#22c55e'   // green: level
  if (props.angle <= 5) return '#eab308'   // yellow: close
  return '#ef4444'                          // red: not level
})
</script>
