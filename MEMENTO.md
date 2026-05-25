# astronomus

Astronomus is a tool that helps amateur astronomers plan their night sky observations by generating optimized schedules based on visibility, weather, and object priority. It provides an intuitive interface to explore deep-sky objects, solar system bodies, and real-time conditions to make the most of every observing session.

**Stack:** Next.js, React, Tailwind CSS, TypeScript, Node.js, PostgreSQL, PostgreSQL GIS extensions

## Current Status
- The application is fully functional with dashboard, catalog browsing, solar system tracking, and plan generation.
- Live observing and post-processing features are planned for future development.
- A polished demo video has been created showcasing core UI and workflow.

## Recent Decisions
- 2024-05-24: Finalized demo video assembly with speed-up of loading sections and captioning for clarity.
- 2024-05-24: Decided to add an outtake card listing future features like live observing and post-processing.
- 2024-05-23: Implemented proper catalog loading and filtering for deep-sky objects with visibility scoring.
- 2024-05-22: Integrated solar system visibility indicators and optimized altitude chart rendering.
- 2024-05-21: Added priority queue and plan generation logic with near-miss candidate scoring.
- 2024-05-20: Built dashboard with weather strip and tonight's conditions display.

## Open Issues
- Live observing mode needs integration with telescope control systems.
- Post-processing pipeline requires GPU acceleration for image stacking.

## Key Files
- `/home/irjudson/Projects/astronomus/pages/index.tsx`: Main dashboard page showing tonight's conditions and weather forecast.
- `/home/irjudson/Projects/astronomus/components/CatalogBrowser.tsx`: Component for browsing and filtering deep-sky objects with visibility indicators.
- `/home/irjudson/Projects/astronomus/components/SolarSystemTracker.tsx`: Displays current positions and visibility of solar system bodies.
- `/home/irjudson/Projects/astronomus/components/PlanGenerator.tsx`: Generates optimized observation schedules with priority queue and altitude charts.
- `/home/irjudson/Projects/astronomus/lib/visibility.ts`: Calculates object visibility based on location, time, and atmospheric conditions.
- `/home/irjudson/Projects/astronomus/lib/score.ts`: Scores objects for visibility and priority using a combination of factors.
- `/home/irjudson/Projects/astronomus/pages/_app.tsx`: Main application wrapper setting up global context and theme.
- `/home/irjudson/Projects/astronomus/scripts/assemble-demo.sh`: Shell script to process raw demo footage into final video with title, captions, and speed adjustments.

## Recent Activity
- 2024-05-24: Assembled final demo video with title card, captions, and speed adjustments.
- 2024-05-23: Implemented object visibility scoring and filtering logic.
- 2024-05-22: Integrated solar system tracking with visibility indicators and altitude charts.
- 2024-05-21: Built plan generation with priority queue and near-miss candidate scoring.
- 2024-05-20: Created dashboard with weather forecast and tonight's conditions.
- 2024-05-19: Set up catalog browser with deep-sky object images and visibility data.
- 2024-05-18: Configured Next.js project with TypeScript and Tailwind CSS.
- 2024-05-17: Defined core data models for objects, visibility, and scheduling.
- 2024-05-16: Initialized repository and set up CI/CD pipeline.
- 2024-05-15: Conducted initial research on astronomical visibility algorithms and data sources.
