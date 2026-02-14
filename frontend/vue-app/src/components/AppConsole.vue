<template>
  <div class="flex flex-col h-full">
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 bg-astro-elevated shrink-0 border-b border-astro-border">
      <div class="flex items-center gap-2">
        <TerminalIcon class="w-4 h-4 text-astro-text-muted" />
        <h3 class="text-sm font-semibold text-astro-text">Telescope Messages</h3>
        <span class="text-xs text-astro-text-muted">(0)</span>
      </div>
      <button
        @click="appStore.toggleConsole"
        class="text-xs text-astro-text-muted hover:text-astro-text transition-colors px-2 py-1 rounded hover:bg-astro-surface"
      >
        {{ appStore.consoleCollapsed ? 'Show' : 'Hide' }}
      </button>
    </div>

    <!-- Console Content -->
    <div class="flex-1 overflow-auto p-4 font-mono text-xs bg-astro-background">
      <div class="text-astro-text-dim space-y-1">
        <p><span class="text-astro-text-muted">[00:00:00]</span> System ready. Awaiting telescope connection...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { TerminalIcon } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
