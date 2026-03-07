import { describe, it, expect } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { routes } from '../index'

describe('Router', () => {
  it('has all required routes', () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })

    const routePaths = router.getRoutes().map(r => r.path)
    expect(routePaths).toContain('/')
    expect(routePaths).toContain('/sky')
    expect(routePaths).toContain('/plan')
    expect(routePaths).toContain('/observe')
    expect(routePaths).toContain('/archive')
    expect(routePaths).toContain('/execute')
    expect(routePaths).toContain('/process')
  })

  it('has correct route names', () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })

    const routeNames = router.getRoutes().map(r => r.name).filter(Boolean)
    expect(routeNames).toContain('tonight')
    expect(routeNames).toContain('sky')
    expect(routeNames).toContain('plan')
    expect(routeNames).toContain('observe')
    expect(routeNames).toContain('archive')
  })

  it('redirects legacy execute path to observe', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })
    await router.push('/execute')
    expect(router.currentRoute.value.path).toBe('/observe')
  })

  it('redirects legacy process path to archive', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })
    await router.push('/process')
    expect(router.currentRoute.value.path).toBe('/archive')
  })
})
