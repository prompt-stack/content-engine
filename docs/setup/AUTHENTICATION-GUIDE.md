# Authentication Guide (Clerk + API Tokens)

## Overview

Content Engine now relies on **Clerk** for interactive user authentication and uses the backend to perform Just-In-Time (JIT) provisioning. Every protected API route requires:

1. A valid Clerk session token (`Authorization: Bearer <token>`).
2. Optionally an `X-API-Key` header if you configure `API_SECRET_KEY` for cost-controlled endpoints.

---

## Frontend Flow (Clerk)

1. The frontend (`app/layout.tsx`) wraps the application with `ClerkProvider`.
2. Protected routes live under `app/(protected)/`. The middleware (`middleware.ts`) and `AuthGate` component ensure only signed-in users render those pages.
3. `src/lib/api.ts` automatically reads `window.Clerk.session?.getToken()` and attaches the token to every request.

No additional work is required on the frontend once your Clerk keys are in place.

### Required Environment Variables

| Location            | Variable                             | Purpose                                      |
|--------------------|--------------------------------------|----------------------------------------------|
| `frontend/.env.local` | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`   | Frontend-side Clerk key                      |
| `backend/.env`        | `CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` | Backend token verification + JIT provisioning |

For production, duplicate these values in Vercel (frontend) and Railway (backend).

---

## Backend Flow (FastAPI)

`backend/app/core/clerk.py` implements the full verification pipeline:

1. Extracts the `Authorization` header, validates the Bearer token.
2. Fetches Clerk’s JWKS for signature verification.
3. Reads the `sub` (Clerk user ID) and email from the token.
4. Performs `SELECT` on `users.clerk_user_id`.
5. If no record exists, creates a new user with Clerk metadata (JIT provisioning).
6. Returns the SQLAlchemy `User` object to the endpoint.

Every protected route depends on `get_current_user_from_clerk`, for example:

```python
@router.post("/api/extract/auto")
async def extract_auto(
    request: ExtractRequest,
    current_user: User = Depends(get_current_user_from_clerk),
    _: bool = Depends(verify_api_key)  # optional API key check
):
    ...
```

---

## Optional API-Key Layer

Set `API_SECRET_KEY` in `backend/.env` (and Railway) to require an additional header:

```bash
API_SECRET_KEY=super-secret-string
```

When set, high-cost routes (extractors, LLM, search) enforce:

```bash
X-API-Key: super-secret-string
```

Leave `API_SECRET_KEY` empty in development to avoid the extra header.

---

## Owner / Elevated Access

Clerk provisions every new user as `role=USER`, `tier=FREE`. To grant unlimited access:

1. Sign in through Clerk with the account you want to promote (which creates the database row).
2. Run the owner promotion script:
   ```bash
   cd backend
   python scripts/create_owner.py
   ```
3. Enter the same email and choose `Upgrade existing user to OWNER? (yes)` when prompted.

This sets `role=OWNER`, `tier=OWNER`, `is_superuser=True`, and bypasses rate limits.

---

## Testing Authentication Locally

1. `frontend/.env.local` should already point to `http://localhost:9765`.
2. Start the backend with `./use-local.sh` to ensure the Clerk keys from `.env.local` are copied into `.env`.
3. Run `npm run dev` in the frontend and sign in using the Clerk test instance. The dashboard redirects back to the originally requested protected route.
4. Use browser devtools to grab the session token for manual API testing if needed.

Example manual request:

```bash
TOKEN="$(node -e 'process.stdout.write((await import("@clerk/nextjs/server"))).auth().sessionClaims.__raw || ""')"  # or copy from devtools
curl -X GET http://localhost:9765/api/auth/me   -H "Authorization: Bearer $TOKEN"
```

---

## Summary

- Clerk handles all interactive authentication and session management.
- The backend verifies Clerk JWTs and maps them to database users automatically.
- `API_SECRET_KEY` (optional) provides an additional shared-secret guardrail for costly endpoints.
- Promote specific accounts to OWNER through `scripts/create_owner.py` after they sign in once via Clerk.

With this configuration, the local development experience mirrors production while keeping sensitive endpoints protected.
