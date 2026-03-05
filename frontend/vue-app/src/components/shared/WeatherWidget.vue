<template>
  <div class="weather-widget flex items-center gap-2 text-sm">
    <button
      @click="toggleModal"
      class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-800 transition-colors"
      :title="tooltipText"
    >
      <span class="text-lg">{{ weatherIcon }}</span>
      <div class="text-left">
        <div class="text-gray-200 font-medium flex items-center gap-1.5">
          {{ displayTemperature }}
          <span v-if="weatherStore.local?.humidity_pct != null" class="text-xs text-gray-400">
            {{ weatherStore.local.humidity_pct }}%
          </span>
          <span v-if="weatherStore.local?.wind_speed_mph" class="text-xs text-gray-400">
            {{ Math.round(weatherStore.local.wind_speed_mph) }}mph
          </span>
        </div>
        <div class="text-xs flex items-center gap-1">
          <span :class="qualityColor">{{ weatherStore.weatherQuality }}</span>
          <span v-if="weatherStore.isRaining" class="text-blue-400">· Rain</span>
          <span v-else-if="weatherStore.astronomyIssues.length" class="text-yellow-500">
            · {{ weatherStore.astronomyIssues[0].split('(')[0].trim() }}
          </span>
          <span v-if="weatherStore.local" class="text-gray-600">· local</span>
        </div>
      </div>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useWeatherStore } from '@/stores/weather'
import { useSettingsStore } from '@/stores/settings'

const emit = defineEmits(['open-weather'])

const weatherStore = useWeatherStore()
const settingsStore = useSettingsStore()

const temperatureUnit = computed(() => settingsStore.settings.temperatureUnit || 'F')

const displayTemperature = computed(() => {
  const tempC = weatherStore.currentTempC
  if (tempC == null) return '--'
  if (temperatureUnit.value === 'F') {
    return `${Math.round((tempC * 9/5) + 32)}°F`
  }
  return `${Math.round(tempC)}°C`
})

const weatherIcon = computed(() => {
  if (weatherStore.isRaining) return '🌧️'
  const cloudCover = weatherStore.current?.cloud_cover ?? 0
  if (cloudCover < 20) return '☀️'
  if (cloudCover < 50) return '⛅'
  if (cloudCover < 80) return '☁️'
  return '☁️'
})

const qualityColor = computed(() => {
  const score = weatherStore.weatherScore
  if (score === null) return 'text-gray-500'
  if (score >= 80) return 'text-green-400'
  if (score >= 60) return 'text-yellow-400'
  if (score >= 40) return 'text-orange-400'
  return 'text-red-400'
})

const tooltipText = computed(() => {
  const issues = weatherStore.astronomyIssues
  if (!issues.length) return 'Conditions look good for observing'
  return issues.join(' · ')
})

const toggleModal = () => {
  emit('open-weather')
}

onMounted(() => {
  weatherStore.fetchCurrentWeather()
  // Refresh local station every 5 min, full weather every 30 min
  setInterval(() => weatherStore.fetchLocalWeather(), 5 * 60 * 1000)
  setInterval(() => weatherStore.fetchCurrentWeather(), 30 * 60 * 1000)
})
</script>
