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
      <div class="space-y-2 pt-2 border-t border-gray-700">
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Dew Heater
        </h4>

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

      <!-- Object Tracking Section -->
      <div class="space-y-2 pt-2 border-t border-gray-700">
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Object Tracking
        </h4>

        <div v-if="!executionStore.tracking.active">
          <!-- Object Type Selector -->
          <div class="mb-2">
            <label class="block text-xs text-gray-500 mb-1">Object Type</label>
            <select
              v-model="objectType"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 text-sm focus:outline-none focus:ring-2 focus:border-blue-500 focus:ring-blue-500/50 transition-all"
            >
              <option value="satellite">Satellite</option>
              <option value="comet">Comet</option>
              <option value="asteroid">Asteroid</option>
            </select>
          </div>

          <!-- Object ID Input -->
          <div class="mb-2">
            <label class="block text-xs text-gray-500 mb-1">Object ID</label>
            <input
              v-model="objectId"
              type="text"
              :placeholder="getPlaceholder(objectType)"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:border-blue-500 focus:ring-blue-500/50 transition-all"
              @keyup.enter="startTracking"
            />
          </div>

          <!-- Start Tracking Button -->
          <button
            @click="startTracking"
            :disabled="!objectId.trim()"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Tracking
          </button>
        </div>

        <div v-else>
          <!-- Active Tracking Info -->
          <div class="p-3 bg-purple-900/20 border border-purple-800 rounded-lg mb-2">
            <div class="flex items-center gap-2 mb-1">
              <span class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
              <span class="text-sm font-medium text-purple-400">Tracking Active</span>
            </div>
            <p class="text-xs text-gray-400">
              {{ executionStore.tracking.objectType }}: {{ executionStore.tracking.objectId }}
            </p>
          </div>

          <!-- Stop Tracking Button -->
          <button
            @click="stopTracking"
            class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
          >
            Stop Tracking
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
const telescopeIp = ref('192.168.2.47')
const dewHeaterPower = ref(50)

// Object tracking fields
const objectType = ref('satellite')
const objectId = ref('')

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

const getPlaceholder = (type) => {
  const placeholders = {
    satellite: 'ISS, STARLINK-1234, etc.',
    comet: '1P/Halley, C/2023 A3, etc.',
    asteroid: '433 Eros, 2024 AB1, etc.'
  }
  return placeholders[type] || 'Enter object identifier'
}

const startTracking = async () => {
  if (!objectId.value.trim()) return
  await executionStore.startTracking(objectType.value, objectId.value)
  // Keep the values in the form for easy reference
}

const stopTracking = async () => {
  await executionStore.stopTracking()
  // Clear the form after stopping
  objectId.value = ''
}
</script>
