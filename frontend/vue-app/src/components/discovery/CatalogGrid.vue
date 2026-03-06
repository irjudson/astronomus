<template>
  <div class="catalog-view">
    <!-- Catalog Stats Banner -->
    <div class="catalog-stats" ref="statsEl">
      <span class="stats-count">{{ catalogStore.totalItems }} object{{ catalogStore.totalItems !== 1 ? 's' : '' }}</span>
      <span class="stats-filters">{{ activeFiltersDisplay }}</span>
    </div>

    <!-- Catalog Grid -->
    <div class="catalog-grid" ref="gridEl">
      <div v-if="catalogStore.loading" class="empty-state">Loading catalog data...</div>
      <div v-else-if="catalogStore.error" class="empty-state error-message">{{ catalogStore.error }}</div>
      <div v-else-if="catalogStore.items.length === 0" class="empty-state">No objects found. Try adjusting your search or filters.</div>
      <div v-else class="grid-container">
        <div v-for="item in catalogStore.items" :key="item.catalog_id || item.id" class="catalog-card">
          <div class="catalog-card-image">
            <img :src="getImageUrl(item)" :alt="item.name" loading="lazy" @error="hideParentOnError">
          </div>
          <div class="catalog-card-content">
            <div class="catalog-card-header cursor-pointer" @click="toggleCard(item)">
              <h4 class="catalog-card-title" v-html="formatTitle(item)"></h4>
              <div class="flex items-center gap-1 flex-shrink-0">
                <span class="catalog-card-type">{{ item.type || 'unknown' }}</span>
                <span class="text-gray-500 text-xs">{{ expandedCardId === cardKey(item) ? '▲' : '▼' }}</span>
              </div>
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
              <div v-if="item.score" class="catalog-card-detail border-t border-gray-700 pt-2 mt-2">
                <span class="catalog-card-label">Capture Score:</span>
                <span class="catalog-card-value font-semibold" :class="getScoreColor(item.score.total_score)">
                  {{ (item.score.total_score * 100).toFixed(0) }}%
                </span>
              </div>
              <div v-if="item.score" class="catalog-card-detail text-xs text-gray-500">
                <div class="flex justify-between">
                  <span>Visibility: {{ (item.score.visibility_score * 100).toFixed(0) }}%</span>
                  <span>Weather: {{ (item.score.weather_score * 100).toFixed(0) }}%</span>
                  <span>Object: {{ (item.score.object_score * 100).toFixed(0) }}%</span>
                </div>
              </div>
              <!-- Capture History -->
              <div v-if="item.capture_history" class="border-t border-gray-700 pt-2 mt-2">
                <div class="flex items-center justify-between">
                  <span :class="captureStatusClass(item.capture_history.status)" class="text-xs font-semibold px-2 py-0.5 rounded-full">
                    {{ formatCaptureStatus(item.capture_history.status) }}
                  </span>
                  <span class="catalog-card-value text-xs">
                    {{ formatExposure(item.capture_history.total_exposure_seconds) }}
                  </span>
                </div>
                <div class="flex gap-3 text-xs text-gray-500 mt-1">
                  <span v-if="item.capture_history.total_sessions">
                    {{ item.capture_history.total_sessions }} session{{ item.capture_history.total_sessions !== 1 ? 's' : '' }}
                  </span>
                  <span v-if="item.capture_history.best_fwhm">
                    FWHM {{ item.capture_history.best_fwhm.toFixed(2) }}"
                  </span>
                  <span v-if="item.capture_history.total_frames">
                    {{ item.capture_history.total_frames }} frames
                  </span>
                </div>
              </div>
              <!-- Viewing Months (shown when card expanded) -->
              <div v-if="expandedCardId === cardKey(item)" class="border-t border-gray-700 pt-2 mt-2">
                <p class="text-xs text-gray-500 mb-1">Viewing months</p>
                <div v-if="monthsLoading === cardKey(item)" class="text-xs text-gray-600">Loading…</div>
                <div v-else-if="viewingMonthsCache[cardKey(item)]" class="flex gap-1">
                  <div
                    v-for="(m, i) in viewingMonthsCache[cardKey(item)]"
                    :key="m.month"
                    :title="`${m.month_name}: ${m.rating} (${m.visibility_hours.toFixed(1)}h)`"
                    class="flex flex-col items-center gap-0.5"
                  >
                    <div :class="[RATING_COLOR[m.rating], 'w-4 h-4 rounded-full']"></div>
                    <span class="text-gray-600 text-[9px]">{{ MONTH_ABBR[i] }}</span>
                  </div>
                </div>
                <div v-else class="text-xs text-gray-600">No data</div>
              </div>
              <!-- Capture Review (shown when card expanded) -->
              <div v-if="expandedCardId === cardKey(item)" class="border-t border-gray-700 pt-2 mt-2">
                <p class="text-xs text-gray-500 mb-1">Capture status</p>
                <CaptureReviewPanel
                  :capture="item.capture_history ?? catalogStore.captureMap[cardKey(item)] ?? null"
                  @set-status="s => updateCardStatus(item, s)"
                />
              </div>
            </div>
            <div class="catalog-card-actions">
              <button
                @click="toggleWishlist(item)"
                :title="catalogStore.isInWishlist(item.name) ? 'Remove from wishlist' : 'Add to wishlist'"
                :class="catalogStore.isInWishlist(item.name)
                  ? 'px-3 py-2 bg-yellow-600/30 hover:bg-yellow-600/50 text-yellow-400 text-base rounded transition-colors'
                  : 'px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-400 hover:text-yellow-400 text-base rounded transition-colors'"
              >{{ catalogStore.isInWishlist(item.name) ? '★' : '☆' }}</button>
              <button
                @click="catalogStore.addSelectedTarget(item)"
                class="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                Add to Plan
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div class="catalog-pagination" :style="{ display: showPagination ? 'flex' : 'none' }">
      <button
        @click="catalogStore.setPage(catalogStore.currentPage - 1)"
        :disabled="!catalogStore.hasPrevPage"
        class="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700 text-gray-300 text-sm rounded transition-colors"
      >
        Previous
      </button>
      <span class="page-info">Page {{ catalogStore.currentPage }} of {{ catalogStore.totalPages }}</span>
      <button
        @click="catalogStore.setPage(catalogStore.currentPage + 1)"
        :disabled="!catalogStore.hasNextPage"
        class="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-700 text-gray-300 text-sm rounded transition-colors"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useCatalogStore } from '@/stores/catalog';
import { useSettingsStore } from '@/stores/settings';
import CaptureReviewPanel from '@/components/shared/CaptureReviewPanel.vue';
import axios from 'axios';

const catalogStore = useCatalogStore();
const settingsStore = useSettingsStore();
const gridEl = ref(null);

// --- Card expand / viewing months ---
const expandedCardId = ref(null);
const viewingMonthsCache = ref({});
const monthsLoading = ref(null);

const MONTH_ABBR = ['J','F','M','A','M','J','J','A','S','O','N','D'];
const RATING_COLOR = {
  excellent: 'bg-green-500',
  good: 'bg-green-400',
  fair: 'bg-amber-400',
  poor: 'bg-red-400',
  not_visible: 'bg-gray-700',
};

function cardKey(item) {
  return item.catalog_id ?? item.id ?? item.name;
}

function toggleCard(item) {
  const key = cardKey(item);
  if (expandedCardId.value === key) {
    expandedCardId.value = null;
    return;
  }
  expandedCardId.value = key;
  if (!viewingMonthsCache.value[key] && item.ra != null && item.dec != null) {
    fetchViewingMonths(item);
  }
}

async function fetchViewingMonths(item) {
  const key = cardKey(item);
  monthsLoading.value = key;
  try {
    const lat = settingsStore.settings.latitude ?? 0;
    const res = await axios.get('/api/viewing-months', {
      params: { ra_hours: item.ra, dec_degrees: item.dec, latitude: lat }
    });
    viewingMonthsCache.value[key] = res.data.months;
  } catch (e) {
    console.error('Viewing months fetch failed', e);
  } finally {
    monthsLoading.value = null;
  }
}

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

const showPagination = computed(() => catalogStore.totalItems > catalogStore.pageSize);

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

const toggleWishlist = (item) => {
  if (catalogStore.isInWishlist(item.name)) {
    catalogStore.removeFromWishlist(item.name);
  } else {
    catalogStore.addToWishlist(item);
  }
};

async function updateCardStatus(item, status) {
  await catalogStore.updateCaptureStatus(cardKey(item), status);
  if (item.capture_history) item.capture_history.status = status;
}

const getScoreColor = (score) => {
  if (score >= 0.8) return 'text-green-400';
  if (score >= 0.6) return 'text-blue-400';
  if (score >= 0.4) return 'text-yellow-400';
  return 'text-orange-400';
};

function formatExposure(seconds) {
  if (!seconds) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatCaptureStatus(status) {
  return { new: 'New', needs_more: 'Needs More', complete: 'Complete' }[status] ?? status;
}

function captureStatusClass(status) {
  return {
    new: 'bg-gray-700 text-gray-300',
    needs_more: 'bg-amber-900/50 text-amber-400',
    complete: 'bg-green-900/50 text-green-400',
  }[status] ?? 'bg-gray-700 text-gray-300';
}

// --- Dynamic Page Size based on visible grid area ---
let resizeObserver = null;
let resizeTimeout = null;

const CARD_MIN_WIDTH = 260;
const CARD_MIN_WIDTH_MOBILE = 220;
const CARD_ROW_HEIGHT = 346; // card height + 16px gap
const GAP = 16;
const PAGINATION_HEIGHT = 52; // pagination bar reserved height

const calculatePageSize = () => {
  if (!gridEl.value) return 20;

  // gridEl is flex:1 in the column — its clientHeight is exactly the space available
  // for cards before we add items (measured before render fills it)
  const availableHeight = gridEl.value.clientHeight - PAGINATION_HEIGHT;
  const gridWidth = gridEl.value.clientWidth;

  const cardMinWidth = window.innerWidth > 768 ? CARD_MIN_WIDTH : CARD_MIN_WIDTH_MOBILE;
  const cardsPerRow = Math.max(1, Math.floor((gridWidth + GAP) / (cardMinWidth + GAP)));
  const rowsThatFit = Math.max(1, Math.floor(availableHeight / CARD_ROW_HEIGHT));

  return Math.min(50, rowsThatFit * cardsPerRow);
};

const updatePageSize = () => {
  catalogStore.setPageSize(calculatePageSize());
};

onMounted(() => {
  if (gridEl.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(updatePageSize, 200);
    });
    resizeObserver.observe(gridEl.value);
  }
  updatePageSize();
});

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect();
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
/* Full-height flex column — no scroll at this level */
.catalog-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Catalog Stats Banner */
.catalog-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgb(17, 24, 39);
  border-bottom: 1px solid rgb(31, 41, 55);
  flex-shrink: 0;
}

.stats-count {
  color: rgb(229, 231, 235);
  font-weight: 600;
}

.stats-filters {
  color: rgb(107, 114, 128);
  font-size: 0.875rem;
}

/* Grid area fills remaining space — no overflow scroll */
.catalog-grid {
  flex: 1;
  overflow: hidden;
  padding: 1rem 1rem 0;
}

/* Basic grid container for cards */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  align-items: start;
}

/* Catalog Card styles (ported from unified-layout.css) */
.catalog-card {
  background: rgb(17, 24, 39);
  border: 1px solid rgb(31, 41, 55);
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

/* Ensure catalog-grid has no scroll, even on older browsers */
.catalog-grid {
  overflow: hidden;
}

.catalog-card:hover {
  transform: translateY(-2px);
  border-color: rgb(75, 85, 99);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.catalog-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 12px 0;
  margin-bottom: 12px;
}

.catalog-card-title {
  color: rgb(229, 231, 235);
  font-weight: 600;
  font-size: 0.875rem;
  margin: 0;
  line-height: 1.3;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

.object-type-badge,
.catalog-card-type {
  background: rgba(59, 130, 246, 0.2);
  color: rgb(59, 130, 246);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  text-transform: uppercase;
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
  color: rgb(107, 114, 128);
}

.catalog-card-value {
  color: rgb(229, 231, 235);
}

.catalog-card-actions {
  display: flex;
  gap: 8px;
  padding: 0 12px 12px;
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 48px 24px;
  color: rgb(107, 114, 128);
}

/* Pagination — fixed at bottom of the flex column */
.catalog-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  flex-shrink: 0;
}

.page-info {
  color: rgb(107, 114, 128);
  font-size: 0.875rem;
}
</style>
