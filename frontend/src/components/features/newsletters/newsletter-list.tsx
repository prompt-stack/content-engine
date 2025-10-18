'use client';

import { Button } from '@/components/primitives/ui/button';
import { Card } from '@/components/primitives/ui/card';
import { Accordion, AccordionItem } from '@/components/composed/accordion';

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

interface NewsletterListProps {
  extractions: Extraction[];
  loading: boolean;
  onRefresh: () => void;
  expandedExtractionId?: string | null;
}

export function NewsletterList({
  extractions,
  loading,
  onRefresh,
  expandedExtractionId
}: NewsletterListProps) {

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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Past Extractions</h2>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
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
        <Accordion>
          {extractions.map((extraction) => (
            <AccordionItem
              key={extraction.id}
              defaultOpen={extraction.id === expandedExtractionId}
              title={
                <h3 className="font-semibold text-lg">
                  {extraction.newsletter_count} newsletters • {extraction.total_links} article links
                </h3>
              }
              subtitle={
                <>
                  {extraction.created_at && (
                    <p className="text-sm text-muted-foreground">
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
                </>
              }
            >
              <div className="p-4 space-y-3">
                {extraction.newsletters.map((newsletter, idx) => (
                  <AccordionItem
                    key={idx}
                    title={
                      <>
                        <h4 className="font-semibold">{newsletter.newsletter_subject}</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          From: {newsletter.newsletter_sender}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(newsletter.newsletter_date)}
                        </p>
                        <p className="text-sm font-medium mt-1">
                          {newsletter.link_count} article links
                        </p>
                      </>
                    }
                  >
                    <div className="p-3 space-y-2 bg-background">
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
                  </AccordionItem>
                ))}
              </div>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </div>
  );
}
