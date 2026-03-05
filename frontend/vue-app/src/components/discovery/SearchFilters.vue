<template>
  <div class="p-3 space-y-4">
    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Search Targets
      </label>
      <input
        v-model="searchQuery"
        type="search"
        placeholder="M31, NGC 7000, Andromeda..."
        @input="onSearchChange"
        class="w-full px-3 py-2 bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      />
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Object Type
      </label>
      <select
        v-model="selectedType"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      >
        <option value="">All Types</option>
        <option value="galaxy">Galaxy</option>
        <option value="nebula">Nebula</option>
        <option value="cluster">Cluster</option>
        <option value="planetary_nebula">Planetary Nebula</option>
        <option value="double_star">Double Star</option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Constellation
      </label>
      <select
        v-model="selectedConstellation"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      >
        <option value="">All Constellations</option>
        <option v-for="constellation in constellations" :key="constellation" :value="constellation">
          {{ constellation }}
        </option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Max Magnitude: {{ maxMagnitude || 'Any' }}
      </label>
      <input
        v-model.number="maxMagnitude"
        type="range"
        min="0"
        max="15"
        step="0.5"
        @change="applyFilters"
        class="w-full accent-blue-500"
      />
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Sort By
      </label>
      <select
        v-model="sortBy"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      >
        <option value="name">Name</option>
        <option value="magnitude">Brightness</option>
        <option value="type">Type</option>
        <option value="score">Best Chance (Score)</option>
      </select>
    </div>

    <div class="border-t border-gray-800 pt-4">
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3 px-1">
        Visibility Options
      </label>

      <div class="flex items-center gap-2 mb-2 px-1">
        <input
          type="checkbox"
          id="visible-now"
          v-model="visibleNow"
          @change="applyFilters"
          class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500"
        />
        <label for="visible-now" class="text-sm text-gray-300 cursor-pointer">
          Visible tonight (alt > 30°)
        </label>
      </div>

      <div class="flex items-center gap-2 px-1">
        <input
          type="checkbox"
          id="use-scoring"
          v-model="useScoring"
          @change="applyFilters"
          :disabled="!visibleNow"
          class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500 disabled:opacity-50"
        />
        <label for="use-scoring" class="text-sm text-gray-300 cursor-pointer" :class="{ 'opacity-50': !visibleNow }">
          Use comprehensive scoring
        </label>
      </div>

      <p class="text-xs text-gray-500 mt-2 px-1">
        Scoring considers location, coverage, brightness, size, and field rotation for optimal capture.
      </p>
    </div>

    <button
      @click="clearFilters"
      class="w-full px-3 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
    >
      Clear Filters
    </button>

    <div class="text-xs text-gray-500 pt-2 border-t border-gray-800 px-1">
      {{ catalogStore.totalItems }} objects found
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'

const catalogStore = useCatalogStore()

const searchQuery = ref('')
const selectedType = ref('')
const selectedConstellation = ref('')
const maxMagnitude = ref(null)
const sortBy = ref('name')
const visibleNow = ref(false)
const useScoring = ref(false)

const constellations = [
  'Andromeda', 'Aquarius', 'Aquila', 'Aries', 'Auriga',
  'Cancer', 'Canis Major', 'Cassiopeia', 'Cygnus',
  'Gemini', 'Leo', 'Orion', 'Perseus', 'Sagittarius',
  'Scorpius', 'Taurus', 'Ursa Major', 'Virgo'
]

let searchTimeout = null

const onSearchChange = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 300)
}

const applyFilters = () => {
  catalogStore.applyFilters({
    search: searchQuery.value,
    type: selectedType.value,
    constellation: selectedConstellation.value,
    max_magnitude: maxMagnitude.value || '',
    sort_by: sortBy.value,
    visible_now: visibleNow.value,
    use_scoring: useScoring.value
  })
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedType.value = ''
  selectedConstellation.value = ''
  maxMagnitude.value = null
  sortBy.value = 'name'
  visibleNow.value = false
  useScoring.value = false
  catalogStore.clearFilters()
}

onMounted(() => {
  // Initial load happens in DiscoveryView
})
</script>
