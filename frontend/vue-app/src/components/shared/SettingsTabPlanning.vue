<template>
  <div class="flex-1 overflow-y-auto p-6 space-y-6">
    <section>
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Daily Plan Generation</h3>
      <div class="bg-gray-800 rounded-lg p-4 space-y-4">

        <!-- Enable toggle -->
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-200">Auto-generate daily plan</p>
            <p class="text-xs text-gray-500">Celery generates a plan once per day</p>
          </div>
          <button
            @click="local.daily_enabled = !local.daily_enabled"
            :class="local.daily_enabled ? 'bg-blue-600' : 'bg-gray-600'"
            class="relative w-10 h-6 rounded-full transition-colors"
          >
            <span
              :class="local.daily_enabled ? 'translate-x-5' : 'translate-x-1'"
              class="block w-4 h-4 bg-white rounded-full absolute top-1 transition-transform"
            />
          </button>
        </div>

        <!-- Time picker -->
        <div>
          <label class="block text-sm text-gray-300 mb-1">Generate at (local hour)</label>
          <select v-model.number="local.daily_time_hour"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200">
            <option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2,'0') }}:00</option>
          </select>
        </div>

        <!-- Target count -->
        <div>
          <label class="block text-sm text-gray-300 mb-1">Targets per plan</label>
          <input v-model.number="local.daily_target_count" type="number" min="1" max="20"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200" />
        </div>

        <!-- Webhook URL -->
        <div>
          <label class="block text-sm text-gray-300 mb-1">Webhook URL (optional)</label>
          <input v-model="local.webhook_url" type="url" placeholder="https://…"
            class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200" />
          <p class="text-xs text-gray-500 mt-1">POST'd when the daily plan is ready</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
const props = defineProps({ modelValue: { type: Object, required: true } })
const emit = defineEmits(['update:modelValue'])

const local = new Proxy({}, {
  get(_, key) { return props.modelValue[key] },
  set(_, key, value) {
    emit('update:modelValue', { ...props.modelValue, [key]: value })
    return true
  }
})
</script>
