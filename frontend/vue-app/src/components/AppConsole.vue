<template>
  <div class="flex flex-col h-full">
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-900 shrink-0">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-semibold text-gray-200">Telescope Messages</h3>
        <span class="text-xs text-gray-500">(0)</span>
      </div>
      <button
        @click="appStore.toggleConsole"
        class="text-xs text-gray-400 hover:text-gray-200 transition-colors"
      >
        {{ appStore.consoleCollapsed ? '▲ Show' : '▼ Hide' }}
      </button>
    </div>

    <!-- Console Content -->
    <div class="flex-1 overflow-auto p-4 font-mono text-xs bg-gray-950">
      <div class="text-gray-600">
        <p>System ready. Awaiting telescope connection...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
