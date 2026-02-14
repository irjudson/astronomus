<template>
  <div class="p-4 space-y-4">
    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Search Targets
      </label>
      <input
        v-model="searchQuery"
        type="search"
        placeholder="M31, NGC 7000, Andromeda..."
        @input="onSearchChange"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
      />
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Object Type
      </label>
      <select
        v-model="selectedType"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
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
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Constellation
      </label>
      <select
        v-model="selectedConstellation"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
      >
        <option value="">All Constellations</option>
        <option v-for="constellation in constellations" :key="constellation" :value="constellation">
          {{ constellation }}
        </option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
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

    <button
      @click="clearFilters"
      class="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm rounded transition-colors"
    >
      Clear Filters
    </button>

    <div class="text-xs text-gray-500 pt-2 border-t border-gray-800">
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
    max_magnitude: maxMagnitude.value || ''
  })
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedType.value = ''
  selectedConstellation.value = ''
  maxMagnitude.value = null
  catalogStore.clearFilters()
}

onMounted(() => {
  // Initial load happens in DiscoveryView
})
</script>
