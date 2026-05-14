<template>
  <div class="flex flex-col h-full p-4 gap-4 overflow-y-auto">
    <!-- Add form -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Add Custom Target</div>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div class="col-span-2">
          <label class="text-xs text-gray-400">Name *</label>
          <input v-model="form.name" class="input-dark w-full mt-1" placeholder="My Nebula" />
        </div>
        <div>
          <label class="text-xs text-gray-400">RA (hours) *</label>
          <input v-model.number="form.ra_hours" type="number" step="0.001" min="0" max="23.999" class="input-dark w-full mt-1" />
        </div>
        <div>
          <label class="text-xs text-gray-400">Dec (degrees) *</label>
          <input v-model.number="form.dec_degrees" type="number" step="0.01" min="-90" max="90" class="input-dark w-full mt-1" />
        </div>
        <div>
          <label class="text-xs text-gray-400">Type</label>
          <select v-model="form.object_type" class="input-dark w-full mt-1">
            <option value="galaxy">Galaxy</option>
            <option value="nebula">Nebula</option>
            <option value="cluster">Cluster</option>
            <option value="planetary_nebula">Planetary Nebula</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-400">Magnitude (optional)</label>
          <input v-model.number="form.magnitude" type="number" step="0.1" class="input-dark w-full mt-1" placeholder="e.g. 9.5" />
        </div>
        <div class="col-span-2">
          <label class="text-xs text-gray-400">Notes (optional)</label>
          <input v-model="form.notes" class="input-dark w-full mt-1" placeholder="Observing notes..." />
        </div>
        <div class="col-span-2">
          <label class="text-xs text-gray-400">Image URL (optional)</label>
          <input v-model="form.image_url" class="input-dark w-full mt-1" placeholder="https://..." />
        </div>
      </div>
      <button
        @click="addTarget"
        :disabled="!form.name || form.ra_hours == null || form.dec_degrees == null || saving"
        class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
      >
        {{ saving ? 'Saving...' : 'Add Target' }}
      </button>
      <span v-if="addError" class="ml-3 text-xs text-red-400">{{ addError }}</span>
    </div>

    <!-- Target list -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
        My Targets ({{ targets.length }})
      </div>
      <div v-if="loading" class="text-xs text-gray-500">Loading...</div>
      <div v-else-if="targets.length === 0" class="text-xs text-gray-600">No custom targets yet.</div>
      <div v-else class="space-y-2">
        <div
          v-for="t in targets"
          :key="t.id"
          class="flex items-start justify-between gap-3 p-2 rounded-lg bg-gray-800/50"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-gray-200">{{ t.name }}</span>
              <span class="text-xs px-1.5 py-0.5 rounded bg-purple-900 text-purple-300">Custom</span>
              <span class="text-xs text-gray-500">{{ t.object_type }}</span>
            </div>
            <div class="text-xs text-gray-500 mt-0.5">
              RA {{ t.ra_hours?.toFixed(3) }}h · Dec {{ t.dec_degrees?.toFixed(2) }}°
              <span v-if="t.magnitude != null"> · mag {{ t.magnitude }}</span>
            </div>
            <div v-if="t.notes" class="text-xs text-gray-600 mt-0.5 truncate">{{ t.notes }}</div>
            <div v-if="t.image_url" class="mt-1">
              <img :src="t.image_url" alt="Target preview" class="h-16 w-24 object-cover rounded border border-gray-700" />
            </div>
          </div>
          <button
            @click="deleteTarget(t.id)"
            class="flex-shrink-0 text-xs text-red-500 hover:text-red-400 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const targets = ref([])
const loading = ref(false)
const saving = ref(false)
const addError = ref(null)

const form = ref({
  name: '',
  ra_hours: null,
  dec_degrees: null,
  object_type: 'other',
  magnitude: null,
  notes: '',
  image_url: '',
})

async function fetchTargets() {
  loading.value = true
  try {
    const resp = await axios.get('/api/targets/custom/')
    targets.value = resp.data
  } catch {
    targets.value = []
  } finally {
    loading.value = false
  }
}

async function addTarget() {
  addError.value = null
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      ra_hours: form.value.ra_hours,
      dec_degrees: form.value.dec_degrees,
      object_type: form.value.object_type || 'other',
      magnitude: form.value.magnitude || null,
      notes: form.value.notes || null,
      image_url: form.value.image_url || null,
    }
    const resp = await axios.post('/api/targets/custom/', payload)
    targets.value.unshift(resp.data)
    form.value = { name: '', ra_hours: null, dec_degrees: null, object_type: 'other', magnitude: null, notes: '', image_url: '' }
  } catch (err) {
    addError.value = err.response?.data?.detail || 'Failed to add target'
  } finally {
    saving.value = false
  }
}

async function deleteTarget(id) {
  try {
    await axios.delete(`/api/targets/custom/${id}`)
    targets.value = targets.value.filter(t => t.id !== id)
  } catch (err) {
    console.error('Delete failed:', err)
  }
}

onMounted(fetchTargets)
</script>

<style scoped>
.input-dark {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #e5e7eb;
  padding: 0.375rem 0.5rem;
  font-size: 0.75rem;
  outline: none;
}
.input-dark:focus {
  border-color: #3b82f6;
}
</style>
