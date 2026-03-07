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
      <template v-else>
        <p class="text-sm text-gray-500 mb-2">No plan loaded.</p>
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
        <span class="text-sm font-medium text-gray-300">Archive</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useWeatherStore } from '@/stores/weather'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'

const weatherStore = useWeatherStore()
const executionStore = useExecutionStore()
const planningStore = usePlanningStore()

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

onMounted(async () => {
  await weatherStore.fetchLocalWeather()
  await planningStore.loadSavedPlans()
})
</script>
