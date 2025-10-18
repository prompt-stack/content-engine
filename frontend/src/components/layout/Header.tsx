'use client';

import Link from 'next/link';
import { SignInButton, SignUpButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs';
import { Button } from '@/components/primitives/ui/button';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        {/* Logo / Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold text-lg">Content Engine</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-4 text-sm">
            <Link
              href="/extract"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Extract
            </Link>
            <Link
              href="/vault"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Vault
            </Link>
            <Link
              href="/newsletters"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Newsletters
            </Link>
          </nav>
        </div>

        {/* Auth Buttons */}
        <div className="flex items-center gap-2">
          <SignedOut>
            <SignInButton mode="modal">
              <Button variant="ghost" size="sm">Sign In</Button>
            </SignInButton>
            <SignUpButton mode="modal">
              <Button size="sm">Sign Up</Button>
            </SignUpButton>
          </SignedOut>

          <SignedIn>
            <UserButton
              afterSignOutUrl="/"
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8"
                }
              }}
            />
          </SignedIn>
        </div>
      </div>
    </header>
  );
}
