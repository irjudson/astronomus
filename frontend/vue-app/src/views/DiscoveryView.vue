<template>
  <div class="discovery-view">
    <CatalogSearchPanel />
    <CatalogGrid />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import CatalogSearchPanel from '@/components/CatalogSearchPanel.vue';
import CatalogGrid from '@/components/CatalogGrid.vue';
import { useCatalogStore } from '@/stores/catalog';

const catalogStore = useCatalogStore();

onMounted(() => {
  catalogStore.fetchCatalogData(); // Initial fetch when the view is mounted
});
</script>

<style scoped>
.discovery-view {
  display: flex;
  height: 100%; /* Ensure it takes full height of its parent */
}

/* Original layout had sidebar and main content area as siblings
   Here, CatalogSearchPanel will be on the left and CatalogGrid will take the rest */
.discovery-view > :first-child { /* CatalogSearchPanel */
  flex-shrink: 0;
  width: 320px; /* Adjust as per original sidebar width */
  margin-right: 24px; /* Gap between sidebar and main content */
}

.discovery-view > :last-child { /* CatalogGrid */
  flex-grow: 1;
  min-width: 0;
}
</style>
