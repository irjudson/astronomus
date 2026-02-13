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
    expect(routePaths).toContain('/catalog')
    expect(routePaths).toContain('/plan')
    expect(routePaths).toContain('/execute')
    expect(routePaths).toContain('/process')
  })
})
