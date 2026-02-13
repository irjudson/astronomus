<template>
  <header class="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900 shrink-0 z-10">
    <!-- Left: Logo and Info -->
    <div class="flex items-center space-x-4">
      <div class="font-bold text-xl tracking-tight text-blue-500 flex items-center gap-2">
        <span>Astronomus</span>
      </div>
      <div class="text-xs text-gray-500 italic">
        {{ locationName || 'No location set' }}
      </div>
    </div>

    <!-- Center: Search -->
    <div class="flex-1 max-w-md mx-4">
      <div class="relative">
        <span class="absolute left-2.5 top-2 text-gray-500">🔍</span>
        <input
          type="text"
          placeholder="Search targets..."
          class="bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-full py-1.5 pl-9 pr-4 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500/20 outline-none w-full transition-all"
        />
      </div>
    </div>

    <!-- Right: Status and Actions -->
    <div class="flex items-center space-x-3">
      <!-- Weather Status -->
      <div class="flex items-center gap-2 text-sm text-gray-400">
        <span>🌤️</span>
        <span>Clear</span>
      </div>

      <!-- Telescope Connection -->
      <button
        class="p-2 text-gray-400 hover:text-white relative rounded-full hover:bg-gray-800 transition-colors"
        title="Telescope Connection"
      >
        <span class="text-lg">🔭</span>
        <span v-if="telescopeStore.connected" class="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-green-500 border-2 border-gray-900 rounded-full"></span>
        <span v-else class="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 border-2 border-gray-900 rounded-full"></span>
      </button>

      <!-- Settings -->
      <button
        class="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-800 transition-colors"
        title="Settings"
      >
        <span class="text-lg">⚙️</span>
      </button>

      <!-- User Avatar -->
      <button class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-xs font-bold text-white shadow-lg hover:shadow-blue-500/20 transition-shadow">
        AS
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()
const locationName = ref('Default Location')
</script>
