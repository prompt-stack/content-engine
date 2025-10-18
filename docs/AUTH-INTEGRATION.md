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
async function getAuthToken(): Promise<string | null> {
  if (typeof window !== 'undefined' && (window as any).Clerk) {
    const session = await (window as any).Clerk.session?.getToken();
    return session || null;
  }
  return null;
}

async function apiRequest<T>(endpoint: string, options?: RequestInit) {
  // Get token from Clerk
  const token = await getAuthToken();

  // Build headers with conditional Authorization
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options?.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorMessage = await parseError(response);
    throw new Error(errorMessage);
  }

  return response.json();
}
```

**All API calls automatically include auth token!**

### Frontend: Protected Routes Architecture

**Protected routes use Next.js route groups for clean organization.**

#### File Structure

```
app/
  (protected)/                     ← Route group (doesn't affect URLs)
    _components/
      auth-gate.tsx                ← Client-side auth checking
    layout.tsx                     ← Server-side protected layout
    vault/page.tsx                 ← Protected pages
    newsletters/page.tsx
    extract/page.tsx

src/
  config/
    routes.ts                      ← 🎯 SINGLE SOURCE OF TRUTH

middleware.ts                      ← Server-side route protection
```

#### Centralized Route Configuration

**Location:** `/frontend/src/config/routes.ts`

```typescript
/**
 * Protected route prefixes - SINGLE SOURCE OF TRUTH
 *
 * Must match folder names in app/(protected)/
 * Validation runs automatically during build
 */
export const PROTECTED_ROUTE_PREFIXES = [
  '/vault',       // Content Vault
  '/newsletters', // Newsletter Extractions & Config
  '/extract',     // Content Extraction
] as const;

// Auto-generated patterns for middleware
export const PROTECTED_ROUTE_PATTERNS = PROTECTED_ROUTE_PREFIXES.map(
  (prefix) => `${prefix}(.*)`
);

// Helper function for client-side routing
export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_ROUTE_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix)
  );
}
```

#### Server-Side Protection (Middleware)

**Location:** `/frontend/middleware.ts`

```typescript
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { PROTECTED_ROUTE_PATTERNS } from "@/config/routes";

const isProtectedRoute = createRouteMatcher(PROTECTED_ROUTE_PATTERNS);

export default clerkMiddleware(async (auth, req) => {
  // Protect routes that require authentication
  if (isProtectedRoute(req)) {
    await auth.protect();  // 401 if not authenticated
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};
```

#### Client-Side Auth Gate

**Location:** `/frontend/app/(protected)/_components/auth-gate.tsx`

```typescript
'use client';

import { useAuth, useClerk } from '@clerk/nextjs';
import { useEffect } from 'react';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  const { redirectToSignIn } = useClerk();

  useEffect(() => {
    // Redirect to sign-in if not authenticated
    // Preserve the current URL so user returns here after signing in
    if (isLoaded && !isSignedIn && typeof window !== 'undefined') {
      redirectToSignIn({
        redirectUrl: window.location.href
      });
    }
  }, [isLoaded, isSignedIn, redirectToSignIn]);

  // Show loading while Clerk initializes
  if (!isLoaded) {
    return <div>Loading authentication...</div>;
  }

  // Don't render protected content if not signed in
  if (!isSignedIn) {
    return <div>Redirecting to sign in...</div>;
  }

  // User is authenticated - render the page
  return <>{children}</>;
}
```

**Key Features:**
- ✅ Waits for Clerk to load before rendering
- ✅ Redirects unauthenticated users to sign-in
- ✅ Preserves original URL for post-sign-in redirect
- ✅ Shows loading states during authentication

#### Protected Layout (Server Component)

**Location:** `/frontend/app/(protected)/layout.tsx`

```typescript
import { AuthGate } from './_components/auth-gate';

export default function ProtectedLayout({
  children
}: {
  children: React.ReactNode
}) {
  return <AuthGate>{children}</AuthGate>;
}
```

**Why separate layout and auth gate?**
- Layout stays server-side → Child pages can use server components
- Auth gate is client-side → Can use Clerk React hooks
- Best of both worlds!

#### Build-Time Route Validation

**Location:** `/frontend/scripts/validate-protected-routes.mjs`

Automatically validates that:
1. All folders in `app/(protected)/` are listed in `routes.ts`
2. No extra routes in `routes.ts` that don't have folders

```bash
# Run manually
npm run validate:routes

# Runs automatically during build
npm run build
```

**Example output:**
```
🔍 Validating protected routes...

📁 Folders in app/(protected)/:
   - extract
   - newsletters
   - vault

⚙️  Configured in src/config/routes.ts:
   - vault
   - newsletters
   - extract

✅ All protected routes are properly configured!
```

#### Adding a New Protected Route

1. **Create the folder:**
   ```bash
   mkdir app/(protected)/admin
   ```

2. **Add to config:**
   ```typescript
   // src/config/routes.ts
   export const PROTECTED_ROUTE_PREFIXES = [
     '/vault',
     '/newsletters',
     '/extract',
     '/admin',  // ← Add this
   ] as const;
   ```

3. **Validate:**
   ```bash
   npm run validate:routes
   ```

4. **Done!** The route is now protected and requires authentication.

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

- [x] Add Clerk keys to Railway environment variables
- [x] Add Clerk keys to Vercel environment variables
- [x] Run migrations on production database
- [x] Update CORS origins to include production frontend URL
- [x] Remove old API key authentication system
- [ ] Set `CLERK_SECRET_KEY` (production key, not test key) - Currently using test keys
- [ ] Enable HTTPS-only cookies

### Environment Variables (Production)

**Railway (Backend):**
```bash
# Add Clerk keys via CLI
railway variables --set "CLERK_PUBLISHABLE_KEY=pk_test_..."
railway variables --set "CLERK_SECRET_KEY=sk_test_..."

# Verify
railway variables | grep CLERK
```

**Vercel (Frontend):**
```bash
# Add Clerk keys for all environments
echo "pk_test_..." | vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
echo "pk_test_..." | vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY preview
echo "pk_test_..." | vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY development

echo "sk_test_..." | vercel env add CLERK_SECRET_KEY production
echo "sk_test_..." | vercel env add CLERK_SECRET_KEY preview
echo "sk_test_..." | vercel env add CLERK_SECRET_KEY development

# Verify
vercel env ls
```

### Deployment Process

1. **Push changes to GitHub:**
   ```bash
   git add .
   git commit -m "Implement Clerk authentication"
   git push origin main
   ```

2. **Railway auto-deploys backend:**
   - Watches `main` branch
   - Runs migrations automatically
   - Picks up new environment variables

3. **Vercel auto-deploys frontend:**
   - Watches `main` branch
   - Runs `npm run build` (includes route validation)
   - Uses environment variables from project settings

4. **Verify deployment:**
   ```bash
   # Check backend health
   curl https://content-engine-production.up.railway.app/health

   # Check frontend
   curl -I https://content-engine-frontend-green.vercel.app
   ```

### Migration Notes

**Old API Key System → Clerk**

We removed the old `verify_api_key` authentication dependency from all endpoints:

```python
# BEFORE (Old system)
from app.api.deps import verify_api_key

@router.post("/api/extract/auto")
async def extract_auto(
    user: User = Depends(get_current_user_from_clerk),
    _: bool = Depends(verify_api_key)  # ❌ Removed
):
    pass

# AFTER (Clerk only)
@router.post("/api/extract/auto")
async def extract_auto(
    user: User = Depends(get_current_user_from_clerk)  # ✅ Only this
):
    pass
```

**Affected endpoints:**
- `/api/extract/reddit`
- `/api/extract/tiktok`
- `/api/extract/youtube`
- `/api/extract/article`
- `/api/extract/auto`
- All `/api/newsletters/*` endpoints
- All `/api/capture/*` endpoints

### Current Production URLs

- **Backend:** https://content-engine-production.up.railway.app
- **Frontend:** https://content-engine-frontend-green.vercel.app
- **Direct Deployment:** https://content-engine-frontend-ghnbnbyhf-prompt-stacks-projects.vercel.app

---

## Related Files

### Backend
- Auth utility: `/backend/app/core/clerk.py` - JWT verification & JIT provisioning
- User model: `/backend/app/models/user.py` - User schema with clerk_user_id
- Auth endpoints: `/backend/app/api/endpoints/auth.py` - /auth/me endpoint
- Extractor endpoints: `/backend/app/api/endpoints/extractors.py` - Updated to use Clerk
- Newsletter endpoints: `/backend/app/api/endpoints/newsletters.py` - Updated to use Clerk
- Capture endpoints: `/backend/app/api/endpoints/capture.py` - Updated to use Clerk

### Frontend
- API client: `/frontend/src/lib/api.ts` - Automatic JWT token injection
- Middleware: `/frontend/middleware.ts` - Server-side route protection
- Route config: `/frontend/src/config/routes.ts` - Single source of truth
- Root layout: `/frontend/app/layout.tsx` - ClerkProvider & Header
- Protected layout: `/frontend/app/(protected)/layout.tsx` - Protected route wrapper
- Auth gate: `/frontend/app/(protected)/_components/auth-gate.tsx` - Client auth checking
- Header: `/frontend/src/components/layout/Header.tsx` - Sign in/out buttons

### Scripts & Validation
- Route validation: `/frontend/scripts/validate-protected-routes.mjs`
- Package scripts: `/frontend/package.json` - Build-time validation

### Documentation
- Database schema: `/docs/database-schema.mmd`
- Protected routes: `/frontend/docs/PROTECTED_ROUTES.md`
- This file: `/docs/AUTH-INTEGRATION.md`

---

## Summary

✅ **Clerk handles authentication** (login, signup, password reset)
✅ **Database stores user data** (quotas, captures, settings)
✅ **JIT provisioning** connects them automatically
✅ **No manual user management** needed
✅ **Ready for production** deployment

Users can sign up instantly and their database records are created on first API call!
