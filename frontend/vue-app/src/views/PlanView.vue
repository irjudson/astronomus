<template>
  <div class="flex flex-col h-full bg-gray-950 text-gray-100">
    <!-- Page Header -->
    <div class="px-6 py-4 border-b border-gray-800 bg-gray-900/50">
      <h1 class="text-2xl font-semibold text-gray-200">Observation Plans</h1>
      <p class="text-sm text-gray-500 mt-1">Review your saved observation plans</p>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <div v-if="plans.length === 0" class="text-center py-8 text-gray-500">
        <h3 class="text-xl font-semibold mb-2">No Plans Yet</h3>
        <p>Start by creating a new observation plan using the planning tools.</p>
        <button class="mt-4 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md transition-colors duration-200">
          Create New Plan
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="plan in plans" :key="plan.id"
             class="bg-gray-800/50 border border-gray-700 rounded-lg p-6 shadow-lg hover:border-purple-500 transition-colors duration-200">
          <h2 class="text-xl font-semibold text-gray-200 mb-2">{{ plan.name }}</h2>
          <p class="text-gray-400 text-sm mb-4">{{ plan.date }} - {{ plan.location }}</p>

          <div class="mb-4">
            <h3 class="text-lg font-medium text-gray-300 mb-2">Targets ({{ plan.targets.length }})</h3>
            <ul class="list-disc list-inside text-gray-400 text-sm">
              <li v-for="target in plan.targets" :key="target">{{ target }}</li>
            </ul>
          </div>

          <div class="flex gap-2 mt-4">
            <button class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md text-sm transition-colors duration-200">
              View Details
            </button>
            <button class="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md text-sm transition-colors duration-200">
              Export
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const plans = ref([
  {
    id: 1,
    name: "Andromeda & Triangulum Hunt",
    date: "2024-10-26",
    location: "Joshua Tree, CA",
    targets: ["M31 (Andromeda Galaxy)", "M33 (Triangulum Galaxy)", "NGC 752 (Open Cluster)"],
  },
  {
    id: 2,
    name: "Orion Nebula Deep Dive",
    date: "2024-12-15",
    location: "Death Valley, NV",
    targets: ["M42 (Orion Nebula)", "M43 (De Mairan's Nebula)", "Horsehead Nebula (B33)"],
  },
  {
    id: 3,
    name: "Summer Globular Clusters",
    date: "2025-07-01",
    location: "Anza-Borrego, CA",
    targets: ["M13 (Hercules Globular Cluster)", "M92 (Globular Cluster)", "M5 (Globular Cluster)"],
  },
])
</script>

<style scoped>
/* Scoped styles for PlanView.vue */
</style>
