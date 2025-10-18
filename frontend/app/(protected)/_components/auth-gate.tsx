'use client';

import { useAuth, useClerk } from '@clerk/nextjs';
import { useEffect } from 'react';

/**
 * Auth Gate - Client component that handles authentication checking
 *
 * Separated from layout to keep layout server-side, allowing child pages
 * to use server components and metadata if needed.
 *
 * Features:
 * - Waits for Clerk to load before rendering
 * - Redirects to sign-in if not authenticated
 * - Preserves the original URL for post-sign-in redirect
 * - Shows loading states during authentication
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  const { redirectToSignIn } = useClerk();

  useEffect(() => {
    // Redirect to sign-in if not authenticated (backup to middleware)
    // Preserve the current URL so user returns here after signing in
    if (isLoaded && !isSignedIn && typeof window !== 'undefined') {
      redirectToSignIn({
        redirectUrl: window.location.href
      });
    }
  }, [isLoaded, isSignedIn, redirectToSignIn]);

  // Show loading while Clerk initializes
  if (!isLoaded) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <p className="text-muted-foreground">Loading authentication...</p>
      </div>
    );
  }

  // Don't render protected content if not signed in (show loading while redirecting)
  if (!isSignedIn) {
    return (
      <div className="container mx-auto py-8 px-4 text-center">
        <p className="text-muted-foreground">Redirecting to sign in...</p>
      </div>
    );
  }

  // User is authenticated - render the page
  return <>{children}</>;
}
