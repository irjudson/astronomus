<template>
  <div class="panel panel-collapsible" :class="{ 'collapsed': collapsed }" id="location-device-panel">
    <div class="panel-header" @click="toggleCollapse">
      <h3>Location & Device</h3>
      <span class="panel-chevron">▼</span>
    </div>
    <div class="panel-body">
      <!-- Location Inputs -->
      <div class="form-group">
        <label for="plan-latitude">Latitude</label>
        <input type="number" id="plan-latitude" class="form-control" placeholder="e.g. 40.7128" step="0.0001" v-model.number="planningStore.latitude">
      </div>

      <div class="form-group">
        <label for="plan-longitude">Longitude</label>
        <input type="number" id="plan-longitude" class="form-control" placeholder="e.g. -74.0060" step="0.0001" v-model.number="planningStore.longitude">
      </div>

      <div class="form-group">
        <label for="plan-elevation">Elevation (m)</label>
        <input type="number" id="plan-elevation" class="form-control" placeholder="e.g. 10" step="1" v-model.number="planningStore.elevation">
      </div>

      <!-- Device Selection -->
      <div class="form-group">
        <label for="plan-device">Device</label>
        <select id="plan-device" class="form-control" v-model="planningStore.selectedDevice">
          <option value="">Select device...</option>
          <option v-for="device in planningStore.availableDevices" :key="device.id" :value="device.id">
            {{ device.name }}
          </option>
        </select>
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
</style>
