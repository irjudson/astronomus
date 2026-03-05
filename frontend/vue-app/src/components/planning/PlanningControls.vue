<template>
  <div class="flex flex-col h-full">

    <!-- Fixed controls at top -->
    <div class="flex-shrink-0 space-y-4 p-4">
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
          {{ planningStore.loading ? 'Generating Plan...' : 'Generate Plan' }}
        </button>
        <p v-if="wishlistCount === 0" class="text-xs text-gray-500 mt-1 text-center">
          Auto-selects best targets for tonight
        </p>
        <p v-else-if="dsoWishlistCount > 0 && solarWishlistCount > 0" class="text-xs text-gray-500 mt-1 text-center">
          Best targets tonight + {{ dsoWishlistCount }} DSO{{ dsoWishlistCount !== 1 ? 's' : '' }} preferred for gaps + {{ solarWishlistCount }} solar system
        </p>
        <p v-else-if="dsoWishlistCount > 0" class="text-xs text-gray-500 mt-1 text-center">
          Best targets tonight, gaps filled with wishlist ({{ dsoWishlistCount }} DSO{{ dsoWishlistCount !== 1 ? 's' : '' }})
        </p>
        <p v-else class="text-xs text-gray-500 mt-1 text-center">
          Best targets tonight + your {{ solarWishlistCount }} solar system target{{ solarWishlistCount !== 1 ? 's' : '' }}
        </p>

        <p v-if="planningStore.error" class="text-xs text-red-400 mt-2">
          {{ planningStore.error }}
        </p>
      </section>
    </div>

    <!-- Tabbed bottom section: Wishlist | Saved Plans -->
    <div class="flex-1 min-h-0 border-t border-gray-800 flex flex-col">

      <!-- Tab bar -->
      <div class="flex-shrink-0 flex border-b border-gray-800">
        <button
          @click="bottomTab = 'wishlist'"
          :class="[
            'flex-1 py-2 text-xs font-medium transition-colors',
            bottomTab === 'wishlist'
              ? 'text-blue-400 border-b-2 border-blue-500'
              : 'text-gray-500 hover:text-gray-300'
          ]"
        >
          Wishlist ({{ wishlistCount }})
        </button>
        <button
          @click="switchToSavedPlans"
          :class="[
            'flex-1 py-2 text-xs font-medium transition-colors',
            bottomTab === 'saved'
              ? 'text-blue-400 border-b-2 border-blue-500'
              : 'text-gray-500 hover:text-gray-300'
          ]"
        >
          Saved Plans ({{ planningStore.savedPlans.length }})
        </button>
      </div>

      <!-- Wishlist tab -->
      <div v-if="bottomTab === 'wishlist'" class="flex-1 min-h-0 overflow-y-auto px-2 py-2">
        <div v-if="wishlistCount === 0" class="text-sm text-gray-400 p-3 bg-gray-800/50 rounded mx-2">
          No targets in wishlist. Add targets from Discovery view.
        </div>
        <template v-else>
          <!-- Needs Imaging section -->
          <div class="text-xs text-gray-500 px-2 py-1 uppercase tracking-wide font-medium">
            Needs Imaging ({{ needsImagingTargets.length }})
          </div>
          <div v-if="needsImagingTargets.length === 0" class="px-2 py-3 text-xs text-gray-600 text-center">
            All targets complete! Add more from Discovery.
          </div>
          <div v-for="target in needsImagingTargets" :key="target.name">
            <div class="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-800 rounded cursor-pointer"
                 @click="toggleWishlistExpand(target.name)">
              <span class="flex-1 text-sm text-gray-200 truncate">{{ target.name }}</span>
              <span class="text-xs text-gray-500 capitalize flex-shrink-0">{{ target.type }}</span>
              <span v-if="catalogStore.captureMap[target.name]"
                    class="w-2 h-2 rounded-full flex-shrink-0"
                    :class="statusDotClass(effectiveStatus(target))"></span>
              <span class="text-gray-600 text-xs flex-shrink-0">
                {{ expandedWishlistItem === target.name ? '▲' : '▼' }}
              </span>
              <button @click.stop="catalogStore.removeFromWishlist(target.name)"
                      class="text-red-500 hover:text-red-400 text-xs px-1 flex-shrink-0">×</button>
            </div>
            <div v-if="expandedWishlistItem === target.name" class="px-2 pb-2">
              <CaptureReviewPanel
                :capture="catalogStore.captureMap[target.name] ?? null"
                @set-status="s => setWishlistStatus(target, s)"
              />
            </div>
          </div>

          <!-- Completed section -->
          <div v-if="completedTargets.length" class="mt-2 border-t border-gray-700 pt-2">
            <div class="text-xs text-gray-500 px-2 py-1 uppercase tracking-wide font-medium">
              Completed ({{ completedTargets.length }})
            </div>
            <div v-for="target in completedTargets" :key="target.name">
              <div class="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-800 rounded cursor-pointer opacity-60"
                   @click="toggleWishlistExpand(target.name)">
                <span class="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"></span>
                <span class="flex-1 text-sm text-gray-400 truncate line-through">{{ target.name }}</span>
                <span class="text-xs text-gray-600 capitalize flex-shrink-0">{{ target.type }}</span>
                <button @click.stop="catalogStore.removeFromWishlist(target.name)"
                        class="text-red-500 hover:text-red-400 text-xs px-1 flex-shrink-0">×</button>
              </div>
              <div v-if="expandedWishlistItem === target.name" class="px-2 pb-2">
                <CaptureReviewPanel
                  :capture="catalogStore.captureMap[target.name] ?? null"
                  @set-status="s => setWishlistStatus(target, s)"
                />
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Saved Plans tab -->
      <div v-else class="flex-1 min-h-0 overflow-y-auto px-4 py-3">
        <div v-if="planningStore.savedPlans.length > 0" class="space-y-2">
          <div
            v-for="plan in planningStore.savedPlans"
            :key="plan.id"
            class="p-2 bg-gray-800 rounded"
          >
            <div class="flex items-start justify-between gap-2 mb-1">
              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-200 truncate font-medium">{{ plan.name }}</div>
                <div class="text-xs text-gray-500">
                  {{ plan.observing_date }} · {{ plan.total_targets }} targets · {{ plan.location_name }}
                </div>
              </div>
            </div>
            <div class="flex gap-2 mt-2">
              <button
                @click="loadPlan(plan.id)"
                class="flex-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
              >
                Load
              </button>
              <button
                @click="deletePlan(plan.id, plan.name)"
                class="px-2 py-1 bg-gray-700 hover:bg-red-900 text-gray-400 hover:text-red-400 text-xs rounded transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
        <div v-else class="text-sm text-gray-400 p-3 bg-gray-800/50 rounded">
          No saved plans. Generate a plan and click "Save Plan".
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlanningStore } from '@/stores/planning'
import { useCatalogStore } from '@/stores/catalog'
import { useWeatherStore } from '@/stores/weather'
import { useSettingsStore } from '@/stores/settings'
import CaptureReviewPanel from '@/components/shared/CaptureReviewPanel.vue'

const planningStore = usePlanningStore()
const catalogStore = useCatalogStore()
const weatherStore = useWeatherStore()
const settingsStore = useSettingsStore()

const bottomTab = ref('wishlist')

// Set default observation date to today
const observationDate = ref(new Date().toISOString().split('T')[0])

const wishlistCount = computed(() => catalogStore.wishlist.length)

const SOLAR_TYPES = new Set(['planet', 'moon', 'sun'])
const dsoWishlistCount = computed(() => catalogStore.wishlist.filter(t => !SOLAR_TYPES.has(t.type)).length)
const solarWishlistCount = computed(() => catalogStore.wishlist.filter(t => SOLAR_TYPES.has(t.type)).length)

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

const switchToSavedPlans = () => {
  bottomTab.value = 'saved'
  planningStore.loadSavedPlans()
}

const loadPlan = async (id) => {
  try {
    await planningStore.loadPlan(id)
  } catch (err) {
    console.error('Failed to load plan:', err)
  }
}

const deletePlan = async (id, name) => {
  if (!confirm(`Delete "${name}"?`)) return
  try {
    await planningStore.deleteSavedPlan(id)
  } catch (err) {
    console.error('Failed to delete plan:', err)
  }
}

// --- Wishlist capture tracking ---

function effectiveStatus(target) {
  const c = catalogStore.captureMap[target.name]
  if (!c) return null
  const s = c.status ?? c.suggested_status
  return s === 'needs_more_data' ? 'needs_more' : s
}

function statusDotClass(status) {
  return { complete: 'bg-green-500', needs_more: 'bg-amber-500' }[status] ?? 'bg-gray-500'
}

const needsImagingTargets = computed(() =>
  catalogStore.wishlist.filter(t => effectiveStatus(t) !== 'complete')
)
const completedTargets = computed(() =>
  catalogStore.wishlist.filter(t => effectiveStatus(t) === 'complete')
)

const expandedWishlistItem = ref(null)
function toggleWishlistExpand(name) {
  expandedWishlistItem.value = expandedWishlistItem.value === name ? null : name
}
async function setWishlistStatus(target, status) {
  await catalogStore.updateCaptureStatus(target.name, status)
}

onMounted(() => {
  weatherStore.fetchCurrentWeather()
  planningStore.loadSavedPlans()
})
</script>
