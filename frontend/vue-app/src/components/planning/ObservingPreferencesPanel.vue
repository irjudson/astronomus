<template>
  <div class="panel panel-collapsible" :class="{ 'collapsed': collapsed }" id="observing-preferences-panel">
    <div class="panel-header" @click="toggleCollapse">
      <h3>Observing Preferences</h3>
      <span class="panel-chevron">▼</span>
    </div>
    <div class="panel-body">
      <!-- Date/Time Selection -->
      <div class="form-group">
        <label for="plan-date">Observation Date</label>
        <input type="date" id="plan-date" class="form-control" v-model="planningStore.observationDate" @change="planningStore.setObservationDate($event.target.value)">
      </div>

      <div class="form-group">
        <label for="plan-start-time">Start Time</label>
        <input type="time" id="plan-start-time" class="form-control" v-model="planningStore.startTime" @change="planningStore.setStartTime($event.target.value)">
      </div>

      <div class="form-group">
        <label for="plan-end-time">End Time</label>
        <input type="time" id="plan-end-time" class="form-control" v-model="planningStore.endTime" @change="planningStore.setEndTime($event.target.value)">
      </div>

      <!-- Constraints -->
      <div class="form-group">
        <label for="min-altitude">Minimum Altitude (°)</label>
        <input type="number" id="min-altitude" class="form-control" placeholder="e.g. 30" min="0" max="90" v-model.number="planningStore.minAltitude" @change="planningStore.setMinAltitude($event.target.value)">
      </div>

      <div class="form-group">
        <label for="max-moon-phase">Max Moon Illumination (%)</label>
        <input type="number" id="max-moon-phase" class="form-control" placeholder="e.g. 50" min="0" max="100" v-model.number="planningStore.maxMoonPhase" @change="planningStore.setMaxMoonPhase($event.target.value)">
      </div>

      <!-- Preference Toggles -->
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="avoid-moon" v-model="planningStore.avoidMoon" @change="planningStore.setAvoidMoon($event.target.checked)">
          <span>Avoid bright moon</span>
        </label>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="prioritize-transits" v-model="planningStore.prioritizeTransits" @change="planningStore.setPrioritizeTransits($event.target.checked)">
          <span>Prioritize meridian transits</span>
        </label>
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
</style>
