<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Directional Control
    </h3>

    <div class="space-y-4">
      <!-- Speed Selection -->
      <div class="flex items-center justify-center gap-2">
        <button
          @click="selectedSpeed = 'slow'"
          :class="[
            'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
            selectedSpeed === 'slow'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          ]"
          :disabled="!executionStore.connected"
        >
          Slow
        </button>
        <button
          @click="selectedSpeed = 'fast'"
          :class="[
            'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
            selectedSpeed === 'fast'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          ]"
          :disabled="!executionStore.connected"
        >
          Fast
        </button>
      </div>

      <!-- Directional Pad -->
      <div class="flex flex-col items-center gap-2">
        <!-- Up -->
        <button
          @mousedown="startMove('up')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart="startMove('up')"
          @touchend="stopMove"
          :disabled="!executionStore.connected"
          :class="[
            'w-16 h-16 rounded-lg font-bold text-lg transition-all',
            activeDirection === 'up'
              ? 'bg-blue-600 text-white scale-95'
              : 'bg-gray-700 text-gray-200 hover:bg-gray-600',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          ]"
        >
          ↑
        </button>

        <!-- Left, Center, Right -->
        <div class="flex items-center gap-2">
          <button
            @mousedown="startMove('left')"
            @mouseup="stopMove"
            @mouseleave="stopMove"
            @touchstart="startMove('left')"
            @touchend="stopMove"
            :disabled="!executionStore.connected"
            :class="[
              'w-16 h-16 rounded-lg font-bold text-lg transition-all',
              activeDirection === 'left'
                ? 'bg-blue-600 text-white scale-95'
                : 'bg-gray-700 text-gray-200 hover:bg-gray-600',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            ]"
          >
            ←
          </button>

          <!-- Center Stop Button -->
          <button
            @click="stopMove"
            :disabled="!executionStore.connected"
            class="w-16 h-16 rounded-lg font-medium text-xs bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            STOP
          </button>

          <button
            @mousedown="startMove('right')"
            @mouseup="stopMove"
            @mouseleave="stopMove"
            @touchstart="startMove('right')"
            @touchend="stopMove"
            :disabled="!executionStore.connected"
            :class="[
              'w-16 h-16 rounded-lg font-bold text-lg transition-all',
              activeDirection === 'right'
                ? 'bg-blue-600 text-white scale-95'
                : 'bg-gray-700 text-gray-200 hover:bg-gray-600',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            ]"
          >
            →
          </button>
        </div>

        <!-- Down -->
        <button
          @mousedown="startMove('down')"
          @mouseup="stopMove"
          @mouseleave="stopMove"
          @touchstart="startMove('down')"
          @touchend="stopMove"
          :disabled="!executionStore.connected"
          :class="[
            'w-16 h-16 rounded-lg font-bold text-lg transition-all',
            activeDirection === 'down'
              ? 'bg-blue-600 text-white scale-95'
              : 'bg-gray-700 text-gray-200 hover:bg-gray-600',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          ]"
        >
          ↓
        </button>
      </div>

      <!-- Status Message -->
      <div v-if="statusMessage" :class="[
        'p-3 rounded-lg text-sm text-center',
        statusType === 'error' ? 'bg-red-900/20 border border-red-800 text-red-400' :
        'bg-blue-900/20 border border-blue-800 text-blue-400'
      ]">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

const selectedSpeed = ref('slow')
const activeDirection = ref(null)
const statusMessage = ref('')
const statusType = ref('info')

const startMove = async (direction) => {
  if (!executionStore.connected || activeDirection.value) return

  activeDirection.value = direction

  try {
    await executionStore.moveDirection(direction, selectedSpeed.value)
    showStatus(`Moving ${direction} (${selectedSpeed.value})`, 'info')
  } catch (err) {
    showStatus(err.message || 'Movement failed', 'error')
    activeDirection.value = null
  }
}

const stopMove = async () => {
  if (!activeDirection.value) return

  try {
    await executionStore.stopMotion()
    showStatus('Motion stopped', 'info')
  } catch (err) {
    showStatus(err.message || 'Failed to stop', 'error')
  } finally {
    activeDirection.value = null
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
