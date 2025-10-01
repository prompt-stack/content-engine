'use client';

import { useState } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Input } from '@/components/primitives/ui/input';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/primitives/ui/card';
import { LoadingState } from '@/components/composed/loading-state';
import { ErrorState } from '@/components/composed/error-state';
import { api } from '@/lib/api';
import type { ExtractedContent } from '@/lib/types';

interface ExtractFormProps {
  onSuccess: (data: ExtractedContent) => void;
}

export function ExtractForm({ onSuccess }: ExtractFormProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);

    try {
      // Use auto-detect endpoint
      const result = await api.extract.auto(url);
      onSuccess(result);
      setUrl(''); // Clear input on success
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract content');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Extracting content..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => setError(null)} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extract Content</CardTitle>
        <CardDescription>
          Paste a URL from TikTok, YouTube, Reddit, or any article
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="url"
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <Button type="submit" disabled={!url} className="w-full">
            Extract
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}