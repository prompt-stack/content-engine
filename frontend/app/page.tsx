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
          AI-powered content extraction and processing
        </p>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Backend Status</CardTitle>
            <CardDescription>Connection to API server</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && <p>Checking connection...</p>}
            {error && <p className="text-destructive">❌ {error}</p>}
            {health && (
              <div className="space-y-2 text-left">
                <p className="text-green-600 font-semibold">✅ Connected</p>
                <p className="text-sm"><strong>Status:</strong> {health.status}</p>
                <p className="text-sm"><strong>Environment:</strong> {health.environment}</p>
                <div className="text-sm">
                  <strong>Features:</strong>
                  <ul className="ml-4 mt-1 space-y-1">
                    <li>OpenAI: {health.features?.openai ? '✅' : '❌'}</li>
                    <li>Anthropic: {health.features?.anthropic ? '✅' : '❌'}</li>
                    <li>Gemini: {health.features?.gemini ? '✅' : '❌'}</li>
                    <li>DeepSeek: {health.features?.deepseek ? '✅' : '❌'}</li>
                    <li>Default LLM: {health.features?.default_llm}</li>
                  </ul>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-4 justify-center mt-6">
          <Link href="/extract">
            <Button>Extract Content</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}