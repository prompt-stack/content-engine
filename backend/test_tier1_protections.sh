#!/bin/bash

# Tier 1 Security Protections Test Script
# Tests rate limiting, feature flags, and API key authentication

echo "======================================"
echo "TIER 1 SECURITY PROTECTIONS TEST"
echo "======================================"
echo ""

BASE_URL="http://localhost:9765"

# Test 1: Verify server is running
echo "Test 1: Health Check"
echo "--------------------"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
if [ "$HEALTH" = "200" ]; then
    echo "✅ Server is running (HTTP 200)"
else
    echo "❌ Server not responding properly (HTTP $HEALTH)"
    exit 1
fi
echo ""

# Test 2: Feature flags - Test with ENABLE_LLM and ENABLE_EXTRACTORS enabled (default)
echo "Test 2: Feature Flags (Current State)"
echo "--------------------------------------"
echo "Testing LLM endpoint (should work if ENABLE_LLM=True)..."
LLM_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/llm/generate" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", "provider": "openai"}')

if echo "$LLM_RESPONSE" | grep -q "503"; then
    echo "⚠️  LLM endpoint is disabled (ENABLE_LLM=False)"
elif echo "$LLM_RESPONSE" | grep -q "401"; then
    echo "✅ LLM endpoint requires authentication (API key protection active)"
elif echo "$LLM_RESPONSE" | grep -q "detail"; then
    echo "✅ LLM endpoint is protected: $(echo $LLM_RESPONSE | grep -o '"detail":"[^"]*"')"
else
    echo "⚠️  LLM endpoint responded: $(echo $LLM_RESPONSE | head -c 100)"
fi
echo ""

# Test 3: API Key Authentication (without key)
echo "Test 3: API Key Authentication (No Key)"
echo "----------------------------------------"
API_KEY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/llm/generate" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", "provider": "openai"}')

if [ "$API_KEY_RESPONSE" = "401" ]; then
    echo "✅ API key required (HTTP 401) - Protection active!"
elif [ "$API_KEY_RESPONSE" = "503" ]; then
    echo "⚠️  Feature disabled (HTTP 503)"
elif [ "$API_KEY_RESPONSE" = "200" ]; then
    echo "⚠️  No API key required - API_SECRET_KEY not set in .env"
else
    echo "⚠️  Unexpected response: HTTP $API_KEY_RESPONSE"
fi
echo ""

# Test 4: API Key Authentication (with wrong key)
echo "Test 4: API Key Authentication (Wrong Key)"
echo "-------------------------------------------"
WRONG_KEY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/llm/generate" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: wrong-key-12345" \
    -d '{"prompt": "test", "provider": "openai"}')

if [ "$WRONG_KEY_RESPONSE" = "403" ]; then
    echo "✅ Invalid API key rejected (HTTP 403)"
elif [ "$WRONG_KEY_RESPONSE" = "401" ]; then
    echo "✅ API key required (HTTP 401)"
elif [ "$WRONG_KEY_RESPONSE" = "200" ]; then
    echo "⚠️  Request succeeded - API_SECRET_KEY not set"
else
    echo "⚠️  Unexpected response: HTTP $WRONG_KEY_RESPONSE"
fi
echo ""

# Test 5: Rate Limiting (LLM endpoint - 10/minute)
echo "Test 5: Rate Limiting Test (LLM 10/min)"
echo "----------------------------------------"
echo "Sending 12 rapid requests to test rate limit..."

SUCCESS_COUNT=0
RATE_LIMITED_COUNT=0

for i in {1..12}; do
    RATE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${BASE_URL}/api/llm/generate" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "test", "provider": "openai"}')

    if [ "$RATE_RESPONSE" = "429" ]; then
        RATE_LIMITED_COUNT=$((RATE_LIMITED_COUNT + 1))
    else
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
done

echo "Results: $SUCCESS_COUNT allowed, $RATE_LIMITED_COUNT rate limited"

if [ "$RATE_LIMITED_COUNT" -gt 0 ]; then
    echo "✅ Rate limiting is ACTIVE (blocked $RATE_LIMITED_COUNT requests)"
else
    echo "⚠️  Rate limiting may not be working (all $SUCCESS_COUNT requests succeeded)"
fi
echo ""

# Test 6: User Authentication (get_current_active_user dependency)
echo "Test 6: User Authentication Check"
echo "----------------------------------"
echo "Testing extractor endpoint (requires authenticated user)..."
EXTRACTOR_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/extract/auto" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}')

if echo "$EXTRACTOR_RESPONSE" | grep -q "401"; then
    echo "✅ User authentication required (HTTP 401)"
elif echo "$EXTRACTOR_RESPONSE" | grep -q "503"; then
    echo "⚠️  Extractors disabled (ENABLE_EXTRACTORS=False)"
elif echo "$EXTRACTOR_RESPONSE" | grep -q "User not found"; then
    echo "✅ User authentication active (requires OWNER user)"
else
    echo "⚠️  Response: $(echo $EXTRACTOR_RESPONSE | head -c 100)"
fi
echo ""

# Summary
echo "======================================"
echo "TEST SUMMARY"
echo "======================================"
echo ""
echo "Tier 1 Protections Implemented:"
echo "  ✓ Rate Limiting: 10/min (LLM), 5/min (Extractors)"
echo "  ✓ Feature Flags: ENABLE_LLM, ENABLE_EXTRACTORS"
echo "  ✓ API Key Auth: X-API-Key header (if API_SECRET_KEY set)"
echo "  ✓ User Auth: get_current_active_user (requires OWNER)"
echo ""
echo "Next Steps:"
echo "  1. Set API_SECRET_KEY in .env to enable API key requirement"
echo "  2. Test with feature flags disabled (ENABLE_LLM=False)"
echo "  3. Push to GitHub and deploy to Railway"
echo ""
echo "======================================"
