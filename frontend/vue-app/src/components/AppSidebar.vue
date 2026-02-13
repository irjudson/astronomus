<template>
  <aside
    :class="['relative bg-tron-panel border-r border-tron-border transition-all duration-300',
             sidebarWidth]"
  >
    <!-- Collapse Toggle -->
    <button
      @click="appStore.toggleSidebar"
      class="absolute top-4 -right-3 bg-tron-panel border border-tron-border rounded-full w-6 h-6 flex items-center justify-center hover:bg-tron-bg"
    >
      <span class="text-xs">{{ appStore.sidebarCollapsed ? '▶' : '◀' }}</span>
    </button>

    <div v-if="!appStore.sidebarCollapsed" class="p-4">
      <!-- Navigation -->
      <nav class="space-y-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="block px-4 py-2 rounded hover:bg-tron-bg transition-colors"
          active-class="bg-tron-accent/20 text-tron-accent"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Saved Plans Section -->
      <div class="mt-8">
        <h3 class="text-sm font-semibold text-tron-text/60 px-4 mb-2">SAVED PLANS</h3>
        <div class="text-sm text-tron-text/40 px-4">No saved plans</div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const navItems = [
  { path: '/', label: 'Home' },
  { path: '/catalog', label: 'Catalog' },
  { path: '/plan', label: 'Plan' },
  { path: '/execute', label: 'Execute' },
  { path: '/process', label: 'Process' }
]

const sidebarWidth = computed(() =>
  appStore.sidebarCollapsed ? 'w-16' : 'w-64'
)
</script>
