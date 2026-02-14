<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
    <h3 class="text-sm font-semibold text-gray-500 mb-3">
      HARDWARE STATUS
    </h3>

    <div class="space-y-3">
      <div class="flex justify-between items-center">
        <span class="text-xs text-gray-500">Temperature:</span>
        <span class="text-sm text-gray-200 font-mono">
          {{ executionStore.hardware.sensorTemp !== null ? executionStore.hardware.sensorTemp + '°C' : '--' }}
        </span>
      </div>

      <div class="flex justify-between items-center">
        <span class="text-xs text-gray-500">Dew Heater:</span>
        <span class="text-sm text-gray-200 font-mono">
          {{ executionStore.hardware.dewHeaterStatus }}
        </span>
      </div>

      <div class="flex justify-between items-center">
        <span class="text-xs text-gray-500">Tracking:</span>
        <span class="text-sm text-gray-200 font-mono">
          {{ executionStore.hardware.trackingStatus }}
        </span>
      </div>

      <div class="pt-2 border-t border-gray-800 space-y-2">
        <button
          @click="executionStore.toggleDewHeater()"
          :disabled="!executionStore.connected"
          class="w-full px-4 py-2 rounded font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Toggle Dew Heater
        </button>

        <div class="grid grid-cols-2 gap-2">
          <button
            @click="executionStore.unparkTelescope()"
            :disabled="!executionStore.connected || executionStore.hardware.trackingStatus !== 'Parked'"
            class="px-3 py-1.5 rounded font-medium transition-colors text-sm bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Unpark
          </button>

          <button
            @click="executionStore.parkTelescope()"
            :disabled="!executionStore.connected || executionStore.hardware.trackingStatus === 'Parked'"
            class="px-3 py-1.5 rounded font-medium transition-colors text-sm bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Park
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
</script>
