# Makefile for Astronomus
# All tests run inside the Docker container (astronomus).

.PHONY: help test test-verbose test-coverage test-quick test-file test-hardware \
        test-unit test-integration lint format clean \
        dev-up dev-down dev-logs dev-rebuild \
        db-migrate db-upgrade db-downgrade \
        status push

CONTAINER := astronomus
PYTEST    := docker exec $(CONTAINER) pytest

# Default target
help:
	@echo "Astronomus - Available Commands"
	@echo "================================"
	@echo ""
	@echo "Testing (all run inside Docker container):"
	@echo "  make test              - Run all tests (fast, no coverage)"
	@echo "  make test-verbose      - Run tests with verbose output"
	@echo "  make test-coverage     - Run tests with full coverage report"
	@echo "  make test-quick        - Run tests in parallel"
	@echo "  make test-unit         - Run only unit tests"
	@echo "  make test-integration  - Run only integration tests"
	@echo "  make test-file FILE=   - Run a specific test file (e.g. FILE=tests/unit/test_config.py)"
	@echo "  make test-hardware     - Run hardware tests against real S50 (requires --telescope-host)"
	@echo ""
	@echo "Code Quality (runs on host using host-installed tools):"
	@echo "  make lint              - Ruff + mypy"
	@echo "  make format            - Black + ruff --fix"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up            - Start container"
	@echo "  make dev-down          - Stop container"
	@echo "  make dev-logs          - Tail container logs"
	@echo "  make dev-rebuild       - Rebuild image and restart"
	@echo ""
	@echo "Database (runs inside container):"
	@echo "  make db-migrate MSG=   - Create a new migration"
	@echo "  make db-upgrade        - Apply pending migrations"
	@echo "  make db-downgrade      - Revert last migration"
	@echo ""
	@echo "Other:"
	@echo "  make status            - Git status + recent commits"
	@echo "  make push              - Push current branch"
	@echo "  make clean             - Remove local cache files"
	@echo ""

# ── Tests ────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) tests/ --no-cov -q

test-verbose:
	$(PYTEST) tests/ -v --no-cov

test-coverage:
	$(PYTEST) tests/ --cov=app --cov-report=term --cov-report=html
	@echo ""
	@echo "HTML report: backend/htmlcov/index.html"

test-quick:
	$(PYTEST) tests/ -n auto --no-cov -q

test-unit:
	$(PYTEST) tests/unit/ --no-cov -q

test-integration:
	$(PYTEST) tests/integration/ -v --no-cov

test-file:
	$(PYTEST) $(FILE) -v --no-cov

test-hardware:
	$(PYTEST) tests/seestar/ --real-hardware --telescope-host=192.168.2.47 -v --no-cov

# ── Code Quality ─────────────────────────────────────────────────────────────

lint:
	@echo "Linting with ruff..."
	@cd backend && ruff check app/ tests/
	@echo ""
	@echo "Type checking with mypy..."
	@cd backend && mypy app/ || true

format:
	@echo "Formatting with black..."
	@cd backend && black app/ tests/
	@echo ""
	@echo "Fixing imports with ruff..."
	@cd backend && ruff check --fix app/ tests/

# ── Development ───────────────────────────────────────────────────────────────

dev-up:
	docker compose up -d $(CONTAINER)
	@echo "Running at http://localhost:9247/app/"

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f $(CONTAINER)

dev-rebuild:
	docker compose build $(CONTAINER)
	docker compose up -d $(CONTAINER)

# ── Database ─────────────────────────────────────────────────────────────────

db-migrate:
	docker exec $(CONTAINER) sh -c "cd /app && alembic revision --autogenerate -m '$(MSG)'"

db-upgrade:
	docker exec $(CONTAINER) sh -c "cd /app && alembic upgrade head"

db-downgrade:
	docker exec $(CONTAINER) sh -c "cd /app && alembic downgrade -1"

# ── Other ─────────────────────────────────────────────────────────────────────

status:
	@echo "Git Status:"
	@git status --short
	@echo ""
	@echo "Recent Commits:"
	@git log --oneline -5

push:
	git push

clean:
	find backend -type f -name '*.pyc' -delete
	find backend -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/htmlcov backend/.coverage
