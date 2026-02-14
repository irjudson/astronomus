<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-500 mb-3">
      TELESCOPE CONNECTION
    </h3>

    <div v-if="!executionStore.connected" class="space-y-3">
      <div class="relative">
        <input
          v-model="telescopeIp"
          type="text"
          placeholder="192.168.1.100"
          :class="[
            'w-full px-3 py-2 bg-gray-800 border rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
            executionStore.error ? 'border-red-500 focus:border-red-500' : 'border-gray-700 focus:border-blue-500'
          ]"
        />
      </div>

      <button
        @click="connect"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Connect
      </button>

      <div v-if="executionStore.error" class="text-xs text-red-500">
        {{ executionStore.error }}
      </div>
    </div>

    <div v-else class="space-y-3">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 bg-green-500 rounded-full"></span>
        <span class="text-sm text-gray-200">Connected to {{ executionStore.telescopeIp }}</span>
      </div>

      <button
        @click="executionStore.disconnectTelescope()"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
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
const telescopeIp = ref('192.168.1.100')

const connect = async () => {
  await executionStore.connectTelescope(telescopeIp.value)
}
</script>
