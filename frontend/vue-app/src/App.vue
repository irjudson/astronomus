<template>
  <div class="flex flex-col h-screen bg-gray-950">
    <!-- Global Header -->
    <AppHeader />

    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppHeader from '@/components/shared/AppHeader.vue'
import { useSettingsStore } from '@/stores/settings'
import { useCatalogStore } from '@/stores/catalog'
import { usePlanningStore } from '@/stores/planning'
import { useExecutionStore } from '@/stores/execution'

const settingsStore = useSettingsStore()
const catalogStore = useCatalogStore()
const planningStore = usePlanningStore()
const executionStore = useExecutionStore()

onMounted(async () => {
  await settingsStore.load()
  const s = settingsStore.settings
  // Push DB-loaded settings into each store (overrides localStorage-seeded defaults)
  planningStore.initFromSettings(s)
  executionStore.initFromSettings(s)
  catalogStore.initFromSettings(s)
  // Load wishlist (separate API call)
  catalogStore.fetchWishlist()
})
</script>

<style scoped>
/* No custom styles - use Tailwind */
</style>
