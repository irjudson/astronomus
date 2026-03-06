<template>
  <div class="flex-1 overflow-y-auto p-6 space-y-6">
    <!-- Observing Location -->
    <section>
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Observing Location</h3>
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-gray-300 mb-1">Location Name</label>
          <input
            v-model="local.locationName"
            type="text"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            placeholder="My Backyard Observatory"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-300 mb-1">Latitude</label>
            <input
              v-model.number="local.latitude"
              type="number"
              step="0.0001"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
              placeholder="40.7128"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-300 mb-1">Longitude</label>
            <input
              v-model.number="local.longitude"
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
            v-model="local.timezone"
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
              @click="local.temperatureUnit = 'F'"
              class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
              :class="local.temperatureUnit === 'F' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
            >Fahrenheit (°F)</button>
            <button
              @click="local.temperatureUnit = 'C'"
              class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
              :class="local.temperatureUnit === 'C' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
            >Celsius (°C)</button>
          </div>
        </div>
        <div>
          <label class="block text-sm text-gray-300 mb-2">Distance</label>
          <div class="flex gap-2">
            <button
              @click="local.distanceUnit = 'mi'"
              class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
              :class="local.distanceUnit === 'mi' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
            >Miles</button>
            <button
              @click="local.distanceUnit = 'km'"
              class="flex-1 px-4 py-2 text-sm rounded-lg transition-colors"
              :class="local.distanceUnit === 'km' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
            >Kilometers</button>
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
          <input v-model="local.showThumbnails" type="checkbox"
            class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50" />
        </label>
        <label class="flex items-center justify-between p-3 bg-gray-800 rounded-lg cursor-pointer hover:bg-gray-750 transition-colors">
          <span class="text-sm text-gray-300">Auto-refresh catalog data</span>
          <input v-model="local.autoRefresh" type="checkbox"
            class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50" />
        </label>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(['update:modelValue'])

// Transparent proxy: reads from props, writes by emitting a merged copy
const local = new Proxy({}, {
  get(_, key) { return props.modelValue[key] },
  set(_, key, value) {
    emit('update:modelValue', { ...props.modelValue, [key]: value })
    return true
  }
})
</script>
