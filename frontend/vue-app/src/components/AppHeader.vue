<template>
  <header class="h-14 bg-tron-panel border-b border-tron-border flex items-center px-4 gap-4">
    <!-- Logo/Title -->
    <div class="flex items-center gap-2">
      <span class="text-2xl font-bold text-tron-accent">Astronomus</span>
    </div>

    <!-- Search Bar -->
    <div class="flex-1 max-w-md">
      <input
        type="search"
        placeholder="Search targets..."
        class="w-full px-3 py-1.5 bg-tron-bg border border-tron-border rounded text-sm focus:outline-none focus:border-tron-accent"
      />
    </div>

    <!-- Status Items -->
    <div class="flex items-center gap-4">
      <!-- Weather Status -->
      <div class="flex items-center gap-2 text-sm">
        <span>🌤️</span>
        <span>Loading...</span>
      </div>

      <!-- Connection Status -->
      <div class="flex items-center gap-2 text-sm">
        <span :class="connectionStatusClass">●</span>
        <span>{{ telescopeStore.statusText }}</span>
      </div>

      <!-- Settings Icon -->
      <button class="p-2 hover:bg-tron-bg rounded">
        ⚙️
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()

const connectionStatusClass = computed(() => ({
  'text-green-500': telescopeStore.connected,
  'text-red-500': !telescopeStore.connected
}))
</script>
