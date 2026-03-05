<template>
  <div class="panel panel-collapsible" :class="{ 'collapsed': collapsed }" id="info-panel">
    <div class="panel-header" @click="toggleCollapse">
      <h3>Session Info</h3>
      <span class="panel-chevron">▼</span>
    </div>
    <div class="panel-body">
      <div class="session-stats">
        <div class="stat-row">
          <label>Session Time:</label>
          <span id="session-time" class="status-value">{{ executionStore.sessionTime }}</span>
        </div>
        <div class="stat-row">
          <label>Frames Captured:</label>
          <span id="frames-captured" class="status-value">{{ executionStore.framesCaptured }}</span>
        </div>
        <div class="stat-row">
          <label>Total Exposure:</label>
          <span id="total-exposure" class="status-value">{{ executionStore.totalExposure }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useExecutionStore } from '@/stores/execution';

const executionStore = useExecutionStore();
const collapsed = ref(false); // Initial state, can be controlled by parent or settings

const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
};
</script>

<style scoped>
/* Reusing styles from unified-layout.css for panels and form elements */
.panel-collapsible .panel-header {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 200ms;
}

.panel-collapsible .panel-header:hover {
  background: rgba(0, 217, 255, 0.1);
}

.panel-collapsible.collapsed .panel-header {
  border-radius: 8px;
  border-bottom: none;
}

.panel-collapsible.collapsed .panel-body {
  display: none; /* Hide body when collapsed */
}

.panel-chevron {
  font-size: 12px;
  color: #00d9ff;
  transition: transform 300ms ease-in-out;
}

.panel-collapsible.collapsed .panel-chevron {
  transform: rotate(-90deg);
}

.session-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  border-bottom: 1px solid rgba(0, 217, 255, 0.05);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.stat-row .status-value {
  font-size: 14px;
  color: #00d9ff;
  font-weight: 600;
}
</style>
