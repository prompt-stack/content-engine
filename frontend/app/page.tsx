'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/primitives/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/primitives/ui/card';
import type { HealthResponse } from '@/lib/types';

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const result = await api.health();
        setHealth(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center space-y-6 max-w-2xl">
        <h1 className="text-4xl font-bold">Content Engine</h1>
        <p className="text-xl text-muted-foreground">
          Extract clean, LLM-ready content from social media and articles
        </p>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Supported Platforms</CardTitle>
            <CardDescription>Extract from any of these sources</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-left">
              <div className="space-y-2">
                <p className="font-semibold">Social Media</p>
                <ul className="text-sm space-y-1">
                  <li>✅ YouTube (with transcripts)</li>
                  <li>✅ TikTok (with captions)</li>
                  <li>✅ Reddit (posts + comments)</li>
                </ul>
              </div>
              <div className="space-y-2">
                <p className="font-semibold">Web Content</p>
                <ul className="text-sm space-y-1">
                  <li>✅ Articles & Blogs</li>
                  <li>✅ News Sites</li>
                  <li>✅ Any Web Page</li>
                </ul>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t">
              {loading && <p className="text-sm">Checking connection...</p>}
              {error && <p className="text-sm text-destructive">❌ API: {error}</p>}
              {health && (
                <p className="text-sm text-green-600 font-semibold">✅ API Connected ({health.environment})</p>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-4 justify-center mt-6">
          <Link href="/extract">
            <Button size="lg">Start Extracting →</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}