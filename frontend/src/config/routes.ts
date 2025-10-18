/**
 * Route Configuration - SINGLE SOURCE OF TRUTH
 *
 * ⚠️ IMPORTANT: When you add a new folder to app/(protected)/, you MUST add it here!
 *
 * This file defines all protected routes that require authentication.
 * It's used by:
 * - middleware.ts (server-side route protection)
 * - Client-side utilities (isProtectedPath helper)
 *
 * Validation: Run `npm run validate:routes` to check for drift
 * The build process automatically validates this matches app/(protected)/ structure
 */

/**
 * Protected route prefixes
 *
 * Any route starting with these paths requires authentication.
 * Must match folder names in app/(protected)/
 *
 * @example
 * // To add a new protected route:
 * // 1. Create folder: app/(protected)/admin/
 * // 2. Add here: '/admin'
 * // 3. Run: npm run validate:routes
 */
export const PROTECTED_ROUTE_PREFIXES = [
  '/vault',       // Content Vault - saved captures
  '/newsletters', // Newsletter Extractions & Config
  '/extract',     // Content Extraction
  '/settings',    // User Settings & Account Management
] as const;

/**
 * Protected route patterns for middleware
 *
 * Auto-generated from PROTECTED_ROUTE_PREFIXES.
 * Includes wildcards to match all subroutes.
 *
 * @example ['/vault(.*)', '/newsletters(.*)', '/extract(.*)']
 */
export const PROTECTED_ROUTE_PATTERNS = PROTECTED_ROUTE_PREFIXES.map(
  (prefix) => `${prefix}(.*)`
);

/**
 * Check if a pathname is a protected route
 *
 * Useful for client-side routing decisions
 *
 * @example
 * if (isProtectedPath('/vault/123')) {
 *   // User must be authenticated
 * }
 */
export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_ROUTE_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix)
  );
}
