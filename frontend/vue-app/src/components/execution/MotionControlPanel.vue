<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Motion Control
    </h3>

    <div class="space-y-4">
      <!-- Goto Target Inputs -->
      <div class="space-y-3">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Target Name</label>
          <input
            v-model="targetName"
            type="text"
            placeholder="M31"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all"
            :disabled="!executionStore.connected"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">RA (hours)</label>
            <input
              v-model="targetRA"
              type="text"
              placeholder="00:42:44"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm font-mono focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all"
              :disabled="!executionStore.connected"
            />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Dec (degrees)</label>
            <input
              v-model="targetDec"
              type="text"
              placeholder="+41:16:09"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm font-mono focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition-all"
              :disabled="!executionStore.connected"
            />
          </div>
        </div>
      </div>

      <!-- Control Buttons -->
      <div class="grid grid-cols-2 gap-2">
        <button
          @click="slewToTarget"
          :disabled="!canSlew"
          class="px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Slew to Target
        </button>

        <button
          @click="stopMotion"
          :disabled="!executionStore.connected"
          class="px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Stop
        </button>
      </div>

      <button
        @click="parkTelescope"
        :disabled="!executionStore.connected"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-white border border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Park Telescope
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
import { ref, computed } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

const targetName = ref('')
const targetRA = ref('')
const targetDec = ref('')
const statusMessage = ref('')
const statusType = ref('info')

const canSlew = computed(() => {
  return executionStore.connected && targetRA.value && targetDec.value
})

const slewToTarget = async () => {
  if (!canSlew.value) return

  try {
    await executionStore.slewToTarget({
      name: targetName.value || 'Target',
      ra: targetRA.value,
      dec: targetDec.value
    })

    showStatus(`Slewing to ${targetName.value || 'target'}...`, 'info')
  } catch (err) {
    showStatus(err.message, 'error')
  }
}

const stopMotion = async () => {
  try {
    await executionStore.stopMotion()
    showStatus('Motion stopped', 'info')
  } catch (err) {
    showStatus(err.message, 'error')
  }
}

const parkTelescope = async () => {
  if (!confirm('Park telescope?')) return

  try {
    await executionStore.parkTelescope()
    showStatus('Parking telescope...', 'info')
  } catch (err) {
    showStatus(err.message, 'error')
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
