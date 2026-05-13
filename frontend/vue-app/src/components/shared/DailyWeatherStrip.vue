<template>
  <div class="flex gap-1 overflow-x-auto pb-1">
    <div
      v-for="day in forecasts"
      :key="day.date"
      class="flex-1 min-w-[72px] rounded-lg p-2 text-center border"
      :class="cardClass(day)"
    >
      <div class="text-xs font-medium text-gray-400 mb-1">{{ formatDay(day.date) }}</div>
      <div class="text-xs text-gray-300 mb-1">&#x2601; {{ Math.round(day.cloud_pct) }}%</div>
      <div
        class="text-xs font-semibold px-1.5 py-0.5 rounded-full inline-block"
        :class="scoreClass(day)"
      >
        {{ Math.round(day.astronomy_score) }}
      </div>
    </div>
    <div v-if="!forecasts || forecasts.length === 0" class="text-xs text-gray-600 py-2">
      No forecast data
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  forecasts: {
    type: Array,
    default: () => [],
  },
})

function formatDay(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' })
}

function scoreClass(day) {
  if (day.astronomy_score >= 70) return 'bg-green-900 text-green-300'
  if (day.astronomy_score >= 40) return 'bg-yellow-900 text-yellow-300'
  return 'bg-red-900 text-red-300'
}

function cardClass(day) {
  if (day.astronomy_score >= 70) return 'bg-gray-900 border-green-800/40'
  if (day.astronomy_score >= 40) return 'bg-gray-900 border-yellow-800/40'
  return 'bg-gray-900 border-red-800/40'
}
</script>
