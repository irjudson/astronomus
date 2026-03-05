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
# Run tests (watch mode by default)
npm test

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
