# Content Engine - Quick Start

## What You Have Now

A working FastAPI backend with:
- ✅ Reddit extractor (Python port complete)
- ✅ Docker setup (PostgreSQL + Redis + FastAPI)
- ✅ API endpoints with auto-docs
- ✅ Base extractor class for easy extension
- ✅ Configuration with environment variables

## Getting Started

### 1. Start the services

```bash
cd /Users/hoff/My\ Drive/tools/data-processing/content-engine

# Start all services
make up

# Or manually:
docker-compose up -d
```

### 2. Check API is running

```bash
# Health check
curl http://localhost:8765/health

# API documentation
open http://localhost:8765/docs
```

**Note**: Using port **8765** (not 8000) to avoid conflicts. Change in `.env` if needed.

### 3. Test Reddit extraction

```bash
curl -X POST http://localhost:8765/api/extract/reddit \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/programming/comments/abc123/...",
    "max_comments": 10
  }'
```

Or visit http://localhost:8765/docs and test interactively!

## Project Structure

```
content-engine/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/         # API routes
│   │   │   └── extractors.py      # ✅ Reddit endpoint working
│   │   ├── core/
│   │   │   └── config.py          # Settings
│   │   ├── db/                    # Database setup
│   │   ├── models/                # SQLAlchemy models
│   │   │   ├── user.py            # User + tiers
│   │   │   └── content.py         # Content + newsletters
│   │   └── services/
│   │       └── extractors/
│   │           ├── base.py        # Base extractor class
│   │           └── reddit_extractor.py  # ✅ Working!
│   ├── .env                       # Configuration
│   ├── requirements.txt           # Python deps
│   └── Dockerfile
├── docker-compose.yml
├── Makefile
└── README.md
```

## Next Steps

### Phase 1: Port Remaining Extractors (2-4 hours)

1. **TikTok** - Port from `/content-hub/backend/extractors/tiktok/tiktok-extractor.js`
2. **YouTube** - Port from `/content-hub/backend/extractors/youtube/youtube-extractor.js`
3. **Article** - Port from `/content-hub/backend/extractors/article/article-extractor.js`

Each follows the same pattern as Reddit:
```python
class TikTokExtractor(BaseExtractor):
    @property
    def platform(self) -> str:
        return "tiktok"

    @property
    def url_patterns(self) -> list[str]:
        return [r"tiktok\.com/@[\w.-]+/video/\d+"]

    async def extract(self, url: str) -> Dict[str, Any]:
        # Your extraction logic
        return self._standardize_output(...)
```

### Phase 2: Port LLM Services (1-2 hours)

Copy from `/dev/projects/prompt-stack/web/backend/app/services/llm/`:
- `llm_service.py` → `/backend/app/services/llm/llm_service.py`
- Already has OpenAI, Anthropic, Gemini, DeepSeek

### Phase 3: Build Content Orchestration (2-3 hours)

Create `ContentService` that combines:
1. Extractor (get content)
2. LLM (process content)
3. Database (save results)

### Phase 4: Newsletter Pipeline (3-4 hours)

The killer feature! Port email extractor and create pipeline:
```python
# One API call does everything:
POST /api/newsletter/process
{
  "gmail_query": "label:newsletters after:2025-01-01",
  "generate_digest": true
}
```

## Development Commands

```bash
# View logs
make logs

# API logs only
make logs-api

# Stop services
make down

# Clean everything (including volumes)
make clean

# Restart
make down && make up
```

## Testing

```bash
# Run tests
make test

# Or manually:
docker-compose exec backend pytest
```

## Configuration

Edit `backend/.env` to configure:
- Database URL (use Neon for production)
- LLM API keys (OpenAI, Anthropic, etc.)
- Feature flags

## What's Next?

1. **Want to test locally?** Start Docker and test Reddit extraction
2. **Ready to add more extractors?** Follow Phase 1 above
3. **Want to add LLM processing?** Follow Phase 2 & 3
4. **Want the newsletter feature?** Follow Phase 4

All the hard architectural decisions are done. Now it's just porting code!