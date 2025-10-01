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
    <div className="container mx-auto py-8 px-4 max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Content Extractor</h1>
          <p className="text-muted-foreground mt-2">
            Extract content from social media and articles
          </p>
        </div>
        <Link href="/">
          <Button variant="ghost">← Home</Button>
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