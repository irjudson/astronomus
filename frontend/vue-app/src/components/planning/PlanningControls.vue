<template>
  <div class="flex flex-col h-full">

    <!-- Fixed controls at top -->
    <div class="flex-shrink-0 space-y-4 p-4">
      <section>
        <label class="block text-xs text-gray-500 mb-1">Observation Date</label>
        <input
          v-model="observationDate"
          type="date"
          class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500 transition-all"
        />
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

      <!-- Wishlist — compact input queue -->
      <section v-if="wishlistCount > 0" class="border-t border-gray-800 pt-3">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs text-gray-500 uppercase tracking-wide font-medium">Priority Queue</span>
          <span class="text-xs text-gray-600">{{ needsImagingCount }} remaining</span>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="target in needsImagingTargets"
            :key="target.name"
            class="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-800 rounded text-xs text-gray-300 group"
          >
            {{ target.name }}
            <button
              @click="catalogStore.removeFromWishlist(target.name)"
              class="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity leading-none"
            >×</button>
          </span>
        </div>
        <div v-if="completedTargets.length" class="mt-1.5 text-xs text-gray-600">
          {{ completedTargets.length }} captured ✓
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
        <p v-if="planningStore.error" class="text-xs text-red-400 mt-2">
          {{ planningStore.error }}
        </p>
      </section>
    </div>

    <!-- Saved Plans — primary output, gets remaining space -->
    <div class="flex-1 min-h-0 border-t border-gray-800 flex flex-col">
      <div class="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-gray-800">
        <span class="text-xs font-medium text-gray-400 uppercase tracking-wide">Saved Plans</span>
        <span v-if="planningStore.savedPlans.length" class="text-xs text-gray-600">{{ planningStore.savedPlans.length }}</span>
      </div>

      <div class="flex-1 min-h-0 overflow-y-auto px-2 py-2">
        <div v-if="planningStore.savedPlans.length > 0" class="space-y-1">
          <div
            v-for="plan in planningStore.savedPlans"
            :key="plan.id"
            class="flex items-center gap-2 px-2 py-2 hover:bg-gray-800 rounded group cursor-pointer"
            @click="loadPlan(plan.id)"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm text-gray-200 truncate">{{ plan.name }}</div>
              <div class="text-xs text-gray-600">{{ plan.observing_date }} · {{ plan.total_targets }} targets</div>
            </div>
            <button
              @click.stop="deletePlan(plan.id, plan.name)"
              class="text-gray-700 hover:text-red-400 text-xs px-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete"
            >×</button>
          </div>
        </div>
        <div v-else class="text-xs text-gray-500 px-2 py-4 text-center">
          No saved plans yet.<br>
          <span class="text-gray-600">Generate a plan and save it.</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlanningStore } from '@/stores/planning'
import { useCatalogStore } from '@/stores/catalog'

const planningStore = usePlanningStore()
const catalogStore = useCatalogStore()

const observationDate = ref(new Date().toISOString().split('T')[0])

const wishlistCount = computed(() => catalogStore.wishlist.length)

const SOLAR_TYPES = new Set(['planet', 'moon', 'sun'])
const dsoWishlistCount = computed(() => catalogStore.wishlist.filter(t => !SOLAR_TYPES.has(t.type)).length)
const solarWishlistCount = computed(() => catalogStore.wishlist.filter(t => SOLAR_TYPES.has(t.type)).length)

function effectiveStatus(target) {
  const c = catalogStore.captureMap[target.name]
  if (!c) return null
  const s = c.status ?? c.suggested_status
  return s === 'needs_more_data' ? 'needs_more' : s
}

const needsImagingTargets = computed(() =>
  catalogStore.wishlist.filter(t => effectiveStatus(t) !== 'complete')
)
const needsImagingCount = computed(() => needsImagingTargets.value.length)
const completedTargets = computed(() =>
  catalogStore.wishlist.filter(t => effectiveStatus(t) === 'complete')
)

const generatePlan = async () => {
  try {
    planningStore.observationDate = observationDate.value
    planningStore.saveConstraints().catch(() => {})
    await planningStore.generatePlan()
  } catch (err) {
    console.error('Failed to generate plan:', err)
  }
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

onMounted(() => {
  planningStore.loadSavedPlans()
})
</script>
