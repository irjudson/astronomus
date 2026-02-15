<template>
  <div v-if="executionStore.currentPlan" class="space-y-3">
    <div class="text-sm text-gray-200">
      Target {{ executionStore.currentTargetIndex + 1 }} of {{ executionStore.currentPlan.targets.length }}
    </div>

    <button
      v-if="!executionStore.planExecuting"
      @click="executionStore.executePlan()"
      :disabled="!executionStore.connected"
      class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Execute Plan
    </button>

    <div v-else class="space-y-2">
      <button
        @click="executionStore.pausePlan()"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
      >
        Pause
      </button>

      <button
        @click="executionStore.stopPlan()"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-red-900 hover:bg-red-800 text-white"
      >
        Stop
      </button>
    </div>
  </div>
  <div v-else class="text-sm text-gray-500 text-center py-4">
    No plan loaded
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
</script>
