<template>
  <div class="processing-panel">
    <div class="processing-header">
      <h3>Processing Operations</h3>
    </div>

    <div class="processing-content">
      <!-- Selected Files -->
      <div class="selected-files-section">
        <h4>Selected Files</h4>
        <div id="selected-files-list" class="selected-files-list">
          <p v-if="processingStore.selectedFiles.length === 0" class="text-secondary">No files selected</p>
          <div v-for="file in processingStore.selectedFiles" :key="file.name" class="file-item">
            <span>{{ file.name }}</span>
            <button class="btn-remove" @click="processingStore.removeSelectedFile(file.name)">&times;</button>
          </div>
        </div>
        <!-- Temporary button to add a file for testing -->
        <button class="btn btn-sm btn-secondary" @click="addTestFile">Add Test File</button>
      </div>

      <!-- Processing Operations -->
      <div class="operations-section">
        <h4>Operations</h4>

        <div class="form-group">
          <label>Operation Type</label>
          <select id="operation-type" class="form-select" v-model="processingStore.operationType" @change="processingStore.setOperationType($event.target.value)">
            <option value="">Select operation...</option>
            <option value="stack">Stack Images</option>
            <option value="calibrate">Calibrate</option>
            <option value="stretch">Stretch</option>
            <option value="gradient">Gradient Removal</option>
          </select>
        </div>

        <div class="form-group">
          <label>Output Format</label>
          <select id="output-format" class="form-select" v-model="processingStore.outputFormat" @change="processingStore.setOutputFormat($event.target.value)">
            <option value="fits">FITS</option>
            <option value="tiff">TIFF</option>
            <option value="png">PNG</option>
            <option value="jpg">JPG</option>
          </select>
        </div>

        <div class="form-group">
          <label for="output-filename">Output Filename</label>
          <input type="text" id="output-filename" class="form-control" placeholder="output" v-model="processingStore.outputFilename" @change="processingStore.setOutputFilename($event.target.value)">
        </div>

        <button class="btn btn-primary" id="start-processing-btn" :disabled="!canStartProcessing" @click="processingStore.startProcessing">Start Processing</button>
      </div>

      <!-- Processing Jobs -->
      <div class="jobs-section">
        <h4>Processing Queue</h4>
        <div id="processing-jobs" class="processing-jobs">
          <p v-if="processingStore.processingJobs.length === 0" class="text-secondary">No active jobs</p>
          <div v-for="job in processingStore.processingJobs" :key="job.id" class="job-item">
            <span>{{ job.name }} ({{ job.status }})</span>
            <progress :value="job.progress" max="100"></progress>
            <span>{{ job.progress }}%</span>
          </div>
        </div>
        <button class="btn btn-sm btn-secondary" @click="processingStore.clearProcessingJobs">Clear All Jobs</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useProcessingStore } from '@/stores/processing';

const processingStore = useProcessingStore();

const canStartProcessing = computed(() => {
  return processingStore.selectedFiles.length > 0 &&
         processingStore.operationType !== '' &&
         processingStore.outputFilename !== '' &&
         !processingStore.loading;
});

const addTestFile = () => {
  const fileNum = processingStore.selectedFiles.length + 1;
  processingStore.addSelectedFile({ name: `test_image_${fileNum}.fits` });
};
</script>

<style scoped>
.processing-panel {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.processing-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-grow: 1;
  overflow-y: auto;
}

.selected-files-section,
.operations-section,
.jobs-section {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 217, 255, 0.15);
  border-radius: 6px;
  padding: 16px;
}

.selected-files-section h4,
.operations-section h4,
.jobs-section h4 {
  color: white;
  font-size: 14px;
  margin: 0 0 12px 0;
  font-weight: 600;
}

.selected-files-list,
.processing-jobs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.file-item, .job-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 217, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 4px;
  font-size: 13px;
  color: white;
}

.btn-remove {
  background: none;
  border: none;
  color: #ff4444;
  font-size: 20px;
  font-weight: bold;
  cursor: pointer;
  padding: 0 5px;
  line-height: 1;
}

.btn-remove:hover {
  color: #ff6666;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: #00d9ff;
  margin-bottom: 4px;
  font-weight: 600;
}

.form-control, .form-select {
  width: 100%;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 217, 255, 0.3);
  border-radius: 4px;
  color: white;
  font-size: 14px;
}

.form-control:focus, .form-select:focus {
  outline: none;
  border-color: #00d9ff;
}

progress {
  width: 100px;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  margin-left: 10px;
  margin-right: 5px;
}

progress::-webkit-progress-bar {
  background-color: rgba(0, 217, 255, 0.1);
  border-radius: 4px;
}

progress::-webkit-progress-value {
  background-color: #00d9ff;
  border-radius: 4px;
  transition: width 0.3s ease-in-out;
}

.text-secondary {
  color: rgba(255, 255, 255, 0.5);
}

.btn-primary {
    background: #00d9ff;
    color: #0a0e27;
}

.btn-primary:hover:not(:disabled) {
    background: #00eaff;
    transform: scale(1.02);
}

.btn-primary:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
}

.btn-sm {
    padding: 6px 12px;
    font-size: 12px;
}
.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style>
