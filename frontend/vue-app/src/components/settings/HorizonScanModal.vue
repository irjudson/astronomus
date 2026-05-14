<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-2xl shadow-xl">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Horizon Scan</h2>

      <div class="bg-gray-950 rounded p-2 mb-4">
        <svg viewBox="0 0 360 90" class="w-full h-32 border border-gray-700 rounded" preserveAspectRatio="none">
          <line v-for="alt in [15,30,45,60,75]" :key="alt"
            x1="0" :y1="90-alt" x2="360" :y2="90-alt"
            stroke="#374151" stroke-width="0.5" />
          <polygon v-if="points.length >= 2"
            :points="polygonPoints"
            fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="1.5" />
        </svg>
      </div>

      <p class="text-sm text-gray-300 mb-4">
        <template v-if="status === 'scanning'">
          Scanning azimuth {{ currentAz }}° — {{ progressPct }}% complete
        </template>
        <template v-else-if="status === 'complete'">
          Scan complete — {{ points.length }} points found
        </template>
        <template v-else-if="status === 'error'">
          <span class="text-red-400">Error: {{ errorMsg }}</span>
        </template>
      </p>

      <div class="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-blue-500 transition-all duration-500"
          :style="{ width: progressPct + '%' }" />
      </div>

      <div class="flex justify-end gap-2">
        <button v-if="status !== 'complete'" @click="cancel"
          class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded transition-colors">
          Cancel
        </button>
        <button v-if="status === 'complete'" @click="$emit('scan-complete', points)"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
          Use These Points
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  scanId: { type: String, required: true },
  scanMode: { type: String, default: 'binary' },
})
const emit = defineEmits(['scan-complete', 'close'])

const points = ref([])
const currentAz = ref(0)
const progressPct = ref(0)
const status = ref('scanning')
const errorMsg = ref('')
let pollInterval = null

const polygonPoints = computed(() => {
  const pts = [...points.value].sort((a, b) => a.az - b.az)
  if (pts.length < 2) return ''
  const coords = pts.map(p => `${p.az},${90 - p.alt}`).join(' ')
  return `0,90 ${coords} 360,90`
})

async function poll() {
  try {
    const res = await axios.get(`/api/horizon/scan/${props.scanId}/status`)
    const d = res.data
    currentAz.value = d.current_az ?? 0
    progressPct.value = Math.round(d.progress ?? 0)
    if (d.points?.length) points.value = d.points
    status.value = d.status ?? 'scanning'
    if (d.status === 'error') errorMsg.value = d.error || 'Unknown error'
    if (d.status === 'complete' || d.status === 'error') clearInterval(pollInterval)
  } catch (e) {
    status.value = 'error'
    errorMsg.value = e.message
    clearInterval(pollInterval)
  }
}

async function cancel() {
  clearInterval(pollInterval)
  try { await axios.delete(`/api/horizon/scan/${props.scanId}`) } catch {}
  emit('close')
}

onMounted(() => { pollInterval = setInterval(poll, 2000); poll() })
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>
