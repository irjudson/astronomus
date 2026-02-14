<template>
  <div class="execution-view flex h-full">
    <div class="execution-sidebar w-80 border-r border-astro-border bg-astro-surface overflow-y-auto space-y-4 p-4">
      <!-- Plan Execution Panel -->
      <BaseCard v-if="executionStore.currentPlan" padding="md">
        <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
          PLAN EXECUTION
        </h3>

        <div class="space-y-3">
          <div class="text-sm text-astro-text">
            Target {{ executionStore.currentTargetIndex + 1 }} of {{ executionStore.currentPlan.targets.length }}
          </div>

          <BaseButton
            v-if="!executionStore.planExecuting"
            variant="primary"
            @click="executionStore.executePlan()"
            :disabled="!executionStore.connected"
            class="w-full"
          >
            Execute Plan
          </BaseButton>

          <div v-else class="space-y-2">
            <BaseButton
              variant="secondary"
              @click="executionStore.pausePlan()"
              class="w-full"
            >
              Pause
            </BaseButton>

            <BaseButton
              variant="danger"
              @click="executionStore.stopPlan()"
              class="w-full"
            >
              Stop
            </BaseButton>
          </div>
        </div>
      </BaseCard>

      <TelescopePanel />
      <ImagingPanel />
      <HardwarePanel />
      <MessagesPanel />
    </div>

    <div class="execution-main flex-1 p-6">
      <div v-if="executionStore.currentTarget" class="space-y-6">
        <div class="text-center">
          <h2 class="text-3xl font-semibold text-astro-text mb-2">
            {{ executionStore.currentTarget.name }}
          </h2>
          <p class="text-sm text-astro-text-muted">
            {{ executionStore.currentTarget.type }}
          </p>
        </div>

        <BaseCard>
          <div class="grid grid-cols-2 gap-4 text-center">
            <div>
              <div class="text-xs text-astro-text-muted">RA</div>
              <div class="text-lg text-astro-text font-mono">
                {{ formatRA(executionStore.position.ra) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Dec</div>
              <div class="text-lg text-astro-text font-mono">
                {{ formatDec(executionStore.position.dec) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Alt</div>
              <div class="text-lg text-astro-text font-mono">
                {{ executionStore.position.alt.toFixed(1) }}°
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Az</div>
              <div class="text-lg text-astro-text font-mono">
                {{ executionStore.position.az.toFixed(1) }}°
              </div>
            </div>
          </div>
        </BaseCard>

        <div v-if="executionStore.imaging.active">
          <div class="text-sm text-astro-text-muted mb-2">
            Progress: {{ executionStore.progressPercent }}%
          </div>
          <div class="w-full bg-astro-elevated rounded-full h-2">
            <div
              class="bg-astro-accent h-2 rounded-full transition-all"
              :style="{ width: executionStore.progressPercent + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <div v-else class="flex items-center justify-center h-full">
        <p class="text-astro-text-muted">
          Load a plan or connect telescope to begin
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import HardwarePanel from '@/components/execution/HardwarePanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const executionStore = useExecutionStore()

const formatRA = (ra) => {
  const hours = ra / 15
  const h = Math.floor(hours)
  const m = Math.floor((hours - h) * 60)
  const s = Math.floor(((hours - h) * 60 - m) * 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const formatDec = (dec) => {
  const sign = dec >= 0 ? '+' : '-'
  const absDec = Math.abs(dec)
  const d = Math.floor(absDec)
  const m = Math.floor((absDec - d) * 60)
  const s = Math.floor(((absDec - d) * 60 - m) * 60)
  return `${sign}${d.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}
</script>
