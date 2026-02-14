<template>
  <div class="catalog-view">
    <!-- Catalog Stats Banner -->
    <div class="catalog-stats">
      <span class="stats-count">{{ catalogStore.totalItems }} object{{ catalogStore.totalItems !== 1 ? 's' : '' }}</span>
      <span class="stats-filters">{{ activeFiltersDisplay }}</span>
    </div>

    <!-- Catalog Grid -->
    <div class="catalog-grid" id="catalog-grid">
      <div v-if="catalogStore.loading" class="empty-state">Loading catalog data...</div>
      <div v-else-if="catalogStore.error" class="empty-state error-message">{{ catalogStore.error }}</div>
      <div v-else-if="catalogStore.items.length === 0" class="empty-state">No objects found. Try adjusting your search or filters.</div>
      <div v-else class="grid-container">
        <div v-for="item in catalogStore.items" :key="item.id || item.name" class="catalog-card">
          <div class="catalog-card-image">
            <img :src="getImageUrl(item)" :alt="item.name" loading="lazy" @error="hideParentOnError">
          </div>
          <div class="catalog-card-content">
            <div class="catalog-card-header">
              <h4 class="catalog-card-title" v-html="formatTitle(item)"></h4>
              <span class="catalog-card-type">{{ item.type || 'unknown' }}</span>
            </div>
            <div class="catalog-card-body">
              <div class="catalog-card-detail">
                <span class="catalog-card-label">Constellation:</span>
                <span class="catalog-card-value" v-html="catalogStore.formatConstellation(item)"></span>
              </div>
              <div class="catalog-card-detail">
                <span class="catalog-card-label">Magnitude:</span>
                <span class="catalog-card-value">{{ item.magnitude !== null && item.magnitude !== undefined ? item.magnitude.toFixed(1) : 'N/A' }}</span>
              </div>
              <div class="catalog-card-detail">
                <span class="catalog-card-label">RA/Dec:</span>
                <span class="catalog-card-value">{{ catalogStore.formatCoordinates(item.ra, item.dec) }}</span>
              </div>
              <div v-if="item.size" class="catalog-card-detail">
                <span class="catalog-card-label">Size:</span>
                <span class="catalog-card-value">{{ item.size }}</span>
              </div>
            </div>
            <div class="catalog-card-actions">
              <BaseButton variant="primary" size="sm" @click="catalogStore.addSelectedTarget(item)">Add to Plan</BaseButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="catalog-pagination" :style="{ display: showPagination ? 'flex' : 'none' }">
      <BaseButton variant="secondary" :disabled="!catalogStore.hasPrevPage" @click="catalogStore.setPage(catalogStore.currentPage - 1)">Previous</BaseButton>
      <span class="page-info">Page {{ catalogStore.currentPage }} of {{ catalogStore.totalPages }}</span>
      <BaseButton variant="secondary" :disabled="!catalogStore.hasNextPage" @click="catalogStore.setPage(catalogStore.currentPage + 1)">Next</BaseButton>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useCatalogStore } from '@/stores/catalog';
import BaseButton from '@/components/common/BaseButton.vue';
// import Masonry from 'masonry-layout'; // Will integrate later if needed

const catalogStore = useCatalogStore();

// --- Computed Properties ---
const activeFiltersDisplay = computed(() => {
  const filters = catalogStore.filters;
  const active = [];
  if (filters.search) active.push(`Search: "${filters.search}"`);
  if (filters.type) active.push(`Type: ${filters.type}`);
  if (filters.constellation) active.push(`Constellation: ${filters.constellation}`);
  if (filters.max_magnitude) active.push(`Max Mag: ${filters.max_magnitude}`);
  return active.length > 0 ? active.join(' • ') : '';
});

const showPagination = computed(() => {
  return catalogStore.totalItems > catalogStore.pageSize;
});

// --- Methods ---
const getImageUrl = (item) => {
  return item.image_url || `/api/images/targets/${encodeURIComponent(item.id || item.name)}`;
};

const hideParentOnError = (event) => {
  event.target.parentElement.style.display = 'none';
};

const formatTitle = (item) => {
  let title = item.id || item.name || 'Unknown';
  if (item.common_name && item.common_name !== item.id) {
    title = `${catalogStore.escapeHtml(item.id)} - ${catalogStore.escapeHtml(item.common_name)}`;
  }
  return title;
};

// --- Dynamic Page Size Calculation (Ported from old JS) ---
let resizeObserver = null;
let resizeTimeout = null;

const calculatePageSize = () => {
  const mainContent = document.getElementById('main-content'); // Assuming main-content is the parent
  const catalogGrid = document.getElementById('catalog-grid');
  const catalogPagination = document.querySelector('.catalog-pagination');

  if (!mainContent || !catalogGrid) {
    return 20; // Default if elements not found
  }

  const mainHeight = mainContent.clientHeight;
  const paginationHeight = catalogPagination ? catalogPagination.offsetHeight : 50; // Estimate if hidden

  const mainPadding = 48; // 24px top + 24px bottom from .main-content padding
  const availableHeight = mainHeight - paginationHeight - mainPadding;

  const gridWidth = catalogGrid.clientWidth;

  // These values should ideally come from CSS variables or a utility for consistency
  const screenWidth = window.innerWidth;
  const cardMinWidth = screenWidth > 768 ? 260 : 220;
  const gap = 16;

  const exactCardsPerRow = (gridWidth + gap) / (cardMinWidth + gap);
  const cardsPerRow = Math.max(1, exactCardsPerRow % 1 >= 0.8 ? Math.ceil(exactCardsPerRow) : Math.floor(exactCardsPerRow));

  const rowHeight = 326; // Approx. card height (310px) + gap (16px)

  const exactRowsThatFit = availableHeight / rowHeight;
  const rowsThatFit = Math.max(1, exactRowsThatFit % 1 >= 0.8 ? Math.ceil(exactRowsThatFit) : Math.floor(exactRowsThatFit));
  const itemsThatFit = rowsThatFit * cardsPerRow;

  const newSize = Math.max(cardsPerRow, Math.min(50, itemsThatFit));
  // console.log(`📊 Page size: ${newSize} items (${rowsThatFit} rows × ${cardsPerRow} per row)`);
  // console.log(`   Grid: ${gridWidth}px wide, ${availableHeight}px available height`);
  return newSize;
};

const updatePageSize = () => {
  const newSize = calculatePageSize();
  catalogStore.setPageSize(newSize);
};

onMounted(() => {
  catalogStore.fetchCatalogData(); // Initial data fetch

  // Setup ResizeObserver
  const mainContent = document.getElementById('main-content');
  if (mainContent) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        updatePageSize();
      }, 250); // Debounce
    });
    resizeObserver.observe(mainContent);
  }

  // Initial page size calculation
  updatePageSize();
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});

// Watch for changes in pageSize from store to re-evaluate grid if Masonry was used
// watch(() => catalogStore.pageSize, (newSize, oldSize) => {
//   if (newSize !== oldSize && masonryInstance) {
//     masonryInstance.layout();
//   }
// });

// --- Masonry Integration (Future) ---
// let masonryInstance = null;
// const initMasonry = () => {
//   const grid = document.getElementById('catalog-grid');
//   if (grid && typeof Masonry !== 'undefined') {
//     masonryInstance = new Masonry(grid, {
//       itemSelector: '.catalog-card',
//       columnWidth: '.catalog-card',
//       gutter: 16,
//       fitWidth: false,
//       percentPosition: false
//     });
//   }
// };

// onMounted(() => {
//   // Call initMasonry after data is loaded and DOM is updated
//   watch(() => catalogStore.items, (newItems) => {
//     if (newItems.length > 0) {
//       setTimeout(() => {
//         initMasonry();
//       }, 0);
//     }
//   }, { immediate: true });
// });

// onUnmounted(() => {
//   if (masonryInstance) {
//     masonryInstance.destroy();
//   }
// });
</script>

<style scoped>
/* Catalog Stats Banner */
.catalog-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  @apply px-4 py-3 bg-astro-elevated border-b border-astro-border mb-4;
}

.stats-count {
  @apply text-astro-text font-semibold;
}

.stats-filters {
  @apply text-astro-text-muted text-sm;
}

/* Basic grid container for cards - can be replaced by Masonry setup */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); /* Adapts to available width */
  gap: 16px; /* Gap between cards */
  padding-bottom: 16px; /* Ensure space below last row */
  align-items: start; /* Align items to the top */
}

/* Catalog Card styles (ported from unified-layout.css) */
.catalog-card {
  @apply bg-astro-surface border border-astro-border;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 200ms, border-color 200ms, box-shadow 200ms;
  display: flex;
  flex-direction: column;
  /* width: 260px; Removed fixed width for grid layout */
}

@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}

@media (max-width: 480px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
}

.catalog-card:hover {
  transform: translateY(-2px);
  @apply border-astro-border-focus;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1); /* astro-accent with 10% opacity */
}

.catalog-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 12px 0;
  margin-bottom: 12px;
}

.catalog-card-title {
  @apply text-astro-text font-semibold text-sm;
  margin: 0;
  line-height: 1.3;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.object-type-badge,
.catalog-card-type {
  @apply bg-astro-accent/20 text-astro-accent px-2 py-1 rounded text-xs uppercase;
  display: inline-block;
}

.catalog-card-image {
  width: 100%;
  height: 140px;
  background: rgba(0, 0, 0, 0.4);
  overflow: hidden;
  flex-shrink: 0;
}

.catalog-card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.catalog-card-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.catalog-card-body {
  padding: 0 12px;
  margin-bottom: 12px;
}

.catalog-card-detail {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}

.catalog-card-label {
  @apply text-astro-text-muted;
}

.catalog-card-value {
  @apply text-astro-text;
}

.catalog-card-actions {
  display: flex;
  gap: 8px;
  padding: 0 12px 12px;
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1; /* Span across all columns */
  text-align: center;
  padding: 48px 24px;
  @apply text-astro-text-muted;
}

/* Pagination */
.catalog-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 12px 16px 0 16px;
  flex-shrink: 0;
  margin-top: auto;
}

.page-info {
  @apply text-astro-text-muted text-sm;
}
</style>
