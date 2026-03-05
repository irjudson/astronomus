<template>
  <div v-if="isOpen" class="modal" @click.self="closeModal">
    <div class="modal-content modal-dark">
      <div class="modal-header">
        <h2>Weather Conditions</h2>
        <button class="modal-close" @click="closeModal">×</button>
      </div>
      <div class="modal-body">
        <div v-if="weatherStore.loading">Loading weather data...</div>
        <div v-else-if="weatherStore.error" class="error-message">{{ weatherStore.error }}</div>
        <div v-else-if="weatherStore.currentWeather" class="weather-current">
          <div class="weather-main">
            <span class="weather-icon-large">{{ weatherStore.weatherIcon }}</span>
            <div class="weather-temp">
              <span>{{ weatherStore.temperature }}</span>°C
            </div>
          </div>
          <div class="weather-details-full">
            <div class="weather-detail-row">
              <label>Source:</label>
              <span>{{ weatherStore.weatherSource }}</span>
            </div>
            <div class="weather-detail-row">
              <label>Humidity:</label>
              <span>{{ weatherStore.humidity }}</span>%
            </div>
            <div class="weather-detail-row">
              <label>Cloud Cover:</label>
              <span>{{ weatherStore.cloudCover }}</span>%
            </div>
            <div class="weather-detail-row">
              <label>Wind Speed:</label>
              <span>{{ weatherStore.windSpeed }}</span> km/h
            </div>
            <div class="weather-detail-row">
              <label>Observability:</label>
              <span :class="weatherStore.observabilityClass">{{ weatherStore.observability }}</span>
            </div>
          </div>
        </div>
        <div v-else>No weather data available.</div>
        <div class="weather-forecast">
          <h4>Forecast</h4>
          <div class="weather-forecast-list">
            <!-- Forecast items will be populated here -->
            <p v-if="!weatherStore.weatherForecast || weatherStore.weatherForecast.length === 0">No forecast available.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useWeatherStore } from '../stores/weather';

const isOpen = ref(false);
const weatherStore = useWeatherStore();

const openModal = () => {
  isOpen.value = true;
  weatherStore.fetchWeatherData();
};

const closeModal = () => {
  isOpen.value = false;
};

defineExpose({
  openModal
});

onMounted(() => {
  // Optionally fetch weather data when the component is first mounted,
  // or rely solely on `openModal` to trigger the fetch.
  // weatherStore.fetchWeatherData();
});
</script>

<style scoped>
/* Scoped styles for the modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: #1a1a1a;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  color: #fff;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #333;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.modal-header h2 {
  margin: 0;
  color: #4a9eff;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #888;
  cursor: pointer;
}

.weather-current {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.weather-main {
  text-align: center;
}

.weather-icon-large {
  font-size: 60px;
}

.weather-temp {
  font-size: 48px;
  font-weight: bold;
}

.weather-details-full {
  flex-grow: 1;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
}

.weather-detail-row {
  display: contents;
}

.weather-detail-row label {
  color: #888;
  text-align: right;
  padding-right: 10px;
}

.observability-good {
  color: #4CAF50; /* Green */
}

.observability-fair {
  color: #FFC107; /* Amber */
}

.observability-poor {
  color: #F44336; /* Red */
}

.observability-unknown {
  color: #9E9E9E; /* Grey */
}

.weather-forecast h4 {
  color: #4a9eff;
  border-bottom: 1px solid #333;
  padding-bottom: 10px;
  margin-bottom: 10px;
}
</style>
