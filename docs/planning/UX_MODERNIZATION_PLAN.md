## Astronomus UX Modernization Plan: Target-Centric Observation Orchestration

### Philosophy
**OLD:** Multi-page, form-driven plan generation and manual catalog browsing.
**NEW:** Target-centric, intelligent observation orchestration with real-time feedback and a unified interface.

Astronomus should feel like a co-pilot for astrophotographers, guiding them through discovery, planning, and execution with an intuitive and responsive experience, focusing on the celestial targets as the primary interaction point.

---

### Proposed Frontend Architecture

To achieve a modern, fluid, and maintainable user experience, the current vanilla JS/MPA frontend will be migrated to a Single-Page Application (SPA) using a modern framework.

*   **Framework:** **Vue.js 3** (given its mention in the README, familiarity, and progressive adoption capabilities)
    *   **Build Tool:** **Vite** (for fast development and optimized production builds)
    *   **State Management:** **Pinia** (simple, intuitive, and Vue.js native store)
    *   **Routing:** **Vue Router** (for seamless navigation within the SPA)
    *   **UI Component Library (Optional but Recommended):** **Element Plus** or **Quasar** (for pre-built, accessible components and consistent design)
*   **Styling:**
    *   **Utility-First CSS:** **Tailwind CSS** (for rapid and consistent styling, allowing for easy customization and adherence to design principles). The existing `tron-theme.css` can be adapted or re-implemented using Tailwind.
*   **API Communication:** Continue using standard REST API calls to the FastAPI backend.
*   **Real-time Communication:** Integrate **WebSockets** (if the backend supports it or is enhanced) for live telescope status, observation progress, and message updates, moving beyond simple polling.

---

### Main Application Layout

The layout will adopt a consistent, three-panel structure similar to the Lumina plan, providing a clear hierarchy and efficient access to information and controls.

```
┌─────────────────────────────────────────────────────────────────┐
│               App Header / Global Status Bar (Top)              │
│  [Astronomus Logo]       [Search Bar]       [User] [Settings]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LEFT SIDEBAR        │      MAIN CONTENT AREA       │  RIGHT PANEL │
│  (Primary Nav,       │      (Dynamic Views)         │  (Contextual │
│   Quick Actions)     │                              │   Details/   │
│                      │                              │   Controls)  │
│  Home                │  ┌────────────────────────┐  │              │
│  Catalog             │  │                        │  │              │
│  Plan                │  │                        │  │              │
│  Execute             │  │    Sky Map / Grid /    │  │              │
│  Process             │  │   Plan Timeline /      │  │              │
│                      │  │  Execution Monitor     │  │              │
│  [Saved Plans]       │  │                        │  │              │
│  [Active Session]    │  │                        │  │              │
│                      │  │                        │  │              │
│                      │  └────────────────────────┘  │              │
│                                                                 │
└──────────────────────┴──────────────────────────────┴───────────────────┘
│                     Telescope Messages Console (Bottom)             │
└─────────────────────────────────────────────────────────────────┘
```

*   **App Header:** Global search, main application title, user profile/settings access, global status (weather, connection, current target).
*   **Left Sidebar:** Primary navigation (Home, Catalog, Plan, Execute, Process), access to saved plans and active sessions. Collapsible to maximize main content space.
*   **Main Content Area:** The dynamic core of the application, displaying the active view (e.g., Sky Map, Catalog Grid, Plan Timeline, Execution Monitor).
*   **Right Panel:** Contextual information, details, or controls depending on the active view or selected item (e.g., Target details, Plan parameters, Telescope controls). This consolidates many of the forms currently in the sidebar of `index.html`.
*   **Telescope Messages Console:** A persistent, collapsible console at the bottom for real-time telescope communication and system messages, combining the current "status-console" and "telescope messages" panels.

---

### Key Views & Components

1.  **Dashboard/Home View:**
    *   **Purpose:** Provide an overview of current status, upcoming observation windows, and recent activity.
    *   **Components:**
        *   Weather forecast summary (from modal content).
        *   Telescope connection status and basic controls (park/unpark).
        *   Summary of next planned observation.
        *   Quick links to active session or recent plans.
        *   "News/Updates" section (e.g., new catalog objects, software updates).

2.  **Interactive Sky Map (New View / Component):**
    *   **Purpose:** Visual selection of celestial targets and real-time telescope position.
    *   **Components:**
        *   Overlay of catalog objects (Messier, NGC, IC) with filtering.
        *   Display of current telescope RA/Dec/Alt/Az.
        *   Field of View (FOV) overlay for selected telescope.
        *   Ability to click on a target to select it for planning or direct slew.
        *   Integration with a time slider to see object visibility over the night.

3.  **Enhanced Catalog Browser (Unified View):**
    *   **Purpose:** Comprehensive search, filter, and detailed display of celestial objects.
    *   **Components:**
        *   Unified interface for Deep Sky Objects, Comets, and Asteroids (when implemented).
        *   Advanced filters (type, magnitude, constellation, visibility, rise/set times).
        *   Search by name or catalog ID (autocompletion).
        *   Responsive grid view (similar to current `catalog.html` but integrated).
        *   Target detail panel (right side) displaying rich metadata, ephemeris data, links to external resources, and "Add to Plan" button. This replaces the dedicated `catalog.html`.

4.  **Observation Planner (Unified View):**
    *   **Purpose:** Define and optimize observation plans.
    *   **Components:**
        *   **Location & Device Configuration:** Consolidate current settings (latitude, longitude, elevation, device selection).
        *   **Observation Preferences:** Date, start/end times, min/max altitude, moon phase, specific constraints.
        *   **Target Selection:** Drag-and-drop from Catalog or Sky Map, manual entry.
        *   **Mosaic Planning:** Enhanced visual grid setup, FOV overlap.
        *   **Plan Generation & Visualization:** Clear feedback during generation, interactive timeline view of scheduled targets, ability to reorder/tweak, graphical representation of target altitude over time.
        *   **Export Options:** Prominent export buttons (seestar_alp CSV, JSON, PDF).

5.  **Live Session Tracking / Execution Monitor (Unified View):**
    *   **Purpose:** Monitor and control active observation sessions.
    *   **Components:**
        *   Real-time telescope status (RA/Dec, Alt/Az, tracking, parking state).
        *   Current target and progress indicators.
        *   Live preview image (if supported and streaming).
        *   Sequence progress (current step, remaining time).
        *   Manual telescope controls (slew, stop, park/unpark, manual navigation).
        *   Imaging controls (exposure, gain, auto-focus, start/stop imaging).
        *   Environmental sensors (temperature, dew heater controls).
        *   Event log/messaging.

6.  **Image Processing Interface (Unified View):**
    *   **Purpose:** Manage captured images and initiate processing workflows.
    *   **Components:**
        *   Image library browser (thumbnail grid, filters, search).
        *   Selection of images for processing.
        *   Processing operations panel (stacking, calibration, stretching, etc.).
        *   Real-time processing job status.
        *   Before/After preview of processed images.

7.  **Settings / Configuration (Unified Modal/View):**
    *   **Purpose:** Manage application-wide and user-specific settings.
    *   **Components:**
        *   Device management (adding/editing telescope profiles, connection settings).
        *   Location settings (default coordinates, time zone).
        *   Weather API key configuration.
        *   Display preferences (units, theme).
        *   Automation settings (daily plan generation schedule, webhooks).
        *   Advanced settings (GPU config, database management, cache clearing).

---

### Key User Flows

1.  **"Generate My First Plan"**
    *   User navigates to "Plan" view.
    *   Configures location, device, observation date/times, and preferences (right panel).
    *   Selects targets from Catalog or Sky Map (main content).
    *   Initiates "Generate Plan" button.
    *   Views optimized plan timeline and exports (main content).

2.  **"Find a Specific Target and Observe It"**
    *   User navigates to "Catalog" view or "Sky Map" view.
    *   Uses search/filters to locate target.
    *   Clicks on target to view details (right panel).
    *   From detail panel, selects "Add to Plan" or "Slew Telescope Directly".
    *   If "Slew", confirms in "Execute" view.

3.  **"Monitor an Active Observation Session"**
    *   User navigates to "Execute" view.
    *   Sees live telescope status, current target, and imaging progress.
    *   Receives real-time messages in the bottom console.
    *   Can pause, stop, or adjust imaging parameters from controls (right panel).

---

### Design Principles (Adapted from Lumina)

1.  **Target First:** The celestial object is the primary focus of interaction, not just a data entry.
2.  **Workflow-Driven:** Group related features and information according to the observation workflow (Discover → Plan → Execute → Process).
3.  **Real-time Feedback:** Provide immediate visual and textual feedback on system status, telescope actions, and data updates.
4.  **Progressive Disclosure:** Present complex options and advanced settings only when relevant or explicitly requested by the user, keeping the core interface clean.
5.  **Unified Experience:** Eliminate redundant pages and ensure consistent navigation, styling, and interaction patterns across all features.
6.  **Actionable Insights:** Highlight critical information (e.g., optimal observation windows, weather warnings, processing job status) to help users make informed decisions.
7.  **Responsive & Accessible:** Design for a range of screen sizes and ensure usability for all users.

---

### Phased Implementation Plan

This plan breaks down the modernization into manageable phases, prioritizing core functionality and a consistent user experience.

**Phase 0: Setup & Scaffolding**
*   Initialize a new Vue.js 3 project with Vite.
*   Configure Vue Router, Pinia, and Tailwind CSS.
*   Establish basic project structure (components, views, stores, services).
*   Implement the main application layout (Header, Left Sidebar, Main Content, Right Panel, Message Console).
*   Integrate API client for backend communication.

**Phase 1: Core Navigation & Initial Views**
*   Implement primary navigation in the Left Sidebar (Home, Catalog, Plan, Execute, Process).
*   **Home View:** Basic dashboard showing weather summary, connection status, and next plan.
*   **Enhanced Catalog Browser:**
    *   Migrate existing `catalog.html` functionality into a Vue component in the main content area.
    *   Integrate DSO, Comet, and future Asteroid filtering and search.
    *   Implement a new right panel for target details and "Add to Plan" actions.
*   **Basic Plan View:** Display a read-only list of generated plans with export options.

**Phase 2: Interactive Planning & Initial Execution Controls**
*   **Observation Planner:**
    *   Migrate all plan generation forms (Location, Preferences, Mosaic) from `index.html`'s sidebar into the "Plan" view's right panel.
    *   Develop an interactive plan timeline/chart visualization in the main content.
    *   Integrate target selection from the new Catalog Browser/Sky Map.
*   **Live Session Tracking (Basic):**
    *   Develop the "Execute" view with real-time telescope status and current target (utilizing WebSockets for updates).
    *   Implement basic telescope controls (Park/Unpark, Slew to Target) in the right panel.
    *   Migrate Telescope Messages Console to the new bottom console.

**Phase 3: Advanced Views & Settings**
*   **Interactive Sky Map:** Implement the visual Sky Map for target discovery and selection.
*   **Image Processing Interface:**
    *   Migrate processing controls and image library from `index.html` into the "Process" view.
    *   Develop interactive preview and job status.
*   **Unified Settings:** Consolidate all application settings into a dedicated Settings view or modal, accessible from the header.

**Phase 4: Polish, Performance & Future Expansion**
*   Refine UI/UX across all views for consistency and responsiveness.
*   Implement advanced features (e.g., multi-panel mosaic visualization, advanced session re-planning, multi-telescope support).
*   Add unit and end-to-end tests for critical components and flows.
*   Optimize performance and load times.
*   Integrate service worker for offline capabilities (if desired).
*   Review and update all relevant documentation (user guides, development setup).

---

This plan outlines a clear path to transforming Astronomus's user interface into a modern, intuitive, and powerful tool that aligns with the advanced capabilities of its backend. It leverages best practices from modern web development and the user's implicit desire for a "Lumina-like" experience while respecting the unique domain of astrophotography planning.
