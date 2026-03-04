<template>
  <div class="planning-controls space-y-4 p-4">
    <section>
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Observation Session
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Date</label>
          <input
            v-model="observationDate"
            type="date"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500 transition-all"
          />
        </div>

        <div>
          <label class="block text-xs text-gray-500 mb-1">Location</label>
          <div class="text-sm text-gray-200">
            {{ planningStore.location.name || 'Not set' }}
          </div>
          <div class="text-xs text-gray-500">
            {{ formatCoordinate(planningStore.location.latitude, 'lat') }},
            {{ formatCoordinate(planningStore.location.longitude, 'lon') }}
          </div>
        </div>

        <div v-if="weatherStore.current">
          <label class="block text-xs text-gray-500 mb-1">Current Conditions</label>
          <div class="text-sm text-gray-200">
            {{ displayTemperature }} • {{ weatherStore.weatherQuality }}
          </div>
          <div class="text-xs text-gray-500">
            Cloud cover: {{ weatherStore.current.cloud_cover }}%
          </div>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Target Wishlist ({{ wishlistCount }})
      </h3>

      <div v-if="wishlistCount > 0" class="space-y-2">
        <div
          v-for="target in catalogStore.wishlist"
          :key="target.name"
          class="flex items-center justify-between p-2 bg-gray-800 rounded hover:bg-gray-750 transition-colors"
        >
          <div class="flex-1 min-w-0">
            <div class="text-sm text-gray-200 truncate">{{ target.name }}</div>
            <div class="text-xs text-gray-500 capitalize">{{ target.type }}</div>
          </div>
          <button
            @click="catalogStore.removeFromWishlist(target.name)"
            class="ml-2 text-red-500 hover:text-red-400 text-xs px-2 py-1"
          >
            Remove
          </button>
        </div>
      </div>

      <div v-else class="text-sm text-gray-400 p-3 bg-gray-800/50 rounded">
        No targets in wishlist. Add targets from Discovery view.
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Constraints
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-gray-500 mb-1">
            Altitude Range: {{ planningStore.constraints.min_altitude_degrees }}° - {{ planningStore.constraints.max_altitude_degrees }}°
          </label>
          <div class="flex gap-3 items-center">
            <span class="text-xs text-gray-500 w-8">Min</span>
            <input
              v-model.number="planningStore.constraints.min_altitude_degrees"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
            <span class="text-xs text-gray-400 w-8 text-right">{{ planningStore.constraints.min_altitude_degrees }}°</span>
          </div>
          <div class="flex gap-3 items-center mt-2">
            <span class="text-xs text-gray-500 w-8">Max</span>
            <input
              v-model.number="planningStore.constraints.max_altitude_degrees"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
            <span class="text-xs text-gray-400 w-8 text-right">{{ planningStore.constraints.max_altitude_degrees }}°</span>
          </div>
        </div>

        <label class="flex items-center justify-between p-3 bg-gray-800 rounded cursor-pointer hover:bg-gray-750 transition-colors">
          <span class="text-sm text-gray-200">Avoid Moon</span>
          <input
            v-model="planningStore.constraints.avoid_moon"
            type="checkbox"
            class="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
          />
        </label>

        <div>
          <label class="block text-xs text-gray-500 mb-2">Setup Time</label>
          <div class="flex items-center gap-2">
            <input
              v-model.number="planningStore.constraints.setup_time_minutes"
              type="number"
              min="0"
              max="120"
              class="w-20 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
            />
            <span class="text-sm text-gray-400">minutes</span>
          </div>
        </div>
      </div>
    </section>

    <section>
      <button
        @click="generatePlan"
        :disabled="planningStore.loading"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ planningStore.loading ? 'Generating Plan...' : wishlistCount > 0 ? 'Generate Plan' : 'Auto-Generate Plan' }}
      </button>
      <p v-if="wishlistCount === 0" class="text-xs text-gray-500 mt-1 text-center">
        Will auto-select best targets for tonight
      </p>

      <p v-if="planningStore.error" class="text-xs text-red-400 mt-2">
        {{ planningStore.error }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlanningStore } from '@/stores/planning'
import { useCatalogStore } from '@/stores/catalog'
import { useWeatherStore } from '@/stores/weather'
import { useSettingsStore } from '@/stores/settings'

const planningStore = usePlanningStore()
const catalogStore = useCatalogStore()
const weatherStore = useWeatherStore()
const settingsStore = useSettingsStore()

// Set default observation date to today
const observationDate = ref(new Date().toISOString().split('T')[0])

const wishlistCount = computed(() => catalogStore.wishlist.length)

// Temperature display with user preference
const temperatureUnit = computed(() => settingsStore.settings.temperatureUnit || 'F')

const displayTemperature = computed(() => {
  if (!weatherStore.current?.temperature) return '--'
  const tempC = weatherStore.current.temperature
  if (temperatureUnit.value === 'F') {
    const tempF = (tempC * 9/5) + 32
    return `${Math.round(tempF)}°F`
  }
  return `${Math.round(tempC)}°C`
})

const formatCoordinate = (value, type) => {
  if (value === null || value === undefined) return 'N/A'
  const abs = Math.abs(value)
  const dir = type === 'lat' ? (value >= 0 ? 'N' : 'S') : (value >= 0 ? 'E' : 'W')
  return `${abs.toFixed(4)}°${dir}`
}

const generatePlan = async () => {
  try {
    planningStore.observationDate = observationDate.value
    // Persist any constraint changes before generating
    planningStore.saveConstraints().catch(() => {})
    await planningStore.generatePlan()
  } catch (err) {
    console.error('Failed to generate plan:', err)
  }
}

onMounted(() => {
  // Fetch current weather
  weatherStore.fetchCurrentWeather()
})
</script>
