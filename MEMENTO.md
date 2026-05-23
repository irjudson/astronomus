# astronomus

Astronomus is a web application for planning astrophotography sessions, allowing users to select celestial objects from catalogs, add them to plans, and generate optimized observation schedules.

**Stack:** Vue.js frontend, Python backend services, PostgreSQL database

## Current Status
- Solar system "Add to Plan" functionality is fixed and prioritizes selected targets
- Plan generation respects user-selected priority targets
- Backend scheduler and planner services are updated with priority logic

## Recent Decisions
- 2026-05-22: Fixed 'already in plan' bug in catalog.js where solar system objects without IDs caused false duplicates
- 2026-05-22: Implemented priority scheduling for selected targets in planner and scheduler services

## Open Issues
- Plan generation may not immediately reflect new selections without a refresh

## Key Files
- `frontend/src/components/catalog/SolarSystemCard.vue`: Displays solar system objects and handles 'Add to Plan' interactions
- `frontend/src/stores/catalog.js`: Manages selected and wishlist targets for all catalogs
- `backend/services/planner_service.py`: Generates observation plans by scoring candidate targets
- `backend/services/scheduler_service.py`: Schedules sessions by selecting the best targets based on score and constraints
- `frontend/src/components/planning/PlanGenerator.vue`: Frontend component for initiating and viewing plan generation
- `backend/services/cleardarksky_service.py`: Provides weather and cloud cover data for scheduling
- `backend/services/catalog_service.py`: Manages access to celestial object catalogs including DSOs and solar system bodies
- `frontend/src/stores/useCatalogStore.js`: Pinia store for managing the global catalog state including selected and wishlist targets

## Recent Activity
- 2026-05-22: Fixed 'already in plan' bug in catalog.js and implemented priority scheduling
- 2026-05-22: Updated planner_service.py and scheduler_service.py to support priority target scheduling
- 2026-05-22: Committed fixes, rebuilt, and restarted backend services to deploy changes
