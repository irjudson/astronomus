<template>
  <BaseCard padding="md">
    <h3 class="text-sm font-semibold text-gray-500 mb-3">
      IMAGING CONTROLS
    </h3>

    <div class="space-y-3">
      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Exposure Time (s)
        </label>
        <BaseInput
          type="number"
          :modelValue="executionStore.imaging.currentExposure"
          @update:modelValue="updateExposure"
          min="0.1"
          step="0.1"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Gain
        </label>
        <BaseInput
          type="number"
          :modelValue="gainValue"
          @update:modelValue="updateGain"
          min="0"
          max="200"
        />
      </div>

      <div>
        <label class="text-xs text-gray-500 mb-1 block">
          Frame Count
        </label>
        <BaseInput
          type="number"
          :modelValue="frameCountValue"
          @update:modelValue="updateFrameCount"
          min="1"
        />
      </div>

      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          id="enable-dithering"
          v-model="ditheringEnabled"
          class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500"
        />
        <label for="enable-dithering" class="text-xs text-gray-200 cursor-pointer">
          Enable Dithering
        </label>
      </div>

      <div v-if="executionStore.imaging.active" class="pt-2 border-t border-gray-800">
        <div class="text-xs text-gray-500 mb-1">
          Frames: {{ executionStore.imaging.framesCaptured }} / {{ frameCountValue }}
        </div>
        <div class="w-full bg-gray-800 rounded-full h-2">
          <div
            class="bg-blue-500 h-2 rounded-full transition-all"
            :style="{ width: imagingProgress + '%' }"
          ></div>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseInput from '@/components/common/BaseInput.vue'

const executionStore = useExecutionStore()

const gainValue = ref(80)
const frameCountValue = ref(50)
const ditheringEnabled = ref(false)

const imagingProgress = computed(() => {
  if (!executionStore.imaging.active || frameCountValue.value === 0) return 0
  return Math.round((executionStore.imaging.framesCaptured / frameCountValue.value) * 100)
})

const updateExposure = (value) => {
  executionStore.imaging.currentExposure = value
}

const updateGain = (value) => {
  gainValue.value = value
}

const updateFrameCount = (value) => {
  frameCountValue.value = value
}
</script>
