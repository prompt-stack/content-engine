# Content Engine - Architecture

## Overview

Content Engine is a production-ready API for extracting content from multiple platforms and processing it with LLMs. Built with FastAPI, SQLAlchemy, and async Python.

## Tech Stack

### Backend
- **FastAPI 0.115**: Modern async Python web framework
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **Alembic**: Database migrations
- **Pydantic**: Request/response validation
- **httpx**: Async HTTP client

### Database
- **PostgreSQL 16**: Primary database with pgvector support
- **Redis 7**: Caching, rate limiting, Celery backend

### Background Jobs
- **Celery**: Newsletter processing, batch jobs

### Extractors
- **Reddit**: Public JSON API (no auth)
- **YouTube**: yt-dlp for transcripts
- **TikTok**: Direct API calls
- **Article**: Readability + Playwright fallback

### LLM Integration
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3.5
- **Google**: Gemini Pro
- **DeepSeek**: Most cost-effective ($0.14/M tokens)

## Architecture Layers

### 1. API Layer (`app/api/endpoints/`)

RESTful endpoints with OpenAPI documentation.

```python
# extractors.py - Content extraction endpoints
POST /api/extract/reddit
POST /api/extract/youtube
POST /api/extract/auto     # Auto-detect platform

# content.py - Content management
GET  /api/content/{id}
GET  /api/content/user/{user_id}
POST /api/content/process  # Extract + LLM process

# newsletter.py - Newsletter pipeline
POST /api/newsletter/process
GET  /api/newsletter/{id}
```

### 2. Service Layer (`app/services/`)

Business logic and external integrations.

#### Extractors (`services/extractors/`)
```
base.py                    # BaseExtractor class
reddit_extractor.py        # ✅ Complete
youtube_extractor.py       # TODO
tiktok_extractor.py        # TODO
article_extractor.py       # TODO
email_extractor.py         # TODO
```

**Base Extractor Pattern**:
```python
class BaseExtractor(ABC):
    @property
    @abstractmethod
    def platform(self) -> str: pass

    @property
    @abstractmethod
    def url_patterns(self) -> list[str]: pass

    @abstractmethod
    async def extract(self, url: str) -> Dict[str, Any]: pass

    def can_handle(self, url: str) -> bool:
        # Pattern matching
```

#### LLM Services (`services/llm/`)
```
base.py                    # Base LLM interface
openai_service.py          # OpenAI implementation
anthropic_service.py       # Claude implementation
gemini_service.py          # Google Gemini
deepseek_service.py        # DeepSeek (cheapest)
llm_factory.py             # Factory pattern
```

**LLM Service Interface**:
```python
class BaseLLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str: pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]: pass
```

#### Content Processors (`services/processors/`)
```
summarizer.py              # Summarization
entity_extractor.py        # Named entity extraction
sentiment_analyzer.py      # Sentiment analysis
categorizer.py             # Auto-categorization
```

#### Orchestration (`services/content_service.py`)
```python
class ContentService:
    async def extract_and_process(
        self,
        url: str,
        tasks: List[str] = ['summarize'],
        save_to_db: bool = True
    ) -> Content:
        """
        1. Detect platform
        2. Extract content
        3. Process with LLM
        4. Save to database
        5. Return result
        """
```

### 3. Model Layer (`app/models/`)

SQLAlchemy ORM models with async support.

```python
# User model with tiers
class User(SQLAlchemyBaseUserTable):
    tier: UserTier  # free, starter, pro, business
    requests_this_month: int
    rate_limit: property  # Based on tier

# Content model
class Content:
    platform: Platform
    url: str
    title: str
    author: str
    content: str (Text)
    metadata: dict (JSON)

    # LLM processing results
    summary: str (Text)
    entities: dict (JSON)
    sentiment: str
    categories: list (JSON)

    status: ProcessingStatus

# Newsletter model
class Newsletter:
    title: str
    digest: str (Text)
    source_count: int
    source_content_ids: list (JSON)
```

### 4. Database Layer (`app/db/`)

Async SQLAlchemy session management.

```python
# session.py
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine)

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

### 5. Configuration (`app/core/`)

Pydantic settings with environment variables.

```python
class Settings(BaseSettings):
    # Auto-loaded from .env
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    # ...

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def default_llm_provider(self) -> str:
        # Prefer DeepSeek for cost
```

## Data Flow

### Simple Extraction
```
User Request
    ↓
POST /api/extract/reddit
    ↓
RedditExtractor.extract()
    ↓
Standardized Output
    ↓
JSON Response
```

### Full Processing Pipeline
```
User Request
    ↓
POST /api/content/process
    ↓
ContentService.extract_and_process()
    ↓
┌─────────────────────┐
│ 1. Detect Platform  │ → PlatformDetector
├─────────────────────┤
│ 2. Extract Content  │ → RedditExtractor/etc
├─────────────────────┤
│ 3. LLM Processing   │ → DeepSeekService
│    - Summarize      │
│    - Extract NER    │
│    - Sentiment      │
├─────────────────────┤
│ 4. Save to DB       │ → Content model
├─────────────────────┤
│ 5. Return Result    │ → JSON response
└─────────────────────┘
```

### Newsletter Pipeline (Killer Feature)
```
User Request: "Process my newsletters"
    ↓
POST /api/newsletter/process
{
  "gmail_query": "label:newsletters after:2025-01-01",
  "generate_digest": true
}
    ↓
NewsletterService.process_newsletters()
    ↓
┌─────────────────────────────┐
│ 1. Gmail Extraction         │ → EmailExtractor
│    - Fetch newsletters      │
│    - Extract links          │
├─────────────────────────────┤
│ 2. Batch Content Extraction │ → ContentService (Celery)
│    - For each link:         │
│      → Detect platform      │
│      → Extract              │
│      → Process with LLM     │
├─────────────────────────────┤
│ 3. Digest Generation        │ → Claude
│    - Combine summaries      │
│    - Find common themes     │
│    - Generate digest        │
├─────────────────────────────┤
│ 4. Save Newsletter          │ → Newsletter model
└─────────────────────────────┘
    ↓
Return digest + processed content
```

## Authentication & Authorization

### FastAPI Users
```python
# Provides:
- JWT authentication
- User registration/login
- OAuth2 (Google, GitHub, etc.)
- Email verification
- Password reset

# Usage:
current_user = Depends(fastapi_users.current_user())
```

### Rate Limiting (Redis)
```python
# Based on user tier:
- Free:     100 requests/month
- Starter:  1,000 requests/month
- Pro:      10,000 requests/month
- Business: 50,000 requests/month

# Middleware checks:
if user.requests_this_month >= user.rate_limit:
    raise HTTPException(429, "Rate limit exceeded")
```

## Background Jobs (Celery)

```python
# celery_app.py
@celery_app.task
def process_newsletter_batch(newsletter_id: int):
    """Process newsletter links in background."""
    # Long-running task
    # Updates status in database
    # Sends notification when done
```

## Deployment

### Local Development
```bash
docker-compose up -d
# PostgreSQL:  localhost:5432
# Redis:       localhost:6379
# FastAPI:     localhost:8000
```

### Production (Railway + Neon)
```yaml
# Railway:
- FastAPI backend (auto-scaling)
- Redis instance
- Celery workers

# Neon:
- PostgreSQL database (serverless)
- Automatic backups
- pgvector for embeddings
```

## Cost Analysis

### Infrastructure (Neon + Railway)
- **Neon Free**: 10 projects, 3GB each = $0/mo
- **Railway Starter**: $5/mo credit = ~$5/mo
- **Total**: $5-20/mo

### LLM Costs (per 1,000 requests)
**Newsletter workflow** (extract 10 links, summarize each):
- **DeepSeek**: 100K tokens = $0.06 ✅ CHEAPEST
- **OpenAI GPT-3.5**: 100K tokens = $0.30
- **Claude**: 100K tokens = $3.00
- **GPT-4**: 100K tokens = $15.00

**Recommendation**: Default to DeepSeek, offer premium LLMs as upsell.

## Security

1. **Environment Variables**: All secrets in `.env`, never in code
2. **JWT Authentication**: Secure token-based auth
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Pydantic models validate all inputs
5. **SQL Injection**: SQLAlchemy ORM prevents SQL injection
6. **CORS**: Configured per environment

## Monitoring

```python
# Health check endpoint
GET /health
{
  "status": "healthy",
  "features": {
    "openai": true,
    "deepseek": true,
    "gmail": false
  }
}

# Metrics endpoint (future)
GET /metrics
- Request counts
- Error rates
- Processing times
- LLM token usage
```

## Testing

```python
# Unit tests
tests/test_extractors.py
tests/test_llm_services.py

# Integration tests
tests/test_api.py
tests/test_pipeline.py

# Run tests
pytest
pytest --cov=app tests/
```

## Next Development Phases

1. ✅ **Phase 1**: Core infrastructure + Reddit extractor
2. **Phase 2**: Port remaining extractors (TikTok, YouTube, Article)
3. **Phase 3**: Port LLM services
4. **Phase 4**: Build ContentService orchestration
5. **Phase 5**: Newsletter pipeline
6. **Phase 6**: Authentication + rate limiting
7. **Phase 7**: Frontend dashboard
8. **Phase 8**: Deployment + monitoring