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

      <!-- Footer (General and Planning only — Scope has no save) -->
      <div
        v-if="activeTab === 'general' || activeTab === 'planning'"
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

const props = defineProps({ isOpen: { type: Boolean, required: true } })
const emit = defineEmits(['close', 'save'])

const settingsStore = useSettingsStore()
const activeTab = ref('general')
const tabs = [
  { id: 'general', label: 'General' },
  { id: 'scope', label: 'Scope' },
  { id: 'planning', label: 'Planning' },
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
