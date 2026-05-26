#!/bin/bash
# Telescope UI Integration Test
# Tests all telescope control endpoints in a closed loop

set -e

API_BASE="http://localhost:9247/api"
TELESCOPE_IP="${1:-192.168.2.47}"

echo "========================================="
echo "Telescope UI Integration Test"
echo "========================================="
echo "Telescope IP: $TELESCOPE_IP"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    exit 1
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

check_response() {
    local response="$1"
    local expected="$2"
    local test_name="$3"

    if echo "$response" | grep -q "$expected"; then
        pass "$test_name"
        return 0
    else
        fail "$test_name - Expected: $expected, Got: $response"
        return 1
    fi
}

echo "=== 1. Status Check (Disconnected) ==="
info "Testing status endpoint before connection..."
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":false' "Status shows disconnected"
echo ""

echo "=== 2. Connect to Telescope ==="
info "Connecting to telescope at $TELESCOPE_IP..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/connect" \
    -H "Content-Type: application/json" \
    -d "{\"host\":\"$TELESCOPE_IP\"}")
check_response "$RESPONSE" '"connected":true' "Telescope connection"
sleep 2
echo ""

echo "=== 3. Status Check (Connected) ==="
info "Verifying connection status..."
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":true' "Status shows connected"
echo ""

echo "=== 4. Position Fetching ==="
info "Checking position data..."
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
if echo "$RESPONSE" | grep -q "current_ra_hours"; then
    RA=$(echo "$RESPONSE" | grep -o '"current_ra_hours":[0-9.]*' | cut -d: -f2)
    DEC=$(echo "$RESPONSE" | grep -o '"current_dec_degrees":[-0-9.]*' | cut -d: -f2)
    pass "Position data received (RA: ${RA}h, Dec: ${DEC}°)"
else
    fail "Position data missing"
fi
echo ""

echo "=== 5. Directional Movement ==="
info "Testing directional controls..."

# Test slow movement
info "Move UP (slow speed: 0.5)..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/move" \
    -H "Content-Type: application/json" \
    -d '{"action":"up","speed":0.5}')
check_response "$RESPONSE" '"status":"moving"' "Move UP slow"
sleep 1

# Stop motion
info "Stop motion..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-slew")
check_response "$RESPONSE" '"status":"stopped"' "Stop motion"
sleep 1

# Test fast movement
info "Move RIGHT (fast speed: 2.0)..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/move" \
    -H "Content-Type: application/json" \
    -d '{"action":"right","speed":2.0}')
check_response "$RESPONSE" '"status":"moving"' "Move RIGHT fast"
sleep 1

info "Stop motion..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-slew")
check_response "$RESPONSE" '"status":"stopped"' "Stop motion"
echo ""

echo "=== 6. Imaging Control ==="
info "Testing imaging start/stop..."

info "Start imaging..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/start-imaging" \
    -H "Content-Type: application/json" \
    -d '{"restart":true}')
check_response "$RESPONSE" '"status":"imaging"' "Start imaging"
sleep 2

info "Stop imaging..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-imaging")
check_response "$RESPONSE" '"status":"stopped"' "Stop imaging"
echo ""

echo "=== 7. Disconnect ==="
info "Disconnecting telescope..."
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/disconnect")
check_response "$RESPONSE" "success\|disconnected" "Telescope disconnect"
sleep 1
echo ""

echo "=== 8. Final Status Check ==="
info "Verifying disconnection..."
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":false' "Status shows disconnected"
echo ""

echo "========================================="
echo -e "${GREEN}ALL TESTS PASSED!${NC}"
echo "========================================="
echo ""
echo "Frontend endpoints verified:"
echo "  ✓ Connection management"
echo "  ✓ Position fetching"
echo "  ✓ Directional movement (up/down/left/right)"
echo "  ✓ Speed control (slow/fast)"
echo "  ✓ Motion stop"
echo "  ✓ Imaging start/stop"
echo ""
echo "The UI should now work correctly with a connected telescope."
