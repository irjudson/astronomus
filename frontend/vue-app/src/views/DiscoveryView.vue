<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- Left panel header -->
    <template #left-header>
      <div>
        <h3 class="text-sm font-semibold text-gray-200">Filters</h3>
      </div>
    </template>

    <!-- Left panel label (for peek tab) -->
    <template #left-label>Filters</template>

    <!-- Left: Search Filters (only for Deep Sky tab) -->
    <template #left>
      <div v-if="activeDiscoveryTab === 'deep-sky'" class="p-3 space-y-1">
        <SearchFilters />
      </div>
      <div v-else class="p-3 text-xs text-gray-500">
        Filters apply to Deep Sky catalog only.
      </div>
    </template>

    <!-- Main: Content -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Discovery</h2>
          <p v-if="activeDiscoveryTab === 'deep-sky'" class="text-sm text-gray-500">
            {{ catalogStore.totalItems }} celestial objects
          </p>
          <p v-else class="text-sm text-gray-500">
            Solar system objects
          </p>
        </div>

        <!-- Tab Bar -->
        <div class="flex gap-1 px-4 pt-3 pb-0 border-b border-gray-800 flex-none">
          <button
            @click="activeDiscoveryTab = 'deep-sky'"
            :class="[
              'px-4 py-1.5 rounded-t text-sm font-medium transition-colors',
              activeDiscoveryTab === 'deep-sky'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200'
            ]"
          >
            Deep Sky
          </button>
          <button
            @click="activeDiscoveryTab = 'solar-system'"
            :class="[
              'px-4 py-1.5 rounded-t text-sm font-medium transition-colors',
              activeDiscoveryTab === 'solar-system'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200'
            ]"
          >
            Solar System
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-hidden">
          <template v-if="activeDiscoveryTab === 'deep-sky'">
            <CatalogGrid />
          </template>
          <SolarSystemPanel v-else-if="activeDiscoveryTab === 'solar-system'" />
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import SearchFilters from '@/components/discovery/SearchFilters.vue'
import CatalogGrid from '@/components/discovery/CatalogGrid.vue'
import SolarSystemPanel from '@/components/discovery/SolarSystemPanel.vue'

const catalogStore = useCatalogStore()
const leftPanelVisible = ref(true)
const activeDiscoveryTab = ref('deep-sky')

onMounted(async () => {
  await Promise.all([
    catalogStore.fetchCatalogData(),
    catalogStore.fetchWishlist(),
  ])
})
</script>
