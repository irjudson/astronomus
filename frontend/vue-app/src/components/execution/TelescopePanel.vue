<template>
  <div>
    <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
      Connection & Status
    </h3>

    <!-- Connection Section -->
    <div v-if="!executionStore.connected" class="space-y-3">
      <div>
        <label class="block text-xs text-gray-500 mb-1">Telescope IP Address</label>
        <input
          v-model="telescopeIp"
          type="text"
          placeholder="192.168.2.47"
          :class="[
            'w-full px-3 py-2 bg-gray-800 border rounded-lg text-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 transition-all',
            executionStore.error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/50' : 'border-gray-700 focus:border-blue-500 focus:ring-blue-500/50'
          ]"
          @keyup.enter="connect"
        />
      </div>

      <button
        @click="connect"
        :disabled="executionStore.loading"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ executionStore.loading ? 'Connecting...' : 'Connect Telescope' }}
      </button>

      <div v-if="executionStore.error" class="p-3 bg-red-900/20 border border-red-800 rounded-lg">
        <p class="text-xs text-red-400">{{ executionStore.error }}</p>
      </div>
    </div>

    <!-- Connected State -->
    <div v-else class="space-y-3">
      <!-- Connection Info -->
      <div class="p-3 bg-green-900/20 border border-green-800 rounded-lg">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span class="text-sm font-medium text-green-400">Connected</span>
        </div>
      </div>

      <!-- Park/Unpark Toggle -->
      <button
        v-if="executionStore.hardware.trackingStatus === 'Parked'"
        @click="executionStore.unparkTelescope()"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white"
      >
        Unpark Telescope
      </button>

      <button
        v-else
        @click="parkTelescope"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
      >
        Park Telescope
      </button>

      <!-- Dew Heater Control -->
      <div class="space-y-2">
        <button
          @click="executionStore.toggleDewHeater()"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
        >
          {{ executionStore.hardware.dewHeaterStatus === 'On' ? 'Turn Off' : 'Turn On' }} Dew Heater
        </button>

        <div v-if="executionStore.hardware.dewHeaterStatus === 'On'" class="space-y-1">
          <label class="text-xs text-gray-500">Power: {{ dewHeaterPower }}%</label>
          <input
            v-model.number="dewHeaterPower"
            type="range"
            min="0"
            max="100"
            step="10"
            @change="updateDewHeaterPower"
            class="w-full"
          />
        </div>
      </div>

      <!-- Disconnect Button -->
      <button
        @click="executionStore.disconnectTelescope()"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
      >
        Disconnect
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
const telescopeIp = ref('192.168.2.47')
const dewHeaterPower = ref(50)

// Sync local power with store
watch(() => executionStore.hardware.dewHeaterPower, (newPower) => {
  dewHeaterPower.value = newPower
}, { immediate: true })

const connect = async () => {
  await executionStore.connectTelescope(telescopeIp.value)
}

const parkTelescope = async () => {
  if (!confirm('Park telescope?')) return
  await executionStore.parkTelescope()
}

const updateDewHeaterPower = async () => {
  if (executionStore.hardware.dewHeaterStatus === 'On') {
    await executionStore.setDewHeater(true, dewHeaterPower.value)
  }
}
</script>
