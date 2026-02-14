import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCatalogStore = defineStore('catalog', () => {
  const activeTab = ref('dso')
  const dsoFilters = ref({
    object_type: '',
    max_magnitude: null,
    constellation: '',
    search: ''
  })
  const cometFilters = ref({
    comet_type: '',
    max_magnitude: null,
    search: ''
  })
  const asteroidFilters = ref({
    max_magnitude: null,
    search: ''
  })

  const currentPage = ref(1)
  const itemsPerPage = ref(20)
  const totalItems = ref(0)
  const catalogItems = ref([])
  const loading = ref(false)
  const error = ref(null)

  function setActiveTab(tab) {
    activeTab.value = tab
    currentPage.value = 1 // Reset page when changing tabs
  }

  function updateDSOFilter(filter, value) {
    dsoFilters.value[filter] = value
    currentPage.value = 1 // Reset page on filter change
  }

  function updateCometFilter(filter, value) {
    cometFilters.value[filter] = value
    currentPage.value = 1
  }

  function updateAsteroidFilter(filter, value) {
    asteroidFilters.value[filter] = value
    currentPage.value = 1
  }

  function setCurrentPage(page) {
    currentPage.value = page
  }

  async function fetchCatalogItems() {
    loading.value = true
    error.value = null
    catalogItems.value = [] // Clear previous results

    try {
      let url = ''
      let params = new URLSearchParams()
      params.append('page', currentPage.value)
      params.append('page_size', itemsPerPage.value)

      switch (activeTab.value) {
        case 'dso':
          url = '/api/catalog/search'
          if (dsoFilters.value.object_type) params.append('type', dsoFilters.value.object_type)
          if (dsoFilters.value.max_magnitude) params.append('max_magnitude', dsoFilters.value.max_magnitude)
          if (dsoFilters.value.constellation) params.append('constellation', dsoFilters.value.constellation)
          if (dsoFilters.value.search) params.append('search', dsoFilters.value.search)
          break
        case 'comet':
          url = '/api/comets'
          // Comet type filter not supported by API yet
          if (cometFilters.value.max_magnitude) params.append('max_magnitude', cometFilters.value.max_magnitude)
          if (cometFilters.value.search) params.append('search', cometFilters.value.search) // Assuming API supports search for comets
          break
        case 'asteroid':
          url = '/api/asteroids'
          if (asteroidFilters.value.max_magnitude) params.append('max_magnitude', asteroidFilters.value.max_magnitude)
          if (asteroidFilters.value.search) params.append('search', asteroidFilters.value.search) // Assuming API supports search for asteroids
          break
      }

      // Note: A more robust API service would handle base URL and error handling more gracefully
      const response = await fetch(`${url}?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()

      if (activeTab.value === 'dso') {
        catalogItems.value = data.items // DSO endpoint returns { items: [], total: 0 }
        totalItems.value = data.total
      } else {
        catalogItems.value = data // Comet/Asteroid endpoints return raw list
        totalItems.value = data.length // Assuming total items is the length of the returned list for now
      }

    } catch (e) {
      error.value = 'Failed to fetch catalog items: ' + e.message
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  return {
    activeTab,
    dsoFilters,
    cometFilters,
    asteroidFilters,
    currentPage,
    itemsPerPage,
    totalItems,
    catalogItems,
    loading,
    error,
    setActiveTab,
    updateDSOFilter,
    updateCometFilter,
    updateAsteroidFilter,
    setCurrentPage,
    fetchCatalogItems
  }
})
