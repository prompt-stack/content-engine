# Authentication Integration - Clerk + Database

## Overview

Content Engine uses **Clerk** for authentication with **Just-In-Time (JIT) user provisioning** to automatically sync users into the PostgreSQL database.

---

## How It Works

### Authentication Flow

```
1. User signs in via Clerk (GitHub, Google, or Email)
   ↓
2. Clerk authenticates & issues JWT token
   ↓
3. Frontend sends JWT in Authorization header
   ↓
4. Backend verifies JWT with Clerk's public keys
   ↓
5. Backend checks database for user (by clerk_user_id)
   ↓
6. IF NOT EXISTS: Create new User record
   ↓
7. Return User object to endpoint
```

### Just-In-Time (JIT) Provisioning

**First Time User:**
- Clerk ID: `user_2abc123xyz`
- Email: `you@github.com`
- Creates database record:
  ```sql
  INSERT INTO users (
    clerk_user_id,
    email,
    role,
    tier,
    is_active,
    is_verified,
    oauth_provider
  ) VALUES (
    'user_2abc123xyz',
    'you@github.com',
    'USER',
    'FREE',
    true,
    true,
    'clerk'
  );
  ```

**Returning User:**
- Finds existing record by `clerk_user_id`
- Returns user immediately

---

## Database Schema

### USERS Table (Updated)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| **id** | integer | PRIMARY KEY | Auto-increment database ID |
| **clerk_user_id** | varchar(255) | UNIQUE, INDEX | Clerk user ID (user_xxxxx) |
| email | varchar(320) | UNIQUE | User email |
| hashed_password | varchar(1024) | | Empty for Clerk users |
| is_active | boolean | NOT NULL | Account status |
| is_verified | boolean | NOT NULL | Email verified (always true for Clerk) |
| role | enum | NOT NULL | USER \| ADMIN \| SUPERADMIN \| OWNER |
| tier | enum | NOT NULL | FREE \| STARTER \| PRO \| BUSINESS \| OWNER |
| requests_this_month | integer | NOT NULL, default 0 | API quota tracking |
| oauth_provider | varchar(50) | | "clerk" for all new users |
| created_at | timestamp | NOT NULL | Account creation |
| updated_at | timestamp | NOT NULL | Last update |

**Key Points:**
- `clerk_user_id` is the **primary link** between Clerk and database
- `hashed_password` is empty (Clerk handles auth)
- `is_verified` is always `true` (Clerk handles email verification)
- All new signups get `role=USER` and `tier=FREE`

---

## Code Implementation

### Backend: Clerk JWT Verification

**Location:** `/backend/app/core/clerk.py`

```python
from app.core.clerk import get_current_user_from_clerk

@router.post("/api/capture/text")
async def create_capture(
    content: str,
    user: User = Depends(get_current_user_from_clerk)  # ← Magic dependency!
):
    # user is a full SQLAlchemy User object from database
    capture = Capture(
        user_id=user.id,  # Database ID
        content=content
    )
    # ...
```

**What the dependency does:**
1. Extracts JWT from `Authorization: Bearer {token}` header
2. Verifies JWT signature with Clerk's JWKS
3. Extracts `clerk_user_id` from JWT claims
4. Queries database: `SELECT * FROM users WHERE clerk_user_id = ?`
5. If not found: Creates new user
6. Returns `User` ORM object

### Frontend: Automatic Token Injection

**Location:** `/frontend/src/lib/api.ts`

```typescript
async function apiRequest<T>(endpoint: string, options?: RequestInit) {
  // Get token from Clerk
  const token = await window.Clerk.session?.getToken();

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : undefined,
    ...options?.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  return response.json();
}
```

**All API calls automatically include auth token!**

---

## Environment Variables

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_API_URL=http://localhost:9765
```

### Backend (`.env`)

```env
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
DATABASE_URL=postgresql+asyncpg://...
```

---

## Testing Authentication

### Test in Browser Console

```javascript
// Get your auth token
const token = await window.Clerk.session.getToken();
console.log('Token:', token);

// Call protected endpoint
fetch('http://localhost:9765/api/auth/me', {
  headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(console.log);

// Expected response:
// {
//   "id": 1,
//   "clerk_user_id": "user_2abc123xyz",
//   "email": "you@github.com",
//   "role": "user",
//   "tier": "free",
//   "requests_this_month": 0,
//   "created_at": "2025-10-17T..."
// }
```

### Test in Terminal

```bash
# Get token from browser console first
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Call protected endpoint
curl http://localhost:9765/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## User Roles & Tiers

### Roles (Permissions)

| Role | Description | Capabilities |
|------|-------------|--------------|
| **USER** | Default role | Basic access to all features |
| **ADMIN** | Admin user | Can manage other users |
| **SUPERADMIN** | Super admin | Can manage system settings |
| **OWNER** | System owner | Unlimited access, no quotas |

### Tiers (Quotas)

| Tier | Requests/Month | Description |
|------|----------------|-------------|
| **FREE** | 100 | Default for new signups |
| **STARTER** | 1,000 | Paid tier |
| **PRO** | 10,000 | Paid tier |
| **BUSINESS** | 50,000 | Paid tier |
| **OWNER** | Unlimited | System owner (you) |

---

## Quota Enforcement

### Check Quota in Endpoint

```python
from fastapi import HTTPException

@router.post("/api/extract/auto")
async def extract_auto(
    url: str,
    user: User = Depends(get_current_user_from_clerk)
):
    # Check quota
    if not user.has_quota:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly quota exceeded. You've used {user.requests_this_month} requests."
        )

    # Increment usage
    user.requests_this_month += 1
    await db.commit()

    # Process request...
```

### User Model Properties

```python
@property
def has_quota(self) -> bool:
    """Check if user has remaining quota."""
    if self.tier == UserTier.OWNER:
        return True  # Unlimited
    return self.requests_this_month < self.rate_limit

@property
def rate_limit(self) -> int:
    """Get user's monthly rate limit based on tier."""
    if self.tier == UserTier.OWNER:
        return 999999999

    limits = {
        UserTier.FREE: 100,
        UserTier.STARTER: 1000,
        UserTier.PRO: 10000,
        UserTier.BUSINESS: 50000,
    }
    return limits.get(self.tier, 100)
```

---

## Security Considerations

### JWT Verification
- ✅ Verifies signature with Clerk's public JWKS
- ✅ Checks expiration
- ✅ Validates token format

### Token Storage
- ✅ Frontend: HTTP-only cookies (XSS protection)
- ✅ SameSite=Lax (CSRF protection)
- ✅ Secure flag in production (HTTPS only)

### Database Security
- ✅ Passwords never stored (Clerk handles auth)
- ✅ clerk_user_id is unique and indexed
- ✅ CASCADE delete on related records

---

## Common Operations

### Get Current User

```python
from app.core.clerk import get_current_user_from_clerk

async def my_endpoint(user: User = Depends(get_current_user_from_clerk)):
    # user.id - Database ID
    # user.clerk_user_id - Clerk ID
    # user.email - Email
    # user.role - Role enum
    # user.tier - Tier enum
    pass
```

### Optional Auth (Public + Auth)

```python
from app.core.clerk import get_current_user_from_clerk
from typing import Optional

async def optional_auth_endpoint(
    user: Optional[User] = Depends(get_current_user_from_clerk)
):
    if user:
        # Authenticated user
        return {"message": f"Hello {user.email}"}
    else:
        # Anonymous user
        return {"message": "Hello guest"}
```

### Require Specific Role

```python
async def admin_only(user: User = Depends(get_current_user_from_clerk)):
    if user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(403, "Admin access required")
    # Admin-only logic
```

---

## Migration History

### Migrations Applied

1. `0a3d2a7ef13b` - Initial users table
2. `ac4b2ff42914` - Add Google OAuth fields
3. `8d3e0fed9597` - Add captures table
4. `a27f6d4becae` - Rename metadata to meta
5. `f7a91c41953b` - Add index to captures.title
6. `1efe193e2389` - Ensure captures table exists (idempotent)
7. **`3c6812937dfb` - Add clerk_user_id to users** ← Current

### Rollback (if needed)

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 1efe193e2389
```

---

## Troubleshooting

### "Invalid token" Error

**Cause:** Token expired or invalid signature

**Solution:**
1. Check Clerk keys match in frontend and backend
2. Ensure user is signed in: `window.Clerk.session`
3. Try signing out and back in

### "User not found" but token is valid

**Cause:** Database out of sync

**Solution:**
1. Check database connection
2. Run migrations: `alembic upgrade head`
3. User will be created on next API call (JIT provisioning)

### Quota exceeded unexpectedly

**Cause:** `requests_this_month` not reset

**Solution:**
```python
# Reset quota manually
user.requests_this_month = 0
user.requests_reset_at = datetime.utcnow() + timedelta(days=30)
await db.commit()
```

---

## Production Deployment

### Checklist

- [ ] Add Clerk keys to Railway environment variables
- [ ] Add Clerk keys to Vercel environment variables
- [ ] Run migrations on production database
- [ ] Update CORS origins to include production frontend URL
- [ ] Set `CLERK_SECRET_KEY` (production key, not test key)
- [ ] Enable HTTPS-only cookies

### Environment Variables (Production)

**Railway:**
```env
CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
DATABASE_URL=postgresql://...
```

**Vercel:**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
NEXT_PUBLIC_API_URL=https://content-engine-production.up.railway.app
```

---

## Related Files

- Backend auth utility: `/backend/app/core/clerk.py`
- User model: `/backend/app/models/user.py`
- Auth endpoints: `/backend/app/api/endpoints/auth.py`
- Frontend API client: `/frontend/src/lib/api.ts`
- Frontend middleware: `/frontend/middleware.ts`
- Frontend layout: `/frontend/app/layout.tsx`
- Database schema: `/docs/database-schema.mmd`

---

## Summary

✅ **Clerk handles authentication** (login, signup, password reset)
✅ **Database stores user data** (quotas, captures, settings)
✅ **JIT provisioning** connects them automatically
✅ **No manual user management** needed
✅ **Ready for production** deployment

Users can sign up instantly and their database records are created on first API call!
