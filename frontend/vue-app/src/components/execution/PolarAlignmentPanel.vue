<template>
  <div class="space-y-4">
    <!-- Status Display -->
    <div class="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-400">Status</span>
        <div class="flex items-center gap-2">
          <div
            class="w-2 h-2 rounded-full"
            :class="{
              'bg-green-500 animate-pulse': executionStore.polarAlignment.status === 'active',
              'bg-yellow-500': executionStore.polarAlignment.status === 'paused',
              'bg-gray-500': executionStore.polarAlignment.status === 'idle'
            }"
          ></div>
          <span
            class="text-sm font-mono"
            :class="{
              'text-green-400': executionStore.polarAlignment.status === 'active',
              'text-yellow-400': executionStore.polarAlignment.status === 'paused',
              'text-gray-400': executionStore.polarAlignment.status === 'idle'
            }"
          >
            {{ executionStore.polarAlignment.status.charAt(0).toUpperCase() + executionStore.polarAlignment.status.slice(1) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Control Buttons -->
    <div class="space-y-2">
      <!-- Start Button -->
      <button
        @click="handleStart"
        :disabled="!executionStore.connected || executionStore.polarAlignment.status === 'active'"
        class="w-full px-4 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :class="executionStore.polarAlignment.status === 'active' 
          ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-500 text-white'"
      >
        <div class="flex items-center justify-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Start Alignment</span>
        </div>
      </button>

      <!-- Pause Button -->
      <button
        @click="handlePause"
        :disabled="!executionStore.connected || executionStore.polarAlignment.status !== 'active'"
        class="w-full px-4 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :class="executionStore.polarAlignment.status === 'active'
          ? 'bg-yellow-600 hover:bg-yellow-500 text-white'
          : 'bg-gray-700 text-gray-400 cursor-not-allowed'"
      >
        <div class="flex items-center justify-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Pause</span>
        </div>
      </button>

      <!-- Stop Button -->
      <button
        @click="handleStop"
        :disabled="!executionStore.connected || executionStore.polarAlignment.status === 'idle'"
        class="w-full px-4 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :class="executionStore.polarAlignment.status !== 'idle'
          ? 'bg-red-600 hover:bg-red-500 text-white'
          : 'bg-gray-700 text-gray-400 cursor-not-allowed'"
      >
        <div class="flex items-center justify-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
          <span>Stop</span>
        </div>
      </button>
    </div>

    <!-- Info/Instructions -->
    <div class="bg-blue-900/20 border border-blue-800 rounded-lg p-3">
      <p class="text-xs text-blue-300">
        Start polar alignment to begin the automated alignment process. The telescope will guide you through the necessary adjustments.
      </p>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

const handleStart = async () => {
  try {
    await executionStore.startPolarAlign()
  } catch (err) {
    console.error('Failed to start polar alignment:', err)
  }
}

const handlePause = async () => {
  try {
    await executionStore.pausePolarAlign()
  } catch (err) {
    console.error('Failed to pause polar alignment:', err)
  }
}

const handleStop = async () => {
  try {
    await executionStore.stopPolarAlign()
  } catch (err) {
    console.error('Failed to stop polar alignment:', err)
  }
}
</script>
