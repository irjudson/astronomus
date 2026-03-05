<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
    @click.self="closeModal"
  >
    <div class="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-800">
        <div class="flex items-center gap-2">
          <span class="text-lg">{{ weatherIcon }}</span>
          <h2 class="text-base font-semibold text-gray-100">Weather Conditions</h2>
          <span v-if="weatherStore.local" class="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-300">
            local station
          </span>
          <span v-else-if="weatherStore.current" class="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">
            7Timer forecast
          </span>
        </div>
        <button @click="closeModal" class="text-gray-500 hover:text-gray-200 text-xl leading-none transition-colors">×</button>
      </div>

      <div class="p-5 space-y-5 max-h-[80vh] overflow-y-auto">
        <!-- Loading / Error -->
        <div v-if="weatherStore.loading" class="text-gray-400 text-sm text-center py-4">Loading weather data…</div>
        <div v-else-if="weatherStore.error" class="text-red-400 text-sm">{{ weatherStore.error }}</div>

        <!-- Current conditions -->
        <div v-else-if="weatherStore.current || weatherStore.local">
          <!-- Quality banner -->
          <div class="flex items-center gap-3 mb-4">
            <div class="text-4xl">{{ weatherIcon }}</div>
            <div>
              <div class="text-2xl font-bold text-gray-100">{{ displayTemp }}</div>
              <div :class="qualityColor" class="text-sm font-medium">{{ weatherStore.weatherQuality }}</div>
            </div>
            <div v-if="weatherStore.isRaining" class="ml-auto text-blue-400 text-sm font-medium">🌧 Rain in progress</div>
          </div>

          <!-- Conditions grid -->
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Humidity</div>
              <div class="text-gray-200 font-medium">{{ weatherStore.currentHumidity != null ? weatherStore.currentHumidity + '%' : '—' }}</div>
            </div>
            <div class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Wind</div>
              <div class="text-gray-200 font-medium">
                {{ weatherStore.local?.wind_speed_mph != null ? Math.round(weatherStore.local.wind_speed_mph) + ' mph' : (weatherStore.current?.wind_speed != null ? Math.round(weatherStore.current.wind_speed) + ' km/h' : '—') }}
                <span v-if="weatherStore.local?.wind_direction_compass" class="text-gray-400 text-xs"> {{ weatherStore.local.wind_direction_compass }}</span>
              </div>
            </div>
            <div class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Cloud Cover</div>
              <div class="text-gray-200 font-medium">{{ weatherStore.current?.cloud_cover != null ? weatherStore.current.cloud_cover + '%' : '—' }}</div>
            </div>
            <div class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Dew Point</div>
              <div class="text-gray-200 font-medium">
                {{ weatherStore.local?.dew_point_c != null ? Math.round(weatherStore.local.dew_point_c) + '°C' : '—' }}
              </div>
            </div>
            <div v-if="weatherStore.local?.wind_gust_mph" class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Gusts</div>
              <div class="text-gray-200 font-medium">{{ Math.round(weatherStore.local.wind_gust_mph) }} mph</div>
            </div>
            <div v-if="weatherStore.local?.relative_pressure_inhg" class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Pressure</div>
              <div class="text-gray-200 font-medium">{{ weatherStore.local.relative_pressure_inhg.toFixed(2) }} inHg</div>
            </div>
            <div v-if="weatherStore.current?.seeing" class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Seeing</div>
              <div class="text-gray-200 font-medium">{{ seeingLabel }}</div>
            </div>
            <div v-if="weatherStore.current?.transparency" class="bg-gray-800 rounded-lg px-3 py-2">
              <div class="text-gray-500 text-xs mb-1">Transparency</div>
              <div class="text-gray-200 font-medium">{{ transparencyLabel }}</div>
            </div>
          </div>

          <!-- Astronomy issues -->
          <div v-if="weatherStore.astronomyIssues.length" class="mt-3 space-y-1">
            <div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Astronomy concerns</div>
            <div
              v-for="issue in weatherStore.astronomyIssues"
              :key="issue"
              class="flex items-center gap-2 text-sm text-yellow-400"
            >
              <span>⚠</span> {{ issue }}
            </div>
          </div>
          <div v-else class="mt-3 flex items-center gap-2 text-sm text-green-400">
            <span>✓</span> Conditions look good for observing
          </div>
        </div>

        <div v-else class="text-gray-500 text-sm text-center py-4">No weather data available.</div>

        <!-- Forecast strip -->
        <div v-if="weatherStore.forecast?.length" class="border-t border-gray-800 pt-4">
          <div class="text-xs text-gray-500 uppercase tracking-wider mb-3">Hourly Forecast</div>
          <div class="flex gap-2 overflow-x-auto pb-1">
            <div
              v-for="(item, i) in weatherStore.forecast.slice(0, 12)"
              :key="i"
              class="flex-shrink-0 bg-gray-800 rounded-lg px-3 py-2 text-center min-w-[64px]"
            >
              <div class="text-gray-500 text-xs">+{{ i * 3 }}h</div>
              <div class="text-lg my-1">{{ forecastIcon(item) }}</div>
              <div class="text-gray-200 text-xs font-medium">{{ item.temperature_c != null ? Math.round(item.temperature_c) + '°' : '—' }}</div>
              <div class="text-gray-400 text-xs">{{ item.cloud_cover != null ? item.cloud_cover + '%' : '' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWeatherStore } from '../stores/weather'
import { useSettingsStore } from '../stores/settings'

const isOpen = ref(false)
const weatherStore = useWeatherStore()
const settingsStore = useSettingsStore()

const openModal = () => {
  isOpen.value = true
  weatherStore.fetchCurrentWeather()
}

const closeModal = () => {
  isOpen.value = false
}

defineExpose({ openModal })

const displayTemp = computed(() => {
  const tempC = weatherStore.currentTempC
  if (tempC == null) return '—'
  const unit = settingsStore.settings?.temperatureUnit || 'F'
  if (unit === 'F') return `${Math.round((tempC * 9 / 5) + 32)}°F`
  return `${Math.round(tempC)}°C`
})

const weatherIcon = computed(() => {
  if (weatherStore.isRaining) return '🌧️'
  const cloudCover = weatherStore.current?.cloud_cover ?? 0
  if (cloudCover < 20) return '☀️'
  if (cloudCover < 50) return '⛅'
  if (cloudCover < 80) return '🌥️'
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

// 7Timer seeing: 1=<0.5", 2=0.5-0.75", 3=0.75-1", 4=1-1.25", 5=1.25-1.5", 6=1.5-2", 7=2-2.5", 8=>2.5"
const SEEING_LABELS = ['', '<0.5″ (excellent)', '0.5–0.75″', '0.75–1″', '1–1.25″', '1.25–1.5″', '1.5–2″', '2–2.5″', '>2.5″ (poor)']
const seeingLabel = computed(() => {
  const s = weatherStore.current?.seeing
  if (!s) return '—'
  return SEEING_LABELS[s] ?? `${s}/8`
})

// 7Timer transparency: 1=<0.3, 2=0.3-0.4, 3=0.4-0.5, 4=0.5-0.6, 5=0.6-0.7, 6=0.7-0.85, 7=0.85-1
const TRANS_LABELS = ['', '<0.3 (poor)', '0.3–0.4', '0.4–0.5', '0.5–0.6', '0.6–0.7', '0.7–0.85', '0.85–1 (excellent)']
const transparencyLabel = computed(() => {
  const t = weatherStore.current?.transparency
  if (!t) return '—'
  return TRANS_LABELS[t] ?? `${t}/7`
})

const forecastIcon = (item) => {
  const cc = item.cloud_cover ?? 0
  if (cc < 20) return '☀️'
  if (cc < 50) return '⛅'
  if (cc < 80) return '🌥️'
  return '☁️'
}
</script>
