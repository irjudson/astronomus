<template>
  <div class="h-full flex flex-col gap-3 p-4 bg-gray-900 rounded-lg border border-gray-800">
    <!-- No plan -->
    <div v-if="!executionStore.currentPlan" class="flex-1 flex items-center justify-center text-sm text-gray-500">
      No plan loaded
    </div>

    <template v-else>
      <!-- Current target -->
      <div>
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="text-xs text-gray-500 uppercase tracking-wide">Now</span>
          <span v-if="currentSt" class="px-1.5 py-0.5 text-xs rounded bg-blue-900/50 text-blue-300">
            {{ currentTarget?.imaging_mode === 'planetary' ? 'Video' : 'Stack' }}
          </span>
        </div>
        <div class="text-base font-semibold text-gray-100 leading-tight">
          {{ currentTarget?.name || '—' }}
        </div>
        <div class="text-xs text-gray-500 mt-0.5">
          <span v-if="currentSt">
            Alt {{ Math.round(currentSt.start_altitude ?? 0) }}°
            <span v-if="currentSt.score?.total_score != null">
              · Score {{ (currentSt.score.total_score * 100).toFixed(0) }}%
            </span>
          </span>
        </div>
      </div>

      <!-- Progress + countdown -->
      <div v-if="currentSt && executionStore.executionStatus === 'running'">
        <div class="flex justify-between text-xs text-gray-400 mb-1">
          <span>{{ elapsedLabel }}</span>
          <span class="text-gray-200 font-medium">{{ countdownLabel }} remaining</span>
        </div>
        <div class="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div class="h-full bg-blue-500 transition-none" :style="{ width: progressPct + '%' }" />
        </div>
      </div>

      <!-- Status badge when not running -->
      <div v-if="executionStore.executionStatus !== 'running'" class="flex items-center gap-2">
        <span
          class="px-2 py-0.5 rounded text-xs font-medium"
          :class="{
            'bg-gray-700 text-gray-400': executionStore.executionStatus === 'idle',
            'bg-yellow-900/50 text-yellow-300': executionStore.executionStatus === 'paused',
            'bg-green-900/50 text-green-300': executionStore.executionStatus === 'completed',
          }"
        >{{ executionStore.executionStatus }}</span>
      </div>

      <hr class="border-gray-800" />

      <!-- Next target -->
      <div v-if="nextTarget" class="text-sm">
        <div class="text-xs text-gray-500 uppercase tracking-wide mb-1">Next</div>
        <div class="text-gray-200 font-medium leading-tight">{{ nextTarget.name }}</div>
        <div v-if="nextSt" class="text-xs text-gray-500 mt-0.5">
          {{ formatTime(nextSt.start_time) }} · {{ relativeTime(nextSt.start_time) }}
        </div>
      </div>
      <div v-else class="text-xs text-gray-600 italic">Last target in plan</div>

      <div class="flex-1" />

      <!-- Controls -->
      <div class="space-y-2">
        <!-- Running controls -->
        <template v-if="executionStore.executionStatus === 'running'">
          <div class="flex gap-2">
            <button
              @click="executionStore.skipTarget()"
              :disabled="executionStore.currentTargetIndex + 1 >= (executionStore.scheduledTargets?.length ?? 0)"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Skip ⏭
            </button>
            <button
              @click="executionStore.extendTarget(15)"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors"
            >
              +15 min
            </button>
          </div>
          <div class="flex gap-2">
            <button
              @click="executionStore.pausePlan()"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-gray-300 border border-gray-600 transition-colors"
            >
              Pause
            </button>
            <button
              @click="executionStore.stopPlan()"
              class="flex-1 px-3 py-2 text-sm rounded bg-red-900/60 hover:bg-red-900 text-red-300 border border-red-800 transition-colors"
            >
              Abort
            </button>
          </div>
        </template>

        <!-- Paused controls -->
        <template v-else-if="executionStore.executionStatus === 'paused'">
          <button
            @click="executionStore.resumeExecution()"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 text-sm rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Resume
          </button>
          <button
            @click="executionStore.stopPlan()"
            class="w-full px-3 py-1.5 text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Clear plan
          </button>
        </template>

        <!-- Idle controls (plan loaded but not started) -->
        <template v-else-if="executionStore.executionStatus === 'idle'">
          <button
            @click="executionStore.executePlan()"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 text-sm rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Execute Plan
          </button>
          <div v-if="!executionStore.connected" class="text-xs text-blue-400 text-center">
            Connect telescope to execute
          </div>
        </template>

        <!-- Completed -->
        <template v-else-if="executionStore.executionStatus === 'completed'">
          <button
            @click="executionStore.stopPlan()"
            class="w-full px-3 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
          >
            Clear Plan
          </button>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

// Live clock — ticks every second for countdown
const now = ref(Date.now())
let _ticker = null
onMounted(() => { _ticker = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { if (_ticker) clearInterval(_ticker) })

const currentTarget = computed(() => executionStore.currentTarget)
const nextTarget = computed(() => executionStore.nextTarget)

// scheduledTargets hold start/end time info with altitude + score
const currentSt = computed(() => executionStore.scheduledTargets?.[executionStore.currentTargetIndex] ?? null)
const nextSt = computed(() => executionStore.scheduledTargets?.[executionStore.currentTargetIndex + 1] ?? null)

const endMs = computed(() => {
  if (!currentSt.value?.end_time) return null
  return new Date(currentSt.value.end_time).getTime()
})
const startMs = computed(() => {
  if (!currentSt.value?.start_time) return null
  return new Date(currentSt.value.start_time).getTime()
})

const remainingMs = computed(() => {
  if (endMs.value == null) return null
  return Math.max(0, endMs.value - now.value)
})

const totalDurMs = computed(() => {
  if (startMs.value == null || endMs.value == null) return null
  return endMs.value - startMs.value
})

const progressPct = computed(() => {
  if (totalDurMs.value == null || totalDurMs.value === 0) return 0
  const elapsed = now.value - (startMs.value ?? now.value)
  return Math.min(100, Math.max(0, (elapsed / totalDurMs.value) * 100))
})

const countdownLabel = computed(() => {
  const ms = remainingMs.value
  if (ms == null) return '—'
  const h = Math.floor(ms / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
})

const elapsedLabel = computed(() => {
  if (startMs.value == null) return ''
  const elapsed = Math.max(0, now.value - startMs.value)
  const m = Math.floor(elapsed / 60000)
  return `${m}m elapsed`
})

const formatTime = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

const relativeTime = (iso) => {
  if (!iso) return ''
  const diffMs = new Date(iso).getTime() - now.value
  if (diffMs < 0) return 'overdue'
  const h = Math.floor(diffMs / 3600000)
  const m = Math.floor((diffMs % 3600000) / 60000)
  if (h > 0) return `in ${h}h ${m}m`
  return `in ${m}m`
}
</script>
