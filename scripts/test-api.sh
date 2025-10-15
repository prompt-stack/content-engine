#!/bin/bash

# Content Engine - API Test Script

echo "======================================"
echo "Content Engine API Test"
echo "======================================"
echo ""

# Read port from .env file or default to 8765
API_PORT=${API_PORT:-8765}
BASE_URL="http://localhost:${API_PORT}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
curl -s "$BASE_URL/" | jq '.'
echo ""

# Test 2: Detailed Health
echo -e "${YELLOW}Test 2: Detailed Health${NC}"
curl -s "$BASE_URL/health" | jq '.'
echo ""

# Test 3: Reddit Extraction (example URL)
echo -e "${YELLOW}Test 3: Reddit Extraction${NC}"
echo "Testing with a sample Reddit URL..."
curl -s -X POST "$BASE_URL/api/extract/reddit" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/programming/comments/1234567/example",
    "max_comments": 5
  }' | jq '.'
echo ""

# Test 4: API Documentation
echo -e "${YELLOW}Test 4: API Documentation${NC}"
echo "OpenAPI docs available at: ${GREEN}$BASE_URL/docs${NC}"
echo "ReDoc available at: ${GREEN}$BASE_URL/redoc${NC}"
echo ""

echo "======================================"
echo -e "${GREEN}✓ All tests complete!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8000/docs in your browser"
echo "2. Try the interactive API documentation"
echo "3. Test with real Reddit URLs"
echo ""