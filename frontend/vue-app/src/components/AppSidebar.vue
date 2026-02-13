<template>
  <div class="flex flex-col h-full">
    <!-- Navigation -->
    <nav class="flex-1 p-4">
      <div class="space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200"
          active-class="bg-gray-800 text-white shadow-sm"
          inactive-class="text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </div>

      <!-- Saved Plans Section -->
      <div class="mt-8">
        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Saved Plans
        </div>
        <div class="px-3 py-2 text-sm text-gray-500">
          No saved plans
        </div>
      </div>

      <!-- Active Session -->
      <div class="mt-6">
        <div class="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Active Session
        </div>
        <div class="px-3 py-2 text-sm text-gray-500">
          No active session
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
const navItems = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/catalog', label: 'Catalog', icon: '📚' },
  { path: '/plan', label: 'Plan', icon: '📋' },
  { path: '/execute', label: 'Execute', icon: '▶️' },
  { path: '/process', label: 'Process', icon: '⚙️' }
]
</script>
