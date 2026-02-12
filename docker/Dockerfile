# Multi-stage build for Astro Planner with CUDA support - Single Container Edition
# Using CUDA 13.0 for enhanced compute support
FROM nvidia/cuda:13.0.0-devel-ubuntu22.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set working directory
WORKDIR /app

# Install Python 3.11, PostgreSQL, Redis, and system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    postgresql-14 \
    postgresql-client-14 \
    redis-server \
    sudo \
    gcc \
    g++ \
    curl \
    git \
    libgomp1 \
    ca-certificates \
    gnupg \
    lsb-release \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default python3 and install pip
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && python3.11 -m pip install --upgrade pip setuptools wheel

# Copy requirements
COPY backend/requirements.txt .
COPY backend/requirements-test.txt .

# Install Python dependencies
RUN python3.11 -m pip install --no-cache-dir --force-reinstall -r requirements.txt
RUN python3.11 -m pip install --no-cache-dir --force-reinstall -r requirements-test.txt

# Copy application code
COPY backend/app ./app
COPY backend/tests ./tests
COPY backend/scripts ./scripts
COPY backend/pytest.ini ./pytest.ini
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY docs ./docs
COPY frontend ./frontend

# Copy startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create directories for data and PostgreSQL
RUN mkdir -p /app/data /var/log/postgresql

# Allow passwordless sudo for postgres user (needed for startup script)
RUN echo "postgres ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Expose ports (web API and PostgreSQL)
EXPOSE 9247 5432

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=9247

# Healthcheck - verify both PostgreSQL and web API
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U pg -d astronomus && curl -f http://localhost:9247/api/health || exit 1

# Start PostgreSQL, Redis, Celery, and web application
CMD ["/app/start.sh"]
