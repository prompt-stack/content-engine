'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/primitives/ui/card';
import { Button } from '@/components/primitives/ui/button';
import type { ExtractedContent } from '@/lib/types';

interface ExtractedContentViewProps {
  data: ExtractedContent;
  onProcess?: () => void;
}

export function ExtractedContentView({ data }: ExtractedContentViewProps) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!data) return null;

  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(data.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const handleDownloadJSON = () => {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.platform}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              <CardTitle>Extracted Content</CardTitle>
              <CardDescription>
                Platform: {data.platform || 'Unknown'} • Source: {data.source || 'N/A'}
              </CardDescription>
              {data.capture_id && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-sm text-green-600 font-medium">✓ Saved to Vault</span>
                  <Link href="/vault">
                    <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                      View in Vault →
                    </Button>
                  </Link>
                </div>
              )}
            </div>
            {/* Quick Actions - Top */}
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleCopyText} variant={copied ? "default" : "outline"} size="sm">
                {copied ? '✅ Copied!' : '📋 Copy'}
              </Button>
              <Button onClick={handleDownloadJSON} variant="outline" size="sm">
                ⬇️ JSON
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.title && (
            <div>
              <h3 className="font-semibold text-lg mb-2">{data.title}</h3>
            </div>
          )}

          {data.author && (
            <div className="text-sm text-muted-foreground">
              <strong>Author:</strong> {data.author}
            </div>
          )}

          {data.published_at && (
            <div className="text-sm text-muted-foreground">
              <strong>Published:</strong> {new Date(data.published_at).toLocaleDateString()}
            </div>
          )}

          {data.content && (
            <div className="prose prose-sm max-w-none">
              <p className="text-sm whitespace-pre-wrap break-words">{data.content}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}