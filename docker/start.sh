#!/bin/bash
set -e

# Set up log directory permissions
mkdir -p /var/log/postgresql
chown -R postgres:postgres /var/log/postgresql

# Initialize PostgreSQL data directory if it's not initialized
if [ ! -f "/var/lib/postgresql/14/main/postgresql.conf" ]; then
    echo "Initializing PostgreSQL database..."
    # Clean the directory contents (not the directory itself, in case it's a mount point)
    rm -rf /var/lib/postgresql/14/main/*
    rm -rf /var/lib/postgresql/14/main/.[!.]*
    chown -R postgres:postgres /var/lib/postgresql

    su - postgres -c "/usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main --encoding=UTF8 --locale=C" 2>&1

    # Configure PostgreSQL
    echo "host all all 127.0.0.1/32 md5" >> /var/lib/postgresql/14/main/pg_hba.conf
    echo "host all all ::1/128 md5" >> /var/lib/postgresql/14/main/pg_hba.conf
    echo "local all all md5" >> /var/lib/postgresql/14/main/pg_hba.conf
fi

# Remove stale PID file from previous container run (PIDs don't persist across containers)
if [ -f "/var/lib/postgresql/14/main/postmaster.pid" ]; then
    echo "Removing stale postmaster.pid file..."
    rm -f /var/lib/postgresql/14/main/postmaster.pid
fi

# Start PostgreSQL as postgres user
echo "Starting PostgreSQL..."
su - postgres -c "/usr/lib/postgresql/14/bin/postgres -D /var/lib/postgresql/14/main" &
POSTGRES_PID=$!
echo "PostgreSQL started with PID: $POSTGRES_PID"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
until su - postgres -c "psql -U postgres -c 'SELECT 1' > /dev/null 2>&1"; do
  sleep 1
done

# Create user and database if they don't exist
echo "Setting up database..."
su - postgres -c "psql -U postgres -tc \"SELECT 1 FROM pg_user WHERE usename = 'pg'\" | grep -q 1 || psql -U postgres -c \"CREATE USER pg WITH SUPERUSER PASSWORD 'buffalo-jump';\""
su - postgres -c "psql -U postgres -tc \"SELECT 1 FROM pg_database WHERE datname = 'astronomus'\" | grep -q 1 || psql -U postgres -c \"CREATE DATABASE astronomus OWNER pg ENCODING 'UTF8';\""
su - postgres -c "psql -U postgres -tc \"SELECT 1 FROM pg_database WHERE datname = 'test_astronomus'\" | grep -q 1 || psql -U postgres -c \"CREATE DATABASE test_astronomus OWNER pg ENCODING 'UTF8';\""

echo "PostgreSQL is ready"

# Start Redis
echo "Starting Redis..."
redis-server --daemonize yes --port 6379 --requirepass buffalo-jump
echo "Redis started"

# Run database migrations if needed
cd /app
echo "Running database migrations..."
alembic upgrade head || echo "Warning: Migration failed or no migrations to run"

# Start Celery worker in background (with GPU access)
echo "Starting Celery worker..."
export DATABASE_URL="postgresql://pg:buffalo-jump@localhost:5432/astronomus"
export REDIS_URL="redis://:buffalo-jump@localhost:6379/1"
export CELERY_BROKER_URL="redis://:buffalo-jump@localhost:6379/1"
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4 &
CELERY_WORKER_PID=$!
echo "Celery worker started with PID: $CELERY_WORKER_PID"

# Start Celery Beat scheduler in background
echo "Starting Celery Beat..."
celery -A app.tasks.celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!
echo "Celery Beat started with PID: $CELERY_BEAT_PID"

# Start the web application
echo "Starting Astronomus web application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 9247 --reload
