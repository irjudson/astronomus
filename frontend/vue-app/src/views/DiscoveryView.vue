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

    <!-- Left: Search Filters -->
    <template #left>
      <div class="p-3 space-y-1">
        <SearchFilters />
      </div>
    </template>

    <!-- Main: Catalog Grid -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Discovery</h2>
          <p class="text-sm text-gray-500">
            {{ catalogStore.totalItems }} celestial objects
          </p>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto overflow-x-hidden">
          <CatalogGrid />
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

const catalogStore = useCatalogStore()
const leftPanelVisible = ref(true)

onMounted(async () => {
  await catalogStore.fetchCatalogData()
})
</script>
