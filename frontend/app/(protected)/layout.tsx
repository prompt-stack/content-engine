import { AuthGate } from './_components/auth-gate';

/**
 * Protected Layout - Server Component
 *
 * All pages inside (protected) folder require authentication.
 * Auth checking is delegated to the AuthGate client component,
 * keeping this layout server-side so child pages can:
 * - Use server components
 * - Set metadata
 * - Fetch data on the server
 */
export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGate>{children}</AuthGate>;
}
