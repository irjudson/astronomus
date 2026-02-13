<template>
  <div class="flex flex-col h-full">
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-900 shrink-0 border-b border-gray-800">
      <div class="flex items-center gap-2">
        <TerminalIcon class="w-4 h-4 text-gray-500" />
        <h3 class="text-sm font-semibold text-gray-200">Telescope Messages</h3>
        <span class="text-xs text-gray-500">(0)</span>
      </div>
      <button
        @click="appStore.toggleConsole"
        class="text-xs text-gray-400 hover:text-gray-200 transition-colors px-2 py-1 rounded hover:bg-gray-800"
      >
        {{ appStore.consoleCollapsed ? 'Show' : 'Hide' }}
      </button>
    </div>

    <!-- Console Content -->
    <div class="flex-1 overflow-auto p-4 font-mono text-xs bg-gray-950">
      <div class="text-gray-600 space-y-1">
        <p><span class="text-gray-500">[00:00:00]</span> System ready. Awaiting telescope connection...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { TerminalIcon } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
