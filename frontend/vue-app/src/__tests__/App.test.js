import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from '../App.vue'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppRightPanel from '@/components/AppRightPanel.vue'
import AppConsole from '@/components/AppConsole.vue'

describe('App', () => {
  it('renders main layout components', () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div>Home</div>' } }]
    })

    const wrapper = mount(App, {
      global: {
        plugins: [router, createPinia()]
      }
    })

    expect(wrapper.findComponent(AppHeader).exists()).toBe(true)
    expect(wrapper.findComponent(AppSidebar).exists()).toBe(true)
    // RouterView content is dynamically rendered, so checking for its existence directly is less meaningful
    // Instead, we can check for a common element within the main content area, or the presence of AppRightPanel/AppConsole
    expect(wrapper.findComponent(AppRightPanel).exists()).toBe(true)
    expect(wrapper.findComponent(AppConsole).exists()).toBe(true)
  })
})
