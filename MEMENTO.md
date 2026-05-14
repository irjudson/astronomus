# astronomus

Astronomus is an advanced planning tool for astronomical observations that leverages the Seestar telescope's capabilities to schedule optimal observation windows while avoiding moonlight, satellites, and other interfering conditions. It supports automated horizon scanning and intelligent constraint-based planning for professional and amateur astronomers.

**Stack:** Python, FastAPI, React, PostgreSQL, Celery, Docker

## Current Status
- Feature branch 'feature/horizon-planets-satellites' is active with markdown cleanup and new functionality implementation
- Horizon scanning, planet prioritization, and satellite avoidance features are being developed
- All tests pass and code quality is verified through automated review processes

## Recent Decisions
- 2026-05-12: Implemented markdown cleanup by removing obsolete documentation files and archive directories to improve maintainability
- 2026-05-12: Added 'avoid_satellites' constraint to observing configuration, following same pattern as 'avoid_moon' for consistency
- 2026-05-12: Designed automated horizon scanning using Seestar's slew capabilities during daylight hours for precision
- 2026-05-12: Integrated satellite pass detection using Celestrak's free TLE set with sgp4/skyfield libraries for planning

## Open Issues
- Need to validate satellite avoidance logic with real-world TLE data for accuracy
- Horizon scanning algorithm needs performance optimization for faster execution

## Key Files
- `app/models/constraints.py`: Defines observing constraints including new avoid_satellites flag
- `app/services/scheduler.py`: Contains core scheduling logic with satellite pass filtering
- `app/services/horizon_scanner.py`: Implements daylight-based horizon scanning using Seestar's slew capabilities
- `app/api/observatory.py`: API endpoints for horizon profile and satellite avoidance configuration
- `app/utils/satellite_detector.py`: Utility functions for detecting satellite passes using sgp4 and skyfield
- `app/utils/horizon_calculator.py`: Calculates horizon profiles from scanned alt/az data
- `tests/test_scheduler.py`: Unit tests for scheduler including satellite avoidance
- `tests/test_horizon_scanner.py`: Unit tests for horizon scanning functionality

## Recent Activity
- 2026-05-12: Feature branch created with cleanup of obsolete docs and implementation plan
- 2026-05-12: Implemented satellite avoidance constraint and integrated Celestrak TLE detection
- 2026-05-12: Added horizon scanning logic using Seestar's alt/az slew capability
- 2026-05-12: Updated API endpoints to support new constraints and scanning features
- 2026-05-12: All tests pass with new functionality integrated and verified
- 2026-05-13: Executed implementation plan using subagent-driven development approach
- 2026-05-13: Completed markdown cleanup tasks and verified code quality through automated reviews
- 2026-05-13: Merged feature branch changes into development environment for further testing
