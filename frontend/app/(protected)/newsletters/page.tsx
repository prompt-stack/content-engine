'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { NewsletterExtractForm } from '@/components/features/newsletters/newsletter-extract-form';
import { NewsletterList } from '@/components/features/newsletters/newsletter-list';
import { api } from '@/lib/api';

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

export default function NewslettersPage() {
  // Page-level state - only data management
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [expandedExtractionId, setExpandedExtractionId] = useState<string | null>(null);

  // Load extractions on mount
  useEffect(() => {
    loadExtractions();
  }, []);

  async function loadExtractions() {
    try {
      setLoading(true);
      const data = await api.newsletters.extractions();
      setExtractions(data);
    } catch (error) {
      console.error('Error loading extractions:', error);
      setError(error instanceof Error ? error.message : 'Failed to load extractions');
    } finally {
      setLoading(false);
    }
  }

  async function handleExtractionSuccess(extractionId: string) {
    // Reload extractions to show the new one
    await loadExtractions();

    // Find the extraction to show success message
    const extraction = extractions.find(e => e.id === extractionId);
    if (extraction) {
      const newsletterCount = extraction.newsletter_count || 0;
      const linkCount = extraction.total_links || 0;
      setSuccess(`✅ Extracted ${newsletterCount} newsletters with ${linkCount} article links!`);
    } else {
      setSuccess('✅ Extraction completed successfully!');
    }

    // Auto-expand the new extraction
    setExpandedExtractionId(extractionId);

    // Clear success message after 5 seconds
    setTimeout(() => setSuccess(null), 5000);
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

      {/* Global Success Message */}
      {success && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-md text-sm">
          <p className="font-medium text-green-800 dark:text-green-200">{success}</p>
          <p className="text-green-700 dark:text-green-300 mt-1 text-xs">
            Check "Past Extractions" below to view your results.
          </p>
        </div>
      )}

      {/* Global Error Message */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-md text-sm">
          <p className="font-medium text-red-800 dark:text-red-200">Error</p>
          <p className="text-red-700 dark:text-red-300 mt-1">{error}</p>
        </div>
      )}

      {/* Extract Form Feature Component */}
      <NewsletterExtractForm onSuccess={handleExtractionSuccess} />

      {/* Extractions List Feature Component */}
      <NewsletterList
        extractions={extractions}
        loading={loading}
        onRefresh={loadExtractions}
        expandedExtractionId={expandedExtractionId}
      />
    </div>
  );
}
