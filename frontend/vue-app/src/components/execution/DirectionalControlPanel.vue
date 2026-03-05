<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Directional Control
    </h3>

    <div class="space-y-3">
      <!-- Slew rate selector -->
      <div class="flex items-center justify-center gap-2">
        <span class="text-xs text-gray-500">Slew rate:</span>
        <button
          v-for="r in RATES"
          :key="r.key"
          @click="selectedRate = r.key"
          :class="[
            'px-3 py-1 rounded text-xs font-semibold transition-colors',
            selectedRate === r.key
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700',
          ]"
          :disabled="!executionStore.connected"
        >{{ r.label }}</button>
      </div>

      <!-- Joystick pad -->
      <div class="flex flex-col items-center gap-2">
        <div
          ref="padEl"
          class="relative rounded-full bg-gray-800 border-2 select-none touch-none"
          :class="[
            executionStore.connected ? 'cursor-grab active:cursor-grabbing border-gray-700' : 'cursor-not-allowed border-gray-800 opacity-40'
          ]"
          :style="{ width: PAD_SIZE + 'px', height: PAD_SIZE + 'px' }"
          @mousedown.prevent="startDrag"
          @touchstart.prevent="startDrag"
        >
          <!-- Zone rings (slow/fast visual guides) -->
          <div
            class="absolute rounded-full border border-gray-700/50 pointer-events-none"
            :style="ringStyle(0.45)"
          />
          <div
            class="absolute rounded-full border border-gray-600/40 pointer-events-none"
            :style="ringStyle(0.75)"
          />

          <!-- Crosshairs -->
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="w-full h-px bg-gray-700/40" />
          </div>
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="h-full w-px bg-gray-700/40" />
          </div>

          <!-- Cardinal labels -->
          <div class="absolute inset-0 pointer-events-none text-gray-600" style="font-size:9px">
            <span class="absolute" style="top:4px; left:50%; transform:translateX(-50%)">N</span>
            <span class="absolute" style="bottom:4px; left:50%; transform:translateX(-50%)">S</span>
            <span class="absolute" style="left:6px; top:50%; transform:translateY(-50%)">W</span>
            <span class="absolute" style="right:6px; top:50%; transform:translateY(-50%)">E</span>
          </div>

          <!-- Thumb -->
          <div
            class="absolute rounded-full border-2 shadow-lg pointer-events-none transition-colors"
            :class="[
              isActive
                ? 'bg-blue-500 border-blue-300'
                : 'bg-gray-500 border-gray-400'
            ]"
            :style="thumbStyle"
          />
        </div>

        <!-- Status line -->
        <div class="h-4 text-xs text-center">
          <span v-if="isActive" class="text-blue-400 font-mono">
            {{ dirArrow }} {{ joystickPercent }}%
          </span>
          <span v-else class="text-gray-600">
            {{ executionStore.connected ? 'Drag to move · release to stop' : 'Not connected' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

// ─── Constants ────────────────────────────────────────────────────────────────
const PAD_SIZE   = 160          // px, diameter of joystick pad
const MAX_RADIUS = PAD_SIZE / 2 - 8   // px, max thumb travel from center
const DEAD_ZONE  = 10           // px, centre dead-zone — no movement
const THUMB_SIZE = 32           // px, thumb circle diameter
const CMD_DUR    = 2            // seconds per movement command
const REPEAT_MS  = 1600         // ms between repeated commands (slightly < CMD_DUR*1000)

// Slew rate: caps the maximum percent sent to the firmware
const RATES = [
  { key: 'slow', label: 'Slow', cap: 35 },
  { key: 'fast', label: 'Fast', cap: 100 },
]
const selectedRate = ref('slow')
const currentCap = computed(() => RATES.find(r => r.key === selectedRate.value)?.cap ?? 100)

// ─── Joystick state ───────────────────────────────────────────────────────────
const padEl  = ref(null)
const thumbX = ref(0)   // px offset from centre (clamped to MAX_RADIUS)
const thumbY = ref(0)   // positive = down on screen

// Angle for scope_speed_move: 0=right, 90=up, 180=left, 270=down
const joystickAngle = computed(() => {
  if (thumbX.value === 0 && thumbY.value === 0) return 0
  const rad = Math.atan2(-thumbY.value, thumbX.value)  // flip Y (screen Y inverts)
  const deg = rad * (180 / Math.PI)
  return ((deg % 360) + 360) % 360
})

// Percent: linearly mapped from drag distance to 0–cap, with dead-zone removed
const rawDist = computed(() => Math.sqrt(thumbX.value ** 2 + thumbY.value ** 2))
const joystickPercent = computed(() => {
  if (rawDist.value < DEAD_ZONE) return 0
  const travel = Math.min(rawDist.value - DEAD_ZONE, MAX_RADIUS - DEAD_ZONE)
  return Math.round((travel / (MAX_RADIUS - DEAD_ZONE)) * currentCap.value)
})
const isActive = computed(() => joystickPercent.value > 0)

// ─── Visual helpers ───────────────────────────────────────────────────────────
const thumbStyle = computed(() => ({
  width:     THUMB_SIZE + 'px',
  height:    THUMB_SIZE + 'px',
  left:      `calc(50% + ${thumbX.value}px)`,
  top:       `calc(50% + ${thumbY.value}px)`,
  transform: 'translate(-50%, -50%)',
}))

const ringStyle = (fraction) => {
  const sz = MAX_RADIUS * 2 * fraction
  return {
    width:     sz + 'px',
    height:    sz + 'px',
    left:      `calc(50% - ${sz / 2}px)`,
    top:       `calc(50% - ${sz / 2}px)`,
  }
}

// Direction arrow from angle
const DIR_ARROWS = ['→', '↗', '↑', '↖', '←', '↙', '↓', '↘']
const dirArrow = computed(() => {
  const idx = Math.round(joystickAngle.value / 45) % 8
  return DIR_ARROWS[idx]
})

// ─── Movement commands ────────────────────────────────────────────────────────
let repeatTimer = null

const doSend = () => {
  if (!isActive.value || !executionStore.connected) return
  executionStore.moveJoystick(Math.round(joystickAngle.value), joystickPercent.value, CMD_DUR)
    .catch(() => {}) // swallow errors during repeat
}

// Watch active state to start/stop repeat loop
watch(isActive, (active) => {
  if (active && !repeatTimer) {
    doSend()                                           // send immediately
    repeatTimer = setInterval(doSend, REPEAT_MS)       // then repeat
  } else if (!active) {
    clearRepeat()
  }
})

const clearRepeat = () => {
  if (repeatTimer) { clearInterval(repeatTimer); repeatTimer = null }
}

// ─── Drag handling ────────────────────────────────────────────────────────────
const isDragging = ref(false)

const getClient = (e) =>
  e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY }
             : { x: e.clientX, y: e.clientY }

const updateThumb = (e) => {
  if (!padEl.value) return
  const rect = padEl.value.getBoundingClientRect()
  const cx = rect.left + rect.width  / 2
  const cy = rect.top  + rect.height / 2
  const { x, y } = getClient(e)
  const dx = x - cx, dy = y - cy
  const dist = Math.sqrt(dx * dx + dy * dy)
  const scale = dist > MAX_RADIUS ? MAX_RADIUS / dist : 1
  thumbX.value = dx * scale
  thumbY.value = dy * scale
}

const onDrag = (e) => {
  if (!isDragging.value) return
  e.preventDefault()
  updateThumb(e)
}

const stopDrag = async () => {
  if (!isDragging.value) return
  isDragging.value = false
  clearRepeat()
  thumbX.value = 0
  thumbY.value = 0
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup',  stopDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', stopDrag)
  // Send stop so the scope doesn't coast for the remainder of the last command's dur_sec
  try { await executionStore.stopMotion() } catch { /* ignore */ }
}

const startDrag = (e) => {
  if (!executionStore.connected) return
  isDragging.value = true
  updateThumb(e)
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup',  stopDrag)
  window.addEventListener('touchmove', onDrag, { passive: false })
  window.addEventListener('touchend', stopDrag)
}

onUnmounted(() => {
  clearRepeat()
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup',  stopDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', stopDrag)
})
</script>
