<template>
  <header class="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900 shrink-0 z-10">
    <!-- Left: Logo -->
    <div class="flex items-center space-x-4">
      <div class="font-bold text-xl tracking-tight text-blue-500 flex items-center gap-2">
        <span>🔭</span>
        <span>Astronomus</span>
      </div>
    </div>

    <!-- Center: Navigation -->
    <nav class="flex space-x-1 bg-gray-800 p-1 rounded-lg">
      <router-link
        to="/"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path === '/' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Discovery
      </router-link>
      <router-link
        to="/plan"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/plan') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Planning
      </router-link>
      <router-link
        to="/execute"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/execute') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Execution
      </router-link>
      <router-link
        to="/process"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/process') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Processing
      </router-link>
    </nav>

    <!-- Right: Weather, Settings -->
    <div class="flex items-center space-x-3">
      <WeatherWidget @open-weather="weatherModalRef?.openModal()" />
      <button
        @click="showSettings = true"
        class="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-800 transition-colors"
        title="Settings"
      >
        <SettingsIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Settings Modal -->
    <SettingsModal
      :is-open="showSettings"
      @close="showSettings = false"
      @save="handleSaveSettings"
    />

    <!-- Weather Modal -->
    <WeatherModal ref="weatherModalRef" />
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { SettingsIcon } from 'lucide-vue-next'
import WeatherWidget from './WeatherWidget.vue'
import SettingsModal from './SettingsModal.vue'
import WeatherModal from '../WeatherModal.vue'

const showSettings = ref(false)
const weatherModalRef = ref(null)

const handleSaveSettings = () => {
  // Settings are already saved to backend + localStorage by the modal
}
</script>
