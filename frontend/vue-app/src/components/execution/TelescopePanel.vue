<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
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
    <div v-else class="space-y-4">
      <!-- Connection Info -->
      <div class="p-3 bg-green-900/20 border border-green-800 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span class="text-sm font-medium text-green-400">Connected</span>
        </div>
        <div class="text-xs text-gray-400">
          {{ executionStore.telescopeIp }}
        </div>
      </div>

      <!-- Position Display -->
      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 bg-gray-800 rounded-lg">
          <div class="text-xs text-gray-500 mb-1">RA</div>
          <div class="text-sm font-mono text-gray-200">
            {{ formatRA(executionStore.position.ra) }}
          </div>
        </div>
        <div class="p-3 bg-gray-800 rounded-lg">
          <div class="text-xs text-gray-500 mb-1">Dec</div>
          <div class="text-sm font-mono text-gray-200">
            {{ formatDec(executionStore.position.dec) }}
          </div>
        </div>
        <div class="p-3 bg-gray-800 rounded-lg">
          <div class="text-xs text-gray-500 mb-1">Alt</div>
          <div class="text-sm font-mono text-gray-200">
            {{ executionStore.position.alt.toFixed(1) }}°
          </div>
        </div>
        <div class="p-3 bg-gray-800 rounded-lg">
          <div class="text-xs text-gray-500 mb-1">Az</div>
          <div class="text-sm font-mono text-gray-200">
            {{ executionStore.position.az.toFixed(1) }}°
          </div>
        </div>
      </div>

      <!-- Tracking Status -->
      <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
        <span class="text-sm text-gray-400">Tracking</span>
        <span :class="[
          'text-sm font-medium',
          executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400' : 'text-gray-500'
        ]">
          {{ executionStore.hardware.trackingStatus }}
        </span>
      </div>

      <!-- Current Target -->
      <div v-if="executionStore.currentTarget" class="p-3 bg-blue-900/20 border border-blue-800 rounded-lg">
        <div class="text-xs text-gray-500 mb-1">Current Target</div>
        <div class="text-sm font-medium text-blue-400">
          {{ executionStore.currentTarget.name }}
        </div>
      </div>

      <!-- Disconnect Button -->
      <button
        @click="executionStore.disconnectTelescope()"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
      >
        Disconnect
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
const telescopeIp = ref('192.168.2.47')

const connect = async () => {
  await executionStore.connectTelescope(telescopeIp.value)
}

const formatRA = (ra) => {
  const hours = ra / 15
  const h = Math.floor(hours)
  const m = Math.floor((hours - h) * 60)
  const s = Math.floor(((hours - h) * 60 - m) * 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const formatDec = (dec) => {
  const sign = dec >= 0 ? '+' : '-'
  const absDec = Math.abs(dec)
  const d = Math.floor(absDec)
  const m = Math.floor((absDec - d) * 60)
  const s = Math.floor(((absDec - d) * 60 - m) * 60)
  return `${sign}${d.toString().padStart(2, '0')}°${m.toString().padStart(2, '0')}'${s.toString().padStart(2, '0')}"`
}
</script>
