#!/bin/bash
# Verification script for single-container migration

set -e

echo "========================================="
echo "Astronomus Single Container Verification"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local command=$2
    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

echo "1. Container Status"
echo "-------------------"
if docker ps | grep -q "astronomus"; then
    echo -e "${GREEN}✓${NC} Container is running"
else
    echo -e "${RED}✗${NC} Container is not running"
    exit 1
fi
echo ""

echo "2. Service Health Checks"
echo "------------------------"
check_service "PostgreSQL" "docker exec astronomus pg_isready -U pg -d astronomus"
check_service "Redis" "docker exec astronomus redis-cli -a buffalo-jump ping"
check_service "Web API" "curl -f http://localhost:9247/api/health"
echo ""

echo "3. Database Verification"
echo "------------------------"
check_service "Database 'astronomus' exists" "docker exec astronomus psql -U pg -lqt | cut -d \| -f 1 | grep -qw astronomus"
check_service "Database 'test_astronomus' exists" "docker exec astronomus psql -U pg -lqt | cut -d \| -f 1 | grep -qw test_astronomus"
check_service "Can query database" "docker exec astronomus psql -U pg -d astronomus -c 'SELECT 1' -t"
echo ""

echo "4. Celery Workers"
echo "-----------------"
check_service "Celery worker is running" "docker exec astronomus pgrep -f 'celery.*worker'"
check_service "Celery beat is running" "docker exec astronomus pgrep -f 'celery.*beat'"
echo ""

echo "5. Volume Persistence"
echo "---------------------"
if docker volume ls | grep -q "astronomus-pgdata"; then
    echo -e "${GREEN}✓${NC} PostgreSQL data volume exists"
else
    echo -e "${RED}✗${NC} PostgreSQL data volume not found"
fi
echo ""

echo "6. GPU Access (if available)"
echo "----------------------------"
if docker exec astronomus nvidia-smi > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} GPU is accessible"
else
    echo -e "${YELLOW}⚠${NC} GPU not accessible (this is OK if no GPU is present)"
fi
echo ""

echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "To view logs:"
echo "  docker compose logs -f astronomus"
echo ""
echo "To access PostgreSQL:"
echo "  docker exec -it astronomus psql -U pg -d astronomus"
echo ""
echo "To access Redis:"
echo "  docker exec -it astronomus redis-cli -a buffalo-jump"
echo ""
echo "To check Celery workers:"
echo "  docker exec astronomus celery -A app.tasks.celery_app inspect active"
echo ""
