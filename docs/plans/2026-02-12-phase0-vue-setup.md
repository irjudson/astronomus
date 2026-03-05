# Phase 0: Vue.js 3 Setup & Base Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Initialize Vue.js 3 SPA with Vite, configure tooling, and implement base application layout shell.

**Architecture:** Create new Vue.js 3 application in `frontend/vue-app/` separate from existing vanilla JS frontend. Use Vite for fast dev/build, Pinia for state management, Vue Router for navigation, and Tailwind CSS for styling. Implement three-panel layout (sidebar, main content, right panel) with header and message console. Keep old frontend running in parallel during migration.

**Tech Stack:** Vue.js 3, Vite, Pinia, Vue Router, Tailwind CSS, Vitest (testing), Playwright (E2E)

---

## Task 1: Initialize Vue.js 3 Project with Vite

**Files:**
- Create: `frontend/vue-app/` (entire directory structure)
- Create: `frontend/vue-app/package.json`
- Create: `frontend/vue-app/vite.config.js`
- Create: `frontend/vue-app/index.html`
- Create: `frontend/vue-app/.gitignore`

**Step 1: Create Vue.js 3 project with Vite**

Run:
```bash
cd frontend
npm create vite@latest vue-app -- --template vue
cd vue-app
npm install
```

Expected: Project scaffolded with Vue 3 + Vite template

**Step 2: Install core dependencies**

Run:
```bash
npm install vue-router@4 pinia axios
npm install -D tailwindcss postcss autoprefixer vitest @vitejs/plugin-vue @vue/test-utils happy-dom
```

Expected: All dependencies installed successfully

**Step 3: Initialize Tailwind CSS**

Run:
```bash
npx tailwindcss init -p
```

Expected: `tailwind.config.js` and `postcss.config.js` created

**Step 4: Configure Tailwind CSS**

Edit `frontend/vue-app/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tron-bg': '#0a0e1a',
        'tron-panel': '#111827',
        'tron-border': '#1e3a5f',
        'tron-accent': '#00d4ff',
        'tron-text': '#e0f2ff',
      },
    },
  },
  plugins: [],
}
```

**Step 5: Update main CSS file**

Edit `frontend/vue-app/src/style.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #0a0e1a;

  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#app {
  width: 100%;
  height: 100vh;
}
```

**Step 6: Configure Vite with test support**

Edit `frontend/vue-app/vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:9247',
        changeOrigin: true,
      }
    }
  },
  test: {
    globals: true,
    environment: 'happy-dom',
  }
})
```

**Step 7: Update package.json scripts**

Edit `frontend/vue-app/package.json` scripts section:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Step 8: Create .gitignore**

Create `frontend/vue-app/.gitignore`:
```
# Logs
logs
*.log
npm-debug.log*

# Dependency directories
node_modules/

# Build outputs
dist/
dist-ssr/
*.local

# Test coverage
coverage/

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

**Step 9: Verify dev server runs**

Run: `npm run dev`
Expected: Dev server starts on http://localhost:5173

**Step 10: Commit**

```bash
git add frontend/vue-app
git commit -m "feat: initialize Vue.js 3 project with Vite, Router, Pinia, and Tailwind"
```

---

## Task 2: Set Up Project Structure

**Files:**
- Create: `frontend/vue-app/src/router/index.js`
- Create: `frontend/vue-app/src/stores/app.js`
- Create: `frontend/vue-app/src/stores/telescope.js`
- Create: `frontend/vue-app/src/services/api.js`
- Create: `frontend/vue-app/src/views/.gitkeep`
- Create: `frontend/vue-app/src/components/.gitkeep`
- Modify: `frontend/vue-app/src/main.js`

**Step 1: Create Vue Router configuration**

Create `frontend/vue-app/src/router/index.js`:
```javascript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/catalog',
      name: 'catalog',
      component: () => import('@/views/CatalogView.vue')
    },
    {
      path: '/plan',
      name: 'plan',
      component: () => import('@/views/PlanView.vue')
    },
    {
      path: '/execute',
      name: 'execute',
      component: () => import('@/views/ExecuteView.vue')
    },
    {
      path: '/process',
      name: 'process',
      component: () => import('@/views/ProcessView.vue')
    }
  ]
})

export default router
```

**Step 2: Create Pinia app store**

Create `frontend/vue-app/src/stores/app.js`:
```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const rightPanelCollapsed = ref(false)
  const consoleCollapsed = ref(true)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleRightPanel() {
    rightPanelCollapsed.value = !rightPanelCollapsed.value
  }

  function toggleConsole() {
    consoleCollapsed.value = !consoleCollapsed.value
  }

  return {
    sidebarCollapsed,
    rightPanelCollapsed,
    consoleCollapsed,
    toggleSidebar,
    toggleRightPanel,
    toggleConsole
  }
})
```

**Step 3: Create Pinia telescope store**

Create `frontend/vue-app/src/stores/telescope.js`:
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTelescopeStore = defineStore('telescope', () => {
  const connected = ref(false)
  const ip = ref('')
  const currentTarget = ref(null)
  const ra = ref(0)
  const dec = ref(0)
  const alt = ref(0)
  const az = ref(0)

  const statusText = computed(() => {
    return connected.value ? 'Connected' : 'Disconnected'
  })

  const targetDisplay = computed(() => {
    return currentTarget.value?.name || 'No Target'
  })

  function setConnectionStatus(status, ipAddress = '') {
    connected.value = status
    ip.value = ipAddress
  }

  function updatePosition(position) {
    ra.value = position.ra
    dec.value = position.dec
    alt.value = position.alt
    az.value = position.az
  }

  function setCurrentTarget(target) {
    currentTarget.value = target
  }

  return {
    connected,
    ip,
    currentTarget,
    ra,
    dec,
    alt,
    az,
    statusText,
    targetDisplay,
    setConnectionStatus,
    updatePosition,
    setCurrentTarget
  }
})
```

**Step 4: Create API service**

Create `frontend/vue-app/src/services/api.js`:
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const catalogApi = {
  getTargets: (params) => api.get('/targets', { params }),
  getTarget: (id) => api.get(`/targets/${id}`),
  searchTargets: (query) => api.get('/targets/search', { params: { q: query } }),
  getStats: () => api.get('/targets/stats')
}

export const plannerApi = {
  generatePlan: (data) => api.post('/plan', data),
  getPlans: () => api.get('/plans'),
  getPlan: (id) => api.get(`/plans/${id}`),
  exportPlan: (id, format) => api.get(`/plans/${id}/export/${format}`)
}

export const weatherApi = {
  getCurrent: () => api.get('/weather/current'),
  getForecast: () => api.get('/weather/forecast')
}

export const telescopeApi = {
  connect: (ip) => api.post('/telescope/connect', { ip }),
  disconnect: () => api.post('/telescope/disconnect'),
  getStatus: () => api.get('/telescope/status'),
  slewTo: (target) => api.post('/telescope/slew', target),
  park: () => api.post('/telescope/park'),
  unpark: () => api.post('/telescope/unpark')
}

export default api
```

**Step 5: Update main.js to use Router and Pinia**

Edit `frontend/vue-app/src/main.js`:
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
```

**Step 6: Create placeholder directories**

Run:
```bash
mkdir -p frontend/vue-app/src/views
mkdir -p frontend/vue-app/src/components
touch frontend/vue-app/src/views/.gitkeep
touch frontend/vue-app/src/components/.gitkeep
```

**Step 7: Write test for app store**

Create `frontend/vue-app/src/stores/__tests__/app.test.js`:
```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '../app'

describe('App Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with correct defaults', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.rightPanelCollapsed).toBe(false)
    expect(store.consoleCollapsed).toBe(true)
  })

  it('toggles sidebar state', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('toggles right panel state', () => {
    const store = useAppStore()
    expect(store.rightPanelCollapsed).toBe(false)
    store.toggleRightPanel()
    expect(store.rightPanelCollapsed).toBe(true)
  })

  it('toggles console state', () => {
    const store = useAppStore()
    expect(store.consoleCollapsed).toBe(true)
    store.toggleConsole()
    expect(store.consoleCollapsed).toBe(false)
  })
})
```

**Step 8: Run tests to verify they pass**

Run: `npm test`
Expected: All tests pass (4 tests)

**Step 9: Commit**

```bash
git add frontend/vue-app/src
git commit -m "feat: set up router, stores, and API service layer"
```

---

## Task 3: Implement Base Application Layout

**Files:**
- Create: `frontend/vue-app/src/App.vue`
- Create: `frontend/vue-app/src/components/AppHeader.vue`
- Create: `frontend/vue-app/src/components/AppSidebar.vue`
- Create: `frontend/vue-app/src/components/AppRightPanel.vue`
- Create: `frontend/vue-app/src/components/AppConsole.vue`

**Step 1: Write test for App.vue**

Create `frontend/vue-app/src/__tests__/App.test.js`:
```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import App from '../App.vue'

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

    expect(wrapper.find('.app-container').exists()).toBe(true)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: Test fails - App.vue not implemented correctly

**Step 3: Implement App.vue main layout**

Create `frontend/vue-app/src/App.vue`:
```vue
<template>
  <div class="app-container flex flex-col h-screen bg-tron-bg text-tron-text">
    <!-- Header -->
    <AppHeader />

    <!-- Main content area -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar -->
      <AppSidebar />

      <!-- Main content -->
      <main class="flex-1 overflow-auto">
        <RouterView />
      </main>

      <!-- Right Panel -->
      <AppRightPanel />
    </div>

    <!-- Bottom Console -->
    <AppConsole />
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AppRightPanel from '@/components/AppRightPanel.vue'
import AppConsole from '@/components/AppConsole.vue'
</script>
```

**Step 4: Implement AppHeader component**

Create `frontend/vue-app/src/components/AppHeader.vue`:
```vue
<template>
  <header class="h-14 bg-tron-panel border-b border-tron-border flex items-center px-4 gap-4">
    <!-- Logo/Title -->
    <div class="flex items-center gap-2">
      <span class="text-2xl font-bold text-tron-accent">Astronomus</span>
    </div>

    <!-- Search Bar -->
    <div class="flex-1 max-w-md">
      <input
        type="search"
        placeholder="Search targets..."
        class="w-full px-3 py-1.5 bg-tron-bg border border-tron-border rounded text-sm focus:outline-none focus:border-tron-accent"
      />
    </div>

    <!-- Status Items -->
    <div class="flex items-center gap-4">
      <!-- Weather Status -->
      <div class="flex items-center gap-2 text-sm">
        <span>🌤️</span>
        <span>Loading...</span>
      </div>

      <!-- Connection Status -->
      <div class="flex items-center gap-2 text-sm">
        <span :class="connectionStatusClass">●</span>
        <span>{{ telescopeStore.statusText }}</span>
      </div>

      <!-- Settings Icon -->
      <button class="p-2 hover:bg-tron-bg rounded">
        ⚙️
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()

const connectionStatusClass = computed(() => ({
  'text-green-500': telescopeStore.connected,
  'text-red-500': !telescopeStore.connected
}))
</script>
```

**Step 5: Implement AppSidebar component**

Create `frontend/vue-app/src/components/AppSidebar.vue`:
```vue
<template>
  <aside
    :class="['bg-tron-panel border-r border-tron-border transition-all duration-300',
             sidebarWidth]"
  >
    <!-- Collapse Toggle -->
    <button
      @click="appStore.toggleSidebar"
      class="absolute top-4 -right-3 bg-tron-panel border border-tron-border rounded-full w-6 h-6 flex items-center justify-center hover:bg-tron-bg"
    >
      <span class="text-xs">{{ appStore.sidebarCollapsed ? '▶' : '◀' }}</span>
    </button>

    <div v-if="!appStore.sidebarCollapsed" class="p-4">
      <!-- Navigation -->
      <nav class="space-y-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="block px-4 py-2 rounded hover:bg-tron-bg transition-colors"
          active-class="bg-tron-accent/20 text-tron-accent"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Saved Plans Section -->
      <div class="mt-8">
        <h3 class="text-sm font-semibold text-tron-text/60 px-4 mb-2">SAVED PLANS</h3>
        <div class="text-sm text-tron-text/40 px-4">No saved plans</div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const navItems = [
  { path: '/', label: 'Home' },
  { path: '/catalog', label: 'Catalog' },
  { path: '/plan', label: 'Plan' },
  { path: '/execute', label: 'Execute' },
  { path: '/process', label: 'Process' }
]

const sidebarWidth = computed(() =>
  appStore.sidebarCollapsed ? 'w-16' : 'w-64'
)
</script>
```

**Step 6: Implement AppRightPanel component**

Create `frontend/vue-app/src/components/AppRightPanel.vue`:
```vue
<template>
  <aside
    v-if="!appStore.rightPanelCollapsed"
    class="w-80 bg-tron-panel border-l border-tron-border overflow-auto"
  >
    <div class="p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Details</h2>
        <button
          @click="appStore.toggleRightPanel"
          class="p-1 hover:bg-tron-bg rounded"
        >
          ✕
        </button>
      </div>

      <div class="text-sm text-tron-text/60">
        No item selected
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>
```

**Step 7: Implement AppConsole component**

Create `frontend/vue-app/src/components/AppConsole.vue`:
```vue
<template>
  <div
    :class="['bg-tron-panel border-t border-tron-border transition-all duration-300',
             consoleHeight]"
  >
    <!-- Console Header -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-tron-border">
      <h3 class="text-sm font-semibold">Telescope Messages</h3>
      <button
        @click="appStore.toggleConsole"
        class="text-xs hover:text-tron-accent"
      >
        {{ appStore.consoleCollapsed ? '▲ Show' : '▼ Hide' }}
      </button>
    </div>

    <!-- Console Content -->
    <div v-if="!appStore.consoleCollapsed" class="p-4 h-48 overflow-auto font-mono text-xs">
      <div class="text-tron-text/60">No messages</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const consoleHeight = computed(() =>
  appStore.consoleCollapsed ? 'h-auto' : 'h-56'
)
</script>
```

**Step 8: Run tests to verify they pass**

Run: `npm test`
Expected: All tests pass

**Step 9: Start dev server and verify layout**

Run: `npm run dev`
Then open http://localhost:5173
Expected: Three-panel layout visible with header, sidebar, main content area, and collapsible console

**Step 10: Commit**

```bash
git add frontend/vue-app/src
git commit -m "feat: implement base three-panel application layout"
```

---

## Task 4: Create Placeholder Views

**Files:**
- Create: `frontend/vue-app/src/views/HomeView.vue`
- Create: `frontend/vue-app/src/views/CatalogView.vue`
- Create: `frontend/vue-app/src/views/PlanView.vue`
- Create: `frontend/vue-app/src/views/ExecuteView.vue`
- Create: `frontend/vue-app/src/views/ProcessView.vue`

**Step 1: Create HomeView**

Create `frontend/vue-app/src/views/HomeView.vue`:
```vue
<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <!-- Weather Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Weather Forecast</h2>
        <p class="text-sm text-tron-text/60">Loading weather data...</p>
      </div>

      <!-- Telescope Status Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Telescope Status</h2>
        <p class="text-sm text-tron-text/60">{{ telescopeStore.statusText }}</p>
      </div>

      <!-- Next Observation Card -->
      <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
        <h2 class="text-lg font-semibold mb-2">Next Observation</h2>
        <p class="text-sm text-tron-text/60">No plans scheduled</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTelescopeStore } from '@/stores/telescope'

const telescopeStore = useTelescopeStore()
</script>
```

**Step 2: Create CatalogView**

Create `frontend/vue-app/src/views/CatalogView.vue`:
```vue
<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Catalog Browser</h1>

    <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
      <p class="text-sm text-tron-text/60">Catalog browser will be implemented in Phase 1</p>
    </div>
  </div>
</template>
```

**Step 3: Create PlanView**

Create `frontend/vue-app/src/views/PlanView.vue`:
```vue
<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Observation Planner</h1>

    <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
      <p class="text-sm text-tron-text/60">Observation planner will be implemented in Phase 2</p>
    </div>
  </div>
</template>
```

**Step 4: Create ExecuteView**

Create `frontend/vue-app/src/views/ExecuteView.vue`:
```vue
<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Live Execution</h1>

    <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
      <p class="text-sm text-tron-text/60">Live execution monitor will be implemented in Phase 2</p>
    </div>
  </div>
</template>
```

**Step 5: Create ProcessView**

Create `frontend/vue-app/src/views/ProcessView.vue`:
```vue
<template>
  <div class="p-6">
    <h1 class="text-3xl font-bold mb-6">Image Processing</h1>

    <div class="bg-tron-panel border border-tron-border rounded-lg p-4">
      <p class="text-sm text-tron-text/60">Image processing interface will be implemented in Phase 3</p>
    </div>
  </div>
</template>
```

**Step 6: Write routing test**

Create `frontend/vue-app/src/router/__tests__/router.test.js`:
```javascript
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
```

**Step 7: Update router to export routes**

Edit `frontend/vue-app/src/router/index.js` to export routes:
```javascript
import { createRouter, createWebHistory } from 'vue-router'

export const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/catalog',
    name: 'catalog',
    component: () => import('@/views/CatalogView.vue')
  },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/views/PlanView.vue')
  },
  {
    path: '/execute',
    name: 'execute',
    component: () => import('@/views/ExecuteView.vue')
  },
  {
    path: '/process',
    name: 'process',
    component: () => import('@/views/ProcessView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
```

**Step 8: Run tests**

Run: `npm test`
Expected: All tests pass

**Step 9: Verify navigation works**

Run: `npm run dev`
Navigate between views using sidebar
Expected: All views load and display correctly

**Step 10: Commit**

```bash
git add frontend/vue-app/src
git commit -m "feat: add placeholder views for all main navigation routes"
```

---

## Task 5: Configure FastAPI to Serve Vue App

**Files:**
- Modify: `backend/app/main.py`
- Create: `frontend/vue-app/.env.production`

**Step 1: Build Vue app for production**

Run:
```bash
cd frontend/vue-app
npm run build
```

Expected: `dist/` directory created with production build

**Step 2: Write test for Vue app serving**

Create `backend/tests/test_vue_app.py`:
```python
"""Test Vue.js app serving."""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path


def test_vue_app_index_served(client: TestClient):
    """Test that Vue app index.html is served at /app route."""
    response = client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_vue_app_catches_all_routes(client: TestClient):
    """Test that Vue app handles SPA routing."""
    # These should all return the Vue app index.html
    for path in ["/app/catalog", "/app/plan", "/app/execute"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


def test_legacy_frontend_still_works(client: TestClient):
    """Test that legacy frontend is still accessible."""
    response = client.get("/")
    assert response.status_code == 200
```

**Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_vue_app.py -v`
Expected: Tests fail - Vue app routes not configured

**Step 4: Update FastAPI main.py to serve Vue app**

Edit `backend/app/main.py`:
```python
"""Main FastAPI application."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.core import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Astro Planner API",
    description="Astrophotography session planner for Seestar S50 smart telescope",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Paths
frontend_path = Path(__file__).parent.parent / "frontend"
vue_app_path = frontend_path / "vue-app" / "dist"


# Route for shared plan viewer (legacy)
@app.get("/plan/{plan_id}")
async def serve_plan_viewer(plan_id: str):
    """Serve the plan viewer page for shared plans."""
    plan_html = frontend_path / "plan.html"
    if plan_html.exists():
        return FileResponse(plan_html)
    return {"error": "Plan viewer not found"}


# Mount legacy frontend static files at root
app.mount(
    "/legacy",
    StaticFiles(directory=str(frontend_path), html=True),
    name="legacy-static"
)


# Serve Vue.js app
if vue_app_path.exists():
    # Mount Vue app static assets
    app.mount(
        "/app/assets",
        StaticFiles(directory=str(vue_app_path / "assets")),
        name="vue-assets"
    )

    # Catch-all route for Vue SPA - must be last
    @app.get("/app{full_path:path}")
    async def serve_vue_app(full_path: str):
        """Serve Vue.js SPA for all /app routes."""
        index_html = vue_app_path / "index.html"
        if index_html.exists():
            return FileResponse(index_html)
        return {"error": "Vue app not found"}
else:
    logger.warning("Vue app dist folder not found at %s", vue_app_path)


# Root route - serve legacy frontend for now
@app.get("/")
async def root():
    """Serve legacy frontend index."""
    index_html = frontend_path / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return {"message": "Astronomus API", "docs": "/api/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

**Step 5: Create production environment config**

Create `frontend/vue-app/.env.production`:
```
VITE_API_BASE_URL=/api
```

**Step 6: Update Vite config for production base path**

Edit `frontend/vue-app/vite.config.js`:
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  base: '/app/',  // Base path for production
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:9247',
        changeOrigin: true,
      }
    }
  },
  test: {
    globals: true,
    environment: 'happy-dom',
  }
})
```

**Step 7: Rebuild Vue app**

Run:
```bash
cd frontend/vue-app
npm run build
```

**Step 8: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_vue_app.py -v`
Expected: All tests pass

**Step 9: Manually verify both frontends work**

Run FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload
```

Check:
- Legacy frontend at http://localhost:9247/ - should work
- Vue app at http://localhost:9247/app - should work
- API docs at http://localhost:9247/api/docs - should work

**Step 10: Commit**

```bash
git add backend/app/main.py backend/tests/test_vue_app.py frontend/vue-app
git commit -m "feat: configure FastAPI to serve Vue.js app at /app route"
```

---

## Task 6: Update Documentation

**Files:**
- Create: `docs/development/VUE_DEVELOPMENT.md`
- Modify: `README.md`

**Step 1: Create Vue development guide**

Create `docs/development/VUE_DEVELOPMENT.md`:
```markdown
# Vue.js Frontend Development Guide

## Overview

The Astronomus frontend is being migrated from vanilla JavaScript to Vue.js 3 with Vite. This guide covers the new Vue.js development workflow.

## Architecture

**Location:** `frontend/vue-app/`

**Tech Stack:**
- Vue.js 3 (Composition API)
- Vite (build tool)
- Vue Router (routing)
- Pinia (state management)
- Tailwind CSS (styling)
- Vitest (unit testing)
- Axios (API client)

## Project Structure

```
frontend/vue-app/
├── src/
│   ├── components/       # Reusable UI components
│   ├── views/           # Page-level components
│   ├── stores/          # Pinia state stores
│   ├── services/        # API services
│   ├── router/          # Vue Router configuration
│   ├── App.vue          # Root component
│   ├── main.js          # Application entry point
│   └── style.css        # Global styles (Tailwind)
├── public/              # Static assets
├── dist/                # Production build output
└── package.json         # Dependencies and scripts
```

## Development Workflow

### Setup

```bash
cd frontend/vue-app
npm install
```

### Development Server

```bash
npm run dev
```

Access at http://localhost:5173

API requests are proxied to http://localhost:9247/api

### Building for Production

```bash
npm run build
```

Output in `dist/` directory, served by FastAPI at `/app` route.

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

## State Management

Pinia stores are located in `src/stores/`:

- `app.js` - UI state (sidebar, panels, console)
- `telescope.js` - Telescope connection and status

### Using Stores

```javascript
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
appStore.toggleSidebar()
```

## API Services

API services are in `src/services/api.js`:

```javascript
import { catalogApi } from '@/services/api'

const targets = await catalogApi.getTargets({ limit: 50 })
```

## Routing

Routes defined in `src/router/index.js`:

- `/app` - Home/Dashboard
- `/app/catalog` - Catalog Browser
- `/app/plan` - Observation Planner
- `/app/execute` - Live Execution
- `/app/process` - Image Processing

## Styling

Using Tailwind CSS with custom Tron theme colors:

- `tron-bg` - Background
- `tron-panel` - Panel background
- `tron-border` - Borders
- `tron-accent` - Accent color (cyan)
- `tron-text` - Text color

## Component Guidelines

1. Use Composition API (`<script setup>`)
2. Follow single-file component structure
3. Write tests for components with logic
4. Use semantic HTML
5. Ensure accessibility (ARIA labels, keyboard navigation)

## Migration Status

**Phase 0: Complete** ✅
- Project setup
- Base layout
- Routing
- State management
- API service layer

**Phase 1: In Progress**
- Catalog browser
- Weather widget
- Telescope status

**Phase 2: Planned**
- Observation planner
- Live execution monitor

**Phase 3: Planned**
- Image processing interface
- Settings management

## Legacy Frontend

The original vanilla JS frontend remains at:
- Root: http://localhost:9247/
- Legacy route: http://localhost:9247/legacy

During migration, both frontends are accessible.

## Resources

- [Vue.js 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Vitest Documentation](https://vitest.dev/)
```

**Step 2: Update README.md**

Edit `README.md` to add Vue.js development info in the Tech Stack section:
```markdown
**Frontend**
- Vue.js 3 (new, in migration)
- Vite for build tooling
- Pinia for state management
- Vue Router for SPA navigation
- Tailwind CSS for styling
- Vanilla JavaScript (legacy, being phased out)
```

**Step 3: Commit**

```bash
git add docs/development/VUE_DEVELOPMENT.md README.md
git commit -m "docs: add Vue.js development guide and update README"
```

---

## Verification Checklist

After completing all tasks, verify the following:

- [ ] Vue dev server runs: `cd frontend/vue-app && npm run dev`
- [ ] All tests pass: `cd frontend/vue-app && npm test`
- [ ] Production build succeeds: `cd frontend/vue-app && npm run build`
- [ ] FastAPI serves Vue app: http://localhost:9247/app
- [ ] Legacy frontend still works: http://localhost:9247/
- [ ] All navigation links work in Vue app
- [ ] Sidebar collapses/expands
- [ ] Right panel opens/closes
- [ ] Console toggles
- [ ] API proxy works (check Network tab)
- [ ] Documentation is accurate

---

## Next Steps

Phase 0 provides the foundation. Next phases will implement:

**Phase 1:** Enhanced Catalog Browser with real data
**Phase 2:** Observation Planner and Live Execution Monitor
**Phase 3:** Image Processing Interface and Settings

See `docs/planning/UX_MODERNIZATION_PLAN.md` for full roadmap.
