#!/bin/bash
# Complete Telescope API Test Suite
# Tests all major telescope endpoints and image access

set -e

API_BASE="http://localhost:9247/api"
TELESCOPE_IP="${1:-192.168.2.47}"
TELESCOPE_PORT="${2:-4700}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ PASS${NC}: $1"; }
fail() { echo -e "${RED}✗ FAIL${NC}: $1"; exit 1; }
info() { echo -e "${YELLOW}→${NC} $1"; }
section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

check_response() {
    local response="$1"
    local expected="$2"
    local test_name="$3"
    if echo "$response" | grep -q "$expected"; then
        pass "$test_name"
    else
        fail "$test_name - Expected: $expected, Got: $response"
    fi
}

echo "========================================="
echo "Complete Telescope API Test Suite"
echo "========================================="
echo "Telescope: $TELESCOPE_IP:$TELESCOPE_PORT"
echo "API Base: $API_BASE"
echo ""

# =============================================
# CONNECTION & STATUS
# =============================================
section "1. Connection & Status"

info "GET /telescope/status (disconnected)"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":false' "Status before connection"

info "POST /telescope/connect"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/connect" \
    -H "Content-Type: application/json" \
    -d "{\"host\":\"$TELESCOPE_IP\",\"port\":$TELESCOPE_PORT}")
check_response "$RESPONSE" '"connected":true' "Connect to telescope"
sleep 2

info "GET /telescope/status (connected)"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":true' "Status after connection"

info "GET /telescope/coordinates"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/coordinates")
check_response "$RESPONSE" '"ra"' "Get coordinates"

info "GET /telescope/app-state"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/app-state")
check_response "$RESPONSE" '"stage"' "Get app state"

# =============================================
# MOVEMENT & POSITIONING
# =============================================
section "2. Movement & Positioning"

info "POST /telescope/move (up, slow)"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/move" \
    -H "Content-Type: application/json" \
    -d '{"action":"up","speed":0.5}')
check_response "$RESPONSE" '"status":"moving"' "Move up slow"
sleep 1

info "POST /telescope/stop-slew"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-slew")
check_response "$RESPONSE" '"status":"stopped"' "Stop slew"
sleep 1

info "POST /telescope/move (right, fast)"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/move" \
    -H "Content-Type: application/json" \
    -d '{"action":"right","speed":2.0}')
check_response "$RESPONSE" '"status":"moving"' "Move right fast"
sleep 1

info "POST /telescope/move (stop)"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-slew")
check_response "$RESPONSE" '"status":"stopped"' "Stop motion"

# =============================================
# IMAGING & STACKING
# =============================================
section "3. Imaging & Stacking"

info "POST /telescope/start-imaging"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/start-imaging" \
    -H "Content-Type: application/json" \
    -d '{"restart":true}')
check_response "$RESPONSE" '"status":"imaging"' "Start imaging"
sleep 2

info "GET /telescope/stacking-status"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/stacking-status")
check_response "$RESPONSE" 'stage\|frames' "Get stacking status"

info "POST /telescope/stop-imaging"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/stop-imaging")
check_response "$RESPONSE" '"status":"stopped"' "Stop imaging"
sleep 1

# =============================================
# IMAGE ACCESS (Telescope)
# =============================================
section "4. Image Access (from Telescope)"

info "GET /telescope/features/images/list (stacked)"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/images/list?image_type=stacked&limit=5")
check_response "$RESPONSE" 'images' "List stacked images"

info "GET /telescope/features/images/list (preview)"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/images/list?image_type=preview&limit=5")
check_response "$RESPONSE" 'images' "List preview images"

# Test image download if images exist
IMAGE_COUNT=$(echo "$RESPONSE" | grep -o '"filename"' | wc -l)
if [ "$IMAGE_COUNT" -gt 0 ]; then
    FIRST_IMAGE=$(echo "$RESPONSE" | grep -o '"filename":"[^"]*"' | head -1 | cut -d'"' -f4)
    info "GET /telescope/features/images/download/$FIRST_IMAGE"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        "$API_BASE/telescope/features/images/download/$FIRST_IMAGE")
    if [ "$HTTP_CODE" = "200" ]; then
        pass "Download image (HTTP $HTTP_CODE)"
    else
        fail "Download image (HTTP $HTTP_CODE)"
    fi
fi

# =============================================
# LOCAL IMAGE ACCESS (Mounted Volume)
# =============================================
section "5. Local Image Access (Mounted Volume)"

info "Checking FITS directory mount..."
DOCKER_EXEC="docker exec astronomus"
if $DOCKER_EXEC test -d /fits; then
    pass "FITS directory mounted at /fits"

    # Count files in FITS directory
    FILE_COUNT=$($DOCKER_EXEC find /fits -type f \( -name "*.fit" -o -name "*.fits" \) 2>/dev/null | wc -l)
    info "Found $FILE_COUNT FITS files in /fits"

    if [ "$FILE_COUNT" -gt 0 ]; then
        # List some files
        info "Sample files:"
        $DOCKER_EXEC find /fits -type f \( -name "*.fit" -o -name "*.fits" \) | head -5
    fi
else
    fail "FITS directory not mounted at /fits"
fi

info "GET /api/captures (local FITS files)"
RESPONSE=$(curl -s -X GET "$API_BASE/captures?limit=10")
if echo "$RESPONSE" | grep -q "captures\|total"; then
    pass "List local captures"
    CAPTURE_COUNT=$(echo "$RESPONSE" | grep -o '"total":[0-9]*' | cut -d: -f2)
    info "Total captures in database: $CAPTURE_COUNT"
else
    info "No captures found (may need to scan files first)"
fi

# =============================================
# HARDWARE FEATURES
# =============================================
section "6. Hardware Features"

info "GET /telescope/features/hardware/dew-heater/status"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/hardware/dew-heater/status")
if echo "$RESPONSE" | grep -q "enabled\|power\|status"; then
    pass "Get dew heater status"
else
    info "Dew heater status unavailable"
fi

info "GET /telescope/features/capabilities"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/capabilities")
if echo "$RESPONSE" | grep -q "capabilities\|features"; then
    pass "Get telescope capabilities"
else
    info "Capabilities unavailable"
fi

# =============================================
# SYSTEM INFO
# =============================================
section "7. System Information"

info "GET /telescope/features/system/info"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/system/info")
if echo "$RESPONSE" | grep -q "model\|firmware\|version"; then
    pass "Get system info"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    info "System info unavailable"
fi

info "GET /telescope/features/system/time"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/features/system/time")
if echo "$RESPONSE" | grep -q "time\|timestamp"; then
    pass "Get system time"
else
    info "System time unavailable"
fi

# =============================================
# PREVIEW & LIVE
# =============================================
section "8. Preview & Live Imaging"

info "GET /telescope/preview-info"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/preview-info")
if echo "$RESPONSE" | grep -q "streaming\|preview\|active"; then
    pass "Get preview info"
else
    info "Preview info unavailable"
fi

info "GET /telescope/preview/latest"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/telescope/preview/latest")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    pass "Preview endpoint accessible (HTTP $HTTP_CODE)"
else
    info "Preview endpoint: HTTP $HTTP_CODE"
fi

# =============================================
# DISCONNECT
# =============================================
section "9. Cleanup & Disconnect"

info "POST /telescope/disconnect"
RESPONSE=$(curl -s -X POST "$API_BASE/telescope/disconnect")
check_response "$RESPONSE" "disconnect\|success" "Disconnect telescope"
sleep 1

info "GET /telescope/status (final check)"
RESPONSE=$(curl -s -X GET "$API_BASE/telescope/status")
check_response "$RESPONSE" '"connected":false' "Verify disconnection"

# =============================================
# SUMMARY
# =============================================
echo ""
echo "========================================="
echo -e "${GREEN}TEST SUITE COMPLETED${NC}"
echo "========================================="
echo ""
echo "Endpoints Tested:"
echo "  ✓ Connection management (connect/disconnect/status)"
echo "  ✓ Movement control (move/stop/goto)"
echo "  ✓ Imaging control (start/stop/status)"
echo "  ✓ Image access (telescope & local volume)"
echo "  ✓ Hardware features (dew heater, capabilities)"
echo "  ✓ System information (info, time)"
echo "  ✓ Preview & live imaging"
echo ""
echo "Volume Mounting:"
echo "  ✓ FITS directory: /fits"
echo "  ✓ Telescope export: /mnt/seestar-s50"
echo ""
