<template>
  <div class="space-y-4">
    <!-- Horizon chart preview -->
    <div class="bg-gray-900 rounded-lg p-3">
      <svg :viewBox="`0 0 360 90`" class="w-full h-24 border border-gray-700 rounded" preserveAspectRatio="none">
        <!-- Background grid -->
        <line v-for="alt in [15,30,45,60,75]" :key="alt"
          x1="0" :y1="90-alt" x2="360" :y2="90-alt"
          stroke="#374151" stroke-width="0.5" />
        <!-- Horizon profile polygon -->
        <polygon v-if="sortedProfile.length >= 2"
          :points="polygonPoints"
          fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="1.5" />
        <!-- Min altitude line -->
        <line x1="0" :y1="90 - minAltitude" x2="360" :y2="90 - minAltitude"
          stroke="#6b7280" stroke-width="1" stroke-dasharray="4,4" />
        <text x="2" :y="90 - minAltitude - 2" fill="#9ca3af" font-size="6">min alt</text>
      </svg>
    </div>

    <!-- Controls row -->
    <div class="flex gap-2 flex-wrap">
      <button @click="startScan"
        :disabled="scanning"
        class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded transition-colors">
        {{ scanning ? `Scanning ${scanProgress}%…` : 'Scan Horizon' }}
      </button>
      <button @click="addPoint"
        class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded">
        + Add Point
      </button>
      <button @click="clearProfile"
        class="px-3 py-1.5 bg-red-900/50 hover:bg-red-900 text-red-300 text-sm rounded">
        Clear
      </button>
      <button @click="exportProfile"
        class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded ml-auto">
        Export
      </button>
      <label class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded cursor-pointer">
        Import
        <input type="file" accept=".json" @change="importProfile" class="hidden" />
      </label>
    </div>

    <!-- Point table -->
    <div class="space-y-1 max-h-48 overflow-y-auto">
      <div v-if="profile.length === 0" class="text-sm text-gray-500 text-center py-4">
        No horizon points defined. Click "Scan Horizon" or add points manually.
      </div>
      <div v-for="(pt, i) in sortedProfile" :key="i"
        class="flex items-center gap-2 bg-gray-800 px-3 py-1.5 rounded text-sm">
        <span class="text-gray-400 w-6 text-xs">{{ i + 1 }}</span>
        <label class="text-gray-400 text-xs w-12">Az</label>
        <input v-model.number="pt.az" type="number" min="0" max="359" step="5"
          class="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-gray-200 text-xs" />
        <label class="text-gray-400 text-xs w-12">Alt</label>
        <input v-model.number="pt.alt" type="number" min="0" max="45" step="1"
          class="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-gray-200 text-xs" />
        <button @click="removePoint(i)" class="ml-auto text-red-400 hover:text-red-300 text-xs">✕</button>
      </div>
    </div>

    <!-- Save button -->
    <button @click="save" :disabled="saving"
      class="w-full px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white text-sm rounded transition-colors">
      {{ saving ? 'Saving…' : 'Save Horizon Profile' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({ minAltitude: { type: Number, default: 30 } })

const profile = ref([])
const saving = ref(false)
const scanning = ref(false)
const scanProgress = ref(0)
let scanPollInterval = null

const sortedProfile = computed(() =>
  [...profile.value].sort((a, b) => a.az - b.az)
)

const polygonPoints = computed(() => {
  const pts = sortedProfile.value
  if (pts.length < 2) return ''
  const coords = pts.map(p => `${p.az},${90 - p.alt}`).join(' ')
  return `0,90 ${coords} 360,90`
})

onMounted(async () => {
  try {
    const res = await axios.get('/api/settings/horizon-profile')
    profile.value = res.data || []
  } catch {}
})

async function save() {
  saving.value = true
  try {
    await axios.put('/api/settings/horizon-profile', profile.value)
  } finally {
    saving.value = false
  }
}

function addPoint() {
  profile.value.push({ az: 0, alt: 10 })
}

function removePoint(i) {
  profile.value.splice(i, 1)
}

function clearProfile() {
  profile.value = []
}

async function startScan() {
  scanning.value = true
  scanProgress.value = 0
  try {
    const res = await axios.post('/api/horizon/scan')
    const scanId = res.data.scan_id
    scanPollInterval = setInterval(async () => {
      const status = await axios.get(`/api/horizon/scan/${scanId}/status`)
      scanProgress.value = Math.round(status.data.progress || 0)
      if (status.data.points?.length) profile.value = status.data.points
      if (status.data.status === 'complete' || status.data.status === 'error') {
        clearInterval(scanPollInterval)
        scanning.value = false
      }
    }, 2000)
  } catch (e) {
    scanning.value = false
    console.error('Scan failed:', e)
  }
}

function exportProfile() {
  const blob = new Blob([JSON.stringify(sortedProfile.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'horizon-profile.json'; a.click()
  URL.revokeObjectURL(url)
}

async function importProfile(e) {
  const file = e.target.files[0]
  if (!file) return
  const text = await file.text()
  try {
    profile.value = JSON.parse(text)
  } catch { alert('Invalid JSON file') }
}
</script>
