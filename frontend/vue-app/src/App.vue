<template>
  <div class="flex flex-col h-screen bg-gray-900 text-gray-100">
    <!-- Global Header -->
    <AppHeader />

    <!-- Main Content Area with Grid Layout -->
    <main class="flex-1 overflow-hidden">
      <div class="panel-container" :class="panelClasses">
        <!-- Left Panel -->
        <aside class="left-panel overflow-y-auto border-r border-gray-800 bg-gray-900">
          <AppSidebar />
        </aside>

        <!-- Main Content -->
        <div class="main-content overflow-hidden bg-gray-950">
          <RouterView />
        </div>

        <!-- Right Panel -->
        <aside class="right-panel overflow-y-auto border-l border-gray-800 bg-gray-900">
          <AppRightPanel />
        </aside>

        <!-- Console/Filmstrip -->
        <footer class="console border-t border-gray-800 bg-gray-900">
          <AppConsole />
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppRightPanel from '@/components/AppRightPanel.vue'
import AppConsole from '@/components/AppConsole.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const panelClasses = computed(() => ({
  'left-collapsed': appStore.sidebarCollapsed,
  'right-collapsed': appStore.rightPanelCollapsed,
  'console-collapsed': appStore.consoleCollapsed
}))
</script>

<style scoped>
.panel-container {
  display: grid;
  width: 100%;
  height: 100%;
  grid-template-columns: minmax(0, 250px) 1fr minmax(0, 320px);
  grid-template-rows: 1fr minmax(0, 200px);
  grid-template-areas:
    "left main right"
    "console console console";
  transition: grid-template-columns 300ms ease-in-out, grid-template-rows 300ms ease-in-out;
}

.left-panel {
  grid-area: left;
  min-width: 0;
}

.main-content {
  grid-area: main;
  min-width: 0;
}

.right-panel {
  grid-area: right;
  min-width: 0;
}

.console {
  grid-area: console;
  min-height: 0;
}

/* Collapsed states */
.panel-container.left-collapsed {
  grid-template-columns: 0 1fr minmax(0, 320px);
}

.panel-container.left-collapsed .left-panel {
  overflow: hidden;
  visibility: hidden;
  border-right: none;
}

.panel-container.right-collapsed {
  grid-template-columns: minmax(0, 250px) 1fr 0;
}

.panel-container.right-collapsed .right-panel {
  overflow: hidden;
  visibility: hidden;
  border-left: none;
}

.panel-container.left-collapsed.right-collapsed {
  grid-template-columns: 0 1fr 0;
}

.panel-container.console-collapsed {
  grid-template-rows: 1fr 0;
}

.panel-container.console-collapsed .console {
  overflow: hidden;
  visibility: hidden;
  border-top: none;
}
</style>
