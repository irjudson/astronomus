# Single Container Migration - Phase 1

## Overview
Migrated Astronomus from multi-container architecture (separate postgres, redis, celery-worker, celery-beat, flower containers) to a single-container architecture with embedded PostgreSQL and Redis.

This follows the same pattern used in the Lumina project's migration to single-container architecture.

## Changes Made

### New Files
- `docker/start.sh` - Startup script that initializes and runs PostgreSQL, Redis, Celery worker, Celery beat, and the web API

### Modified Files

#### `docker/Dockerfile`
- Added PostgreSQL 14, Redis, and sudo packages
- Removed entrypoint.sh dependency
- Added start.sh as the CMD
- Updated healthcheck to verify both PostgreSQL and web API
- Added PostgreSQL log directory creation
- Added sudo permissions for postgres user

#### `docker-compose.yml`
- Consolidated all services into single `astronomus` service
- Added `astronomus-pgdata` volume for PostgreSQL data persistence
- Updated all connection strings to use `localhost` instead of external service names
- Removed dependency on `shared-infra` network
- Added GPU support with `deploy.resources.reservations`
- Moved Flower to optional profile using `network_mode: service:astronomus`
- Added environment variables for PostgreSQL, Redis, Celery, and GPU configuration

#### `.gitignore`
- Added PostgreSQL runtime file patterns
- Added docker-compose backup patterns

### Removed Dependencies
- No longer depends on external `postgres` container in shared-infra network
- No longer depends on external `redis` container in shared-infra network
- Removed separate `celery-worker` container
- Removed separate `celery-beat` container

## Architecture

### Before (Multi-Container)
```
┌─────────────┐     ┌──────────┐     ┌───────┐
│ astronomus  │────▶│ postgres │     │ redis │
│   (web)     │     │(external)│     │(ext.) │
└─────────────┘     └──────────┘     └───┬───┘
                                          │
┌─────────────┐     ┌──────────┐         │
│celery-worker│────▶│celery-beat│────────┘
│  (nvidia)   │     │           │
└─────────────┘     └──────────┘
```

### After (Single Container)
```
┌─────────────────────────────────────┐
│         astronomus:latest           │
│                                     │
│  ┌──────────┐  ┌───────┐           │
│  │PostgreSQL│  │ Redis │           │
│  │    14    │  │       │           │
│  └─────┬────┘  └───┬───┘           │
│        │           │                │
│  ┌─────▼───────────▼─────┐         │
│  │   Celery Worker       │         │
│  │   (with GPU access)   │         │
│  └───────────────────────┘         │
│  ┌───────────────────────┐         │
│  │   Celery Beat         │         │
│  └───────────────────────┘         │
│  ┌───────────────────────┐         │
│  │   Web API (FastAPI)   │         │
│  │   uvicorn :9247       │         │
│  └───────────────────────┘         │
│                                     │
│  GPU Access: NVIDIA Runtime         │
└─────────────────────────────────────┘
```

## Environment Variables

All services now use `localhost` for connections:

- `DATABASE_URL=postgresql://pg:buffalo-jump@localhost:5432/astronomus`
- `REDIS_URL=redis://:buffalo-jump@localhost:6379/1`
- `CELERY_BROKER_URL=redis://:buffalo-jump@localhost:6379/1`

## Volumes

### Persistent Data
- `astronomus-pgdata:/var/lib/postgresql/14/main` - PostgreSQL database files

### Development Mounts
- `./backend/app:/app/app` - Live code reload
- `./frontend:/app/frontend` - Frontend files
- `./data:/app/data` - Application data
- `/mnt/seestar-s50:/fits:rw` - FITS files from telescope

### GPU Support
- `/tmp/nvidia-mps:/tmp/nvidia-mps` - NVIDIA MPS for multi-process GPU sharing
- `/tmp/nvidia-log:/tmp/nvidia-log` - NVIDIA MPS logs

## Startup Sequence

1. Initialize PostgreSQL data directory (first run only)
2. Remove stale PID files
3. Start PostgreSQL as postgres user
4. Wait for PostgreSQL to be ready
5. Create database user `pg` and databases `astronomus` and `test_astronomus`
6. Start Redis server with password authentication
7. Run Alembic database migrations
8. Start Celery worker (4 workers with GPU access)
9. Start Celery beat scheduler
10. Start web API with uvicorn (with reload for development)

## Building and Running

### Build the container
```bash
docker compose build
```

### Start the service
```bash
docker compose up
```

### Start with Flower monitoring (optional)
```bash
docker compose --profile monitoring up
```

### Verify services are running
```bash
# Check PostgreSQL
docker exec astronomus pg_isready -U pg -d astronomus

# Check Redis
docker exec astronomus redis-cli -a buffalo-jump ping

# Check Celery workers
docker exec astronomus celery -A app.tasks.celery_app inspect ping

# Check web API
curl http://localhost:9247/api/health
```

### View logs
```bash
docker compose logs -f astronomus
```

## Testing

After migration, verify:

1. ✅ Container builds successfully
2. ✅ PostgreSQL starts and is accessible
3. ✅ Redis starts and is accessible
4. ✅ Celery worker starts with GPU access
5. ✅ Celery beat scheduler starts
6. ✅ Web API responds to health checks
7. ✅ Database migrations run successfully
8. ✅ Celery tasks execute properly
9. ✅ GPU is accessible in background tasks
10. ✅ Data persists across container restarts

## Rollback

If you need to rollback to the multi-container setup:

```bash
# Stop current container
docker compose down

# Restore backup
mv docker-compose.yml.multi-container-backup docker-compose.yml

# Start with shared-infra network
docker compose up
```

## Next Steps (Phase 2 - Optional)

Phase 2 would involve:
1. Removing Redis and Celery completely
2. Implementing threading-based background job system
3. Simplifying startup script (no Redis, no Celery)
4. Faster startup and fewer moving parts

This would match Lumina's final architecture state.

## Benefits

### Immediate (Phase 1)
- ✅ No external service dependencies
- ✅ Simplified deployment (one container)
- ✅ Easier development setup
- ✅ All services co-located
- ✅ Unified healthcheck
- ✅ Persistent database in Docker volume

### Future (Phase 2)
- ⏳ Simpler architecture (no Redis, no Celery)
- ⏳ Faster startup
- ⏳ Fewer dependencies to manage
- ⏳ Built-in background job system

## Notes

- PostgreSQL data is stored in a Docker volume (`astronomus-pgdata`) for persistence
- First container start will initialize the PostgreSQL database (takes ~10 seconds)
- Subsequent starts are faster as database is already initialized
- The startup script automatically handles database user and database creation
- Migrations run automatically on each container start
- GPU access is maintained for Celery workers through NVIDIA runtime configuration
