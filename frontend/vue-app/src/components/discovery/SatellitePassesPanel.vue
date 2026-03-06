<template>
  <div class="h-full overflow-y-auto p-4">
    <!-- Header row -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold text-gray-200">ISS Passes</h3>
        <p class="text-xs text-gray-500">Next {{ days }} days · from your location</p>
      </div>
      <div class="flex items-center gap-2">
        <select
          v-model="minAlt"
          @change="fetchPasses"
          class="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
        >
          <option :value="0">Any altitude</option>
          <option :value="10">≥ 10° alt</option>
          <option :value="20">≥ 20° alt</option>
          <option :value="30">≥ 30° alt</option>
        </select>
        <button
          @click="fetchPasses"
          :disabled="loading"
          class="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-40 px-2 py-1 rounded border border-blue-800 hover:border-blue-600 transition-colors"
        >
          ↻ Refresh
        </button>
      </div>
    </div>

    <!-- No location configured -->
    <div
      v-if="!hasLocation"
      class="p-4 bg-yellow-900/20 border border-yellow-700 rounded-lg text-yellow-400 text-sm"
    >
      Observer location not configured. Set your latitude/longitude in Settings to enable satellite pass predictions.
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="text-center text-gray-400 py-12">
      <div class="text-2xl mb-2">🛰</div>
      Loading satellite passes…
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm"
    >
      {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="passes.length === 0" class="text-center text-gray-500 py-12 text-sm space-y-2">
      <div class="text-2xl">🌌</div>
      <p>No ISS passes found for the next {{ days }} days at your location.</p>
      <p class="text-xs text-gray-600">
        Try lowering the minimum altitude filter, or check that your N2YO API key is configured.
      </p>
    </div>

    <!-- Passes grouped by day -->
    <div v-else class="space-y-5">
      <div v-for="group in groupedPasses" :key="group.date">
        <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 border-b border-gray-800 pb-1">
          {{ group.date }}
        </h4>
        <div class="space-y-2">
          <div
            v-for="pass in group.passes"
            :key="pass.start_time"
            class="bg-gray-800 rounded-lg p-3 flex items-start gap-3"
          >
            <!-- Visibility badge (left column) -->
            <div class="flex-shrink-0 w-20 text-center">
              <span :class="visibilityBadgeClass(pass.visibility)" class="text-xs font-semibold px-2 py-0.5 rounded">
                {{ pass.visibility.toUpperCase() }}
              </span>
              <div class="text-xs text-gray-500 mt-1">{{ pass.max_altitude_deg.toFixed(0) }}° max</div>
            </div>

            <!-- Details (right column) -->
            <div class="flex-1 min-w-0">
              <!-- Time + duration -->
              <div class="flex items-baseline gap-2 flex-wrap">
                <span class="text-sm font-medium text-gray-200">{{ formatTime(pass.start_time) }}</span>
                <span class="text-xs text-gray-500">– {{ formatTime(pass.end_time) }}</span>
                <span class="text-xs text-gray-600">({{ formatDuration(pass.duration_minutes) }})</span>
              </div>

              <!-- Direction + magnitude -->
              <div class="text-xs text-gray-400 mt-0.5 flex items-center gap-2 flex-wrap">
                <span>{{ azToCompass(pass.start_azimuth_deg) }} → {{ azToCompass(pass.end_azimuth_deg) }}</span>
                <span v-if="pass.magnitude != null" class="text-gray-500">
                  · mag {{ pass.magnitude >= 0 ? '+' : '' }}{{ pass.magnitude.toFixed(1) }}
                </span>
              </div>

              <!-- Quality bar -->
              <div class="mt-2 flex items-center gap-2">
                <div class="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    :style="{ width: (pass.quality_score * 100).toFixed(0) + '%' }"
                    :class="qualityBarClass(pass.quality_score)"
                    class="h-full rounded-full"
                  />
                </div>
                <span class="text-xs text-gray-600 w-8 text-right">
                  {{ (pass.quality_score * 100).toFixed(0) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const loading = ref(false)
const error = ref(null)
const passes = ref([])
const minAlt = ref(10)
const days = 10

const hasLocation = computed(() => {
  const s = settingsStore.settings
  return s?.latitude != null && s?.longitude != null
})

// Group passes by local date string
const groupedPasses = computed(() => {
  const groups = {}
  for (const p of passes.value) {
    const dateKey = formatDate(p.start_time)
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(p)
  }
  return Object.entries(groups).map(([date, passList]) => ({ date, passes: passList }))
})

async function fetchPasses() {
  if (!hasLocation.value) return
  loading.value = true
  error.value = null
  try {
    const s = settingsStore.settings
    const res = await axios.get('/api/satellites/iss', {
      params: {
        lat: s.latitude,
        lon: s.longitude,
        days,
        min_altitude: minAlt.value,
      },
    })
    passes.value = res.data.passes ?? []
  } catch (e) {
    error.value = e.response?.data?.detail ?? 'Failed to load satellite passes.'
  } finally {
    loading.value = false
  }
}

// ─── Formatters ──────────────────────────────────────────────────────────────

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}

function formatDuration(minutes) {
  if (minutes < 1) return `${(minutes * 60).toFixed(0)}s`
  return `${minutes.toFixed(0)} min`
}

const COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
function azToCompass(az) {
  return COMPASS[Math.round(az / 45) % 8]
}

function visibilityBadgeClass(v) {
  return {
    excellent: 'bg-green-900/50 text-green-400 border border-green-700',
    good:      'bg-blue-900/50 text-blue-400 border border-blue-700',
    fair:      'bg-yellow-900/50 text-yellow-400 border border-yellow-700',
    poor:      'bg-gray-700 text-gray-400 border border-gray-600',
  }[v] ?? 'bg-gray-700 text-gray-400'
}

function qualityBarClass(score) {
  if (score >= 0.7) return 'bg-green-500'
  if (score >= 0.4) return 'bg-blue-500'
  return 'bg-amber-500'
}

onMounted(fetchPasses)
</script>
