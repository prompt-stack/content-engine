'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Card } from '@/components/primitives/ui/card';
import { ProgressIndicator } from '@/components/composed/progress-indicator';
import { api } from '@/lib/api';

interface NewsletterExtractFormProps {
  onSuccess: (extractionId: string) => void;
  disabled?: boolean;
}

export function NewsletterExtractForm({ onSuccess, disabled = false }: NewsletterExtractFormProps) {
  // Form controls
  const [timeUnit, setTimeUnit] = useState<'hours' | 'days'>('days');
  const [timeValue, setTimeValue] = useState(7);
  const [maxResults, setMaxResults] = useState(30);
  const [selectedSenders, setSelectedSenders] = useState<string[]>([]);

  // Extraction state
  const [extracting, setExtracting] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState<number>(0);
  const [extractionMessage, setExtractionMessage] = useState<string>('');

  // Refs for polling management
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isCompletingRef = useRef<boolean>(false);
  const isPollingRef = useRef<boolean>(false); // Prevent overlapping polls

  // Local error state
  const [error, setError] = useState<string | null>(null);

  // Available senders from config
  const availableSenders = [
    { email: 'news@alphasignal.ai', name: 'AlphaSignal' },
    { email: 'news@daily.therundown.ai', name: 'The Rundown AI' },
    { email: 'crew@technews.therundown.ai', name: 'The Rundown Tech' }
  ];

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  async function pollExtractionStatus(extractionId: string) {
    // Prevent overlapping polls
    if (isPollingRef.current) {
      return;
    }

    isPollingRef.current = true;

    try {
      const status = await api.newsletters.extractionStatus(extractionId);

      // Update progress
      setExtractionProgress(status.progress || 0);
      setExtractionMessage(status.progress_message || '');

      // Check if complete
      if (status.status === 'completed') {
        // Stop polling FIRST to prevent more requests
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }

        // Prevent multiple completion handlers
        if (isCompletingRef.current) {
          return;
        }

        isCompletingRef.current = true;

        // Reset state
        setExtracting(false);
        setExtractionProgress(0);
        setExtractionMessage('');
        isCompletingRef.current = false;

        // Notify parent
        onSuccess(extractionId);

      } else if (status.status === 'failed') {
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }

        setError(status.error_message || 'Extraction failed');
        setExtracting(false);
        setExtractionProgress(0);
        setExtractionMessage('');
      }
      // Otherwise keep polling (pending or processing)

    } catch (error) {
      // Keep polling even if one poll fails
    } finally {
      isPollingRef.current = false;
    }
  }

  async function handleExtract() {
    try {
      setExtracting(true);
      setError(null);
      setExtractionProgress(0);
      setExtractionMessage('Starting extraction...');
      isCompletingRef.current = false;

      // Build request body
      const requestBody: any = {
        max_results: maxResults
      };

      if (timeUnit === 'hours') {
        requestBody.hours_back = timeValue;
      } else {
        requestBody.days_back = timeValue;
      }

      if (selectedSenders.length > 0) {
        requestBody.senders = selectedSenders;
      }

      // Start extraction
      const data = await api.newsletters.extract(requestBody);

      if (!data.extraction_id) {
        throw new Error('Invalid response from server');
      }

      // Start polling every 2 seconds
      pollingIntervalRef.current = setInterval(() => {
        pollExtractionStatus(data.extraction_id);
      }, 2000);

      // Do initial poll immediately
      pollExtractionStatus(data.extraction_id);

    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      setExtracting(false);
      setExtractionProgress(0);
      setExtractionMessage('');
    }
  }

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">Run Extraction</h2>
      <div className="space-y-4">
        {/* Time Range Control */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Time Unit Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Time Unit</label>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setTimeUnit('hours');
                  setTimeValue(1);
                }}
                disabled={extracting || disabled}
                className={`flex-1 px-3 py-2 rounded-md border text-sm font-medium transition-colors ${
                  timeUnit === 'hours'
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background hover:bg-accent'
                }`}
              >
                Hours
              </button>
              <button
                onClick={() => {
                  setTimeUnit('days');
                  setTimeValue(1);
                }}
                disabled={extracting || disabled}
                className={`flex-1 px-3 py-2 rounded-md border text-sm font-medium transition-colors ${
                  timeUnit === 'days'
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background hover:bg-accent'
                }`}
              >
                Days
              </button>
            </div>
          </div>

          {/* Time Value Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Look back {timeUnit === 'hours' ? 'hours' : 'days'}
            </label>
            <select
              value={timeValue}
              onChange={(e) => setTimeValue(Number(e.target.value))}
              className="w-full px-3 py-2 border rounded-md bg-background"
              disabled={extracting || disabled}
            >
              {timeUnit === 'hours' ? (
                <>
                  <option value={1}>1 hour</option>
                  <option value={3}>3 hours</option>
                  <option value={6}>6 hours</option>
                  <option value={12}>12 hours</option>
                  <option value={24}>24 hours</option>
                </>
              ) : (
                <>
                  <option value={1}>1 day</option>
                  <option value={3}>3 days</option>
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                </>
              )}
            </select>
          </div>

          {/* Max Results */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Max newsletters</label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full px-3 py-2 border rounded-md bg-background"
              disabled={extracting || disabled}
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={30}>30</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>

        {/* Sender Selection */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Filter by senders (optional)</label>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedSenders(availableSenders.map(s => s.email))}
                disabled={extracting}
                className="text-xs px-2 py-1 rounded-md hover:bg-accent text-muted-foreground"
              >
                Select All
              </button>
              <button
                onClick={() => setSelectedSenders([])}
                disabled={extracting}
                className="text-xs px-2 py-1 rounded-md hover:bg-accent text-muted-foreground"
              >
                Clear All
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {availableSenders.map((sender) => (
              <label
                key={sender.email}
                className="flex items-center gap-2 p-2 rounded-md border hover:bg-accent cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedSenders.includes(sender.email)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedSenders([...selectedSenders, sender.email]);
                    } else {
                      setSelectedSenders(selectedSenders.filter(s => s !== sender.email));
                    }
                  }}
                  disabled={extracting}
                  className="h-4 w-4"
                />
                <span className="text-sm flex-1">{sender.name}</span>
              </label>
            ))}
          </div>
          {selectedSenders.length === 0 && (
            <p className="text-xs text-muted-foreground">
              No senders selected - will extract from all configured newsletters
            </p>
          )}
        </div>

        {/* Extract Button */}
        <Button
          onClick={handleExtract}
          disabled={extracting || disabled}
          className="w-full"
          size="lg"
        >
          {extracting ? 'Extracting...' : disabled ? 'Connect Gmail to Extract' : 'Extract'}
        </Button>
      </div>

      {/* Progress Display */}
      {extracting && (
        <ProgressIndicator
          progress={extractionProgress}
          message={extractionMessage}
          title="Extraction in progress..."
          hint="💡 Feel free to navigate away - we'll save your results"
        />
      )}

      {/* Error Display */}
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
  );
}
