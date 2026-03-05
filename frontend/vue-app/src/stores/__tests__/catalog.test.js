import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCatalogStore } from '../catalog'
import axios from 'axios'

vi.mock('axios')

describe('Catalog Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches catalog data from API', async () => {
    const mockData = {
      items: [
        { id: 'M31', name: 'Andromeda Galaxy', type: 'galaxy' },
        { id: 'M42', name: 'Orion Nebula', type: 'nebula' }
      ],
      total: 2
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    await store.fetchCatalogData()

    expect(store.items).toHaveLength(2)
    expect(store.items[0].id).toBe('M31')
    expect(store.totalItems).toBe(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('handles API errors gracefully', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))

    const store = useCatalogStore()
    await store.fetchCatalogData()

    expect(store.error).toContain('Failed to load catalog data')
    expect(store.items).toHaveLength(0)
    expect(store.loading).toBe(false)
  })

  it('applies filters and fetches data', async () => {
    const mockData = {
      items: [{ id: 'M31', name: 'Andromeda Galaxy', type: 'galaxy' }],
      total: 1
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    store.applyFilters({ type: 'galaxy', search: 'Andromeda' })

    // Wait for fetchCatalogData to complete
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(store.filters.type).toBe('galaxy')
    expect(store.filters.search).toBe('Andromeda')
    expect(store.currentPage).toBe(1)
    expect(axios.get).toHaveBeenCalled()
  })

  it('clears filters and resets to default', async () => {
    const mockData = {
      items: [],
      total: 0
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    store.applyFilters({ type: 'galaxy', search: 'Test' })
    store.clearFilters()

    expect(store.filters.type).toBe('')
    expect(store.filters.search).toBe('')
    expect(store.currentPage).toBe(1)
  })

  it('changes page and fetches data', async () => {
    const mockData = {
      items: [{ id: 'M45', name: 'Pleiades', type: 'open cluster' }],
      total: 100
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    store.totalItems = 100 // Set total to enable pagination
    await store.setPage(2)

    expect(store.currentPage).toBe(2)
    expect(axios.get).toHaveBeenCalled()
  })

  it('caches fetched data', async () => {
    const mockData = {
      items: [{ id: 'M31', name: 'Andromeda Galaxy', type: 'galaxy' }],
      total: 1
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    await store.fetchCatalogData()

    // Second fetch should use cache
    axios.get.mockClear()
    await store.fetchCatalogData()

    // Should not call API again due to cache
    expect(axios.get).not.toHaveBeenCalled()
    expect(store.items).toHaveLength(1)
  })

  it('adds selected target', () => {
    const store = useCatalogStore()
    const target = { id: 'M31', name: 'Andromeda Galaxy' }

    store.addSelectedTarget(target)

    expect(store.selectedTargets).toHaveLength(1)
    expect(store.selectedTargets[0].name).toBe('Andromeda Galaxy')
  })

  it('prevents duplicate selected targets', () => {
    const store = useCatalogStore()
    const target = { id: 'M31', name: 'Andromeda Galaxy' }

    store.addSelectedTarget(target)
    store.addSelectedTarget(target)

    expect(store.selectedTargets).toHaveLength(1)
  })

  it('removes selected target', () => {
    const store = useCatalogStore()
    const target1 = { id: 'M31', name: 'Andromeda Galaxy' }
    const target2 = { id: 'M42', name: 'Orion Nebula' }

    store.addSelectedTarget(target1)
    store.addSelectedTarget(target2)
    store.removeSelectedTarget('Andromeda Galaxy')

    expect(store.selectedTargets).toHaveLength(1)
    expect(store.selectedTargets[0].name).toBe('Orion Nebula')
  })

  it('formats coordinates correctly', () => {
    const store = useCatalogStore()

    // Test RA/Dec formatting (M31: RA=10.68°, Dec=41.27°)
    const formatted = store.formatCoordinates(10.68, 41.27)
    expect(formatted).toMatch(/^\d{2}:\d{2}:\d{2} \/ [+-]\d{2}:\d{2}:\d{2}$/)
  })

  it('handles null coordinates gracefully', () => {
    const store = useCatalogStore()

    const formatted = store.formatCoordinates(null, null)
    expect(formatted).toBe('N/A')
  })
})
