<template>
  <div class="h-full flex flex-col">
    <!-- Page Header -->
    <div class="px-6 py-4 border-b border-gray-800">
      <h1 class="text-2xl font-semibold text-gray-200">Dashboard</h1>
      <p class="text-sm text-gray-500 mt-1">Overview of your observation session</p>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-auto p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Weather Card -->
        <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <span class="text-2xl">🌤️</span>
            </div>
            <div>
              <h2 class="text-sm font-medium text-gray-400">Weather Forecast</h2>
              <p class="text-lg font-semibold text-gray-200">Clear Skies</p>
            </div>
          </div>
          <div class="text-xs text-gray-500">
            <p>Temperature: 68°F</p>
            <p>Humidity: 45%</p>
            <p>Wind: 5 mph</p>
          </div>
        </div>

        <!-- Telescope Status Card -->
        <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
              <span class="text-2xl">🔭</span>
            </div>
            <div>
              <h2 class="text-sm font-medium text-gray-400">Telescope Status</h2>
              <p class="text-lg font-semibold" :class="telescopeStore.connected ? 'text-green-400' : 'text-red-400'">
                {{ telescopeStore.statusText }}
              </p>
            </div>
          </div>
          <div class="text-xs text-gray-500">
            <p v-if="telescopeStore.connected">Ready for imaging</p>
            <p v-else>Connect telescope to begin</p>
          </div>
        </div>

        <!-- Next Observation Card -->
        <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 hover:border-gray-600 transition-colors">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <span class="text-2xl">📋</span>
            </div>
            <div>
              <h2 class="text-sm font-medium text-gray-400">Next Observation</h2>
              <p class="text-lg font-semibold text-gray-200">No plans scheduled</p>
            </div>
          </div>
          <div class="text-xs text-gray-500">
            <p>Create a plan to get started</p>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="mt-6">
        <h2 class="text-lg font-semibold text-gray-200 mb-4">Recent Activity</h2>
        <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
          <div class="flex flex-col items-center justify-center py-8 text-center">
            <div class="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
              <span class="text-3xl">🌟</span>
            </div>
            <p class="text-sm text-gray-500">No recent activity</p>
            <p class="text-xs text-gray-600 mt-1">Start your first observation session</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()
</script>
