<template>
  <header class="flex flex-col px-4 py-2 border-b border-astro-border bg-astro-surface shrink-0 z-10">
    <div class="flex items-center justify-between mb-2">
      <!-- Left: Logo and Info -->
      <div class="flex items-center space-x-4">
        <div class="font-semibold text-xl tracking-tight text-astro-text flex items-center gap-2">
          <TelescopeIcon class="w-5 h-5" />
          <span>Astronomus</span>
        </div>
        <div class="text-xs text-astro-text-dim italic">
          {{ locationName || 'No location set' }}
        </div>
      </div>

      <!-- Center: Search -->
      <div class="flex-1 max-w-md mx-4">
        <div class="relative">
          <SearchIcon class="w-4 h-4 absolute left-2.5 top-2 text-astro-text-dim" />
          <input
            type="text"
            placeholder="Search targets..."
            class="bg-astro-elevated border border-astro-border focus:border-astro-accent rounded-full py-1.5 pl-9 pr-4 text-sm text-astro-text placeholder-astro-text-dim focus:ring-2 focus:ring-astro-accent/20 outline-none w-full transition-all"
          />
        </div>
      </div>

      <!-- Right: Status and Actions -->
      <div class="flex items-center space-x-3">
        <!-- Weather Status -->
        <button
          class="p-2 text-astro-text-muted hover:text-astro-text relative rounded-full hover:bg-astro-elevated transition-colors"
          title="Weather: Clear"
        >
          <CloudIcon class="w-5 h-5" />
        </button>

        <!-- Telescope Connection -->
        <button
          class="p-2 text-astro-text-muted hover:text-astro-text relative rounded-full hover:bg-astro-elevated transition-colors"
          title="Telescope Connection"
        >
          <TelescopeIcon class="w-5 h-5" />
          <span v-if="telescopeStore.connected" class="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-accent-success border-2 border-astro-surface rounded-full"></span>
          <span v-else class="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-accent-danger border-2 border-astro-surface rounded-full"></span>
        </button>

        <!-- Settings -->
        <button
          class="p-2 text-astro-text-muted hover:text-astro-text rounded-full hover:bg-astro-elevated transition-colors"
          title="Settings"
        >
          <SettingsIcon class="w-5 h-5" />
        </button>

        <!-- User Avatar -->
        <button class="w-8 h-8 rounded-full bg-gradient-to-br from-astro-accent/80 to-astro-accent flex items-center justify-center text-xs font-bold text-astro-bg shadow-lg hover:shadow-astro-accent/20 transition-shadow">
          AS
        </button>
      </div>
    </div>

    <!-- Main Navigation Links -->
    <nav class="flex justify-start space-x-6 text-sm">
      <RouterLink to="/" class="nav-link" active-class="nav-link-active">Discovery</RouterLink>
      <RouterLink to="/plan" class="nav-link" active-class="nav-link-active">Planning</RouterLink>
      <RouterLink to="/execute" class="nav-link" active-class="nav-link-active">Execution</RouterLink>
      <RouterLink to="/process" class="nav-link" active-class="nav-link-active">Processing</RouterLink>
    </nav>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { SearchIcon, TelescopeIcon, CloudIcon, SettingsIcon } from 'lucide-vue-next'
import { useTelescopeStore } from '@/stores/telescope'
import { RouterLink } from 'vue-router' // Import RouterLink

const telescopeStore = useTelescopeStore()
const locationName = ref('Default Location')
</script>

<style scoped>
.nav-link {
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem; /* rounded-md */
  color: #8b92a0; /* text-astro-text-muted */
  transition: all 0.2s ease-in-out;
}

.nav-link:hover {
  background-color: #1f2937; /* bg-astro-elevated */
  color: #d1d5db; /* text-astro-text */
}

.nav-link-active {
  background-color: #3b82f6; /* bg-astro-accent */
  color: #0a0e14; /* text-astro-bg */
  font-weight: 600;
}
</style>
