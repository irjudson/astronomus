<template>
  <div class="processing-preview">
    <div class="processing-header">
      <h3>Preview</h3>
      <button class="btn btn-sm btn-secondary" @click="processingStore.fetchPreview" :disabled="processingStore.previewLoading">Refresh Preview</button>
    </div>
    <div class="preview-content">
      <p v-if="processingStore.previewLoading" class="text-secondary">Loading preview...</p>
      <p v-else-if="processingStore.previewError" class="text-error">{{ processingStore.previewError }}</p>
      <img v-else-if="processingStore.previewImageUrl" :src="processingStore.previewImageUrl" alt="Processing Preview" class="full-width-image">
      <p v-else class="text-secondary">No preview available. Select files and operations, then click "Refresh Preview".</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useProcessingStore } from '@/stores/processing';

const processingStore = useProcessingStore();

onMounted(() => {
  // Optionally fetch a default preview or the last generated one on mount
  // processingStore.fetchPreview();
});
</script>

<style scoped>
.processing-preview {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.processing-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 217, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.processing-header h3 {
  color: white;
  font-size: 15px;
  margin: 0;
  font-weight: 600;
}

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  overflow-y: auto;
}

.full-width-image {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.text-secondary {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.text-error {
  color: #ff4444;
  text-align: center;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
}
</style>
