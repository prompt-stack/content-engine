#!/bin/bash
# Sync API keys from .env to .env.local and .env.railway

for key in OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY DEEPSEEK_API_KEY TAVILY_API_KEY GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET; do
  value=$(grep "^${key}=" .env 2>/dev/null | cut -d'=' -f2-)
  if [ ! -z "$value" ]; then
    sed -i '' "s|^${key}=.*|${key}=${value}|" .env.local 2>/dev/null
    sed -i '' "s|^${key}=.*|${key}=${value}|" .env.railway 2>/dev/null
  fi
done

echo "✅ API keys synced to .env.local and .env.railway"
