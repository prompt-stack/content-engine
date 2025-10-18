# 🎯 Frontend Development Strategy – October 2025

Clerk authentication is fully integrated, and protected routes live under `app/(protected)/`. Here’s how to iterate quickly while keeping the auth layer intact.

---

## Recommended Workflow

1. **Build/modify UI inside `app/(protected)/`**
   - The shared layout (`app/(protected)/layout.tsx`) wraps pages with `AuthGate` so you never repeat authentication logic.
   - New pages inherit protection automatically; add the route prefix to `src/config/routes.ts` and re-run `npm run validate:routes`.

2. **Use Clerk test accounts during development**
   - Sign in once; Clerk remembers the session and the backend provisions the user. No need to stub auth locally.
   - For unauthenticated testing, temporarily move a page outside of `(protected)` or create a dedicated public route group.

3. **Leverage the API client** (`src/lib/api.ts`)
   - All fetch requests already attach the Clerk token; focus on feature logic rather than boilerplate.
   - If you enable `API_SECRET_KEY`, update the client to include `X-API-Key` in one place.

4. **Component-first iteration**
   - Build feature components in `src/components` as normal React/Next components.
   - Wire them into `(protected)` pages once ready. Auth gating is transparent to component logic.

---

## When to Disable Auth Locally (Rare)

If you need to demo the UI without sign-in (e.g., screenshot generation), you can:

- Comment out the relevant matcher in `middleware.ts` **temporarily**, or
- Create a feature flag that bypasses `AuthGate` when `process.env.NEXT_PUBLIC_CLERK_BYPASS === 'true'`.

Re-enable protections before committing changes.

---

## Testing Considerations

- Use Clerk’s test mode to create mock users.
- Integration tests can call the backend with a Clerk session token (see `/api/auth/me`).
- Validate route-protection drift via `npm run validate:routes` in CI to ensure new protected folders are reflected in the config.

---

## Summary

- Keep feature development inside `(protected)` to benefit from the shared auth layout.
- Rely on Clerk sessions during development; no need to stub auth anymore.
- Adjust API client and middleware in one place if auth requirements change.

This approach keeps the developer experience fast while preserving production parity.
