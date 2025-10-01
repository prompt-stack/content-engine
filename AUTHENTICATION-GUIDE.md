# 🔐 Authentication Guide - Content Engine

**Current Status**: Development (No Auth) → Production (JWT + API Keys)

---

## 🎯 Current State (Development)

### No Authentication Required ✅
Right now, **all endpoints are open** for development:

```bash
# Anyone can call any endpoint
curl http://localhost:9765/api/extract/tiktok -d '{"url": "..."}'
curl http://localhost:9765/api/llm/generate -d '{"prompt": "..."}'
curl http://localhost:9765/api/media/generate-image -d '{"prompt": "..."}'
curl http://localhost:9765/api/search/search -d '{"query": "..."}'
```

**Why**: Speed of development, testing, local use

**Risk**: ⚠️ Anyone with access to your server can use unlimited resources

---

## 🚀 Production Authentication (When Ready)

### Two Authentication Methods

#### 1. **JWT Tokens** (For Web Dashboard)
**Use Case**: Users log into web dashboard

**Flow**:
```
1. User signs up → Create account
2. User logs in → Get JWT token
3. Include token in requests → Authenticated
4. Token expires → Refresh or re-login
```

**Example**:
```bash
# Step 1: Login
curl -X POST http://api.contentengine.ai/auth/login \
  -d '{"email": "user@example.com", "password": "..."}'

# Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}

# Step 2: Use token in requests
curl -X POST http://api.contentengine.ai/api/extract/tiktok \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{"url": "..."}'
```

#### 2. **API Keys** (For Programmatic Access)
**Use Case**: Developers integrate Content Engine into their apps

**Flow**:
```
1. User generates API key in dashboard
2. Store API key securely
3. Include in all requests
4. Revoke/rotate as needed
```

**Example**:
```bash
# Generate API key (in dashboard)
API_KEY=ce_sk_abc123xyz789...

# Use in requests
curl -X POST http://api.contentengine.ai/api/extract/tiktok \
  -H "X-API-Key: ce_sk_abc123xyz789..." \
  -d '{"url": "..."}'
```

---

## 📊 Authentication Architecture

### User Table Structure
```python
# app/models/user.py (already exists)
class User(Base):
    id: int
    email: str
    hashed_password: str

    # Role & Tier
    role: UserRole  # USER, ADMIN, SUPERADMIN, OWNER
    tier: UserTier  # FREE, STARTER, PRO, BUSINESS, OWNER

    # Rate Limiting
    requests_this_month: int
    rate_limit: int  # Based on tier

    # Status
    is_active: bool
    is_superuser: bool
    is_verified: bool
```

### API Key Table (Need to Add)
```python
# app/models/api_key.py (future)
class APIKey(Base):
    id: int
    user_id: int  # Foreign key to User
    key_hash: str  # Hashed API key
    name: str  # "Production Server", "Development", etc.

    # Permissions
    scopes: List[str]  # ["extract", "llm", "media", "search"]

    # Usage tracking
    last_used_at: datetime
    requests_count: int

    # Status
    is_active: bool
    expires_at: datetime
    created_at: datetime
```

---

## 🔒 How Authentication Will Work

### Current (Development)
```python
# No authentication
@router.post("/api/extract/tiktok")
async def extract_tiktok(request: ExtractRequest):
    # Anyone can call this
    return await extractor.extract(request.url)
```

### Production (With Auth)
```python
from fastapi import Depends
from app.core.auth import get_current_user

# JWT Authentication
@router.post("/api/extract/tiktok")
async def extract_tiktok(
    request: ExtractRequest,
    user: User = Depends(get_current_user)  # ← Requires auth
):
    # Check rate limit
    if not user.has_quota:
        raise HTTPException(403, "Rate limit exceeded")

    # Track usage
    user.requests_this_month += 1

    return await extractor.extract(request.url)

# API Key Authentication
@router.post("/api/extract/tiktok")
async def extract_tiktok(
    request: ExtractRequest,
    api_key: str = Depends(get_api_key)  # ← Alternative auth
):
    user = await get_user_from_api_key(api_key)
    # Same rate limit checks...
```

---

## 🎯 Rate Limiting by Tier

| Tier | Monthly Requests | Cost | Who |
|------|-----------------|------|-----|
| **FREE** | 100 | Free | Trying it out |
| **STARTER** | 1,000 | $29/mo | Small projects |
| **PRO** | 10,000 | $99/mo | Growing businesses |
| **BUSINESS** | 50,000 | $299/mo | Large companies |
| **OWNER** | ♾️ Unlimited | N/A | You! |

**Rate limit applies to**:
- Content extractions
- LLM API calls
- Image generations
- Search queries

**Not counted**:
- Health checks
- Authentication requests
- Dashboard views

---

## 🔐 FastAPI Users Integration

Content Engine uses **FastAPI Users** (already in requirements.txt):

### What It Provides
```python
# Already configured dependencies
from fastapi_users import FastAPIUsers
from app.models.user import User

# Auth backend (JWT)
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="/auth/login"),
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Dependencies for endpoints
current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
```

### Auto-Generated Endpoints
```bash
# Registration
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Login
POST /auth/login
{
  "username": "user@example.com",
  "password": "securepassword"
}
# Returns: {"access_token": "...", "token_type": "bearer"}

# Logout
POST /auth/logout

# Get current user
GET /users/me
Headers: Authorization: Bearer <token>

# Verify email
POST /auth/request-verify-token
POST /auth/verify

# Password reset
POST /auth/forgot-password
POST /auth/reset-password
```

---

## 🎯 Implementation Status

### Already Have ✅
- ✅ User model with roles & tiers
- ✅ Rate limit properties
- ✅ FastAPI Users in requirements.txt
- ✅ JWT configuration in settings

### Need to Add 🟡
- 🟡 Auth router (register/login endpoints)
- 🟡 JWT strategy implementation
- 🟡 Protect endpoints with `Depends(current_user)`
- 🟡 Rate limit middleware
- 🟡 API key system (optional, for developers)
- 🟡 Usage tracking per request

---

## 🚀 Enabling Authentication (When Ready)

### Step 1: Create Auth Router
```python
# app/api/endpoints/auth.py
from fastapi import APIRouter
from fastapi_users import FastAPIUsers

router = APIRouter()

# Add FastAPI Users routes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)
```

### Step 2: Protect Endpoints
```python
# app/api/endpoints/extractors.py
from app.core.auth import current_active_user

@router.post("/tiktok")
async def extract_tiktok(
    request: ExtractRequest,
    user: User = Depends(current_active_user)  # ← Add this
):
    # Now authenticated!
    if not user.has_quota:
        raise HTTPException(403, "Rate limit exceeded")

    # Track usage
    await track_usage(user, "extraction")

    return await extractor.extract(request.url)
```

### Step 3: Add Rate Limit Middleware
```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from app.models.user import User

async def rate_limit_middleware(request: Request, call_next):
    # Get user from request
    user = request.state.user

    # Skip if owner
    if user.is_owner:
        return await call_next(request)

    # Check rate limit
    if not user.has_quota:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Used {user.requests_this_month}/{user.rate_limit} this month"
        )

    # Increment usage
    user.requests_this_month += 1
    await db.commit()

    return await call_next(request)
```

---

## 🎯 Your Options

### Option 1: Keep No Auth (Current)
**Pros**:
- ✅ Easy to use
- ✅ Fast development
- ✅ Good for personal use

**Cons**:
- ❌ Anyone on network can access
- ❌ No rate limiting
- ❌ No user tracking
- ❌ Not production-ready for others

**Recommendation**: Keep for now, add auth later when needed

### Option 2: Add JWT Auth Only
**Pros**:
- ✅ Secure
- ✅ User accounts
- ✅ Rate limiting
- ✅ Good for web dashboard

**Cons**:
- ⚠️ Requires login flow
- ⚠️ Tokens expire

**Recommendation**: Add when building web dashboard

### Option 3: Add JWT + API Keys
**Pros**:
- ✅ All of Option 2
- ✅ Developer-friendly
- ✅ Long-lived keys
- ✅ Production-ready

**Cons**:
- ⚠️ More complex
- ⚠️ Need key management UI

**Recommendation**: Add when opening to external users

---

## 🔑 API Key Format (Future)

### Format
```
ce_sk_1_abc123def456ghi789jkl012mno345pqr678stu901
│  │  │ │
│  │  │ └─ Random key (40 chars)
│  │  └─── User ID
│  └────── Type (sk = secret key)
└───────── Prefix (ce = Content Engine)
```

### Example Usage
```bash
# Store in environment
export CONTENT_ENGINE_API_KEY="ce_sk_1_abc123..."

# Use in requests
curl -X POST https://api.contentengine.ai/api/extract/tiktok \
  -H "X-API-Key: $CONTENT_ENGINE_API_KEY" \
  -d '{"url": "..."}'
```

---

## 📊 Current API Endpoints (All Open)

### Extractors
```bash
POST /api/extract/tiktok
POST /api/extract/youtube
POST /api/extract/reddit
POST /api/extract/article
POST /api/extract/auto
```

### LLM
```bash
GET  /api/llm/providers
POST /api/llm/generate
POST /api/llm/process-content
```

### Media
```bash
GET  /api/media/providers
POST /api/media/generate-image
POST /api/media/generate-from-content
```

### Search
```bash
GET  /api/search/capabilities
POST /api/search/search
POST /api/search/context
POST /api/search/trending
POST /api/search/fact-check
POST /api/search/news
POST /api/search/research
```

### System
```bash
GET  /
GET  /health
GET  /docs  # OpenAPI documentation
```

**All currently accessible without authentication** ✅

---

## 🎯 Summary

### Current Setup
- ✅ **No authentication** - All endpoints open
- ✅ **Perfect for development** - Fast testing
- ✅ **User model ready** - Has roles, tiers, rate limits
- ⚠️ **Not production-ready** for external users

### When You Need Auth
**Add JWT authentication when**:
- Opening to other users
- Building web dashboard
- Need usage tracking
- Want rate limiting

**Add API keys when**:
- Developers want to integrate
- Need long-lived credentials
- Building SaaS product

### For Now
**Keep it simple**:
- No auth needed
- You're the only user
- Local development
- Test everything first

**Add auth later** when you're ready to:
- Open to users
- Deploy to production
- Track usage
- Charge for access

---

## 🚀 Quick Reference

### Test All Endpoints (No Auth Required)
```bash
# Health check
curl http://localhost:9765/health

# Extract TikTok
curl -X POST http://localhost:9765/api/extract/tiktok \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tiktok.com/..."}'

# Process with LLM
curl -X POST http://localhost:9765/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "provider": "deepseek"}'

# Generate image
curl -X POST http://localhost:9765/api/media/generate-image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "sunset", "provider": "openai"}'

# Search
curl -X POST http://localhost:9765/api/search/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI news", "max_results": 5}'
```

**All work without authentication right now!** ✅