import { defineStore } from 'pinia';
import axios from 'axios';

export const useCatalogStore = defineStore('catalog', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
    currentPage: 1,
    pageSize: 20, // Initial default, will be dynamic
    totalItems: 0,
    filters: {
      search: '',
      type: '',
      constellation: '',
      max_magnitude: '',
      sort_by: 'name',
    },
    prefetchCache: new Map(),
    selectedTargets: [], // For "Add to Plan" functionality
  }),
  getters: {
    totalPages: (state) => Math.ceil(state.totalItems / state.pageSize),
    hasPrevPage: (state) => state.currentPage > 1,
    hasNextPage: (state) => state.currentPage < state.totalPages,
  },
  actions: {
    /**
     * Fetch catalog data from API
     */
    async fetchCatalogData(page = this.currentPage) {
      this.loading = true;
      this.error = null;
      this.currentPage = page;

      const currentFilters = {
        ...this.filters,
        page: this.currentPage,
        page_size: this.pageSize,
      };
      const cacheKey = JSON.stringify(currentFilters);

      // Check cache first
      if (this.prefetchCache.has(cacheKey)) {
        const cached = this.prefetchCache.get(cacheKey);
        this.items = cached.items || [];
        this.totalItems = cached.total || 0;
        this.loading = false;
        // Still prefetch next page in background
        this.prefetchNextPage(currentFilters);
        return;
      }

      try {
        const queryParams = new URLSearchParams();
        Object.entries(currentFilters).forEach(([key, value]) => {
          if (value !== '') {
            queryParams.append(key, value);
          }
        });

        const response = await axios.get(`/api/catalog/search?${queryParams.toString()}`);
        const data = response.data;

        this.items = data.items || [];
        this.totalItems = data.total || 0;

        // Cache the result
        this.prefetchCache.set(cacheKey, data);
        // Limit cache size to 5 pages
        if (this.prefetchCache.size > 5) {
            // Remove the oldest entry
            const oldestKey = this.prefetchCache.keys().next().value;
            this.prefetchCache.delete(oldestKey);
        }

      } catch (err) {
        this.error = 'Failed to load catalog data: ' + err.message;
        console.error('Error loading catalog data:', err);
      } finally {
        this.loading = false;
        this.prefetchNextPage(currentFilters);
      }
    },

    /**
     * Prefetch the next page in the background
     */
    async prefetchNextPage(currentFilters) {
      const nextPage = this.currentPage + 1;
      if (nextPage > this.totalPages) {
        return; // No next page to prefetch
      }

      const nextFilters = { ...currentFilters, page: nextPage };
      const cacheKey = JSON.stringify(nextFilters);

      if (this.prefetchCache.has(cacheKey)) {
        return; // Already cached
      }

      try {
        const queryParams = new URLSearchParams();
        Object.entries(nextFilters).forEach(([key, value]) => {
          if (value !== '') {
            queryParams.append(key, value);
          }
        });

        const response = await axios.get(`/api/catalog/search?${queryParams.toString()}`);
        const data = response.data;
        this.prefetchCache.set(cacheKey, data);
        console.log(`Prefetched page ${nextPage} (${data.items.length} items)`);
      } catch (err) {
        console.warn('Prefetch failed:', err);
        // Silent failure - prefetch is non-critical
      }
    },

    /**
     * Apply new filters and reset to first page
     */
    applyFilters(newFilters) {
      this.filters = { ...this.filters, ...newFilters };
      this.currentPage = 1;
      this.prefetchCache.clear(); // Clear cache on new filters
      this.fetchCatalogData();
    },

    /**
     * Clear all filters and reload data
     */
    clearFilters() {
      this.filters = {
        search: '',
        type: '',
        constellation: '',
        max_magnitude: '',
        sort_by: 'name',
      };
      this.currentPage = 1;
      this.prefetchCache.clear(); // Clear cache on clear filters
      this.fetchCatalogData();
    },

    /**
     * Set current page and fetch data
     */
    setPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.fetchCatalogData(page);
      }
    },

    /**
     * Set page size (e.g., from dynamic calculation)
     */
    setPageSize(size) {
      if (this.pageSize !== size) {
        this.pageSize = size;
        this.currentPage = 1; // Reset to first page when page size changes
        this.prefetchCache.clear(); // Clear cache on page size change
        this.fetchCatalogData();
      }
    },

    /**
     * Add a target to the selected targets list for planning
     */
    addSelectedTarget(item) {
      const exists = this.selectedTargets.some(t => t.id === item.id || t.name === item.name);
      if (!exists) {
        this.selectedTargets.push(item);
        // TODO: Implement a global notification system instead of console log
        console.log(`Added ${item.name} to plan. Total selected: ${this.selectedTargets.length}`);
      } else {
        console.log(`${item.name} is already in your plan.`);
      }
    },

    /**
     * Remove a target from the selected targets list
     */
    removeSelectedTarget(itemName) {
      this.selectedTargets = this.selectedTargets.filter(t => t.name !== itemName);
      console.log(`Removed ${itemName} from plan. Total selected: ${this.selectedTargets.length}`);
    },

    /**
     * Utility to escape HTML for display
     */
    escapeHtml(text) {
      if (text === null || text === undefined) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },

    /**
     * Format RA/Dec coordinates
     */
    formatCoordinates(ra, dec) {
        if (ra === null || ra === undefined || dec === null || dec === undefined) {
            return 'N/A';
        }
        // Convert degrees to hours (360° = 24h)
        const hours = ra / 15.0;
        const h = Math.floor(hours);
        const m = Math.floor((hours - h) * 60);
        const s = Math.floor(((hours - h) * 60 - m) * 60);
        const formattedRA = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

        const sign = dec >= 0 ? '+' : '-';
        const absDec = Math.abs(dec);
        const d = Math.floor(absDec);
        const arcmin = Math.floor((absDec - d) * 60);
        const arcsec = Math.floor(((absDec - d) * 60 - arcmin) * 60);
        const formattedDec = `${sign}${d.toString().padStart(2, '0')}:${arcmin.toString().padStart(2, '0')}:${arcsec.toString().padStart(2, '0')}`;

        return `${formattedRA} / ${formattedDec}`;
    },

    /**
     * Format constellation with full name and common name
     * This might need to be sourced from a static list or a different API endpoint
     * For now, it mirrors the old JS logic.
     */
    formatConstellation(item) {
      if (!item.constellation_full) {
          return item.constellation || 'N/A';
      }

      if (item.constellation_common) {
          // Note: Returning raw HTML here. In a Vue component, this would typically be done with v-html or separate elements.
          return `<div style="text-align: right;">${this.escapeHtml(item.constellation_full)}<br><span style="font-size: 0.9em; color: rgba(255, 255, 255, 0.6);">(${this.escapeHtml(item.constellation_common)})</span></div>`;
      }

      return this.escapeHtml(item.constellation_full);
    },
  },
});
