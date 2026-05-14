<template>
  <div class="h-full overflow-y-auto bg-gray-950 p-6 space-y-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Tonight</h1>
      <span class="text-sm text-gray-400">{{ todayLabel }}</span>
    </div>

    <!-- Conditions + Telescope (2-col grid) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <!-- Conditions card -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Conditions</div>
        <template v-if="weatherStore.local">
          <div class="flex items-center gap-4 mb-2">
            <span class="text-2xl font-semibold text-white">{{ tempF }}&deg;F</span>
            <span class="text-sm text-gray-400">{{ weatherStore.currentHumidity != null ? weatherStore.currentHumidity + '% humidity' : '' }}</span>
            <span class="text-sm text-gray-400">{{ weatherStore.currentWindMph != null ? weatherStore.currentWindMph.toFixed(1) + ' mph' : '' }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="text-xs font-semibold px-2 py-0.5 rounded-full"
              :class="suitabilityClass"
            >{{ suitabilityLabel }}</span>
            <span v-if="weatherStore.astronomyIssues.length" class="text-xs text-gray-500">
              &middot; {{ weatherStore.astronomyIssues[0] }}
            </span>
          </div>
        </template>
        <template v-else>
          <p class="text-sm text-gray-500">No local weather data</p>
        </template>
      </div>

      <!-- Telescope card -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Telescope</div>
        <div class="flex items-center gap-2 mb-3">
          <span
            class="w-2 h-2 rounded-full flex-shrink-0"
            :class="executionStore.connected ? 'bg-green-500' : 'bg-gray-600'"
          ></span>
          <span class="text-sm font-medium" :class="executionStore.connected ? 'text-green-400' : 'text-gray-400'">
            {{ executionStore.connected ? 'Connected' : 'Not connected' }}
          </span>
          <span v-if="executionStore.connected && executionStore.telescopeIp" class="text-xs text-gray-500">
            &middot; {{ executionStore.telescopeIp }}
          </span>
        </div>
        <router-link
          to="/observe"
          class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {{ executionStore.connected ? 'Open Observe &rarr;' : 'Connect telescope &rarr;' }}
        </router-link>
      </div>
    </div>

    <!-- 7-day weather strip -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">7-Day Forecast</div>
      <DailyWeatherStrip :forecasts="weatherStore.multiDayForecast" />
    </div>

    <!-- Visible Comets card -->
    <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h3 class="text-sm font-semibold text-gray-300 mb-3">Comets Visible Tonight</h3>
      <div v-if="cometsLoading" class="text-xs text-gray-500">Loading…</div>
      <div v-else-if="visibleComets.length === 0" class="text-xs text-gray-500 italic">
        No comets above 20° tonight
      </div>
      <div v-else class="space-y-2">
        <div v-for="c in visibleComets" :key="c.designation"
          class="flex items-center justify-between text-sm">
          <div>
            <span class="text-gray-200 font-medium">{{ c.name || c.designation }}</span>
            <span class="text-gray-500 text-xs ml-2">mag {{ c.magnitude?.toFixed(1) ?? '?' }}</span>
            <span class="text-gray-500 text-xs ml-2">alt {{ c.altitude }}°</span>
          </div>
          <button @click="planningStore.toggleCometWishlist(c.designation)"
            class="px-2 py-1 text-xs rounded transition-colors"
            :class="planningStore.isCometWishlisted(c.designation)
              ? 'bg-blue-600/30 text-blue-400 hover:bg-blue-600/50'
              : 'bg-gray-700 text-gray-400 hover:text-blue-400'">
            {{ planningStore.isCometWishlisted(c.designation) ? '&#x2713; Added' : '+ Plan' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Active Plan card (full width) -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Active Plan</div>
      <template v-if="planningStore.currentPlan">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="text-base font-semibold text-white mb-1">{{ planningStore.planName || 'Unnamed Plan' }}</div>
            <div class="text-sm text-gray-400">
              {{ targetCount }} target{{ targetCount !== 1 ? 's' : '' }}
              <template v-if="sessionTimeRange">
                &middot; {{ sessionTimeRange }}
              </template>
            </div>
          </div>
          <router-link
            to="/observe"
            class="flex-shrink-0 text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            Execute Plan &rarr;
          </router-link>
        </div>
      </template>
      <template v-else-if="planningStore.savedPlans.length">
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="text-base font-semibold text-white mb-1">{{ planningStore.savedPlans[0].name }}</div>
            <div class="text-sm text-gray-400">Most recent saved plan</div>
          </div>
          <button
            class="flex-shrink-0 text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
            @click="loadMostRecent"
          >
            Load Plan &rarr;
          </button>
        </div>
      </template>
      <template v-else>
        <p class="text-sm text-gray-500 mb-2">No plan yet.</p>
        <router-link
          to="/plan"
          class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          Go to Plan &rarr;
        </router-link>
      </template>
    </div>

    <!-- Quick links (3-col grid) -->
    <div class="grid grid-cols-3 gap-4">
      <router-link
        to="/sky"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col items-center gap-2 hover:border-indigo-600 transition-colors cursor-pointer"
      >
        <span class="text-2xl">&#x1F52D;</span>
        <span class="text-sm font-medium text-gray-300">Sky</span>
      </router-link>

      <router-link
        to="/plan"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col items-center gap-2 hover:border-indigo-600 transition-colors cursor-pointer"
      >
        <span class="text-2xl">&#x1F4C5;</span>
        <span class="text-sm font-medium text-gray-300">Plan</span>
      </router-link>

      <router-link
        to="/archive"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col items-center gap-2 hover:border-indigo-600 transition-colors cursor-pointer"
      >
        <span class="text-2xl">&#x1F5C2;&#xFE0F;</span>
        <span class="text-sm font-medium text-gray-300">Review</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { useWeatherStore } from '@/stores/weather'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'
import DailyWeatherStrip from '@/components/shared/DailyWeatherStrip.vue'

const weatherStore = useWeatherStore()
const executionStore = useExecutionStore()
const planningStore = usePlanningStore()

// Visible comets
const visibleComets = ref([])
const cometsLoading = ref(false)

async function fetchVisibleComets() {
  cometsLoading.value = true
  try {
    const resp = await axios.get('/api/comets/visible-tonight', { params: { min_altitude: 20 } })
    visibleComets.value = resp.data
  } catch (e) {
    visibleComets.value = []
  } finally {
    cometsLoading.value = false
  }
}

// Header date label
const todayLabel = computed(() => {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
})

// Temperature in Fahrenheit
const tempF = computed(() => {
  const c = weatherStore.currentTempC
  if (c == null) return '--'
  return Math.round(c * 9 / 5 + 32)
})

// Suitability derived from local astronomy score (0–1 float)
const astronomyScore = computed(() => weatherStore.local?.astronomy?.score ?? null)

const suitabilityLabel = computed(() => {
  const score = astronomyScore.value
  if (score == null) return 'Unknown'
  if (score >= 0.7) return 'Good'
  if (score >= 0.4) return 'Fair'
  return 'Poor'
})

const suitabilityClass = computed(() => {
  const label = suitabilityLabel.value
  if (label === 'Good') return 'bg-green-900 text-green-300'
  if (label === 'Fair') return 'bg-yellow-900 text-yellow-300'
  if (label === 'Poor') return 'bg-red-900 text-red-300'
  return 'bg-gray-800 text-gray-400'
})

// Plan info
const targetCount = computed(() => {
  return planningStore.currentPlan?.scheduled_targets?.length ?? 0
})

function formatSessionTime(iso) {
  if (!iso) return null
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

const sessionTimeRange = computed(() => {
  const session = planningStore.currentPlan?.session
  if (!session) return null
  const start = formatSessionTime(session.imaging_start)
  const end = formatSessionTime(session.imaging_end)
  if (!start || !end) return null
  return `${start} – ${end}`
})

async function loadMostRecent() {
  const plan = planningStore.savedPlans[0]
  if (plan) await planningStore.loadPlan(plan.id)
}

onMounted(async () => {
  await weatherStore.fetchLocalWeather()
  weatherStore.fetchMultiDayForecast()
  await planningStore.loadSavedPlans()
  fetchVisibleComets()
})
</script>
