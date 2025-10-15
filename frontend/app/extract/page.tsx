'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ExtractForm } from '@/components/features/extract/extract-form';
import { ExtractedContentView } from '@/components/features/extract/extracted-content-view';
import { Button } from '@/components/primitives/ui/button';
import type { ExtractedContent } from '@/lib/types';

export default function ExtractPage() {
  const [extractedData, setExtractedData] = useState<ExtractedContent | null>(null);

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-4xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Content Extractor</h1>
          <p className="text-muted-foreground mt-2 text-sm sm:text-base">
            Extract content from social media and articles
          </p>
        </div>
        <Link href="/" className="self-start sm:self-center">
          <Button variant="ghost" size="sm">← Home</Button>
        </Link>
      </div>

      <ExtractForm onSuccess={setExtractedData} />

      {extractedData && (
        <ExtractedContentView
          data={extractedData}
          onProcess={() => {
            // TODO: Navigate to process page
            console.log('Process clicked', extractedData);
          }}
        />
      )}
    </div>
  );
}