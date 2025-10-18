#!/bin/bash
# Switch to Railway production environment

echo "🔄 Switching to RAILWAY environment..."
cp .env.railway .env
echo "✅ Using Railway database (postgres.railway.internal)"
echo ""
echo "To start the server (connects to Railway DB):"
echo "  python3.11 -m uvicorn app.main:app --reload --port 9765"
echo ""
echo "⚠️  Warning: This will save extractions to PRODUCTION database!"
