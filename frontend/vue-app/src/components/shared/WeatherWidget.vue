<template>
  <div class="weather-widget flex items-center gap-2 text-sm">
    <button
      @click="toggleModal"
      class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-800 transition-colors"
    >
      <span class="text-lg">{{ weatherIcon }}</span>
      <div class="text-left">
        <div class="text-gray-200 font-medium">
          {{ displayTemperature }}
        </div>
        <div class="text-xs text-gray-500">
          {{ weatherStore.weatherQuality }}
        </div>
      </div>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useWeatherStore } from '@/stores/weather'

const weatherStore = useWeatherStore()

const temperatureUnit = computed(() => {
  const settings = localStorage.getItem('astronomus_settings')
  return settings ? JSON.parse(settings).temperatureUnit || 'F' : 'F'
})

const displayTemperature = computed(() => {
  if (!weatherStore.current?.temperature) return '--'

  const tempC = weatherStore.current.temperature
  if (temperatureUnit.value === 'F') {
    const tempF = (tempC * 9/5) + 32
    return `${Math.round(tempF)}°F`
  }
  return `${Math.round(tempC)}°C`
})

const weatherIcon = computed(() => {
  if (!weatherStore.current) return '🌤️'

  const cloudCover = weatherStore.current.cloud_cover || 0

  if (cloudCover < 20) return '☀️'
  if (cloudCover < 50) return '⛅'
  if (cloudCover < 80) return '☁️'
  return '🌧️'
})

const toggleModal = () => {
  // Emit event to parent to show weather modal
  // Or navigate to weather details page
  console.log('Show weather details')
}

onMounted(() => {
  weatherStore.fetchCurrentWeather()

  // Refresh every 30 minutes
  setInterval(() => {
    weatherStore.fetchCurrentWeather()
  }, 30 * 60 * 1000)
})
</script>
