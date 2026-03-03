<template>
  <svg :viewBox="`0 0 ${W} ${W}`" :width="size" :height="size" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <circle :cx="C" :cy="C" r="46" fill="#111827" stroke="#374151" stroke-width="1"/>

    <!-- Red outer zone (visible annulus r=30..44): ≥15' error -->
    <circle :cx="C" :cy="C" r="44" :fill="zone === 'red' ? '#7f1d1d' : '#1c0a0a'"/>
    <!-- Yellow middle zone (visible annulus r=15..30): 5–15' error -->
    <circle :cx="C" :cy="C" r="30" :fill="zone === 'yellow' ? '#78350f' : '#1c1608'"/>
    <!-- Green inner zone (circle r=15): <5' error — excellent -->
    <circle :cx="C" :cy="C" r="15" :fill="zone === 'green' ? '#14532d' : '#080f0a'"/>

    <!-- Zone boundary rings -->
    <circle :cx="C" :cy="C" r="30" fill="none" stroke="#374151" stroke-width="0.8"/>
    <circle :cx="C" :cy="C" r="15" fill="none" stroke="#374151" stroke-width="0.8"/>

    <!-- Crosshairs (broken at center zone) -->
    <line :x1="C" y1="6"  :x2="C"       :y2="C - 16" stroke="#374151" stroke-width="0.5"/>
    <line :x1="C" :y1="C + 16" :x2="C"  y2="94"      stroke="#374151" stroke-width="0.5"/>
    <line x1="6"  :y1="C" :x2="C - 16"  :y2="C"      stroke="#374151" stroke-width="0.5"/>
    <line :x1="C + 16" :y1="C" x2="94"  :y2="C"      stroke="#374151" stroke-width="0.5"/>

    <!-- Center quality dot -->
    <circle :cx="C" :cy="C" r="7" :fill="dotColor"/>

    <!-- Center text: error in arcminutes -->
    <text
      :x="C" :y="C + 3"
      text-anchor="middle"
      :fill="textColor"
      font-size="7"
      font-family="monospace"
      font-weight="bold"
    >{{ errorArcmin !== null ? errorArcmin.toFixed(1) + "'" : '--' }}</text>

    <!-- Active: pulsing outer ring (SVG SMIL animation) -->
    <circle v-if="active" :cx="C" :cy="C" r="46" fill="none" stroke="#3b82f6" stroke-width="1.5">
      <animate attributeName="opacity" values="0.6;0.1;0.6" dur="2s" repeatCount="indefinite"/>
    </circle>

    <!-- Done ring: green outer glow when excellent alignment achieved -->
    <circle
      v-if="errorArcmin !== null && errorArcmin < 5"
      :cx="C" :cy="C" r="46"
      fill="none"
      stroke="#22c55e"
      stroke-width="2"
      opacity="0.5"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const W = 100
const C = 50

const props = defineProps({
  errorArcmin: { type: Number, default: null },
  active:      { type: Boolean, default: false },
  size:        { type: Number, default: 120 }
})

// Quality zone based on total alignment error in arcminutes
const zone = computed(() => {
  if (props.errorArcmin === null) return 'none'
  if (props.errorArcmin < 5)  return 'green'   // excellent
  if (props.errorArcmin < 15) return 'yellow'  // acceptable
  return 'red'                                   // needs adjustment
})

const dotColor = computed(() => ({
  green: '#22c55e', yellow: '#eab308', red: '#ef4444', none: '#374151'
}[zone.value]))

const textColor = computed(() => ({
  green: '#22c55e', yellow: '#eab308', red: '#ef4444', none: '#6b7280'
}[zone.value]))
</script>
