# Content Engine - Architecture

> **Last Updated:** October 2025
> **Status:** Production-ready system with Clerk authentication

## Overview

Content Engine is a full-stack application for extracting, processing, and organizing content from multiple platforms. Users can extract content from Reddit, YouTube, TikTok, articles, and newsletters, with all data secured by user-specific authentication.

**Live Production:**
- Frontend: https://content-engine-frontend-green.vercel.app
- Backend API: https://content-engine-production.up.railway.app
- Database: Railway PostgreSQL

---

## Tech Stack

### Frontend
- **Next.js 15.5** - React framework with App Router
- **Clerk** - Authentication & user management
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Styling
- **Vercel** - Deployment platform

### Backend
- **FastAPI 0.115** - Modern async Python web framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Alembic** - Database migrations
- **Pydantic** - Request/response validation
- **httpx** - Async HTTP client
- **Clerk SDK** - JWT verification

### Database
- **PostgreSQL 16** - Relational database (Railway)
- **User-specific data isolation** - All content linked to users

### Extractors (All Implemented ✅)
- **Reddit** - Public JSON API + comment extraction
- **YouTube** - yt-dlp for video transcripts
- **TikTok** - Caption extraction
- **Article** - Readability.js for clean text extraction
- **Email/Newsletter** - Gmail API integration

### LLM Integration (Available)
- **OpenAI** - GPT-4, GPT-3.5
- **Anthropic** - Claude 3.5
- **Google** - Gemini Pro
- **DeepSeek** - Cost-effective option ($0.14/M tokens)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                  (Clerk Session + JWT Token)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├─ Sign In/Out (Clerk Modal)
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                 FRONTEND (Next.js on Vercel)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Middleware (middleware.ts)                           │   │
│  │  - Protects routes: /vault, /extract, /newsletters  │   │
│  │  - Verifies Clerk session                           │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Protected Pages (app/(protected)/)                   │   │
│  │  - AuthGate component verifies authentication       │   │
│  │  - Returns user to original page after sign-in      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Client (src/lib/api.ts)                         │   │
│  │  - Gets JWT from Clerk: window.Clerk.session.token  │   │
│  │  - Adds Authorization header to all requests        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                Authorization: Bearer <jwt-token>
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                BACKEND API (FastAPI on Railway)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Clerk Auth (app/core/clerk.py)                       │   │
│  │  1. Verify JWT signature with Clerk JWKS            │   │
│  │  2. Extract clerk_user_id from token                │   │
│  │  3. Query database for user                         │   │
│  │  4. If not found: Create user (JIT provisioning)    │   │
│  │  5. Return User object to endpoint                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Endpoints                                        │   │
│  │  - extractors.py: /api/extract/*                    │   │
│  │  - newsletters.py: /api/newsletters/*               │   │
│  │  - capture.py: /api/capture/*                       │   │
│  │  - llm.py: /api/llm/*                               │   │
│  │  All protected with: Depends(get_current_user)      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Extractors (app/services/extractors/)               │   │
│  │  - RedditExtractor ✅                                │   │
│  │  - YouTubeExtractor ✅                               │   │
│  │  - TikTokExtractor ✅                                │   │
│  │  - ArticleExtractor ✅                               │   │
│  │  - EmailExtractor ✅                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            DATABASE (PostgreSQL on Railway)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ users                                                │   │
│  │  - id (PK)                                           │   │
│  │  - clerk_user_id (UK, Primary auth method)          │   │
│  │  - email, role, tier                                │   │
│  │  - requests_this_month (quota tracking)             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ captures (user-specific content)                     │   │
│  │  - id, user_id (FK)                                  │   │
│  │  - title, content, meta                             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ extractions (newsletter sessions)                    │   │
│  │  - id, user_id (FK)                                  │   │
│  │  - created_at, days_back, max_results               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### 1. Frontend Layer (Next.js)

**Location:** `/frontend/`

#### Route Protection
- **Middleware** (`middleware.ts`) - Server-side route protection
  - Uses Clerk's `clerkMiddleware` to protect routes
  - Matches routes from centralized config (`src/config/routes.ts`)
  - Returns 401 for unauthenticated requests

- **Auth Gate** (`app/(protected)/_components/auth-gate.tsx`) - Client-side
  - Waits for Clerk to load
  - Redirects to sign-in if needed
  - Preserves return URL

- **Single Source of Truth** (`src/config/routes.ts`)
  ```typescript
  export const PROTECTED_ROUTE_PREFIXES = [
    '/vault',
    '/newsletters',
    '/extract',
  ] as const;
  ```

- **Build-Time Validation** (`scripts/validate-protected-routes.mjs`)
  - Ensures folder structure matches config
  - Prevents drift between middleware and routes

#### API Client
**Location:** `/frontend/src/lib/api.ts`

Centralized client with automatic JWT injection:
```typescript
// Automatic authentication for all API calls
const extractions = await api.newsletters.extractions();
const capture = await api.captures.create({ content: "..." });
```

### 2. Backend API Layer

**Location:** `/backend/app/api/endpoints/`

#### Implemented Endpoints

**Extractors** (`extractors.py`) - ✅ All platforms implemented
```python
POST /api/extract/auto        # Auto-detect platform
POST /api/extract/reddit       # Reddit posts + comments
POST /api/extract/youtube      # Video transcripts
POST /api/extract/tiktok       # TikTok captions
POST /api/extract/article      # Web articles

# All return standardized format:
{
  "platform": "reddit",
  "title": "...",
  "author": "...",
  "content": "...",
  "metadata": {...},
  "capture_id": 123  # Saved to user's vault
}
```

**Newsletters** (`newsletters.py`)
```python
POST /api/newsletters/extract          # Extract from Gmail
GET  /api/newsletters/extractions      # List user's extractions
GET  /api/newsletters/extractions/{id} # Get extraction details
GET  /api/newsletters/config           # Get user config
PUT  /api/newsletters/config           # Update config
POST /api/newsletters/config/test-url  # Test URL extraction
```

**Captures** (`capture.py`) - User's content vault
```python
GET  /api/capture/list                # User's saved content
GET  /api/capture/{id}                # Single capture
POST /api/capture/text                # Save text capture
DELETE /api/capture/{id}              # Delete capture
GET  /api/capture/stats/count         # Count user's captures
```

**LLM** (`llm.py`) - Text generation
```python
POST /api/llm/generate               # Generate with multiple providers
```

**Authentication** (`auth.py`)
```python
GET /api/auth/me                     # Current user info
```

### 3. Service Layer

**Location:** `/backend/app/services/`

#### Extractors (All Implemented ✅)

**Base Extractor Pattern** (`extractors/base.py`)
```python
class BaseExtractor(ABC):
    @property
    @abstractmethod
    def platform(self) -> str: pass

    @abstractmethod
    async def extract(self, url: str) -> Dict[str, Any]: pass

    @abstractmethod
    def can_handle(self, url: str) -> bool: pass
```

**Platform Detector** (`extractors/base.py`)
```python
class PlatformDetector:
    @staticmethod
    def detect(url: str) -> Optional[str]:
        # Returns: "reddit", "youtube", "tiktok", "article", or None
```

**Implemented Extractors:**
- `reddit_extractor.py` - Posts + top-level comments with metadata
- `youtube_extractor.py` - Video transcripts via yt-dlp
- `tiktok_extractor.py` - Caption extraction
- `article_extractor.py` - Clean article text
- `email/pipeline.py` - Gmail newsletter extraction with link resolution

#### LLM Services

**Factory Pattern** (`llm/llm_factory.py`)
```python
LLMFactory.create("openai")     # GPT-4
LLMFactory.create("anthropic")  # Claude
LLMFactory.create("gemini")     # Gemini Pro
LLMFactory.create("deepseek")   # Most cost-effective
```

### 4. Authentication System

**Location:** `/backend/app/core/clerk.py`

#### Clerk JWT Verification

```python
async def get_current_user_from_clerk(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    1. Extract JWT from Authorization header
    2. Fetch Clerk's JWKS (public keys)
    3. Verify JWT signature and expiration
    4. Extract clerk_user_id from JWT claims
    5. Query database for user
    6. If not found: Create new user (JIT provisioning)
    7. Return User object
    """
```

#### Just-In-Time (JIT) User Provisioning

**First-time user flow:**
```
User signs in with GitHub via Clerk
        ↓
User makes first API call
        ↓
Backend verifies JWT (clerk_user_id: "user_34DOE0...")
        ↓
Query database: User with clerk_user_id exists?
        ↓
NO → Create new user:
     INSERT INTO users (
       clerk_user_id,
       email,
       role = 'USER',
       tier = 'FREE',
       oauth_provider = 'clerk'
     )
        ↓
Return User object to endpoint
```

#### Endpoint Protection

```python
# Old way (removed):
@router.post("/api/extract/auto")
async def extract_auto(
    user: User = Depends(get_current_active_user),  # ❌ Removed
    _: bool = Depends(verify_api_key)  # ❌ Removed
):
    pass

# New way (Clerk only):
@router.post("/api/extract/auto")
async def extract_auto(
    user: User = Depends(get_current_user_from_clerk)  # ✅ Only this
):
    # user.id - Database ID
    # user.clerk_user_id - Clerk user ID
    # user.email
    # user.role, user.tier
    pass
```

### 5. Database Layer

**Location:** `/backend/app/models/`, `/backend/app/db/`

#### Core Models

**User Model** (`models/user.py`)
```python
class User(Base):
    id: int                           # Primary key
    clerk_user_id: str                # Unique, primary auth method
    email: str                        # From Clerk
    role: UserRole                    # USER, ADMIN, OWNER
    tier: UserTier                    # FREE, STARTER, PRO, BUSINESS
    requests_this_month: int          # Quota tracking
    requests_reset_at: datetime       # Monthly reset

    # OAuth fields (legacy, can be removed)
    google_id, google_email, google_picture

    # Relationships
    captures: List[Capture]
    extractions: List[Extraction]
    newsletter_config: NewsletterConfig
```

**Capture Model** (`models/capture.py`)
```python
class Capture(Base):
    id: int                           # Primary key
    user_id: int                      # Foreign key (CASCADE delete)
    title: str
    content: Text
    meta: dict                        # JSON metadata
    created_at: datetime
```

**Extraction Model** (`models/extraction.py`)
```python
class Extraction(Base):
    id: str                           # Session ID (e.g., "20251015_162827")
    user_id: int                      # Foreign key (CASCADE delete)
    created_at: datetime
    days_back: int
    max_results: int

    # Relationships
    email_content: List[EmailContent]
```

#### Session Management

```python
# Async session factory
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine)

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

### 6. Configuration

**Location:** `/backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Clerk Authentication
    CLERK_PUBLISHABLE_KEY: str
    CLERK_SECRET_KEY: str

    # LLM Providers
    OPENAI_API_KEY: Optional[str]
    ANTHROPIC_API_KEY: Optional[str]
    GEMINI_API_KEY: Optional[str]
    DEEPSEEK_API_KEY: Optional[str]

    # Feature Flags
    ENABLE_EXTRACTORS: bool = True
    ENABLE_LLM: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3456",
        "https://content-engine-frontend-green.vercel.app"
    ]

    @property
    def default_llm_provider(self) -> str:
        """Prefer DeepSeek for cost efficiency"""
        if self.DEEPSEEK_API_KEY:
            return "deepseek"
        # ... fallback logic
```

---

## Data Flows

### Content Extraction Flow

```
User visits /extract page
        ↓
Enters Reddit URL, clicks "Extract"
        ↓
Frontend: POST /api/extract/auto
Headers: { Authorization: "Bearer <jwt>" }
Body: { url: "https://reddit.com/r/..." }
        ↓
Backend: get_current_user_from_clerk()
  - Verify JWT ✅
  - Load/create user ✅
        ↓
Backend: PlatformDetector.detect(url) → "reddit"
        ↓
Backend: RedditExtractor.extract(url)
  - Fetch post JSON
  - Extract top 20 comments
  - Format as clean text
        ↓
Backend: Save to database
  INSERT INTO captures (
    user_id = user.id,
    title = post_title,
    content = post + comments,
    meta = {platform, author, url, ...}
  )
        ↓
Backend: Return extraction result
  { title, content, metadata, capture_id }
        ↓
Frontend: Show success + link to /vault
```

### Newsletter Extraction Flow

```
User visits /newsletters page
        ↓
Clicks "Extract Newsletters"
        ↓
Frontend: POST /api/newsletters/extract
Headers: { Authorization: "Bearer <jwt>" }
Body: { days: 7, max_results: 10 }
        ↓
Backend: Authenticate user
        ↓
Backend: EmailExtractor.extract()
  1. Connect to Gmail API
  2. Fetch emails from last 7 days
  3. Extract links from each email
  4. Resolve redirects/tracking URLs
  5. Save to database:
     - Extraction session
     - EmailContent records
     - ExtractedLinks
        ↓
Backend: Return extraction ID
        ↓
Frontend: Show list of extracted links
        ↓
User clicks link to view details
```

### User-Specific Data Isolation

All endpoints filter by `user_id`:
```python
# Captures - only user's content
captures = await db.execute(
    select(Capture)
    .where(Capture.user_id == current_user.id)
    .order_by(Capture.created_at.desc())
)

# Extractions - only user's sessions
extractions = await db.execute(
    select(Extraction)
    .where(Extraction.user_id == current_user.id)
)
```

---

## Deployment

### Production Stack

| Component | Platform | URL |
|-----------|----------|-----|
| Frontend | Vercel | https://content-engine-frontend-green.vercel.app |
| Backend | Railway | https://content-engine-production.up.railway.app |
| Database | Railway | PostgreSQL 16 (managed) |

### Deployment Process

**Backend (Railway):**
1. Push to GitHub `main` branch
2. Railway auto-detects changes
3. Runs Alembic migrations automatically
4. Deploys new backend version
5. Health check: `/health` endpoint

**Frontend (Vercel):**
1. Push to GitHub `main` branch
2. Vercel auto-builds Next.js app
3. Runs `npm run validate:routes` (build-time validation)
4. Deploys to production domain
5. Updates alias automatically

### Environment Variables

**Railway (Backend):**
```bash
# Set via CLI
railway variables --set "CLERK_PUBLISHABLE_KEY=pk_..."
railway variables --set "CLERK_SECRET_KEY=sk_..."
railway variables --set "OPENAI_API_KEY=sk-..."

# Or use Railway dashboard
```

**Vercel (Frontend):**
```bash
# Set via CLI for all environments
echo "pk_..." | vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
echo "sk_..." | vercel env add CLERK_SECRET_KEY production
echo "https://content-engine-production.up.railway.app" | vercel env add NEXT_PUBLIC_API_URL production

# Or use Vercel dashboard
```

### Database Migrations

**Automatic on Railway:**
```bash
# Defined in start.sh (runs before server starts)
alembic upgrade head
```

**Local development:**
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Security

### Authentication
- ✅ JWT tokens (Clerk) with JWKS verification
- ✅ Secure token storage (httpOnly cookies via Clerk)
- ✅ Server-side middleware protection
- ✅ Client-side Auth Gate for UX
- ✅ Return URL preservation after sign-in

### Authorization
- ✅ User-specific data isolation (all queries filter by `user_id`)
- ✅ Role-based access control (USER, ADMIN, OWNER)
- ✅ Tier-based quotas (FREE, STARTER, PRO, BUSINESS)

### Data Protection
- ✅ All secrets in environment variables
- ✅ CORS configured per environment
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation (Pydantic models)
- ✅ CASCADE delete (user deletion removes all data)

### API Security
- ✅ Rate limiting per user tier
- ✅ Request quota tracking (`requests_this_month`)
- ✅ HTTPS only in production
- ✅ No API keys (removed old system)

---

## Monitoring

### Health Check

```bash
curl https://content-engine-production.up.railway.app/health

{
  "status": "healthy",
  "environment": "production",
  "features": {
    "openai": true,
    "anthropic": true,
    "gemini": true,
    "deepseek": true,
    "gmail": false,
    "tavily": true,
    "default_llm": "deepseek"
  }
}
```

### User Endpoint

```bash
curl https://content-engine-production.up.railway.app/api/auth/me \
  -H "Authorization: Bearer <jwt>"

{
  "id": 2,
  "clerk_user_id": "user_34DOE0...",
  "email": "you@github.com",
  "role": "user",
  "tier": "free",
  "requests_this_month": 5,
  "created_at": "2025-10-17T..."
}
```

---

## Cost Analysis

### Infrastructure

| Service | Plan | Cost |
|---------|------|------|
| Vercel (Frontend) | Hobby | $0/mo (5GB bandwidth included) |
| Railway (Backend + DB) | Starter | ~$5-10/mo |
| Clerk (Auth) | Free | $0/mo (up to 10,000 MAU) |
| **Total** | | **~$5-10/mo** |

### LLM Costs (Optional)

Per 1,000 content extractions with summaries (100K tokens):
- **DeepSeek**: $0.06 ✅ Most cost-effective
- **OpenAI GPT-3.5**: $0.30
- **Claude 3.5**: $3.00
- **GPT-4**: $15.00

**Note:** LLM processing is optional. Core extraction is free.

---

## Development Phases

### ✅ Completed
1. ✅ Core infrastructure (FastAPI + SQLAlchemy + PostgreSQL)
2. ✅ All extractors (Reddit, YouTube, TikTok, Article, Email)
3. ✅ LLM integration (OpenAI, Claude, Gemini, DeepSeek)
4. ✅ Newsletter extraction pipeline
5. ✅ Clerk authentication + JIT provisioning
6. ✅ User-specific data isolation
7. ✅ Frontend (Next.js) with protected routes
8. ✅ Production deployment (Vercel + Railway)
9. ✅ Database migrations (Alembic)

### 🚧 Future Enhancements
1. Advanced LLM features (summarization, entity extraction, sentiment)
2. Batch processing for newsletter digests
3. Webhook notifications for completed extractions
4. Search/filtering in vault
5. Export functionality (PDF, Markdown, JSON)
6. Admin dashboard for user management
7. Usage analytics and metrics
8. Stripe integration for paid tiers

---

## Related Documentation

- **Authentication:** `/docs/AUTH-INTEGRATION.md` - Complete auth system guide
- **Protected Routes:** `/frontend/docs/PROTECTED_ROUTES.md` - Frontend route protection
- **CORS:** `/docs/CORS-CONFIGURATION.md` - CORS setup and troubleshooting
- **Database:** `/docs/database-schema.mmd` - Database schema diagram
- **API Docs:** `/backend/README.md` - Backend API documentation

---

## Summary

Content Engine is a **production-ready, full-stack application** with:

✅ **Secure authentication** via Clerk with JIT user provisioning
✅ **User-specific data isolation** - Every user has their own vault
✅ **Multi-platform extraction** - Reddit, YouTube, TikTok, Articles, Emails
✅ **Optional LLM processing** - Summarization and analysis
✅ **Protected frontend routes** - Seamless auth UX
✅ **Scalable deployment** - Vercel + Railway
✅ **Comprehensive documentation** - Every system documented

**Ready for users and future growth! 🚀**
