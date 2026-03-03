<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
    <div class="bg-gray-900 border border-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h2 class="text-lg font-semibold text-gray-200">Settings</h2>
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Tab bar -->
      <div class="flex gap-1 px-6 pt-4">
        <button
          @click="activeTab = 'general'"
          class="px-4 py-2 text-sm rounded-lg transition-colors"
          :class="activeTab === 'general' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
        >
          General
        </button>
        <button
          @click="activeTab = 'scope'"
          class="px-4 py-2 text-sm rounded-lg transition-colors"
          :class="activeTab === 'scope' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
        >
          Scope
        </button>
      </div>

      <!-- Content: General tab -->
      <div v-if="activeTab === 'general'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Observing Location -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Observing Location</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-300 mb-1">Location Name</label>
              <input
                v-model="localSettings.locationName"
                type="text"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="My Backyard Observatory"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm text-gray-300 mb-1">Latitude</label>
                <input
                  v-model.number="localSettings.latitude"
                  type="number"
                  step="0.0001"
                  class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  placeholder="40.7128"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-300 mb-1">Longitude</label>
                <input
                  v-model.number="localSettings.longitude"
                  type="number"
                  step="0.0001"
                  class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  placeholder="-74.0060"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-300 mb-1">Timezone</label>
              <input
                v-model="localSettings.timezone"
                type="text"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="America/New_York"
              />
            </div>
          </div>
        </section>

        <!-- Units -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Units</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-300 mb-2">Temperature</label>
              <div class="flex gap-2">
                <button
                  @click="localSettings.temperatureUnit = 'F'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.temperatureUnit === 'F' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Fahrenheit (°F)
                </button>
                <button
                  @click="localSettings.temperatureUnit = 'C'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.temperatureUnit === 'C' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Celsius (°C)
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-300 mb-2">Distance</label>
              <div class="flex gap-2">
                <button
                  @click="localSettings.distanceUnit = 'mi'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.distanceUnit === 'mi' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Miles
                </button>
                <button
                  @click="localSettings.distanceUnit = 'km'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.distanceUnit === 'km' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Kilometers
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Display Preferences -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Display</h3>
          <div class="space-y-3">
            <label class="flex items-center justify-between p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750 transition-colors">
              <span class="text-sm text-gray-300">Show object thumbnails</span>
              <input
                v-model="localSettings.showThumbnails"
                type="checkbox"
                class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
            </label>
            <label class="flex items-center justify-between p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750 transition-colors">
              <span class="text-sm text-gray-300">Auto-refresh catalog data</span>
              <input
                v-model="localSettings.autoRefresh"
                type="checkbox"
                class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
            </label>
          </div>
        </section>
      </div>

      <!-- Content: Scope tab -->
      <div v-else-if="activeTab === 'scope'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Leveling -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Leveling</h3>
          <div class="bg-gray-800 rounded-lg p-4 space-y-4">
            <!-- Not monitoring yet -->
            <div v-if="!levelingActive" class="flex flex-col items-center gap-3 py-2">
              <p class="text-sm text-gray-400 text-center">
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
                Start Leveling
              </button>
              <p v-if="!executionStore.connected" class="text-xs text-gray-500">
                Connect telescope to enable leveling.
              </p>
            </div>

            <!-- Active monitoring -->
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
                    <button
                      @click="handleCalibrateImu"
                      class="px-3 py-1.5 text-xs rounded-lg transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200"
                    >
                      Calibrate IMU
                    </button>
                    <button
                      @click="handleStopLeveling"
                      class="px-3 py-1.5 text-xs rounded-lg transition-colors bg-gray-700 hover:bg-gray-600 text-gray-400"
                    >
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
              <!-- Visual: compass rose with sector coverage -->
              <CompassCalibration
                :heading="executionStore.compass.heading"
                :active="executionStore.compass.status === 'calibrating'"
                :size="120"
              />

              <!-- Right: status + instruction + button -->
              <div class="flex-1 space-y-3">
                <!-- Status -->
                <div class="flex items-center gap-2 text-sm">
                  <span
                    class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="executionStore.compass.status === 'calibrating' ? 'bg-blue-400 animate-pulse' : 'bg-gray-500'"
                  ></span>
                  <span :class="executionStore.compass.status === 'calibrating' ? 'text-blue-300' : 'text-gray-400'">
                    {{ executionStore.compass.status === 'calibrating' ? 'Calibrating…' : 'Idle' }}
                  </span>
                </div>

                <!-- Instruction -->
                <p class="text-xs text-gray-400 leading-relaxed">
                  <template v-if="executionStore.compass.status === 'calibrating'">
                    Slowly rotate the scope through a full 360°. Blue sectors indicate covered angles.
                  </template>
                  <template v-else>
                    Start calibration then slowly rotate the scope 360° to cover all sectors.
                  </template>
                </p>

                <!-- Button -->
                <button
                  v-if="executionStore.compass.status !== 'calibrating'"
                  :disabled="!executionStore.connected"
                  @click="handleStartCompass"
                  class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
                  :class="executionStore.connected
                    ? 'bg-blue-600 hover:bg-blue-500 text-white'
                    : 'bg-gray-700 text-gray-600 cursor-not-allowed'"
                >
                  Start Calibration
                </button>
                <button
                  v-else
                  @click="handleStopCompass"
                  class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors bg-red-700 hover:bg-red-600 text-white"
                >
                  Stop
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Polar Alignment -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Polar Alignment</h3>
          <div class="bg-gray-800 rounded-lg p-4 space-y-3">
            <div class="flex items-center gap-5">
              <!-- Visual: bullseye quality indicator -->
              <PolarAlignVisual
                :errorArcmin="executionStore.polarAlignment.errorArcmin"
                :active="executionStore.polarAlignment.status === 'active'"
                :size="120"
              />

              <!-- Right: status + quality + guidance + controls -->
              <div class="flex-1 space-y-3">
                <!-- Status dot + label -->
                <div class="flex items-center gap-2 text-sm">
                  <span
                    class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="{
                      'bg-green-500 animate-pulse': executionStore.polarAlignment.status === 'active',
                      'bg-yellow-500': executionStore.polarAlignment.status === 'paused',
                      'bg-gray-500': executionStore.polarAlignment.status === 'idle'
                    }"
                  ></span>
                  <span :class="{
                    'text-green-400': executionStore.polarAlignment.status === 'active',
                    'text-yellow-400': executionStore.polarAlignment.status === 'paused',
                    'text-gray-400': executionStore.polarAlignment.status === 'idle'
                  }">{{ polarStatusLabel }}</span>
                </div>

                <!-- Alignment error + quality label -->
                <div v-if="executionStore.polarAlignment.errorArcmin !== null" class="text-sm">
                  <span class="text-gray-400">Error: </span>
                  <span class="font-mono" :class="polarErrorClass">
                    {{ executionStore.polarAlignment.errorArcmin.toFixed(1) }}'
                  </span>
                  <span class="ml-2 text-xs" :class="polarErrorClass">{{ polarQualityLabel }}</span>
                </div>

                <!-- Guided instruction text -->
                <p class="text-xs text-gray-400 leading-relaxed">{{ polarInstructionText }}</p>

                <!-- Controls: context-sensitive buttons -->
                <div class="flex gap-2">
                  <!-- Idle: show Start -->
                  <button
                    v-if="executionStore.polarAlignment.status === 'idle'"
                    :disabled="!executionStore.connected"
                    @click="handlePolarStart"
                    class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors"
                    :class="executionStore.connected
                      ? 'bg-blue-600 hover:bg-blue-500 text-white'
                      : 'bg-gray-700 text-gray-600 cursor-not-allowed'"
                  >
                    Start Alignment
                  </button>

                  <!-- Active or paused: Pause/Resume + Stop -->
                  <template v-else>
                    <button
                      v-if="executionStore.polarAlignment.status === 'active'"
                      @click="handlePolarPause"
                      class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors bg-yellow-600 hover:bg-yellow-500 text-white"
                    >
                      Pause
                    </button>
                    <button
                      v-else
                      @click="handlePolarStart"
                      class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-500 text-white"
                    >
                      Resume
                    </button>
                    <button
                      @click="handlePolarStop"
                      class="px-3 py-1.5 text-xs rounded-lg font-medium transition-colors bg-red-700 hover:bg-red-600 text-white"
                    >
                      Stop
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Footer (General tab only) -->
      <div v-if="activeTab === 'general'" class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveSettings"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          Save Changes
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { XIcon } from 'lucide-vue-next'
import axios from 'axios'
import { useExecutionStore } from '@/stores/execution'
import BubbleLevel from './BubbleLevel.vue'
import CompassCalibration from './CompassCalibration.vue'
import PolarAlignVisual from './PolarAlignVisual.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close', 'save'])

const executionStore = useExecutionStore()
const activeTab = ref('general')
const levelingActive = ref(false)

// Load settings from localStorage
const loadSettings = () => {
  const saved = localStorage.getItem('astronomus_settings')
  if (saved) {
    return JSON.parse(saved)
  }
  return {
    locationName: '',
    latitude: 40.7128,
    longitude: -74.0060,
    timezone: 'America/New_York',
    temperatureUnit: 'F',
    distanceUnit: 'mi',
    showThumbnails: true,
    autoRefresh: false
  }
}

const localSettings = ref(loadSettings())

// Reload settings when modal opens; reset to general tab
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    localSettings.value = loadSettings()
    activeTab.value = 'general'
  }
})

const saveSettings = () => {
  localStorage.setItem('astronomus_settings', JSON.stringify(localSettings.value))
  emit('save', localSettings.value)
  emit('close')
}

// Level status helpers
const levelStatusDot = computed(() => {
  const angle = executionStore.balance.angle
  if (angle <= 2) return 'bg-green-500'
  if (angle <= 5) return 'bg-yellow-500'
  return 'bg-red-500'
})

const levelStatusText = computed(() => {
  const angle = executionStore.balance.angle
  if (angle <= 2) return 'text-green-400'
  if (angle <= 5) return 'text-yellow-400'
  return 'text-red-400'
})

const levelStatusLabel = computed(() => {
  const angle = executionStore.balance.angle
  if (angle <= 2) return 'Level'
  if (angle <= 5) return 'Almost level — adjust tripod'
  return 'Not level — adjust tripod'
})

// ── Leveling poll ─────────────────────────────────────────────────────────────
let levelingTimer = null

const stopLevelingPoll = () => {
  clearInterval(levelingTimer)
  levelingTimer = null
  levelingActive.value = false
}

watch(activeTab, (tab) => {
  if (tab !== 'scope') {
    stopLevelingPoll()
    stopCompassPoll()
    stopPolarPoll()
  }
})
watch(() => props.isOpen, (open) => {
  if (!open) {
    stopLevelingPoll()
    stopCompassPoll()
    stopPolarPoll()
  }
})

const handleStartLeveling = async () => {
  try { await executionStore.startLeveling() } catch { /* firmware may return non-zero but still activates */ }
  levelingActive.value = true
  await executionStore.fetchBalance()
  levelingTimer = setInterval(() => executionStore.fetchBalance(), 500)
}

const handleStopLeveling = () => stopLevelingPoll()

const handleCalibrateImu = async () => {
  try { await executionStore.calibrateGsensor() } catch { /* ignore */ }
}

// ── Compass poll ───────────────────────────────────────────────────────────────
let compassTimer = null

const stopCompassPoll = () => {
  clearInterval(compassTimer)
  compassTimer = null
}

const handleStartCompass = async () => {
  await executionStore.startCompassCalibration()
  await executionStore.fetchCompassState()
  compassTimer = setInterval(() => executionStore.fetchCompassState(), 1000)
}

const handleStopCompass = async () => {
  await executionStore.stopCompassCalibration()
  stopCompassPoll()
}

// ── Polar alignment poll ───────────────────────────────────────────────────────
let polarTimer = null

const stopPolarPoll = () => {
  clearInterval(polarTimer)
  polarTimer = null
}

const handlePolarStart = async () => {
  try {
    await executionStore.startPolarAlign()
    if (!polarTimer) {
      polarTimer = setInterval(() => executionStore.fetchPolarAlignStatus(), 2000)
    }
  } catch { /* ignore */ }
}

const handlePolarPause = async () => {
  try { await executionStore.pausePolarAlign() } catch { /* ignore */ }
}

const handlePolarStop = async () => {
  try {
    await executionStore.stopPolarAlign()
    stopPolarPoll()
  } catch { /* ignore */ }
}

// ── Polar alignment helpers ────────────────────────────────────────────────────
const polarStatusLabel = computed(() => {
  const s = executionStore.polarAlignment.status
  if (s === 'active') return 'Measuring alignment…'
  if (s === 'paused') return 'Paused'
  return 'Idle'
})

const polarErrorClass = computed(() => {
  const e = executionStore.polarAlignment.errorArcmin
  if (e === null) return 'text-gray-400'
  if (e < 5)  return 'text-green-400'
  if (e < 15) return 'text-yellow-400'
  return 'text-red-400'
})

const polarQualityLabel = computed(() => {
  const e = executionStore.polarAlignment.errorArcmin
  if (e === null) return ''
  if (e < 5)  return '● Excellent'
  if (e < 15) return '● Good'
  if (e < 30) return '● Fair'
  return '● Poor'
})

const polarInstructionText = computed(() => {
  const s = executionStore.polarAlignment.status
  if (s === 'active') return "Analyzing polar axis. Adjust the mount's altitude and azimuth bolts to minimize the error shown."
  if (s === 'paused') return 'Paused — resume when ready to continue adjustments.'
  return 'Start polar alignment to measure and guide polar axis correction. Telescope must be in equatorial mode.'
})
</script>
