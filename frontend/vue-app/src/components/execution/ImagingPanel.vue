<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Imaging Controls
    </h3>

    <div class="space-y-4">
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

      <!-- Control Buttons -->
      <div class="space-y-2">
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

const autoFocus = async () => {
  try {
    await executionStore.autoFocus()
    showStatus('Auto focus started...', 'info')
  } catch (err) {
    showStatus(err.message || 'Auto focus failed', 'error')
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
