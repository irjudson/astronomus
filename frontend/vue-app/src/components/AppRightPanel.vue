<template>
  <aside
    v-if="!appStore.rightPanelCollapsed"
    class="w-80 bg-tron-panel border-l border-tron-border overflow-auto"
  >
    <div class="p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Details</h2>
        <button
          @click="appStore.toggleRightPanel"
          class="p-1 hover:bg-tron-bg rounded"
        >
          ✕
        </button>
      </div>

      <div class="text-sm text-tron-text/60">
        No item selected
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
