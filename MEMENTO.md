# astronomus

Astronomus is a web application for planning and executing astrophotography sessions with a Seestar S50 telescope, featuring automated scheduling, weather monitoring, and catalog-based target selection.

**Stack:** FastAPI, Vue 3, PostgreSQL, Redis, Celery, Docker

## Architecture

Single Docker container (`astronomus`) running PostgreSQL 14, Redis, FastAPI (uvicorn), and Celery.
Frontend: Vue 3 SPA served from `/app/` by FastAPI.
Container port: 9247.

## Key Files

- `backend/app/main.py` — FastAPI application entry point
- `backend/app/api/routes.py` — consolidated API route definitions
- `backend/app/services/catalog_service.py` — DSO catalog search and scoring
- `backend/app/services/planner_service.py` — session planning and scheduling
- `backend/app/services/scheduler_service.py` — gap-filling optimizer
- `backend/app/services/telescope_service.py` — S50 telescope integration
- `backend/app/clients/seestar/` — low-level Seestar S50 client
- `frontend/vue-app/src/` — Vue 3 frontend (views, stores, components)
- `docker/start.sh` — container entrypoint (PostgreSQL, Redis, Celery, migrations, uvicorn)
- `docker-compose.yml` — single-container deployment

## Development

```bash
docker compose up -d astronomus          # start
docker exec astronomus pytest tests/ -q  # run tests
make help                                # all available commands
```

## Recent Decisions

- 2026-05-25: Removed Claude attribution from commit history and documentation
- 2026-05-25: Updated to single-container Docker architecture
- 2026-05-26: Maintenance pass — Makefile overhaul, ruff fixes, Pillow deprecation fix, stray scripts moved to scripts/
