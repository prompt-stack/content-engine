'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { Input } from '@/components/primitives/ui/input';
import { Card } from '@/components/primitives/ui/card';
import { api } from '@/lib/api';
import type { Capture } from '@/lib/types';

export default function VaultPage() {
  const [captures, setCaptures] = useState<Capture[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [totalCount, setTotalCount] = useState(0);
  const [selectedCapture, setSelectedCapture] = useState<Capture | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch all captures on mount
  useEffect(() => {
    loadCaptures();
    loadCount();
  }, []);

  const loadCaptures = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.capture.list();
      setCaptures(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load captures');
      console.error('Error loading captures:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCount = async () => {
    try {
      const data = await api.capture.count();
      setTotalCount(data.total_captures);
    } catch (err) {
      console.error('Error loading count:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadCaptures();
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await api.capture.search({ q: searchQuery });
      setCaptures(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      console.error('Error searching:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this capture?')) {
      return;
    }

    try {
      await api.capture.delete(id);
      setCaptures(captures.filter(c => c.id !== id));
      setTotalCount(totalCount - 1);
      if (selectedCapture?.id === id) {
        setSelectedCapture(null);
      }
    } catch (err) {
      alert('Failed to delete capture');
      console.error('Error deleting:', err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const truncateContent = (content: string, maxLength = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Content Vault</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            Your captured content ({totalCount} total)
          </p>
        </div>
        <Link href="/" className="self-start sm:self-center">
          <Button variant="ghost" size="sm">← Home</Button>
        </Link>
      </div>

      {/* Search Bar */}
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="Search captures..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1"
        />
        <Button onClick={handleSearch}>Search</Button>
        {searchQuery && (
          <Button
            variant="outline"
            onClick={() => {
              setSearchQuery('');
              loadCaptures();
            }}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8 text-muted-foreground">
          Loading captures...
        </div>
      )}

      {/* Captures Grid */}
      {!loading && captures.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground text-lg">
            {searchQuery ? 'No captures found matching your search.' : 'No captures yet. Start capturing content!'}
          </p>
        </div>
      )}

      {!loading && captures.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {captures.map((capture) => (
            <Card
              key={capture.id}
              className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedCapture(capture)}
            >
              <div className="space-y-2">
                {/* Title */}
                <h3 className="font-semibold text-lg">
                  {capture.title || 'Untitled'}
                </h3>

                {/* Content Preview */}
                <p className="text-sm text-muted-foreground">
                  {truncateContent(capture.content)}
                </p>

                {/* Metadata */}
                <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                  <span>{formatDate(capture.created_at)}</span>
                  <div className="flex gap-2">
                    {capture.meta?.source && (
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {capture.meta.source}
                      </span>
                    )}
                    {capture.meta?.device && (
                      <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded">
                        {capture.meta.device}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCapture(capture);
                    }}
                  >
                    View Full
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(capture.id);
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Full Capture Modal */}
      {selectedCapture && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedCapture(null)}
        >
          <Card
            className="max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <h2 className="text-2xl font-bold">
                  {selectedCapture.title || 'Untitled'}
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedCapture(null)}
                >
                  ✕
                </Button>
              </div>

              <div className="text-sm text-muted-foreground flex gap-4">
                <span>{formatDate(selectedCapture.created_at)}</span>
                {selectedCapture.meta?.source && (
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {selectedCapture.meta.source}
                  </span>
                )}
                {selectedCapture.meta?.device && (
                  <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded">
                    {selectedCapture.meta.device}
                  </span>
                )}
              </div>

              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap font-sans">
                  {selectedCapture.content}
                </pre>
              </div>

              <div className="flex gap-2 pt-4 border-t">
                <Button
                  variant="destructive"
                  onClick={() => {
                    handleDelete(selectedCapture.id);
                  }}
                >
                  Delete
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedCapture(null)}
                >
                  Close
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
