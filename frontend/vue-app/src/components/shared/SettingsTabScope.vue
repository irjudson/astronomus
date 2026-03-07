<template>
  <div class="flex-1 overflow-y-auto p-6 space-y-6">

    <!-- Leveling -->
    <section>
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Leveling</h3>
      <div class="bg-gray-800 rounded-lg p-4 space-y-4">
        <div v-if="!levelingActive" class="flex flex-col items-center gap-3 py-2">
          <div v-if="hasBalanceData" class="flex items-center gap-2 text-sm w-full justify-center">
            <span class="w-2 h-2 rounded-full flex-shrink-0" :class="levelStatusDot"></span>
            <span :class="levelStatusText">{{ levelStatusLabel }}</span>
            <span class="text-gray-500 font-mono text-xs">({{ executionStore.balance.angle.toFixed(1) }}°)</span>
          </div>
          <p v-else class="text-sm text-gray-400 text-center">
            Activates the IMU and begins reading live tilt data from the telescope.
          </p>
          <button
            :disabled="!executionStore.connected"
            @click="handleStartLeveling"
            class="px-4 py-2 text-sm rounded-lg font-medium transition-colors"
            :class="executionStore.connected
              ? 'bg-blue-600 hover:bg-blue-500 text-white'
              : 'bg-gray-700 text-gray-600 cursor-not-allowed'"
          >
            {{ hasBalanceData ? 'Monitor Live' : 'Start Leveling' }}
          </button>
          <p v-if="!executionStore.connected" class="text-xs text-gray-500">Connect telescope to enable leveling.</p>
        </div>

        <div v-else>
          <div class="flex items-center gap-6">
            <BubbleLevel
              :x="executionStore.balance.x"
              :y="executionStore.balance.y"
              :z="executionStore.balance.z"
              :angle="executionStore.balance.angle"
              :size="80"
            />
            <div class="flex-1 space-y-2">
              <div class="text-sm text-gray-300">
                Tilt: <span class="font-mono text-white">{{ executionStore.balance.angle.toFixed(2) }}°</span>
              </div>
              <div class="flex items-center gap-2 text-sm">
                <span class="w-2 h-2 rounded-full" :class="levelStatusDot"></span>
                <span :class="levelStatusText">{{ levelStatusLabel }}</span>
              </div>
              <div class="flex gap-2 mt-2">
                <button @click="handleCalibrateImu"
                  class="px-3 py-1.5 text-xs rounded-lg transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200">
                  Calibrate IMU
                </button>
                <button @click="handleStopLeveling"
                  class="px-3 py-1.5 text-xs rounded-lg transition-colors bg-gray-700 hover:bg-gray-600 text-gray-400">
                  Stop
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Compass Calibration -->
    <section>
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Compass Calibration</h3>
      <div class="bg-gray-800 rounded-lg p-4 space-y-3">
        <div class="flex items-center gap-5">
          <CompassCalibration
            :heading="executionStore.compass.heading"
            :active="executionStore.compass.status === 'calibrating'"
            :size="120"
          />
          <div class="flex-1 space-y-3">
            <div class="flex items-center gap-2 text-sm">
              <span class="w-2 h-2 rounded-full flex-shrink-0"
                :class="executionStore.compass.status === 'calibrating' ? 'bg-blue-400 animate-pulse' : 'bg-gray-500'"></span>
              <span :class="executionStore.compass.status === 'calibrating' ? 'text-blue-300' : 'text-gray-400'">
                {{ executionStore.compass.status === 'calibrating' ? 'Calibrating…' : 'Ready' }}
              </span>
            </div>
            <div v-if="executionStore.compass.status !== 'calibrating' && executionStore.compass.heading !== null"
                 class="flex items-center gap-2 text-xs">
              <span class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                :class="headingDeltaClass === 'text-green-400' ? 'bg-green-500' : headingDeltaClass === 'text-yellow-400' ? 'bg-yellow-500' : 'bg-red-500'"></span>
              <span :class="headingDeltaClass">{{ headingGuideText }}</span>
            </div>
            <p class="text-xs text-gray-400 leading-relaxed">
              <template v-if="executionStore.compass.status === 'calibrating'">
                Slowly rotate the scope through a full 360°. Blue sectors indicate covered angles.
              </template>
              <template v-else>
                Start calibration then slowly rotate the scope 360° to cover all sectors.
              </template>
            </p>
            <button v-if="executionStore.compass.status !== 'calibrating'"
              :disabled="!executionStore.connected"
              @click="handleStartCompass"
              class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
              :class="executionStore.connected ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-700 text-gray-600 cursor-not-allowed'"
            >Start Calibration</button>
            <button v-else @click="handleStopCompass"
              class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors bg-red-700 hover:bg-red-600 text-white">
              Stop
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Polar Alignment Wizard -->
    <section>
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Polar Alignment</h3>

      <div v-if="polarStep > 0" class="flex items-center justify-center mb-4">
        <template v-for="(s, i) in [{l:'North'},{l:'Elevation'},{l:'Measure'},{l:'Results'}]" :key="i">
          <div class="flex flex-col items-center">
            <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors"
                 :class="polarStep > i+1 ? 'bg-green-700 text-green-100' : polarStep === i+1 ? 'bg-blue-600 text-white ring-2 ring-blue-400' : 'bg-gray-700 text-gray-500'">
              <span v-if="polarStep > i+1">✓</span>
              <span v-else>{{ i+1 }}</span>
            </div>
            <span class="text-xs mt-0.5 w-14 text-center leading-tight"
                  :class="polarStep === i+1 ? 'text-blue-300' : polarStep > i+1 ? 'text-green-500' : 'text-gray-600'">{{ s.l }}</span>
          </div>
          <div v-if="i < 3" class="w-5 h-px mb-4" :class="polarStep > i+1 ? 'bg-green-700' : 'bg-gray-700'"></div>
        </template>
      </div>

      <div class="bg-gray-800 rounded-lg p-4">

        <!-- Step 0 -->
        <template v-if="polarStep === 0">
          <div class="text-center py-2 space-y-2">
            <p class="text-sm text-gray-300 font-medium">Polar Alignment Wizard</p>
            <p class="text-xs text-gray-500 leading-relaxed">Guides you through pointing toward North, setting elevation to your latitude, then running the firmware measurement with live feedback.</p>
            <button :disabled="!executionStore.connected" @click="goToPolarStep(1)"
              class="mt-2 px-4 py-2 text-sm rounded-lg font-medium transition-colors"
              :class="executionStore.connected ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-700 text-gray-600 cursor-not-allowed'">
              Begin Alignment
            </button>
            <p v-if="!executionStore.connected" class="text-xs text-gray-500">Connect telescope to enable.</p>
          </div>
        </template>

        <!-- Step 1: Point toward North -->
        <template v-else-if="polarStep === 1">
          <p class="text-xs text-gray-400 mb-3 font-medium">Step 1 — Rotate scope to face North</p>
          <div class="flex items-start gap-4">
            <svg viewBox="0 0 100 100" class="w-24 h-24 flex-shrink-0">
              <circle cx="50" cy="50" r="46" fill="#111827" stroke="#374151" stroke-width="1.5"/>
              <g stroke="#374151" stroke-width="1">
                <line x1="50" y1="6" x2="50" y2="14"/>  <line x1="50" y1="86" x2="50" y2="94"/>
                <line x1="6" y1="50" x2="14" y2="50"/>  <line x1="86" y1="50" x2="94" y2="50"/>
              </g>
              <text x="50" y="15" fill="#D1FAE5" font-size="11" text-anchor="middle" font-weight="bold">N</text>
              <text x="50" y="93" fill="#6B7280" font-size="8" text-anchor="middle">S</text>
              <text x="92" y="54" fill="#6B7280" font-size="8" text-anchor="middle">E</text>
              <text x="8" y="54" fill="#6B7280" font-size="8" text-anchor="middle">W</text>
              <line x1="50" y1="50" x2="50" y2="20" stroke="#22C55E" stroke-width="2.5" stroke-linecap="round"/>
              <polygon points="50,16 46,22 54,22" fill="#22C55E"/>
              <template v-if="executionStore.compass.heading !== null">
                <line x1="50" y1="50" :x2="headingX2" :y2="headingY2" stroke="#F97316" stroke-width="2" stroke-linecap="round" stroke-dasharray="4,2"/>
                <polygon :points="headingArrow2" fill="#F97316"/>
              </template>
              <circle cx="50" cy="50" r="3" :fill="compassReady ? '#22C55E' : '#F97316'"/>
            </svg>
            <div class="flex-1 space-y-2 pt-1">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full flex-shrink-0"
                      :class="compassReady ? 'bg-green-500' : executionStore.compass.heading === null ? 'bg-gray-500' : 'bg-orange-500 animate-pulse'"></span>
                <span class="text-sm font-medium" :class="compassStatusClass">{{ compassStatusText }}</span>
              </div>
              <p class="text-xs text-gray-500 leading-tight">Green = North target<br>Orange dashed = current heading</p>
              <p v-if="executionStore.compass.heading === null" class="text-xs text-yellow-600 leading-tight">
                No compass data — calibrate compass above first.
              </p>
            </div>
          </div>
          <div class="flex gap-2 mt-3">
            <button @click="goToPolarStep(0)" class="px-3 py-1.5 text-xs rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors">Cancel</button>
            <button @click="goToPolarStep(2)" class="flex-1 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
                    :class="compassReady ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'">
              {{ compassReady ? '→ Next: Set Elevation' : 'Skip →' }}
            </button>
          </div>
        </template>

        <!-- Step 2: Tilt to latitude elevation -->
        <template v-else-if="polarStep === 2">
          <p class="text-xs text-gray-400 mb-3 font-medium">Step 2 — Tilt scope to {{ elevationTarget.toFixed(1) }}° elevation</p>
          <div class="flex items-start gap-4">
            <svg viewBox="0 0 105 80" class="w-28 h-20 flex-shrink-0">
              <line x1="5" y1="65" x2="100" y2="65" stroke="#4B5563" stroke-width="1.5"/>
              <line x1="10" :x2="elevTargetEndX" y1="65" :y2="elevTargetEndY"
                    stroke="#22C55E" stroke-width="1.5" stroke-dasharray="4,2" stroke-linecap="round"/>
              <text :x="Number(elevTargetEndX)+2" :y="Number(elevTargetEndY)-1" fill="#22C55E" font-size="7">★{{ elevationTarget.toFixed(0) }}°</text>
              <line x1="10" :x2="elevCurrentEndX" y1="65" :y2="elevCurrentEndY"
                    :stroke="elevationReady ? '#22C55E' : '#60A5FA'" stroke-width="3" stroke-linecap="round"/>
              <path :d="elevCurrentArcPath" fill="none" :stroke="elevationReady ? '#86EFAC' : '#93C5FD'" stroke-width="1"/>
              <text :x="elevCurrentLabelX" :y="elevCurrentLabelY"
                    :fill="elevationReady ? '#86EFAC' : '#93C5FD'" font-size="9" text-anchor="middle">{{ elevationCurrent.toFixed(1) }}°</text>
            </svg>
            <div class="flex-1 space-y-2 pt-1">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full flex-shrink-0"
                      :class="elevationReady ? 'bg-green-500' : elevationCurrent === 0 ? 'bg-gray-500' : 'bg-orange-500 animate-pulse'"></span>
                <span class="text-sm font-medium" :class="elevStatusClass">{{ elevStatusText }}</span>
              </div>
              <p class="text-xs text-gray-500 leading-tight">
                Green dashed = target {{ elevationTarget.toFixed(1) }}°<br>Blue solid = current angle
              </p>
            </div>
          </div>
          <div class="flex gap-2 mt-3">
            <button @click="goToPolarStep(1)" class="px-3 py-1.5 text-xs rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors">← Back</button>
            <button @click="goToPolarStep(3)" class="flex-1 px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
                    :class="elevationReady ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'">
              {{ elevationReady ? '→ Next: Run Alignment' : 'Skip →' }}
            </button>
          </div>
        </template>

        <!-- Step 3: Run measurement -->
        <template v-else-if="polarStep === 3">
          <p class="text-xs text-gray-400 mb-3 font-medium">Step 3 — Run polar alignment measurement</p>
          <template v-if="executionStore.polarAlignment.status === 'idle'">
            <p class="text-xs text-gray-400 mb-3 leading-relaxed">Scope steady and pointing at Polaris? The firmware analyzes polar axis error (30–90 seconds).</p>
            <div class="flex gap-2">
              <button @click="goToPolarStep(2)" class="px-3 py-1.5 text-xs rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors">← Back</button>
              <button @click="handlePolarStartMeasure" :disabled="!executionStore.connected"
                      class="flex-1 px-3 py-2 text-sm rounded-lg font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50">
                Start Measurement
              </button>
            </div>
          </template>
          <template v-else-if="executionStore.polarAlignment.status === 'active'">
            <div class="flex items-center gap-4">
              <PolarAlignVisual :errorArcmin="null" :active="true" :size="90" />
              <div class="flex-1 space-y-2">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  <span class="text-sm text-green-400 font-medium">Analyzing…</span>
                  <span v-if="polarElapsedSec > 0" class="text-xs text-gray-500">({{ polarElapsedSec }}s)</span>
                </div>
                <p class="text-xs text-gray-400">Hold scope steady — takes 30–90 seconds.</p>
                <div class="flex gap-2">
                  <button @click="handlePolarPause" class="px-3 py-1.5 text-xs rounded-lg bg-yellow-600 hover:bg-yellow-500 text-white transition-colors">Pause</button>
                  <button @click="handlePolarStop" class="px-3 py-1.5 text-xs rounded-lg bg-red-700 hover:bg-red-600 text-white transition-colors">Stop</button>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <p class="text-xs text-gray-400 mb-3">Measurement paused.</p>
            <div class="flex gap-2">
              <button @click="handlePolarStart" class="flex-1 px-3 py-1.5 text-xs rounded-lg font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors">Resume</button>
              <button @click="handlePolarStop" class="px-3 py-1.5 text-xs rounded-lg bg-red-700 hover:bg-red-600 text-white transition-colors">Stop</button>
            </div>
          </template>
        </template>

        <!-- Step 4: Results -->
        <template v-else-if="polarStep === 4">
          <p class="text-xs text-gray-400 mb-3 font-medium">Step 4 — Results</p>
          <div class="flex items-center gap-4">
            <PolarAlignVisual :errorArcmin="executionStore.polarAlignment.errorArcmin" :active="false" :size="110" />
            <div class="flex-1 space-y-2">
              <div v-if="executionStore.polarAlignment.errorArcmin !== null">
                <span class="text-gray-400 text-sm">Error: </span>
                <span class="font-mono font-bold text-xl" :class="polarErrorClass">{{ executionStore.polarAlignment.errorArcmin.toFixed(1) }}'</span>
                <span class="ml-2 text-xs" :class="polarErrorClass">{{ polarQualityLabel }}</span>
              </div>
              <div v-else class="text-sm text-gray-400">No measurement data received.</div>
              <p class="text-xs text-gray-400 leading-relaxed">{{ polarInstructionText }}</p>
            </div>
          </div>
          <div class="flex gap-2 mt-4">
            <button @click="goToPolarStep(1)" class="px-3 py-1.5 text-xs rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors">↺ Start Over</button>
            <button @click="handlePolarMeasureAgain" class="flex-1 px-3 py-1.5 text-xs rounded-lg font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors">Measure Again</button>
            <button @click="handlePolarDone" class="px-3 py-1.5 text-xs rounded-lg font-medium bg-green-700 hover:bg-green-600 text-white transition-colors">✓ Done</button>
          </div>
        </template>

      </div>
    </section>

    <!-- Hardware Info -->
    <section v-if="executionStore.connected">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Hardware Info</h3>
        <button @click="executionStore.fetchSystemInfo()" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">Refresh</button>
      </div>
      <div class="bg-gray-800 rounded-lg p-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <div class="text-gray-500 text-xs mb-0.5">Board Temp</div>
          <div class="text-gray-200 font-mono" :class="executionStore.hardware.isOvertemp ? 'text-red-400' : ''">
            {{ boardTempDisplay }}
            <span v-if="executionStore.hardware.isOvertemp" class="text-red-400 text-xs ml-1">⚠ Overtemp</span>
          </div>
        </div>
        <div>
          <div class="text-gray-500 text-xs mb-0.5">Battery Temp</div>
          <div class="text-gray-200 font-mono">{{ batteryTempDisplay }}</div>
        </div>
        <div>
          <div class="text-gray-500 text-xs mb-0.5">Battery</div>
          <div class="text-gray-200 font-mono">
            {{ executionStore.hardware.batteryCapacity != null ? executionStore.hardware.batteryCapacity + '%' : '--' }}
          </div>
        </div>
        <div>
          <div class="text-gray-500 text-xs mb-0.5">Charger</div>
          <div class="font-mono"
            :class="executionStore.hardware.chargerStatus === 'Full' ? 'text-green-400' : executionStore.hardware.chargerStatus ? 'text-amber-400' : 'text-gray-400'">
            {{ executionStore.hardware.chargerStatus || '--' }}
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import BubbleLevel from './BubbleLevel.vue'
import CompassCalibration from './CompassCalibration.vue'
import PolarAlignVisual from './PolarAlignVisual.vue'

const props = defineProps({
  latitude: { type: Number, default: 0 },
  temperatureUnit: { type: String, default: 'F' },
})

const executionStore = useExecutionStore()

// ── Temperature display ───────────────────────────────────────────────────────
function toDisplayTemp(celsius) {
  if (celsius == null) return '--'
  return props.temperatureUnit === 'F'
    ? Math.round(celsius * 9 / 5 + 32) + '°F'
    : celsius.toFixed(1) + '°C'
}
const boardTempDisplay = computed(() => toDisplayTemp(executionStore.hardware.sensorTemp))
const batteryTempDisplay = computed(() => toDisplayTemp(executionStore.hardware.batteryTemp))

// ── Leveling ──────────────────────────────────────────────────────────────────
const levelingActive = ref(false)
let levelingTimer = null

const hasBalanceData = computed(() =>
  executionStore.balance.x !== 0 || executionStore.balance.y !== 0 || executionStore.balance.angle !== 0
)
const levelStatusDot = computed(() => {
  const a = executionStore.balance.angle
  return a <= 2 ? 'bg-green-500' : a <= 5 ? 'bg-yellow-500' : 'bg-red-500'
})
const levelStatusText = computed(() => {
  const a = executionStore.balance.angle
  return a <= 2 ? 'text-green-400' : a <= 5 ? 'text-yellow-400' : 'text-red-400'
})
const levelStatusLabel = computed(() => {
  const a = executionStore.balance.angle
  return a <= 2 ? 'Level' : a <= 5 ? 'Almost level — adjust tripod' : 'Not level — adjust tripod'
})

const handleStartLeveling = async () => {
  try { await executionStore.startLeveling() } catch { /* firmware may return non-zero */ }
  levelingActive.value = true
  await executionStore.fetchBalance()
  levelingTimer = setInterval(() => executionStore.fetchBalance(), 500)
}
const handleStopLeveling = () => {
  clearInterval(levelingTimer); levelingTimer = null
  levelingActive.value = false
}
const handleCalibrateImu = async () => {
  try { await executionStore.calibrateGsensor() } catch { /* ignore */ }
}

// ── Compass ───────────────────────────────────────────────────────────────────
let compassTimer = null

const handleStartCompass = async () => {
  await executionStore.startCompassCalibration()
  await executionStore.fetchCompassState()
  compassTimer = setInterval(() => executionStore.fetchCompassState(), 1000)
}
const handleStopCompass = async () => {
  await executionStore.stopCompassCalibration()
  clearInterval(compassTimer); compassTimer = null
}

// ── Polar alignment wizard ────────────────────────────────────────────────────
const polarStep = ref(0)
const polarElapsedSec = ref(0)
let polarTimer = null
let polarElapsedTimer = null
let polarCompassTimer = null
let polarBalanceTimer = null

const stopPolarStepTimers = () => {
  clearInterval(polarCompassTimer); polarCompassTimer = null
  clearInterval(polarBalanceTimer); polarBalanceTimer = null
}
const startPolarElapsed = () => {
  polarElapsedSec.value = 0
  clearInterval(polarElapsedTimer)
  polarElapsedTimer = setInterval(() => polarElapsedSec.value++, 1000)
}
const stopPolarElapsed = () => { clearInterval(polarElapsedTimer); polarElapsedTimer = null }
const stopPolarPoll = () => { clearInterval(polarTimer); polarTimer = null; stopPolarElapsed() }

const goToPolarStep = (step) => {
  stopPolarStepTimers()
  polarStep.value = step
  if (!executionStore.connected) return
  if (step === 1) {
    executionStore.fetchCompassState()
    polarCompassTimer = setInterval(() => executionStore.fetchCompassState(), 1000)
  } else if (step === 2) {
    executionStore.fetchBalance()
    polarBalanceTimer = setInterval(() => executionStore.fetchBalance(), 500)
  }
}

watch(() => executionStore.polarAlignment.status, async (status) => {
  if (status === 'complete' && polarStep.value === 3) {
    clearInterval(polarTimer); polarTimer = null
    stopPolarElapsed()
    await executionStore.fetchPolarAlignStatus()
    polarStep.value = 4
  }
})

const handlePolarStartMeasure = async () => {
  try {
    await executionStore.startPolarAlign()
    startPolarElapsed()
    if (!polarTimer) polarTimer = setInterval(() => executionStore.fetchPolarAlignStatus(), 2000)
  } catch { /* ignore */ }
}
const handlePolarStart = async () => {
  try {
    await executionStore.startPolarAlign()
    startPolarElapsed()
    if (!polarTimer) polarTimer = setInterval(() => executionStore.fetchPolarAlignStatus(), 2000)
  } catch { /* ignore */ }
}
const handlePolarPause = async () => {
  try { await executionStore.pausePolarAlign(); stopPolarElapsed() } catch { /* ignore */ }
}
const handlePolarStop = async () => {
  try { await executionStore.stopPolarAlign() } catch { /* ignore */ }
  stopPolarPoll(); stopPolarStepTimers(); polarStep.value = 0
}
const handlePolarMeasureAgain = async () => {
  try { await executionStore.stopPolarAlign() } catch { /* ignore */ }
  clearInterval(polarTimer); polarTimer = null; stopPolarElapsed(); polarStep.value = 3
}
const handlePolarDone = () => { stopPolarPoll(); stopPolarStepTimers(); polarStep.value = 0 }

// ── Polar computed ─────────────────────────────────────────────────────────────
const polarErrorClass = computed(() => {
  const e = executionStore.polarAlignment.errorArcmin
  if (e === null) return 'text-gray-400'
  return e < 5 ? 'text-green-400' : e < 15 ? 'text-yellow-400' : 'text-red-400'
})
const polarQualityLabel = computed(() => {
  const e = executionStore.polarAlignment.errorArcmin
  if (e === null) return ''
  return e < 5 ? '● Excellent' : e < 15 ? '● Good' : e < 30 ? '● Fair' : '● Poor'
})
const polarInstructionText = computed(() => {
  const e = executionStore.polarAlignment.errorArcmin
  if (e !== null && e < 5) return 'Excellent alignment! No adjustment needed.'
  if (e !== null && e < 15) return "Good alignment. Fine-tune the mount's altitude and azimuth bolts slightly."
  if (e !== null) return "Significant error. Adjust the mount's altitude and azimuth bolts, then measure again."
  return 'Measurement complete.'
})

// ── Compass step SVG computed ─────────────────────────────────────────────────
const headingX2 = computed(() => {
  if (executionStore.compass.heading === null) return 50
  return (50 + 30 * Math.sin(executionStore.compass.heading * Math.PI / 180)).toFixed(1)
})
const headingY2 = computed(() => {
  if (executionStore.compass.heading === null) return 50
  return (50 - 30 * Math.cos(executionStore.compass.heading * Math.PI / 180)).toFixed(1)
})
const headingArrow2 = computed(() => {
  if (executionStore.compass.heading === null) return ''
  const h = executionStore.compass.heading * Math.PI / 180
  const sin = Math.sin(h), cos = Math.cos(h)
  const tx = (50 + 36 * sin).toFixed(1), ty = (50 - 36 * cos).toFixed(1)
  const bx = 50 + 28 * sin, by = 50 - 28 * cos
  return `${tx},${ty} ${(bx + 4*cos).toFixed(1)},${(by + 4*sin).toFixed(1)} ${(bx - 4*cos).toFixed(1)},${(by - 4*sin).toFixed(1)}`
})
const compassReady = computed(() => {
  if (executionStore.compass.heading === null) return false
  const h = executionStore.compass.heading
  return (h <= 180 ? h : 360 - h) < 15
})
const compassStatusText = computed(() => {
  if (executionStore.compass.heading === null) return 'No heading data'
  const h = executionStore.compass.heading
  const delta = h <= 180 ? h : 360 - h
  if (delta < 10) return `Facing North (${h}°) ✓`
  return `Rotate ${h <= 180 ? 'left' : 'right'} ${Math.round(delta)}° to face North`
})
const compassStatusClass = computed(() => {
  if (executionStore.compass.heading === null) return 'text-gray-400'
  if (compassReady.value) return 'text-green-400'
  const h = executionStore.compass.heading
  return (h <= 180 ? h : 360 - h) < 45 ? 'text-yellow-400' : 'text-orange-400'
})

// ── Elevation step SVG computed ───────────────────────────────────────────────
const elevationTarget = computed(() => Math.abs(props.latitude || 0))
const elevationCurrent = computed(() => executionStore.balance.angle || 0)
const elevationDelta = computed(() => elevationCurrent.value - elevationTarget.value)
const elevationReady = computed(() => Math.abs(elevationDelta.value) < 1.5)
const latRad = computed(() => elevationTarget.value * Math.PI / 180)
const elevCurrentRad = computed(() => elevationCurrent.value * Math.PI / 180)

const elevTargetEndX = computed(() => (10 + 60 * Math.cos(latRad.value)).toFixed(1))
const elevTargetEndY = computed(() => (65 - 60 * Math.sin(latRad.value)).toFixed(1))
const elevCurrentEndX = computed(() => (10 + 60 * Math.cos(elevCurrentRad.value)).toFixed(1))
const elevCurrentEndY = computed(() => (65 - 60 * Math.sin(elevCurrentRad.value)).toFixed(1))
const elevCurrentArcPath = computed(() => {
  const r = 22, ax = (10 + r * Math.cos(elevCurrentRad.value)).toFixed(1), ay = (65 - r * Math.sin(elevCurrentRad.value)).toFixed(1)
  return `M ${10 + r},65 A ${r},${r} 0 0,0 ${ax},${ay}`
})
const elevCurrentLabelX = computed(() => (10 + 32 * Math.cos(elevCurrentRad.value / 2)).toFixed(1))
const elevCurrentLabelY = computed(() => (65 - 32 * Math.sin(elevCurrentRad.value / 2) + 4).toFixed(1))
const elevStatusText = computed(() => {
  if (elevationCurrent.value === 0) return `Target: ${elevationTarget.value.toFixed(1)}°`
  if (elevationReady.value) return `Elevation set ✓ (${elevationCurrent.value.toFixed(1)}°)`
  const dir = elevationDelta.value < 0 ? 'Raise' : 'Lower'
  return `${dir} ${Math.abs(elevationDelta.value).toFixed(1)}° (${elevationCurrent.value.toFixed(1)}° → ${elevationTarget.value.toFixed(1)}°)`
})
const elevStatusClass = computed(() => {
  if (elevationReady.value) return 'text-green-400'
  if (elevationCurrent.value === 0) return 'text-gray-400'
  return Math.abs(elevationDelta.value) < 4 ? 'text-yellow-400' : 'text-orange-400'
})

// ── Compass idle-state heading indicators ─────────────────────────────────────
const headingDelta = computed(() => {
  if (executionStore.compass.heading === null) return null
  const h = executionStore.compass.heading
  return h <= 180 ? h : 360 - h
})
const headingDeltaClass = computed(() => {
  if (headingDelta.value === null) return 'text-gray-400'
  return headingDelta.value < 15 ? 'text-green-400' : headingDelta.value < 45 ? 'text-yellow-400' : 'text-red-400'
})
const headingGuideText = computed(() => {
  if (executionStore.compass.heading === null) return 'No heading — calibrate compass first'
  const h = executionStore.compass.heading, delta = headingDelta.value
  if (delta < 10) return `Facing North (${h}°) ✓`
  return `Rotate ${h <= 180 ? 'left' : 'right'} ${Math.round(delta)}° to face N (now ${h}°)`
})

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(() => {
  if (executionStore.connected) {
    executionStore.fetchBalance()
    executionStore.fetchCompassState()
  }
})

onUnmounted(() => {
  clearInterval(levelingTimer)
  clearInterval(compassTimer)
  stopPolarPoll()
  stopPolarStepTimers()
})
</script>
