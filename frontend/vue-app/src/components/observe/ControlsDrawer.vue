<template>
  <div class="border-t border-gray-800 pt-4">
    <button
      @click="open = !open"
      class="flex items-center justify-between w-full text-left mb-2 group"
    >
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Controls</h4>
      <ChevronDownIcon
        class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
        :class="open ? 'rotate-0' : '-rotate-90'"
      />
    </button>

    <div v-show="open" class="space-y-4">

      <!-- Gain -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="text-xs text-gray-400">Gain</label>
          <span class="text-xs font-mono text-gray-300">{{ gain }}</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          v-model.number="gain"
          @change="applyExposure"
          class="w-full h-1.5 rounded-full appearance-none bg-gray-700 accent-blue-500 cursor-pointer"
        />
      </div>

      <!-- Exposure -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="text-xs text-gray-400">Exposure (ms)</label>
        </div>
        <input
          type="number"
          v-model.number="exposureMs"
          min="100"
          max="60000"
          step="100"
          @change="applyExposure"
          class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 font-mono focus:border-blue-500 focus:outline-none"
        />
      </div>

      <!-- Auto Focus -->
      <div>
        <button
          @click="runAutoFocus"
          :disabled="autoFocusing"
          class="w-full px-3 py-1.5 bg-indigo-700 hover:bg-indigo-600 text-white text-xs rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ autoFocusing ? 'Focusing…' : 'Auto Focus' }}
        </button>
      </div>

      <!-- Manual Focus (only shown when focusPos is known) -->
      <div v-if="focusPos !== null">
        <div class="flex items-center justify-between mb-1">
          <label class="text-xs text-gray-400">Focus Position</label>
          <span class="text-xs font-mono text-gray-300">{{ focusTarget }}</span>
        </div>
        <input
          type="range"
          min="0"
          max="32767"
          v-model.number="focusTarget"
          @change="applyFocusMove"
          class="w-full h-1.5 rounded-full appearance-none bg-gray-700 accent-indigo-500 cursor-pointer"
        />
      </div>

      <!-- Dew Heater -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs text-gray-400">Dew Heater</span>
          <div class="flex items-center gap-2">
            <span v-if="dewEnabled" class="text-xs text-gray-400">{{ dewPower }}%</span>
            <button
              @click="toggleDewHeater"
              class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
              :class="dewEnabled ? 'bg-blue-600' : 'bg-gray-700'"
            >
              <span
                class="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform"
                :class="dewEnabled ? 'translate-x-4' : 'translate-x-1'"
              />
            </button>
          </div>
        </div>
        <div v-if="dewEnabled" class="mt-1">
          <input
            type="range"
            min="0"
            max="100"
            v-model.number="dewPower"
            @change="applyDewHeater"
            class="w-full h-1.5 rounded-full appearance-none bg-gray-700 accent-blue-500 cursor-pointer"
          />
        </div>
      </div>

      <!-- Stack Reset -->
      <div>
        <button
          @click="resetStack"
          :disabled="stackResetting"
          class="w-full px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ stackResetting ? 'Resetting…' : 'Reset Stack' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ChevronDownIcon } from 'lucide-vue-next'
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

const open = ref(false)

// Exposure / gain state
const gain = ref(80)
const exposureMs = ref(10000)

// Focus state
const autoFocusing = ref(false)
const focusPos = ref(null)
const focusTarget = ref(5000)

// Dew heater state
const dewEnabled = ref(false)
const dewPower = ref(50)

// Stack reset state
const stackResetting = ref(false)

// -------------------------------------------------------
// API helpers
// -------------------------------------------------------

const BASE = '/api/telescope/features'

async function applyExposure() {
  try {
    await axios.post(`${BASE}/imaging/exposure`, {
      exposure_ms: exposureMs.value,
      gain: gain.value,
    })
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Exposure update failed'
    toastStore.error(msg)
  }
}

async function runAutoFocus() {
  autoFocusing.value = true
  try {
    await axios.post(`${BASE}/imaging/autofocus`)
    // Try to read back position — endpoint may not exist
    try {
      const res = await axios.get(`${BASE}/focus/position`)
      const pos = res.data?.position ?? res.data?.result ?? null
      if (pos !== null) {
        focusPos.value = pos
        focusTarget.value = pos
      }
    } catch {
      // GET focus/position not available; keep focusPos null so slider stays hidden
    }
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Autofocus failed'
    toastStore.error(msg)
  } finally {
    autoFocusing.value = false
  }
}

async function applyFocusMove() {
  try {
    await axios.post(`${BASE}/focuser/move`, { position: focusTarget.value })
    focusPos.value = focusTarget.value
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Focus move failed'
    toastStore.error(msg)
  }
}

async function toggleDewHeater() {
  dewEnabled.value = !dewEnabled.value
  try {
    await axios.post(`${BASE}/hardware/dew-heater`, {
      enabled: dewEnabled.value,
      power_level: dewPower.value,
    })
  } catch (err) {
    dewEnabled.value = !dewEnabled.value  // revert on failure
    const msg = err.response?.data?.detail || err.message || 'Dew heater update failed'
    toastStore.error(msg)
  }
}

async function applyDewHeater() {
  try {
    await axios.post(`${BASE}/hardware/dew-heater`, {
      enabled: dewEnabled.value,
      power_level: dewPower.value,
    })
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Dew heater power update failed'
    toastStore.error(msg)
  }
}

async function resetStack() {
  stackResetting.value = true
  try {
    await axios.post(`${BASE}/stack/reset`)
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Stack reset failed'
    toastStore.error(msg)
  } finally {
    stackResetting.value = false
  }
}
</script>
