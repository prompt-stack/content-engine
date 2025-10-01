'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/primitives/ui/card';
import { Button } from '@/components/primitives/ui/button';
import { ResultsModal } from '@/components/composed/results-modal';
import { PromptSelector } from '@/components/composed/prompt-selector';
import { LoadingState } from '@/components/composed/loading-state';
import { ErrorState } from '@/components/composed/error-state';
import { api } from '@/lib/api';
import type { ExtractedContent } from '@/lib/types';

interface ExtractedContentViewProps {
  data: ExtractedContent;
  onProcess?: () => void;
}

export function ExtractedContentView({ data, onProcess }: ExtractedContentViewProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('');
  const [modalDescription, setModalDescription] = useState('');
  const [modalResult, setModalResult] = useState('');

  if (!data) return null;

  const handleSummarize = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.llm.processContent({
        content: data.content || '',
        task: 'summarize',
        provider: 'deepseek',
      });
      setModalTitle('📝 Summary');
      setModalDescription('AI-generated summary of the content');
      setModalResult(result.result);
      setModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to summarize content');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPoints = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.llm.processContent({
        content: data.content || '',
        task: 'extract_key_points',
        provider: 'deepseek',
      });
      setModalTitle('🔑 Key Points');
      setModalDescription('Main takeaways from the content');
      setModalResult(result.result);
      setModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract key points');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(data.content || '');
      setModalTitle('✅ Copied!');
      setModalDescription('Content copied to clipboard');
      setModalResult('The content has been copied to your clipboard. You can now paste it anywhere!');
      setModalOpen(true);
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

  const handleCopyResult = async () => {
    try {
      await navigator.clipboard.writeText(modalResult);
      // Could add a toast notification here
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handlePromptProcess = async (promptText: string, promptName: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.llm.generate({
        prompt: promptText,
        provider: 'deepseek',
      });
      setModalTitle(`✨ ${promptName}`);
      setModalDescription('AI-generated result');
      setModalResult(result.result);
      setModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process prompt');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Processing with AI..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => setError(null)} />;
  }

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
            <h4 className="font-semibold text-sm mb-3">Quick Actions</h4>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleSummarize} variant="default" size="sm">
                📝 Summarize
              </Button>
              <Button onClick={handleKeyPoints} variant="default" size="sm">
                🔑 Key Points
              </Button>
              <Button onClick={handleCopyText} variant="outline" size="sm">
                📋 Copy Text
              </Button>
              <Button onClick={handleDownloadJSON} variant="outline" size="sm">
                ⬇️ Download JSON
              </Button>
            </div>
          </div>

          {onProcess && (
            <div className="pt-4 border-t">
              <Button onClick={onProcess} variant="secondary">
                Advanced Processing →
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Prompt Library Selector */}
      <div className="mt-6">
        <PromptSelector
          content={data.content || ''}
          onProcess={handlePromptProcess}
          loading={loading}
        />
      </div>

      <ResultsModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={modalTitle}
        description={modalDescription}
        result={modalResult}
        onCopy={handleCopyResult}
      />
    </>
  );
}