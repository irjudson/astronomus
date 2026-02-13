<template>
  <div class="app-container flex flex-col h-screen bg-tron-bg text-tron-text">
    <!-- Header -->
    <AppHeader />

    <!-- Main content area -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar -->
      <AppSidebar />

      <!-- Main content -->
      <main class="flex-1 overflow-auto">
        <RouterView />
      </main>

      <!-- Right Panel -->
      <AppRightPanel />
    </div>

    <!-- Bottom Console -->
    <AppConsole />
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppRightPanel from '@/components/AppRightPanel.vue'
import AppConsole from '@/components/AppConsole.vue'
</script>
