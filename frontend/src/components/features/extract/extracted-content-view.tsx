'use client';

import { useState } from 'react';
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
          <CardTitle>Extracted Content</CardTitle>
          <CardDescription>
            Platform: {data.platform || 'Unknown'} • Source: {data.source || 'N/A'}
          </CardDescription>
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
              <p className="text-sm whitespace-pre-wrap">{data.content}</p>
            </div>
          )}

          {/* Quick Actions */}
          <div className="pt-4 border-t">
            <h4 className="font-semibold text-sm mb-3">Actions</h4>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleCopyText} variant={copied ? "default" : "outline"} size="sm">
                {copied ? '✅ Copied!' : '📋 Copy Text'}
              </Button>
              <Button onClick={handleDownloadJSON} variant="outline" size="sm">
                ⬇️ Download JSON
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  );
}