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

  // Create prompt with content for AI platforms
  const createAIPrompt = () => {
    let prompt = "Please analyze this content:\n\n";

    if (data.title) {
      prompt += `Title: ${data.title}\n`;
    }
    if (data.author) {
      prompt += `Author: ${data.author}\n`;
    }
    if (data.source) {
      prompt += `Source: ${data.source}\n`;
    }

    prompt += `\n${data.content || ''}`;

    return prompt;
  };

  const handleOpenInChatGPT = () => {
    const prompt = createAIPrompt();
    // Copy to clipboard and open ChatGPT
    navigator.clipboard.writeText(prompt);
    window.open('https://chatgpt.com/', '_blank');
    // Show brief notification
    setError('✅ Content copied! Paste it in ChatGPT (Cmd/Ctrl+V)');
    setTimeout(() => setError(null), 4000);
  };

  const handleOpenInClaude = () => {
    const prompt = createAIPrompt();
    // Copy to clipboard and open Claude
    navigator.clipboard.writeText(prompt);
    window.open('https://claude.ai/new', '_blank');
    // Show brief notification
    setError('✅ Content copied! Paste it in Claude (Cmd/Ctrl+V)');
    setTimeout(() => setError(null), 4000);
  };

  const handleOpenInGemini = () => {
    const prompt = createAIPrompt();
    // Copy to clipboard and open Gemini
    navigator.clipboard.writeText(prompt);
    window.open('https://gemini.google.com/app', '_blank');
    // Show brief notification
    setError('✅ Content copied! Paste it in Gemini (Cmd/Ctrl+V)');
    setTimeout(() => setError(null), 4000);
  };

  return (
    <>
      {/* Notification for AI platform copy */}
      {error && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md text-sm">
          <p className="text-blue-800 dark:text-blue-200">{error}</p>
        </div>
      )}

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
              <Button onClick={handleOpenInChatGPT} variant="outline" size="sm" title="Copy content & open ChatGPT">
                🤖 ChatGPT
              </Button>
              <Button onClick={handleOpenInClaude} variant="outline" size="sm" title="Copy content & open Claude">
                💬 Claude
              </Button>
              <Button onClick={handleOpenInGemini} variant="outline" size="sm" title="Copy content & open Gemini">
                ✨ Gemini
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