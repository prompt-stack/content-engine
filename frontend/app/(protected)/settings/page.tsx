'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { api } from '@/lib/api';
import type { GoogleOAuthStatus } from '@/lib/types';

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const [googleStatus, setGoogleStatus] = useState<GoogleOAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState(false);

  // Check for OAuth callback messages
  useEffect(() => {
    const connected = searchParams.get('google_connected');
    const errorMsg = searchParams.get('google_error');
    const message = searchParams.get('message');

    if (connected === 'true') {
      setSuccess('✅ Gmail connected successfully! You can now extract newsletters.');
      // Clear URL params after showing message
      window.history.replaceState({}, '', '/settings');
    } else if (errorMsg === 'true') {
      setError(message || 'Failed to connect Gmail. Please try again.');
      // Clear URL params after showing message
      window.history.replaceState({}, '', '/settings');
    }
  }, [searchParams]);

  // Load Gmail connection status
  useEffect(() => {
    loadGoogleStatus();
  }, []);

  async function loadGoogleStatus() {
    try {
      setLoading(true);
      const status = await api.auth.google.status();
      setGoogleStatus(status);
    } catch (err) {
      console.error('Error loading Google status:', err);
      setError(err instanceof Error ? err.message : 'Failed to load connection status');
    } finally {
      setLoading(false);
    }
  }

  async function handleConnectGmail() {
    try {
      setError(null);
      const { authorization_url } = await api.auth.google.start();
      // Redirect to Google OAuth
      window.location.href = authorization_url;
    } catch (err) {
      console.error('Error starting OAuth:', err);
      setError(err instanceof Error ? err.message : 'Failed to start Gmail connection');
    }
  }

  async function handleDisconnectGmail() {
    if (!confirm('Are you sure you want to disconnect your Gmail account? You will need to reconnect to extract newsletters.')) {
      return;
    }

    try {
      setDisconnecting(true);
      setError(null);
      await api.auth.google.disconnect();
      setSuccess('Gmail disconnected successfully');
      // Reload status
      await loadGoogleStatus();
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      console.error('Error disconnecting Gmail:', err);
      setError(err instanceof Error ? err.message : 'Failed to disconnect Gmail');
    } finally {
      setDisconnecting(false);
    }
  }

  const isConnected = googleStatus?.connected && !googleStatus?.is_expired;
  const expiresAt = googleStatus?.expires_at ? new Date(googleStatus.expires_at) : null;
  const expiryWarning = expiresAt && expiresAt.getTime() - Date.now() < 7 * 24 * 60 * 60 * 1000; // 7 days

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            Manage your account and integrations
          </p>
        </div>
        <Link href="/">
          <Button variant="ghost" size="sm">← Home</Button>
        </Link>
      </div>

      {/* Success Message */}
      {success && (
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <p className="font-medium text-green-800 dark:text-green-200">{success}</p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <p className="font-medium text-red-800 dark:text-red-200">Error</p>
          <p className="text-red-700 dark:text-red-300 mt-1 text-sm">{error}</p>
        </div>
      )}

      {/* Gmail Connection Card */}
      <div className="border rounded-lg p-6 space-y-4 bg-card">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold">Gmail Connection</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Connect your Gmail to extract newsletter article links
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <span className="inline-flex items-center gap-2 text-sm font-medium text-green-600 dark:text-green-400">
                <span className="h-2 w-2 rounded-full bg-green-600 dark:bg-green-400" />
                Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-2 text-sm font-medium text-gray-500">
                <span className="h-2 w-2 rounded-full bg-gray-400" />
                Not Connected
              </span>
            )}
          </div>
        </div>

        {loading ? (
          <div className="py-8 text-center text-muted-foreground">
            Loading connection status...
          </div>
        ) : isConnected ? (
          <div className="space-y-4">
            <div className="bg-muted/50 rounded-md p-4 space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Connected Email</p>
                  <p className="text-base font-mono">{googleStatus?.email || 'Unknown'}</p>
                </div>
              </div>

              {expiresAt && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Token Expires</p>
                  <p className="text-base">
                    {expiresAt.toLocaleDateString()} at {expiresAt.toLocaleTimeString()}
                  </p>
                  {expiryWarning && (
                    <p className="text-sm text-amber-600 dark:text-amber-400 mt-1">
                      ⚠️ Token expires soon. You may need to reconnect.
                    </p>
                  )}
                </div>
              )}
            </div>

            <Button
              variant="destructive"
              onClick={handleDisconnectGmail}
              disabled={disconnecting}
            >
              {disconnecting ? 'Disconnecting...' : 'Disconnect Gmail'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-md p-4 border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> You can connect any Gmail account—it doesn't have to match your login email.
                For example, you can sign in with your personal email but connect your work Gmail to extract work newsletters.
              </p>
            </div>

            <Button onClick={handleConnectGmail} size="lg" className="w-full sm:w-auto">
              Connect Gmail Account
            </Button>

            <div className="text-sm text-muted-foreground space-y-1">
              <p>When you connect your Gmail:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>You'll be redirected to Google to authorize access</li>
                <li>We only request read-only access to your Gmail</li>
                <li>We only use it to extract article links from newsletters</li>
                <li>You can disconnect at any time</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Additional Settings Sections (Future) */}
      <div className="border rounded-lg p-6 space-y-4 bg-card opacity-50">
        <h2 className="text-xl font-semibold">Account Settings</h2>
        <p className="text-sm text-muted-foreground">
          Coming soon: Profile settings, notification preferences, and more.
        </p>
      </div>
    </div>
  );
}
