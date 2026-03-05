<template>
  <div class="processing-files">
    <div class="processing-header">
      <h3>Image Library</h3>
      <button class="btn btn-sm btn-secondary" @click="processingStore.fetchLibraryItems">Refresh</button>
    </div>
    <div class="library-browser">
      <div class="library-toolbar-compact">
        <input type="text" id="library-search" class="form-control form-control-sm" placeholder="Search..."
               v-model="librarySearchQuery" @input="processingStore.setLibrarySearch(librarySearchQuery)">
        <select id="library-filter" class="form-select form-select-sm"
                v-model="libraryFilterType" @change="processingStore.setLibraryFilter(libraryFilterType)">
          <option value="all">All</option>
          <option value="new">New</option>
          <option value="needs_more">Needs More</option>
          <option value="complete">Complete</option>
        </select>
      </div>
      <div id="library-grid" class="library-grid-compact">
        <p v-if="processingStore.loading" class="text-secondary">Loading...</p>
        <p v-else-if="processingStore.error" class="text-error">{{ processingStore.error }}</p>
        <p v-else-if="processingStore.filteredLibraryItems.length === 0" class="text-secondary">No images in library.</p>
        <div v-for="item in processingStore.filteredLibraryItems" :key="item.id" class="target-card">
          <h4>{{ item.name }}</h4>
          <span :class="['status-badge', `status-${item.status}`]">{{ item.status }}</span>
          <!-- Add thumbnail and click to select later -->
          <button class="btn btn-sm btn-primary" @click="processingStore.addSelectedFile(item)">Add to Processing</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useProcessingStore } from '@/stores/processing';

const processingStore = useProcessingStore();
const librarySearchQuery = ref(processingStore.librarySearch);
const libraryFilterType = ref(processingStore.libraryFilter);

onMounted(() => {
  processingStore.fetchLibraryItems();
});
</script>

<style scoped>
.processing-files {
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

.library-browser {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.library-toolbar-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
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

.library-grid-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.text-secondary {
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  padding: 10px;
}

.text-error {
  color: #ff4444;
  text-align: center;
  padding: 10px;
}

.target-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  transition: all 150ms ease;
  font-size: 12px;
}

.target-card h4 {
  color: white;
  font-size: 13px;
  margin: 0 0 5px 0;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 5px;
}

.status-badge.status-new {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.status-badge.status-needs_more {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.status-badge.status-complete {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.btn-primary {
  background: #00d9ff;
  color: #0a0e27;
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 4px;
  margin-top: 5px;
}

.btn-primary:hover {
  background: #00eaff;
}
</style>
