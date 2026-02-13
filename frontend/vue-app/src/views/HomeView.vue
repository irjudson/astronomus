<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Weather Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Weather Forecast</h2>
        <p class="text-sm text-tron-text/60">Loading weather data...</p>
      </div>

      <!-- Telescope Status Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Telescope Status</h2>
        <p class="text-sm text-tron-text/60">{{ telescopeStore.statusText }}</p>
      </div>

      <!-- Next Observation Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Next Observation</h2>
        <p class="text-sm text-tron-text/60">No plans scheduled</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()
</script>
