<template>
  <BaseCard padding="md">
    <h3 class="text-sm font-semibold text-gray-500 mb-3">
      TELESCOPE CONNECTION
    </h3>

    <div v-if="!executionStore.connected" class="space-y-3">
      <BaseInput
        v-model="telescopeIp"
        type="text"
        placeholder="192.168.1.100"
        :error="!!executionStore.error"
      />

      <BaseButton
        variant="primary"
        @click="connect"
        class="w-full"
      >
        Connect
      </BaseButton>

      <div v-if="executionStore.error" class="text-xs text-red-500">
        {{ executionStore.error }}
      </div>
    </div>

    <div v-else class="space-y-3">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 bg-green-500 rounded-full"></span>
        <span class="text-sm text-gray-200">Connected to {{ executionStore.telescopeIp }}</span>
      </div>

      <BaseButton
        variant="secondary"
        @click="executionStore.disconnectTelescope()"
        class="w-full"
      >
        Disconnect
      </BaseButton>
    </div>
  </BaseCard>
</template>

<script setup>
import { ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const executionStore = useExecutionStore()
const telescopeIp = ref('192.168.1.100')

const connect = async () => {
  await executionStore.connectTelescope(telescopeIp.value)
}
</script>
