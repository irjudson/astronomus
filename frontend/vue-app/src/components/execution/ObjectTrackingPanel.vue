<template>
  <div class="space-y-2">
    <div v-if="!executionStore.tracking.active">
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

      <div class="mb-2">
        <label class="block text-xs text-gray-500 mb-1">Object ID</label>
        <input
          v-model="objectId"
          type="text"
          :placeholder="placeholder"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:border-blue-500 focus:ring-blue-500/50 transition-all"
          @keyup.enter="startTracking"
        />
      </div>

      <button
        @click="startTracking"
        :disabled="!objectId.trim()"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Start Tracking
      </button>
    </div>

    <div v-else>
      <div class="p-3 bg-purple-900/20 border border-purple-800 rounded-lg mb-2">
        <div class="flex items-center gap-2 mb-1">
          <span class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
          <span class="text-sm font-medium text-purple-400">Tracking Active</span>
        </div>
        <p class="text-xs text-gray-400">
          {{ executionStore.tracking.objectType }}: {{ executionStore.tracking.objectId }}
        </p>
      </div>

      <button
        @click="stopTracking"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
      >
        Stop Tracking
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
const objectType = ref('satellite')
const objectId = ref('')

const placeholder = computed(() => ({
  satellite: 'ISS, STARLINK-1234, etc.',
  comet: '1P/Halley, C/2023 A3, etc.',
  asteroid: '433 Eros, 2024 AB1, etc.'
}[objectType.value] ?? 'Enter object identifier'))

const startTracking = async () => {
  if (!objectId.value.trim()) return
  await executionStore.startTracking(objectType.value, objectId.value)
}

const stopTracking = async () => {
  await executionStore.stopTracking()
  objectId.value = ''
}
</script>
