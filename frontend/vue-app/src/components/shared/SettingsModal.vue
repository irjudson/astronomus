<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
    <div class="bg-gray-900 border border-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h2 class="text-lg font-semibold text-gray-200">Settings</h2>
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Observing Location -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Observing Location</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-300 mb-1">Location Name</label>
              <input
                v-model="localSettings.locationName"
                type="text"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="My Backyard Observatory"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm text-gray-300 mb-1">Latitude</label>
                <input
                  v-model.number="localSettings.latitude"
                  type="number"
                  step="0.0001"
                  class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  placeholder="40.7128"
                />
              </div>
              <div>
                <label class="block text-sm text-gray-300 mb-1">Longitude</label>
                <input
                  v-model.number="localSettings.longitude"
                  type="number"
                  step="0.0001"
                  class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                  placeholder="-74.0060"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-300 mb-1">Timezone</label>
              <input
                v-model="localSettings.timezone"
                type="text"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
                placeholder="America/New_York"
              />
            </div>
          </div>
        </section>

        <!-- Units -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Units</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-sm text-gray-300 mb-2">Temperature</label>
              <div class="flex gap-2">
                <button
                  @click="localSettings.temperatureUnit = 'F'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.temperatureUnit === 'F' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Fahrenheit (°F)
                </button>
                <button
                  @click="localSettings.temperatureUnit = 'C'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.temperatureUnit === 'C' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Celsius (°C)
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-300 mb-2">Distance</label>
              <div class="flex gap-2">
                <button
                  @click="localSettings.distanceUnit = 'mi'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.distanceUnit === 'mi' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Miles
                </button>
                <button
                  @click="localSettings.distanceUnit = 'km'"
                  class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
                  :class="localSettings.distanceUnit === 'km' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
                >
                  Kilometers
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Display Preferences -->
        <section>
          <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Display</h3>
          <div class="space-y-3">
            <label class="flex items-center justify-between p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750 transition-colors">
              <span class="text-sm text-gray-300">Show object thumbnails</span>
              <input
                v-model="localSettings.showThumbnails"
                type="checkbox"
                class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
            </label>
            <label class="flex items-center justify-between p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750 transition-colors">
              <span class="text-sm text-gray-300">Auto-refresh catalog data</span>
              <input
                v-model="localSettings.autoRefresh"
                type="checkbox"
                class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
            </label>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="saveSettings"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          Save Changes
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { XIcon } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close', 'save'])

// Load settings from localStorage
const loadSettings = () => {
  const saved = localStorage.getItem('astronomus_settings')
  if (saved) {
    return JSON.parse(saved)
  }
  return {
    locationName: '',
    latitude: 40.7128,
    longitude: -74.0060,
    timezone: 'America/New_York',
    temperatureUnit: 'F',
    distanceUnit: 'mi',
    showThumbnails: true,
    autoRefresh: false
  }
}

const localSettings = ref(loadSettings())

// Reload settings when modal opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    localSettings.value = loadSettings()
  }
})

const saveSettings = () => {
  localStorage.setItem('astronomus_settings', JSON.stringify(localSettings.value))
  emit('save', localSettings.value)
  emit('close')
}
</script>
