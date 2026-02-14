<template>
  <div class="flex flex-col h-full bg-gray-950 text-gray-100">
    <!-- Page Header -->
    <div class="px-6 py-4 border-b border-gray-800 bg-gray-900/50">
      <h1 class="text-2xl font-semibold text-gray-200">Catalog Browser</h1>
      <p class="text-sm text-gray-500 mt-1">Explore deep sky objects, comets, and asteroids</p>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <!-- Catalog Type Tabs -->
      <div class="flex border-b border-gray-700 mb-6">
        <button
          @click="catalogStore.setActiveTab('dso')"
          :class="{'border-purple-500 text-purple-400': catalogStore.activeTab === 'dso', 'border-transparent text-gray-400 hover:text-gray-200': catalogStore.activeTab !== 'dso'}"
          class="py-2 px-4 text-sm font-medium focus:outline-none border-b-2 transition-colors duration-200"
        >
          Deep Sky Objects
        </button>
        <button
          @click="catalogStore.setActiveTab('comet')"
          :class="{'border-purple-500 text-purple-400': catalogStore.activeTab === 'comet', 'border-transparent text-gray-400 hover:text-gray-200': catalogStore.activeTab !== 'comet'}"
          class="py-2 px-4 text-sm font-medium focus:outline-none border-b-2 transition-colors duration-200"
        >
          Comets
        </button>
        <button
          @click="catalogStore.setActiveTab('asteroid')"
          :class="{'border-purple-500 text-purple-400': catalogStore.activeTab === 'asteroid', 'border-transparent text-gray-400 hover:text-gray-200': catalogStore.activeTab !== 'asteroid'}"
          class="py-2 px-4 text-sm font-medium focus:outline-none border-b-2 transition-colors duration-200"
        >
          Asteroids
        </button>
      </div>

      <!-- Filters Section -->
      <div class="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-6">
        <h2 class="text-lg font-semibold text-gray-200 mb-3">Filters</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Common Search Input -->
          <div class="filter-group">
            <label for="search" class="block text-sm font-medium text-gray-400 mb-1">Search</label>
            <input type="text" id="search" placeholder="Name or catalog ID"
                   v-model="currentFilterValues.search"
                   class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500" />
          </div>

          <template v-if="catalogStore.activeTab === 'dso'">
            <div class="filter-group">
              <label for="dso-type" class="block text-sm font-medium text-gray-400 mb-1">Object Type</label>
              <select id="dso-type"
                      v-model="catalogStore.dsoFilters.object_type"
                      class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500">
                <option value="">All Types</option>
                <option value="galaxy">Galaxy</option>
                <option value="nebula">Nebula</option>
                <option value="cluster">Cluster</option>
                <option value="planetary nebula">Planetary Nebula</option>
              </select>
            </div>
            <div class="filter-group">
              <label for="dso-max-mag" class="block text-sm font-medium text-gray-400 mb-1">Max Magnitude</label>
              <input type="number" id="dso-max-mag" placeholder="e.g., 12.0" step="0.1"
                     v-model="catalogStore.dsoFilters.max_magnitude"
                     class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500" />
            </div>
            <div class="filter-group">
              <label for="dso-constellation" class="block text-sm font-medium text-gray-400 mb-1">Constellation</label>
              <input type="text" id="dso-constellation" placeholder="e.g., Orion"
                     v-model="catalogStore.dsoFilters.constellation"
                     class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500" />
            </div>
          </template>

          <template v-else-if="catalogStore.activeTab === 'comet'">
            <div class="filter-group">
              <label for="comet-type" class="block text-sm font-medium text-gray-400 mb-1">Comet Type</label>
              <select id="comet-type"
                      v-model="catalogStore.cometFilters.comet_type"
                      class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500">
                <option value="">All Types</option>
                <option value="short-period">Short Period</option>
                <option value="long-period">Long Period</option>
                <option value="hyperbolic">Hyperbolic</option>
              </select>
            </div>
            <div class="filter-group">
              <label for="comet-max-mag" class="block text-sm font-medium text-gray-400 mb-1">Max Magnitude</label>
              <input type="number" id="comet-max-mag" placeholder="e.g., 12.0" step="0.1"
                     v-model="catalogStore.cometFilters.max_magnitude"
                     class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500" />
            </div>
          </template>

          <template v-else-if="catalogStore.activeTab === 'asteroid'">
            <div class="filter-group">
              <label for="asteroid-max-mag" class="block text-sm font-medium text-gray-400 mb-1">Max Magnitude</label>
              <input type="number" id="asteroid-max-mag" placeholder="e.g., 12.0" step="0.1"
                     v-model="catalogStore.asteroidFilters.max_magnitude"
                     class="w-full bg-gray-700 text-gray-200 border border-gray-600 rounded-md py-2 px-3 text-sm focus:ring-purple-500 focus:border-purple-500" />
            </div>
          </template>
        </div>
        <button @click="applyFilters"
                class="mt-4 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md transition-colors duration-200">
          Apply Filters
        </button>
      </div>

      <!-- Loading, Error, or Results -->
      <div v-if="catalogStore.loading" class="text-center py-8">
        <svg class="animate-spin h-8 w-8 text-purple-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="text-gray-400 mt-2">Loading catalog items...</p>
      </div>

      <div v-else-if="catalogStore.error" class="bg-red-900/50 border border-red-700 text-red-300 p-4 rounded-lg my-4">
        <p>Error: {{ catalogStore.error }}</p>
      </div>

      <div v-else>
        <div class="mb-4">
          <h2 class="text-lg font-semibold text-gray-200">
            Results ({{ catalogStore.totalItems }} items)
          </h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="item in catalogStore.catalogItems" :key="item.id || item.designation"
               class="bg-gray-800/50 border border-gray-700 rounded-lg p-4 cursor-pointer hover:border-purple-500 transition-colors duration-200">
            <div class="flex justify-between items-start mb-2">
              <div>
                <h3 class="text-lg font-semibold text-gray-200">{{ item.name || item.common_name || item.designation }}</h3>
                <p class="text-sm text-gray-400">{{ item.id || item.designation }}</p>
              </div>
              <span :class="getBadgeClass(item.type || item.object_type || 'unknown')"
                    class="px-2 py-1 text-xs font-medium rounded-full">
                {{ item.type || item.object_type || 'Unknown' }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm text-gray-400">
              <template v-if="catalogStore.activeTab === 'dso'">
                <div><strong>Magnitude:</strong> {{ item.magnitude ? item.magnitude.toFixed(1) : 'N/A' }}</div>
                <div><strong>Size:</strong> {{ item.size || 'N/A' }}</div>
                <div><strong>RA:</strong> {{ formatRA(item.ra) }}</div>
                <div><strong>Dec:</strong> {{ formatDec(item.dec) }}</div>
                <div class="col-span-2"><strong>Constellation:</strong> {{ item.constellation_full || item.constellation || 'N/A' }}</div>
              </template>
              <template v-else-if="catalogStore.activeTab === 'comet' && item.orbital_elements">
                <div><strong>Magnitude:</strong> {{ item.current_magnitude ? item.current_magnitude.toFixed(1) : 'N/A' }}</div>
                <div><strong>Perihelion:</strong> {{ item.orbital_elements.perihelion_distance_au ? item.orbital_elements.perihelion_distance_au.toFixed(2) + ' AU' : 'N/A' }}</div>
                <div><strong>Eccentricity:</strong> {{ item.orbital_elements.eccentricity ? item.orbital_elements.eccentricity.toFixed(3) : 'N/A' }}</div>
                <div><strong>Inclination:</strong> {{ item.orbital_elements.inclination_deg ? item.orbital_elements.inclination_deg.toFixed(1) + '°' : 'N/A' }}</div>
                <div class="col-span-2"><strong>Type:</strong> {{ item.comet_type || 'N/A' }}</div>
              </template>
              <template v-else-if="catalogStore.activeTab === 'asteroid'">
                <div><strong>Magnitude:</strong> {{ item.current_magnitude ? item.current_magnitude.toFixed(1) : 'N/A' }}</div>
                <div><strong>Diameter:</strong> {{ item.diameter_km ? item.diameter_km + ' km' : 'N/A' }}</div>
                <div><strong>Orbital Period:</strong> {{ item.orbital_period_days ? (item.orbital_period_days / 365.25).toFixed(2) + ' years' : 'N/A' }}</div>
                <div class="col-span-2"><strong>Type:</strong> {{ item.asteroid_type || 'N/A' }}</div>
              </template>
            </div>
          </div>
          <div v-if="catalogStore.catalogItems.length === 0 && !catalogStore.loading && !catalogStore.error" class="col-span-full text-center py-8 text-gray-500">
            No items found matching your criteria.
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="catalogStore.totalItems > catalogStore.itemsPerPage" class="flex justify-center mt-6">
          <button @click="changePage(catalogStore.currentPage - 1)"
                  :disabled="catalogStore.currentPage === 1"
                  class="bg-gray-700 hover:bg-gray-600 text-gray-200 font-bold py-2 px-4 rounded-l-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
            Previous
          </button>
          <span class="bg-gray-800 text-gray-200 font-bold py-2 px-4">{{ catalogStore.currentPage }} / {{ totalPages }}</span>
          <button @click="changePage(catalogStore.currentPage + 1)"
                  :disabled="catalogStore.currentPage === totalPages"
                  class="bg-gray-700 hover:bg-gray-600 text-gray-200 font-bold py-2 px-4 rounded-r-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useCatalogStore } from '@/stores/catalog'

const catalogStore = useCatalogStore()

// Computed property to bind search input to appropriate filter
const currentFilterValues = computed(() => {
  if (catalogStore.activeTab === 'dso') return catalogStore.dsoFilters
  if (catalogStore.activeTab === 'comet') return catalogStore.cometFilters
  if (catalogStore.activeTab === 'asteroid') return catalogStore.asteroidFilters
  return {}
})

const totalPages = computed(() => Math.ceil(catalogStore.totalItems / catalogStore.itemsPerPage))

// Watch for changes in activeTab and fetch items
watch(() => catalogStore.activeTab, () => {
  catalogStore.fetchCatalogItems()
})

// Watch for changes in filter values and fetch items
watch(currentFilterValues, (newVal, oldVal) => {
    // Only fetch if actual filter values change, not just the object reference
    if (JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
        catalogStore.fetchCatalogItems();
    }
}, { deep: true });

// Fetch items on component mount
onMounted(() => {
  catalogStore.fetchCatalogItems()
})

const applyFilters = () => {
  catalogStore.currentPage = 1 // Reset to first page on filter apply
  catalogStore.fetchCatalogItems()
}

const changePage = (page) => {
  if (page > 0 && page <= totalPages.value) {
    catalogStore.setCurrentPage(page)
    catalogStore.fetchCatalogItems()
  }
}

// Helper for dynamic badge classes
const getBadgeClass = (type) => {
  switch (type.toLowerCase()) {
    case 'galaxy': return 'bg-blue-500/20 text-blue-400'
    case 'nebula':
    case 'planetary nebula': return 'bg-pink-500/20 text-pink-400'
    case 'cluster': return 'bg-yellow-500/20 text-yellow-400'
    case 'comet': return 'bg-green-500/20 text-green-400'
    case 'asteroid': return 'bg-orange-500/20 text-orange-400'
    default: return 'bg-gray-500/20 text-gray-400'
  }
}

// Helper functions for RA/Dec formatting
const formatRA = (degrees) => {
  if (degrees == null) return 'N/A'
  const hours = degrees / 15
  const h = Math.floor(hours)
  const m = Math.floor((hours - h) * 60)
  const s = Math.floor(((hours - h) * 60 - m) * 60)
  return `${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`
}

const formatDec = (degrees) => {
  if (degrees == null) return 'N/A'
  const sign = degrees >= 0 ? '+' : '-'
  const absDeg = Math.abs(degrees)
  const d = Math.floor(absDeg)
  const m = Math.floor((absDeg - d) * 60)
  const s = Math.floor(((absDeg - d) * 60 - m) * 60)
  return `${sign}${d.toString().padStart(2, '0')}° ${m.toString().padStart(2, '0')}' ${s.toString().padStart(2, '0')}"`
}
</script>

<style scoped>
/* Add any component-specific styles here if necessary, though Tailwind should handle most. */
</style>
