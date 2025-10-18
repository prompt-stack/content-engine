import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { PROTECTED_ROUTE_PATTERNS } from "@/config/routes";

/**
 * Protected Routes Configuration
 *
 * Routes are defined in src/config/routes.ts - single source of truth.
 * This matches the folder structure: app/(protected)/
 *
 * To add a new protected route:
 * 1. Create it under app/(protected)/
 * 2. Add the route prefix to PROTECTED_ROUTE_PREFIXES in src/config/routes.ts
 * 3. The pattern will be automatically generated for middleware
 */
const isProtectedRoute = createRouteMatcher(PROTECTED_ROUTE_PATTERNS);

export default clerkMiddleware(async (auth, req) => {
  // Protect routes that require authentication
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
