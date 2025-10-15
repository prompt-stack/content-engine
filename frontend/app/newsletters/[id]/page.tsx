'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { Card } from '@/components/primitives/ui/card';

interface ArticleInfo {
  title: string;
  url: string;
  file: string;
}

interface NewsletterDetail {
  subject: string;
  sender: string;
  date: string;
  total_links: number;
  successful: number;
  failed: number;
  articles: ArticleInfo[];
}

interface DigestDetail {
  id: string;
  timestamp: string;
  newsletter_count: number;
  total_articles: number;
  successful: number;
  failed: number;
  newsletters: NewsletterDetail[];
}

export default function DigestPage() {
  const params = useParams();
  const digestId = params.id as string;

  const [digest, setDigest] = useState<DigestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNewsletter, setExpandedNewsletter] = useState<number | null>(null);

  useEffect(() => {
    loadDigest();
  }, [digestId]);

  async function loadDigest() {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`http://localhost:9765/api/newsletters/digests/${digestId}`);

      if (!response.ok) {
        if (response.status === 404) {
          setError('Digest not found');
        } else {
          setError('Failed to load digest');
        }
        return;
      }

      const data = await response.json();
      setDigest(data);
    } catch (err) {
      console.error('Error loading digest:', err);
      setError('Failed to load digest');
    } finally {
      setLoading(false);
    }
  }

  function formatDate(timestamp: string) {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">Loading digest...</p>
        </Card>
      </div>
    );
  }

  if (error || !digest) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <Card className="p-8 text-center">
          <p className="text-red-500 mb-4">{error || 'Digest not found'}</p>
          <Link href="/newsletters">
            <Button>Back to Newsletters</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Newsletter Digest</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            {formatDate(digest.timestamp)}
          </p>
        </div>
        <Link href="/newsletters">
          <Button variant="ghost" size="sm">← Back</Button>
        </Link>
      </div>

      {/* Summary Stats */}
      <Card className="p-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Newsletters</p>
            <p className="text-2xl font-bold">{digest.newsletter_count}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Links</p>
            <p className="text-2xl font-bold">{digest.total_articles}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Extracted</p>
            <p className="text-2xl font-bold text-green-600">{digest.successful}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Failed</p>
            <p className="text-2xl font-bold text-red-600">{digest.failed}</p>
          </div>
        </div>
      </Card>

      {/* Newsletters */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Newsletters</h2>

        {digest.newsletters.map((newsletter, idx) => (
          <Card key={idx} className="overflow-hidden">
            {/* Newsletter Header */}
            <button
              onClick={() => setExpandedNewsletter(expandedNewsletter === idx ? null : idx)}
              className="w-full p-6 text-left hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold truncate">{newsletter.subject}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    From: {newsletter.sender}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {newsletter.date}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm">
                    <span className="text-green-600">{newsletter.successful} extracted</span>
                    {newsletter.failed > 0 && (
                      <span className="text-red-600">{newsletter.failed} failed</span>
                    )}
                  </div>
                </div>
                <div className="text-2xl">
                  {expandedNewsletter === idx ? '−' : '+'}
                </div>
              </div>
            </button>

            {/* Articles List */}
            {expandedNewsletter === idx && newsletter.articles.length > 0 && (
              <div className="border-t">
                <div className="p-6 space-y-4">
                  {newsletter.articles.map((article, articleIdx) => (
                    <div
                      key={articleIdx}
                      className="pb-4 border-b last:border-b-0 last:pb-0"
                    >
                      <h4 className="font-medium mb-2">{article.title}</h4>
                      <div className="flex flex-col sm:flex-row gap-2 text-sm">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline truncate"
                        >
                          {article.url}
                        </a>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="sm:ml-auto"
                          onClick={async () => {
                            try {
                              const response = await fetch(
                                `http://localhost:9765/api/newsletters/digests/${digestId}/article/${article.file}`
                              );
                              const data = await response.json();

                              // Open in new window with the markdown content
                              const win = window.open('', '_blank');
                              if (win) {
                                win.document.write(`
                                  <html>
                                    <head>
                                      <title>${article.title}</title>
                                      <style>
                                        body {
                                          font-family: system-ui, -apple-system, sans-serif;
                                          max-width: 800px;
                                          margin: 40px auto;
                                          padding: 0 20px;
                                          line-height: 1.6;
                                        }
                                        pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
                                        code { background: #f5f5f5; padding: 2px 4px; border-radius: 2px; }
                                        h1, h2, h3 { margin-top: 1.5em; }
                                      </style>
                                    </head>
                                    <body>
                                      <pre>${data.content}</pre>
                                    </body>
                                  </html>
                                `);
                              }
                            } catch (err) {
                              console.error('Error loading article:', err);
                            }
                          }}
                        >
                          View Content
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
