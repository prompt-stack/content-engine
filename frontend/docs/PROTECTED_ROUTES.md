# Protected Routes System

This document explains how protected routes work in the Content Engine frontend.

## Quick Start

### Adding a New Protected Route

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

## Architecture

### Single Source of Truth: `src/config/routes.ts`

This file defines all protected routes. It's used by:
- **Middleware** (`middleware.ts`) - Server-side route protection
- **Auth Gate** (`app/(protected)/_components/auth-gate.tsx`) - Client-side loading states
- **Utilities** - `isProtectedPath()` helper for client-side logic

### Route Protection Flow

```
1. User visits /vault
   ↓
2. Middleware checks if route is in PROTECTED_ROUTE_PATTERNS
   ↓
3. If protected: Clerk's auth.protect() runs
   ↓
4. If not authenticated: Redirect to sign-in
   ↓
5. If authenticated: Render (protected)/layout.tsx
   ↓
6. AuthGate checks isLoaded && isSignedIn
   ↓
7. If ready: Render the page
   ↓
8. Page loads normally (auth already verified)
```

### File Structure

```
app/
  (protected)/                     ← Route group (doesn't affect URLs)
    _components/
      auth-gate.tsx                ← Client-side auth checking
    layout.tsx                     ← Server component wrapper
    vault/page.tsx                 ← Your protected page
    newsletters/page.tsx
    extract/page.tsx

src/
  config/
    routes.ts                      ← 🎯 SINGLE SOURCE OF TRUTH

middleware.ts                      ← Imports from routes.ts
```

## Validation

### Automatic Validation

The build process automatically validates that:
1. All folders in `app/(protected)/` are listed in `routes.ts`
2. No extra routes in `routes.ts` that don't have folders

```bash
npm run build  # Runs validation before building
```

### Manual Validation

```bash
npm run validate:routes
```

**Example output (success):**
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

**Example output (drift detected):**
```
🔍 Validating protected routes...

📁 Folders in app/(protected)/:
   - admin
   - extract
   - newsletters
   - vault

⚙️  Configured in src/config/routes.ts:
   - vault
   - newsletters
   - extract

❌ ERROR: Routes missing from src/config/routes.ts:
   - /admin

💡 Add these to PROTECTED_ROUTE_PREFIXES in src/config/routes.ts
```

## Security

### Defense in Depth

1. **Middleware (Primary)** - Runs on the edge, blocks unauthorized access
2. **Auth Gate (Secondary)** - Client-side loading state and backup redirect
3. **API Layer (Backend)** - Each endpoint verifies JWT token independently

### Why Both Middleware and Auth Gate?

- **Middleware**: Prevents access entirely (302 redirect before page loads)
- **Auth Gate**: Handles loading states while Clerk initializes
- **Together**: Smooth UX + strong security

## Common Tasks

### Check if a Path is Protected (Client-Side)

```typescript
import { isProtectedPath } from '@/config/routes';

if (isProtectedPath('/vault/123')) {
  console.log('User must be authenticated');
}
```

### Get All Protected Routes

```typescript
import { PROTECTED_ROUTE_PREFIXES } from '@/config/routes';

console.log(PROTECTED_ROUTE_PREFIXES);
// ['/vault', '/newsletters', '/extract']
```

### Middleware Patterns

```typescript
import { PROTECTED_ROUTE_PATTERNS } from '@/config/routes';

console.log(PROTECTED_ROUTE_PATTERNS);
// ['/vault(.*)', '/newsletters(.*)', '/extract(.*)']
```

## Troubleshooting

### Build Fails: "Routes missing from config"

You added a folder to `app/(protected)/` but forgot to add it to `routes.ts`.

**Fix:**
```typescript
// src/config/routes.ts
export const PROTECTED_ROUTE_PREFIXES = [
  '/vault',
  '/newsletters',
  '/extract',
  '/your-new-route',  // ← Add this
] as const;
```

### Route Not Protected

Check that:
1. Folder is in `app/(protected)/`
2. Route is listed in `src/config/routes.ts`
3. You ran `npm run validate:routes`
4. Server was restarted after changes

### Redirect Loop

If you see infinite redirects:
1. Check that the route is spelled correctly
2. Verify Clerk env vars are set
3. Check browser console for Clerk errors

## Best Practices

✅ **DO:**
- Add routes to `routes.ts` immediately when creating folders
- Run `npm run validate:routes` before committing
- Use comments to explain what each route is for
- Keep route names simple and descriptive

❌ **DON'T:**
- Hard-code route patterns in middleware
- Skip validation before deploying
- Create folders outside `(protected)` that need auth
- Use nested route groups for protected routes

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/ci.yml
- name: Validate protected routes
  run: npm run validate:routes

- name: Build
  run: npm run build  # Already includes validation
```

## Related Files

- `src/config/routes.ts` - Single source of truth
- `middleware.ts` - Server-side route protection
- `app/(protected)/layout.tsx` - Server component wrapper
- `app/(protected)/_components/auth-gate.tsx` - Client auth logic
- `scripts/validate-protected-routes.mjs` - Validation script
- `package.json` - npm scripts

## Questions?

See the main README or check:
- [Clerk Next.js Docs](https://clerk.com/docs/nextjs)
- [Next.js Route Groups](https://nextjs.org/docs/app/building-your-application/routing/route-groups)
- `/docs/AUTH-INTEGRATION.md` - Backend auth integration
