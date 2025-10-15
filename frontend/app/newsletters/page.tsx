'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { Card } from '@/components/primitives/ui/card';

interface ResolvedLink {
  url: string;
  original_url?: string;
}

interface Newsletter {
  newsletter_subject: string;
  newsletter_sender: string;
  newsletter_date: string;
  links: ResolvedLink[];
  link_count: number;
}

interface Extraction {
  id: string;
  filename: string;
  newsletters: Newsletter[];
  newsletter_count: number;
  total_links: number;
  created_at?: string;
  days_back?: number;
  max_results?: number;
  senders?: string[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9765';

export default function NewslettersPage() {
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [daysBack, setDaysBack] = useState(7);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [expandedExtraction, setExpandedExtraction] = useState<string | null>(null);
  const [expandedNewsletter, setExpandedNewsletter] = useState<string | null>(null);

  useEffect(() => {
    loadExtractions();
  }, []);

  async function loadExtractions() {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/newsletters/extractions`);
      if (!response.ok) throw new Error('Failed to fetch extractions');
      const data = await response.json();
      setExtractions(data);
    } catch (error) {
      console.error('Error loading extractions:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleExtract() {
    try {
      setExtracting(true);
      setError(null);
      setSuccess(null);

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minute timeout

      const response = await fetch(`${API_URL}/api/newsletters/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days_back: daysBack, max_results: 30 }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Extraction failed: ${errorText}`);
      }

      const data = await response.json();

      // Validate response structure
      if (!data.newsletters || !data.id) {
        throw new Error('Invalid response format from server');
      }

      // Count results
      const newsletterCount = data.newsletters.length;
      const linkCount = data.newsletters.reduce((sum: number, n: any) => sum + (n.link_count || 0), 0);

      // Show success message
      setSuccess(`✅ Extracted ${newsletterCount} newsletters with ${linkCount} article links!`);

      // Reload extractions list to show new extraction
      await loadExtractions();

      // Auto-expand the new extraction
      setExpandedExtraction(data.id);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000);
    } catch (error) {
      console.error('Error extracting:', error);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          setError('Request timed out. The server may be processing your request. Please refresh the page to check if results are available.');
        } else {
          setError(error.message);
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setExtracting(false);
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  function formatDate(dateStr: string) {
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  function formatExtractionDate(dateStr: string) {
    try {
      return new Date(dateStr).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return dateStr;
    }
  }

  function toggleExtraction(id: string) {
    setExpandedExtraction(expandedExtraction === id ? null : id);
    setExpandedNewsletter(null); // Collapse newsletters when toggling extraction
  }

  function toggleNewsletter(extractionId: string, newsletterIndex: number) {
    const key = `${extractionId}-${newsletterIndex}`;
    setExpandedNewsletter(expandedNewsletter === key ? null : key);
  }

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Newsletter Extractions</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            Extract article links from your newsletters
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/newsletters/config">
            <Button variant="outline" size="sm">⚙️ Config</Button>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm">← Home</Button>
          </Link>
        </div>
      </div>

      {/* Extract Form */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Run Extraction</h2>
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium">Extract newsletters from the last</label>
            <select
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              className="w-full px-3 py-2 border rounded-md bg-background"
              disabled={extracting}
            >
              <option value={1}>1 day</option>
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
          <Button
            onClick={handleExtract}
            disabled={extracting}
            className="w-full sm:w-auto"
            size="lg"
          >
            {extracting ? 'Extracting...' : 'Extract'}
          </Button>
        </div>
        {extracting && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md text-sm">
            <p className="font-medium">Running pipeline (Steps 1-4)...</p>
            <p className="text-muted-foreground mt-1">
              Extracting newsletters → Parsing links → Resolving redirects → Filtering content
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              ⏱️ This may take 2-10 minutes depending on newsletter count and date range...
            </p>
          </div>
        )}
        {success && !extracting && (
          <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-md text-sm">
            <p className="font-medium text-green-800 dark:text-green-200">{success}</p>
            <p className="text-green-700 dark:text-green-300 mt-1 text-xs">
              Check "Past Extractions" below to view your results.
            </p>
          </div>
        )}
        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-md text-sm">
            <p className="font-medium text-red-800 dark:text-red-200">Error</p>
            <p className="text-red-700 dark:text-red-300 mt-1">{error}</p>
            <Button
              onClick={handleExtract}
              variant="outline"
              size="sm"
              className="mt-2"
            >
              Try Again
            </Button>
          </div>
        )}
      </Card>

      {/* Extractions List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">Past Extractions</h2>
          <Button variant="ghost" size="sm" onClick={loadExtractions} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
        </div>

        {loading && extractions.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground">Loading extractions...</p>
          </Card>
        ) : extractions.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground">No extractions yet. Click "Extract" above to get started!</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {extractions.map((extraction) => (
              <Card key={extraction.id} className="overflow-hidden">
                {/* Extraction Header */}
                <button
                  onClick={() => toggleExtraction(extraction.id)}
                  className="w-full p-4 text-left hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">
                        {extraction.newsletter_count} newsletters • {extraction.total_links} article links
                      </h3>
                      {extraction.created_at && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {formatExtractionDate(extraction.created_at)}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        ID: {extraction.id}
                        {extraction.days_back && <span className="mx-1">•</span>}
                        {extraction.days_back && <span>{extraction.days_back} day{extraction.days_back !== 1 ? 's' : ''} back</span>}
                        {extraction.max_results && <span className="mx-1">•</span>}
                        {extraction.max_results && <span>max {extraction.max_results}</span>}
                      </p>
                    </div>
                    <div className="text-2xl ml-4">
                      {expandedExtraction === extraction.id ? '−' : '+'}
                    </div>
                  </div>
                </button>

                {/* Expanded: Show Newsletters */}
                {expandedExtraction === extraction.id && (
                  <div className="border-t bg-accent/10">
                    <div className="p-4 space-y-3">
                      {extraction.newsletters.map((newsletter, idx) => (
                        <Card key={idx} className="overflow-hidden">
                          {/* Newsletter Header */}
                          <button
                            onClick={() => toggleNewsletter(extraction.id, idx)}
                            className="w-full p-3 text-left hover:bg-accent/50 transition-colors"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold">{newsletter.newsletter_subject}</h4>
                                <p className="text-sm text-muted-foreground">
                                  From: {newsletter.newsletter_sender}
                                </p>
                                <p className="text-sm text-muted-foreground">
                                  {formatDate(newsletter.newsletter_date)}
                                </p>
                                <p className="text-sm font-medium mt-1">
                                  {newsletter.link_count} article links
                                </p>
                              </div>
                              <div className="text-xl ml-4">
                                {expandedNewsletter === `${extraction.id}-${idx}` ? '−' : '+'}
                              </div>
                            </div>
                          </button>

                          {/* Expanded: Show Article Links */}
                          {expandedNewsletter === `${extraction.id}-${idx}` && (
                            <div className="border-t bg-background">
                              <div className="p-3 space-y-2">
                                {newsletter.links.map((link, linkIdx) => (
                                  <div
                                    key={linkIdx}
                                    className="p-3 bg-accent/30 rounded-lg hover:bg-accent/50 transition-colors group"
                                  >
                                    <div className="flex items-start gap-3">
                                      <div className="flex-1 min-w-0">
                                        <a
                                          href={link.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:underline block break-all text-sm"
                                        >
                                          {link.url}
                                        </a>
                                      </div>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          copyToClipboard(link.url);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                      >
                                        Copy
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
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
