<template>
  <div
    :class="['bg-tron-panel border-t border-tron-border transition-all duration-300',
             consoleHeight]"
  >
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-tron-border">
      <h3 class="text-sm font-semibold">Telescope Messages</h3>
      <button
        @click="appStore.toggleConsole"
        class="text-xs hover:text-tron-accent"
      >
        {{ appStore.consoleCollapsed ? '▲ Show' : '▼ Hide' }}
      </button>
    </div>

    <!-- Console Content -->
    <div v-if="!appStore.consoleCollapsed" class="p-4 h-48 overflow-auto font-mono text-xs">
      <div class="text-tron-text/60">No messages</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const consoleHeight = computed(() =>
  appStore.consoleCollapsed ? 'h-auto' : 'h-56'
)
</script>
