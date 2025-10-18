#!/bin/bash
# Switch to local development environment

echo "🔄 Switching to LOCAL environment..."
cp .env.local .env
echo "✅ Using local database (localhost:7654)"
echo ""
echo "To start the server:"
echo "  python3.11 -m uvicorn app.main:app --reload --port 9765"
