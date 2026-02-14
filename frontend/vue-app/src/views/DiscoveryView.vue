<template>
  <PanelContainer
    :left-panel-visible="true"
    :right-panel-visible="false"
    :console-visible="false"
  >
    <!-- Left: Search Filters -->
    <template #left>
      <div class="h-full flex flex-col bg-gray-900 border-r border-gray-800">
        <div class="p-4 border-b border-gray-800">
          <h2 class="text-lg font-semibold text-gray-200">Astronomus</h2>
          <p class="text-xs text-gray-500 mt-1">Catalog Browser</p>
        </div>
        <div class="p-3 space-y-1">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-2">
            Filters
          </h3>
          <SearchFilters />
        </div>
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
        <div class="flex-1 overflow-hidden">
          <CatalogGrid />
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import SearchFilters from '@/components/discovery/SearchFilters.vue'
import CatalogGrid from '@/components/discovery/CatalogGrid.vue'

const catalogStore = useCatalogStore()

onMounted(async () => {
  await catalogStore.fetchCatalogData()
})
</script>
