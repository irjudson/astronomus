<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Focuser Control
    </h3>

    <div class="space-y-4">
      <!-- Step Size Input -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">Step Size</label>
        <input
          v-model.number="stepSize"
          type="number"
          min="10"
          max="1000"
          step="10"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all"
          :disabled="!executionStore.connected || moving"
        />
      </div>

      <!-- Movement Controls -->
      <div class="grid grid-cols-2 gap-2">
        <button
          @mousedown="startMove('out')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart="startMove('out')"
          @touchend="stopMove"
          :disabled="!executionStore.connected || moving"
          class="px-4 py-3 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ← Out
        </button>

        <button
          @mousedown="startMove('in')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart="startMove('in')"
          @touchend="stopMove"
          :disabled="!executionStore.connected || moving"
          class="px-4 py-3 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          In →
        </button>
      </div>

      <!-- Auto Focus -->
      <button
        @click="autoFocus"
        :disabled="!executionStore.connected || moving || executionStore.imaging.active"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Auto Focus
      </button>

      <!-- Factory Reset -->
      <button
        @click="factoryReset"
        :disabled="!executionStore.connected || moving"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Factory Reset Position
      </button>

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
import { ref } from 'vue'
import axios from 'axios'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

const stepSize = ref(100)
const moving = ref(false)
const statusMessage = ref('')
const statusType = ref('info')

const startMove = async (direction) => {
  if (!executionStore.connected || moving.value) return

  moving.value = true

  try {
    await axios.post('/api/telescope/features/focuser/move', {
      steps: stepSize.value,
      direction: direction
    })

    showStatus(`Moving focuser ${direction} ${stepSize.value} steps`, 'info')
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Movement failed', 'error')
    moving.value = false
  }
}

const stopMove = async () => {
  if (!moving.value) return

  try {
    await axios.post('/api/telescope/features/focuser/stop')
    showStatus('Focuser stopped', 'info')
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Failed to stop', 'error')
  } finally {
    moving.value = false
  }
}

const autoFocus = async () => {
  if (!executionStore.connected) return

  try {
    await axios.post('/api/telescope/features/imaging/autofocus')
    showStatus('Auto focus started...', 'info')
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Auto focus failed', 'error')
  }
}

const factoryReset = async () => {
  if (!confirm('Reset focuser to factory position?')) return

  try {
    await axios.post('/api/telescope/features/focuser/factory-reset')
    showStatus('Focuser reset to factory position', 'success')
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Reset failed', 'error')
  }
}

const showStatus = (message, type = 'info') => {
  statusMessage.value = message
  statusType.value = type

  setTimeout(() => {
    statusMessage.value = ''
  }, 3000)
}
</script>
