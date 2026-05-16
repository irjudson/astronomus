# astronomus

Astronomus is an automated astronomy capture system that allows users to plan, execute, and monitor telescope observations remotely. It supports scheduled capturing, weather monitoring, and unmanned operation at night.

**Stack:** Python, FastAPI, Celery, PostgreSQL, Skyfield, Docker

## Current Status
- Automated dusk execution and weather abort capabilities are implemented
- Custom target thumbnails and catalog enrichment features are complete
- Full test suite passes with code quality checks

## Recent Decisions
- 2026-05-14: Implemented auto-scheduled execution at dusk and weather watchdog to support unmanned nighttime capturing
- 2026-05-14: Added automation tasks for dusk scheduling and plan execution with retry logic
- 2026-05-14: Integrated Skyfield for astronomical time calculations and Celery Beat for scheduling
- 2026-05-14: Enabled weather abort logic to protect equipment during astronomical night

## Open Issues
- Need to validate full end-to-end unmanned operation in real-world conditions
- Weather API integration needs to be finalized for production use

## Key Files
- `automation_tasks.py`: Contains scheduled tasks for dusk execution and plan kickoff
- `weather_watchdog_task.py`: Monitors weather conditions and aborts session if rain is detected
- `schedule_dusk_execution_task.py`: Schedules execution at computed astronomical dusk
- `auto_execute_plan_task.py`: Executes the auto-generated plan with retry logic
- `test_automation_tasks.py`: Tests the automation task logic and scheduling
- `test_weather_watchdog_task.py`: Tests the weather watchdog and abort functionality
- `celery_app.py`: Main Celery app configuration with Beat scheduler
- `settings.py`: Configuration settings including location and weather API keys

## Recent Activity
- 2026-05-14: Implemented dusk execution automation and weather abort
- 2026-05-14: Added Skyfield integration for astronomical calculations
- 2026-05-14: Fixed formatting and import ordering in automation tasks
- 2026-05-14: Added retry logic to auto-execute task for scope readiness
- 2026-05-14: Created test suite for automation and weather watchdog tasks
- 2026-05-14: Integrated Celery Beat for scheduled task execution
- 2026-05-14: Pushed final code changes for unmanned capture support
- 2026-05-14: Ensured code quality and test suite pass
- 2026-05-14: Updated documentation for unmanned capture workflow
- 2026-05-14: Validated task scheduling and execution logic
- 2026-05-14: Completed test suite for automation and watchdog tasks
- 2026-05-14: Finalized implementation of auto-start and weather abort features
- 2026-05-14: Merged Sprint 3 changes including image_url support for custom targets
- 2026-05-14: Ensured full test suite passes with code quality checks
