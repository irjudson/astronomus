<template>
  <BaseCard padding="md">
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
        <BaseButton
          variant="secondary"
          @click="executionStore.toggleDewHeater()"
          :disabled="!executionStore.connected"
          class="w-full"
        >
          Toggle Dew Heater
        </BaseButton>

        <div class="grid grid-cols-2 gap-2">
          <BaseButton
            variant="primary"
            @click="executionStore.unparkTelescope()"
            :disabled="!executionStore.connected || executionStore.hardware.trackingStatus !== 'Parked'"
            size="sm"
          >
            Unpark
          </BaseButton>

          <BaseButton
            variant="secondary"
            @click="executionStore.parkTelescope()"
            :disabled="!executionStore.connected || executionStore.hardware.trackingStatus === 'Parked'"
            size="sm"
          >
            Park
          </BaseButton>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const executionStore = useExecutionStore()
</script>
