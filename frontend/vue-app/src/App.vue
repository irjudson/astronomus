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

const settingsStore = useSettingsStore()
onMounted(() => settingsStore.load())
</script>

<style scoped>
/* No custom styles - use Tailwind */
</style>
