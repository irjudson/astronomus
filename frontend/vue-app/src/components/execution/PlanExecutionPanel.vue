<template>
  <div v-if="executionStore.currentPlan" class="space-y-3">
    <!-- Plan info -->
    <div class="p-2 bg-gray-800/60 rounded">
      <div class="text-sm font-medium text-gray-200 truncate">{{ executionStore.currentPlan.name }}</div>
      <div class="text-xs text-gray-500 mt-0.5">
        {{ executionStore.currentPlan.targets.length }} targets
        <span v-if="executionStore.executionStatus !== 'idle'">
          · target {{ executionStore.currentTargetIndex + 1 }} of {{ executionStore.currentPlan.targets.length }}
        </span>
      </div>
      <!-- Progress bar when running -->
      <div v-if="executionStore.executionStatus !== 'idle'" class="mt-2 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full bg-blue-500 transition-all"
          :style="{ width: executionStore.progressPercent + '%' }"
        />
      </div>
    </div>

    <!-- Status badge -->
    <div class="flex items-center gap-2 flex-wrap">
      <span
        class="px-2 py-0.5 rounded text-xs font-medium"
        :class="{
          'bg-gray-700 text-gray-400': executionStore.executionStatus === 'idle',
          'bg-blue-900/50 text-blue-300': executionStore.executionStatus === 'running',
          'bg-yellow-900/50 text-yellow-300': executionStore.executionStatus === 'paused',
          'bg-green-900/50 text-green-300': executionStore.executionStatus === 'completed',
        }"
      >{{ executionStore.executionStatus }}</span>
      <span v-if="executionStore.currentTarget" class="text-xs text-gray-400 truncate">
        {{ executionStore.currentTarget.name }}
      </span>
      <!-- Imaging mode badge -->
      <span
        v-if="executionStore.currentTarget?.imaging_mode"
        class="px-1.5 py-0.5 rounded text-xs font-medium"
        :class="executionStore.currentTarget.imaging_mode === 'planetary'
          ? 'bg-purple-900/50 text-purple-300'
          : 'bg-teal-900/50 text-teal-300'"
      >
        {{ executionStore.currentTarget.imaging_mode === 'planetary' ? 'Video' : 'Stack' }}
      </span>
    </div>

    <!-- Connect reminder -->
    <div
      v-if="!executionStore.connected && executionStore.executionStatus === 'idle'"
      class="text-xs text-blue-400 bg-blue-900/20 border border-blue-800/50 rounded px-2 py-1.5"
    >
      Connect telescope (above) to execute
    </div>

    <!-- Controls -->
    <div class="space-y-2">
      <button
        v-if="executionStore.executionStatus === 'idle' || executionStore.executionStatus === 'completed'"
        @click="executionStore.executePlan()"
        :disabled="!executionStore.connected"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm"
      >
        Execute Plan
      </button>

      <button
        v-if="executionStore.executionStatus === 'paused'"
        @click="executionStore.resumeExecution()"
        :disabled="!executionStore.connected"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed text-sm"
      >
        Resume
      </button>

      <div v-if="executionStore.executionStatus === 'running'" class="flex gap-2">
        <button
          @click="executionStore.pausePlan()"
          class="flex-1 px-3 py-2 rounded font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600 text-sm"
        >
          Pause
        </button>
        <button
          @click="executionStore.stopPlan()"
          class="flex-1 px-3 py-2 rounded font-medium transition-colors bg-red-900 hover:bg-red-800 text-white text-sm"
        >
          Stop
        </button>
      </div>

      <button
        v-if="executionStore.executionStatus !== 'idle'"
        @click="executionStore.stopPlan()"
        class="w-full px-3 py-1.5 rounded text-xs text-gray-500 hover:text-red-400 transition-colors"
      >
        Clear plan
      </button>
    </div>
  </div>

  <div v-else class="text-sm text-gray-500 text-center py-3">
    No plan loaded — browse saved plans below
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
</script>
