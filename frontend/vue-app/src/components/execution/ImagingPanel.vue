<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Imaging Controls
    </h3>

    <div class="space-y-4">
      <!-- Imaging Mode -->
      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Imaging Mode
        </label>
        <select
          v-model="imagingMode"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="deep-sky">Deep Sky</option>
          <option value="planetary">Planetary</option>
          <option value="landscape">Landscape / Scenery</option>
        </select>
      </div>

      <!-- Planetary Imaging Controls -->
      <div v-if="imagingMode === 'planetary'" class="space-y-3 p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
        <div class="flex gap-2">
          <button
            @click="scanPlanets"
            :disabled="!executionStore.connected"
            class="flex-1 px-3 py-2 rounded text-sm font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Scan for Planets
          </button>
        </div>

        <div v-if="executionStore.imaging.availablePlanets.length > 0">
          <label class="text-xs text-gray-500 mb-1 block">
            Select Planet
          </label>
          <select
            v-model="selectedPlanet"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Choose Planet --</option>
            <option v-for="planet in executionStore.imaging.availablePlanets" :key="planet" :value="planet">
              {{ planet }}
            </option>
          </select>
        </div>

        <div>
          <label class="text-xs text-gray-500 mb-1 block">
            Exposure (ms)
          </label>
          <input
            type="number"
            v-model="planetaryExposure"
            min="1"
            step="1"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="text-xs text-gray-500 mb-1 block">
            Gain
          </label>
          <input
            type="number"
            v-model="planetaryGain"
            min="0"
            max="200"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <!-- Landscape Controls -->
      <div v-else-if="imagingMode === 'landscape'" class="space-y-3 p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">
            Brightness: {{ landscapeBrightness }}%
          </label>
          <input
            type="range"
            v-model.number="landscapeBrightness"
            min="0"
            max="100"
            step="10"
            class="w-full accent-blue-500"
          />
        </div>
      </div>

      <!-- Deep Sky Controls -->
      <div v-else-if="imagingMode === 'deep-sky'" class="space-y-3">
        <div>
          <label class="text-xs text-gray-500 mb-1 block">
            Exposure Time (s)
          </label>
          <input
            type="number"
            :value="executionStore.imaging.currentExposure"
            @input="updateExposure"
            min="0.1"
            step="0.1"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Gain
        </label>
        <input
          type="number"
          :value="gainValue"
          @input="updateGain"
          min="0"
          max="200"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Frame Count
        </label>
        <input
          type="number"
          :value="frameCountValue"
          @input="updateFrameCount"
          min="1"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

        <div class="flex items-center gap-2">
          <input
            type="checkbox"
            id="enable-dithering"
            v-model="ditheringEnabled"
            class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500"
          />
          <label for="enable-dithering" class="text-xs text-gray-200 cursor-pointer">
            Enable Dithering
          </label>
        </div>
      </div>

      <!-- Annotation Toggle -->
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          id="enable-annotations"
          v-model="annotationsEnabled"
          @change="toggleAnnotations"
          :disabled="!executionStore.connected"
          class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500"
        />
        <label for="enable-annotations" class="text-xs text-gray-200 cursor-pointer">
          Enable Annotations
        </label>
      </div>

      <!-- Control Buttons -->
      <div class="space-y-2">
        <!-- Planetary Imaging -->
        <template v-if="imagingMode === 'planetary'">
          <button
            v-if="!executionStore.imaging.active"
            @click="startPlanetaryImaging"
            :disabled="!executionStore.connected || !selectedPlanet"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Planetary Imaging
          </button>

          <button
            v-else
            @click="stopPlanetaryImaging"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
          >
            Stop Planetary Imaging
          </button>
        </template>

        <!-- Landscape Imaging -->
        <template v-else-if="imagingMode === 'landscape'">
          <button
            v-if="!executionStore.imaging.active || executionStore.imaging.mode !== 'landscape'"
            @click="startLandscapeImaging"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Landscape View
          </button>

          <button
            v-else
            @click="stopLandscapeImaging"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
          >
            Stop Landscape View
          </button>
        </template>

        <!-- Deep Sky Imaging -->
        <template v-else>
          <button
            v-if="!executionStore.imaging.active"
            @click="startImaging"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Imaging
          </button>

          <button
            v-else
            @click="stopImaging"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
          >
            Stop Imaging
          </button>
        </template>

        <!-- Recording Button -->
        <button
          v-if="!executionStore.recording.active"
          @click="startRecording"
          :disabled="!executionStore.connected"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <span class="w-3 h-3 rounded-full bg-white"></span>
          Start Recording
        </button>

        <button
          v-else
          @click="stopRecording"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white flex items-center justify-center gap-2"
        >
          <span class="w-3 h-3 rounded-full bg-white animate-pulse"></span>
          Stop Recording
        </button>

        <button
          @click="autoFocus"
          :disabled="!executionStore.connected || executionStore.imaging.active"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-white border border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Auto Focus
        </button>
      </div>

      <!-- Imaging Progress -->
      <div v-if="executionStore.imaging.active" class="p-3 bg-blue-900/20 border border-blue-800 rounded-lg">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-gray-400">Imaging in progress</span>
          <span class="text-xs font-medium text-blue-400">
            {{ executionStore.imaging.framesCaptured }} / {{ frameCountValue }}
          </span>
        </div>
        <div class="w-full bg-gray-800 rounded-full h-1.5">
          <div
            class="bg-blue-500 h-1.5 rounded-full transition-all"
            :style="{ width: imagingProgress + '%' }"
          ></div>
        </div>
      </div>

      <!-- Recording Indicator -->
      <div v-if="executionStore.recording.active" class="p-3 bg-red-900/20 border border-red-800 rounded-lg">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
          <span class="text-xs text-red-400 font-medium">Recording in progress</span>
        </div>
      </div>

      <!-- Status Message -->
      <div v-if="statusMessage" :class="[
        'p-3 rounded-lg text-sm',
        statusType === 'error' ? 'bg-red-900/20 border border-red-800 text-red-400' :
        statusType === 'success' ? 'bg-green-900/20 border border-green-800 text-green-400' :
        'bg-blue-900/20 border border-blue-800 text-blue-400'
      ]">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

const imagingMode = ref('deep-sky')
const selectedPlanet = ref('')
const planetaryExposure = ref(10)
const planetaryGain = ref(80)
const landscapeBrightness = ref(50)
const annotationsEnabled = ref(false)
const gainValue = ref(80)
const frameCountValue = ref(50)
const ditheringEnabled = ref(false)
const statusMessage = ref('')
const statusType = ref('info')

const imagingProgress = computed(() => {
  if (!executionStore.imaging.active || frameCountValue.value === 0) return 0
  return Math.round((executionStore.imaging.framesCaptured / frameCountValue.value) * 100)
})

const updateExposure = (value) => {
  executionStore.imaging.currentExposure = value
}

const updateGain = (value) => {
  gainValue.value = value
}

const updateFrameCount = (value) => {
  frameCountValue.value = value
}

const startImaging = async () => {
  try {
    await executionStore.startImaging({
      exposure: executionStore.imaging.currentExposure,
      gain: gainValue.value,
      frames: frameCountValue.value
    })
    showStatus(`Started imaging: ${frameCountValue.value} frames @ ${executionStore.imaging.currentExposure}s`, 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to start imaging', 'error')
  }
}

const stopImaging = async () => {
  try {
    await executionStore.stopImaging()
    showStatus('Imaging stopped', 'info')
  } catch (err) {
    showStatus(err.message || 'Failed to stop imaging', 'error')
  }
}

const startRecording = async () => {
  try {
    const filename = `recording_${new Date().toISOString().replace(/[:.]/g, '-')}`
    await executionStore.startRecording(filename)
    showStatus(`Started recording: ${filename}`, 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to start recording', 'error')
  }
}

const stopRecording = async () => {
  try {
    await executionStore.stopRecording()
    showStatus('Recording stopped', 'info')
  } catch (err) {
    showStatus(err.message || 'Failed to stop recording', 'error')
  }
}

const autoFocus = async () => {
  try {
    await executionStore.autoFocus()
    showStatus('Auto focus started...', 'info')
  } catch (err) {
    showStatus(err.message || 'Auto focus failed', 'error')
  }
}

const scanPlanets = async () => {
  try {
    await executionStore.scanPlanets()
    showStatus(`Found ${executionStore.imaging.availablePlanets.length} planets`, 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to scan planets', 'error')
  }
}

const startPlanetaryImaging = async () => {
  try {
    await executionStore.startPlanetaryImaging({
      planet: selectedPlanet.value,
      exposure: planetaryExposure.value,
      gain: planetaryGain.value
    })
    showStatus(`Started planetary imaging: ${selectedPlanet.value}`, 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to start planetary imaging', 'error')
  }
}

const stopPlanetaryImaging = async () => {
  try {
    await executionStore.stopPlanetaryImaging()
    showStatus('Planetary imaging stopped', 'info')
  } catch (err) {
    showStatus(err.message || 'Failed to stop planetary imaging', 'error')
  }
}

const toggleAnnotations = async () => {
  try {
    await executionStore.toggleAnnotations(annotationsEnabled.value)
    showStatus(`Annotations ${annotationsEnabled.value ? 'enabled' : 'disabled'}`, 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to toggle annotations', 'error')
    annotationsEnabled.value = !annotationsEnabled.value // Revert on error
  }
}

const startLandscapeImaging = async () => {
  try {
    await executionStore.startLandscapeImaging(landscapeBrightness.value)
    showStatus('Landscape view started', 'success')
  } catch (err) {
    showStatus(err.message || 'Failed to start landscape view', 'error')
  }
}

const stopLandscapeImaging = async () => {
  try {
    await executionStore.stopLandscapeImaging()
    showStatus('Landscape view stopped', 'info')
  } catch (err) {
    showStatus(err.message || 'Failed to stop landscape view', 'error')
  }
}

const showStatus = (message, type = 'info') => {
  statusMessage.value = message
  statusType.value = type

  setTimeout(() => {
    statusMessage.value = ''
  }, 5000)
}
</script>
