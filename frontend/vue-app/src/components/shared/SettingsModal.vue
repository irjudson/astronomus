<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6">
    <div class="bg-gray-900 border border-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">

      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h2 class="text-lg font-semibold text-gray-200">Settings</h2>
        <button
          @click="$emit('close')"
          class="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <XIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Tab bar -->
      <div class="flex gap-1 px-6 pt-4">
        <button
          v-for="tab in tabs" :key="tab.id"
          @click="activeTab = tab.id"
          class="px-4 py-2 text-sm rounded-lg transition-colors"
          :class="activeTab === tab.id ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
        >{{ tab.label }}</button>
      </div>

      <!-- Tab content -->
      <SettingsTabGeneral
        v-if="activeTab === 'general'"
        v-model="localSettings"
      />
      <SettingsTabScope
        v-else-if="activeTab === 'scope'"
        :latitude="localSettings.latitude"
        :temperatureUnit="localSettings.temperatureUnit"
      />
      <SettingsTabPlanning
        v-else-if="activeTab === 'planning'"
        v-model="planningSettings"
      />
      <div v-else-if="activeTab === 'horizon'" class="flex-1 overflow-y-auto p-6">
        <HorizonProfileEditor :min-altitude="settingsStore.settings.planMinAltitude" />
      </div>

      <!-- Automation tab -->
      <div v-else-if="activeTab === 'automation'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Auto-execute at dusk -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div class="text-sm font-semibold text-gray-300 mb-4">Auto-Execute at Dusk</div>
          <label class="flex items-center gap-3 cursor-pointer mb-3">
            <input
              type="checkbox"
              v-model="localSettings.autoExecuteEnabled"
              true-value="true"
              false-value="false"
              class="w-4 h-4 rounded"
            />
            <span class="text-sm text-gray-300">Automatically start tonight's plan at astronomical dusk</span>
          </label>
          <p class="text-xs text-gray-500 leading-relaxed mb-3">
            Requires a saved plan for today (auto-generated at noon). The scope must be reachable on your home network —
            retries every 5 min for up to {{ localSettings.autoExecuteRetryCount || 6 }} attempts.
          </p>
          <div class="flex items-center gap-2">
            <label class="text-xs text-gray-400 w-32">Scope retry attempts</label>
            <input
              v-model.number="localSettings.autoExecuteRetryCount"
              type="number" min="1" max="12" step="1"
              class="input-sm w-16"
            />
          </div>
        </div>

        <!-- Weather abort -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div class="text-sm font-semibold text-gray-300 mb-4">Weather Abort</div>
          <label class="flex items-center gap-3 cursor-pointer mb-3">
            <input
              type="checkbox"
              v-model="localSettings.weatherAbortOnRain"
              true-value="true"
              false-value="false"
              class="w-4 h-4 rounded"
            />
            <span class="text-sm text-gray-300">Stop session if rain detected</span>
          </label>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <label class="text-xs text-gray-400 w-36">Max wind (mph)</label>
              <input
                v-model.number="localSettings.weatherAbortWindMph"
                type="number" min="0" max="60" step="1"
                class="input-sm w-16"
              />
            </div>
            <div class="flex items-center gap-2">
              <label class="text-xs text-gray-400 w-36">Max humidity (%)</label>
              <input
                v-model.number="localSettings.weatherAbortHumidityPct"
                type="number" min="50" max="100" step="1"
                class="input-sm w-16"
              />
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-3">
            Checked every 10 minutes using your local weather station. Sends a webhook notification if a session is aborted.
          </p>
        </div>

        <p class="text-xs text-gray-600">
          Notifications are sent to the Webhook URL configured in the Planning tab.
        </p>
      </div>

      <!-- Footer (General and Planning only — Scope has no save) -->
      <div
        v-if="activeTab === 'general' || activeTab === 'planning' || activeTab === 'automation'"
        class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-800"
      >
        <button @click="$emit('close')" class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors">
          Cancel
        </button>
        <button @click="saveSettings" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
          Save Changes
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { XIcon } from 'lucide-vue-next'
import axios from 'axios'
import { useSettingsStore } from '@/stores/settings'
import SettingsTabGeneral from './SettingsTabGeneral.vue'
import SettingsTabScope from './SettingsTabScope.vue'
import SettingsTabPlanning from './SettingsTabPlanning.vue'
import HorizonProfileEditor from './HorizonProfileEditor.vue'

const props = defineProps({ isOpen: { type: Boolean, required: true } })
const emit = defineEmits(['close', 'save'])

const settingsStore = useSettingsStore()
const activeTab = ref('general')
const tabs = [
  { id: 'general', label: 'General' },
  { id: 'scope', label: 'Scope' },
  { id: 'planning', label: 'Planning' },
  { id: 'horizon', label: 'Horizon' },
  { id: 'automation', label: 'Automation' },
]

const localSettings = ref({ ...settingsStore.settings })
const planningSettings = ref({ daily_enabled: false, daily_time_hour: 12, daily_target_count: 5, webhook_url: '' })

watch(() => props.isOpen, async (isOpen) => {
  if (!isOpen) return
  localSettings.value = { ...settingsStore.settings }
  activeTab.value = 'general'
  try {
    const res = await axios.get('/api/settings/planning')
    planningSettings.value = { ...planningSettings.value, ...res.data }
  } catch { /* use defaults */ }
})

const saveSettings = async () => {
  await settingsStore.save(localSettings.value)
  try {
    await axios.put('/api/settings/planning', planningSettings.value)
  } catch (e) {
    console.error('Failed to save planning settings', e)
  }
  emit('save', localSettings.value)
  emit('close')
}
</script>

<style scoped>
.input-sm {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #e5e7eb;
  padding: 0.25rem 0.375rem;
  font-size: 0.75rem;
  outline: none;
}
.input-sm:focus {
  border-color: #3b82f6;
}
</style>
