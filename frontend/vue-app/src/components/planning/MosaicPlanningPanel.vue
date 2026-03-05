<template>
  <div class="panel panel-collapsible" :class="{ 'collapsed': collapsed }" id="mosaic-planning-panel">
    <div class="panel-header" @click="toggleCollapse">
      <h3>Mosaic Planning</h3>
      <span class="panel-chevron">▼</span>
    </div>
    <div class="panel-body">
      <!-- Enable Mosaic -->
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="enable-mosaic" v-model="planningStore.enableMosaic" @change="planningStore.setEnableMosaic($event.target.checked)">
          <span>Enable mosaic mode</span>
        </label>
      </div>

      <!-- Mosaic Configuration (hidden unless mosaic enabled) -->
      <div id="mosaic-config" v-if="planningStore.enableMosaic">
        <div class="form-group">
          <label for="mosaic-rows">Grid Rows</label>
          <input type="number" id="mosaic-rows" class="form-control" v-model.number="planningStore.mosaicRows" @change="planningStore.setMosaicRows($event.target.value)" value="2" min="1" max="10">
        </div>

        <div class="form-group">
          <label for="mosaic-cols">Grid Columns</label>
          <input type="number" id="mosaic-cols" class="form-control" v-model.number="planningStore.mosaicCols" @change="planningStore.setMosaicCols($event.target.value)" value="2" min="1" max="10">
        </div>

        <div class="form-group">
          <label for="mosaic-overlap">Overlap (%)</label>
          <input type="number" id="mosaic-overlap" class="form-control" v-model.number="planningStore.mosaicOverlap" @change="planningStore.setMosaicOverlap($event.target.value)" value="20" min="0" max="50" step="5">
        </div>

        <!-- Mosaic Visualization Placeholder -->
        <div class="mosaic-visualization" id="mosaic-visualization">
          <div class="visualization-placeholder">
            <p>Mosaic pattern will be visualized here</p>
          </div>
        </div>

        <!-- Estimated Time -->
        <div class="form-group">
          <label>Estimated Total Time</label>
          <div class="info-display" id="mosaic-estimated-time">
            --:--:--
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { usePlanningStore } from '@/stores/planning';

const planningStore = usePlanningStore();
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
  background: rgba(107, 114, 128, 0.1);
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
  color: rgb(107, 114, 128);
  transition: transform 300ms ease-in-out;
}

.panel-collapsible.collapsed .panel-chevron {
  transform: rotate(-90deg);
}

.form-group {
    margin-bottom: 12px;
}

.form-group label {
    display: block;
    font-size: 12px;
    color: rgb(107, 114, 128);
    margin-bottom: 4px;
    font-weight: 600;
}

.form-control {
    width: 100%;
    padding: 8px 12px;
    background: rgb(31, 41, 55);
    border: 1px solid rgb(55, 65, 81);
    border-radius: 4px;
    color: rgb(229, 231, 235);
    font-size: 14px;
}

.form-control:focus {
    outline: none;
    border-color: rgb(59, 130, 246);
}

.checkbox-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: rgb(229, 231, 235);
    font-size: 13px;
}

.checkbox-label input[type="checkbox"] {
    margin-right: 8px;
    cursor: pointer;
}

.mosaic-visualization {
    margin: 16px 0;
    padding: 16px;
    background: rgb(31, 41, 55);
    border: 1px solid rgb(55, 65, 81);
    border-radius: 4px;
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.visualization-placeholder {
    text-align: center;
    color: rgb(107, 114, 128);
    font-size: 12px;
}

.info-display {
    padding: 8px 12px;
    background: rgb(31, 41, 55);
    border: 1px solid rgb(55, 65, 81);
    border-radius: 4px;
    color: rgb(107, 114, 128);
    font-family: monospace;
    font-size: 14px;
}
</style>
