'use client';

import { useState } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Card } from '@/components/primitives/ui/card';
import { ProgressIndicator } from '@/components/composed/progress-indicator';
import Link from 'next/link';

export default function ProgressPlaygroundPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [completed, setCompleted] = useState(false);

  async function simulateExtraction() {
    setIsRunning(true);
    setCompleted(false);
    setProgress(0);
    setMessage('Queued for extraction');

    // Simulate 0% - Queued
    await sleep(1000);
    setProgress(0);
    setMessage('Queued for extraction');

    // Simulate 10% - Starting
    await sleep(1500);
    setProgress(10);
    setMessage('Starting extraction from Gmail...');

    // Simulate 20% - Extracting
    await sleep(2000);
    setProgress(20);
    setMessage('Extracting newsletters from Gmail...');

    // Simulate 50% - Processing (extra step for demo)
    await sleep(3000);
    setProgress(50);
    setMessage('Processing extracted emails...');

    // Simulate 90% - Loading results
    await sleep(1500);
    setProgress(90);
    setMessage('Loading extraction results...');

    // Simulate 100% - Complete
    await sleep(1000);
    setProgress(100);
    setMessage('Extraction complete!');

    // Reset after showing completion
    await sleep(1500);
    setIsRunning(false);
    setCompleted(true);
    setProgress(0);
    setMessage('');
  }

  function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Progress Indicator Playground</h1>
          <p className="text-muted-foreground mt-2">
            Demo of the newsletter extraction progress indicator
          </p>
        </div>
        <Link href="/">
          <Button variant="ghost" size="sm">← Home</Button>
        </Link>
      </div>

      {/* Demo Card */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Simulated Extraction</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Click the button below to see how the progress indicator updates during a newsletter extraction.
          This simulates the actual flow: 0% → 10% → 20% → 50% → 90% → 100%
        </p>

        <Button
          onClick={simulateExtraction}
          disabled={isRunning}
          className="w-full"
          size="lg"
        >
          {isRunning ? 'Running Simulation...' : 'Start Simulation'}
        </Button>

        {/* Progress Display */}
        {isRunning && (
          <ProgressIndicator
            progress={progress}
            message={message}
            title="Simulated extraction in progress..."
            hint="💡 This is a demo - no actual extraction is running"
          />
        )}

        {/* Completion Message */}
        {completed && (
          <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-md border-2 border-green-500">
            <p className="font-medium text-green-900 dark:text-green-100">
              ✅ Simulation completed successfully!
            </p>
            <p className="text-sm text-green-800 dark:text-green-200 mt-1">
              In the real application, extracted newsletters would appear below.
            </p>
          </div>
        )}
      </Card>

      {/* Progress States Reference */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Progress States Reference</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-accent/30 rounded-md">
            <div className="font-mono text-sm font-bold w-12">0%</div>
            <div className="text-sm">Queued for extraction</div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-accent/30 rounded-md">
            <div className="font-mono text-sm font-bold w-12">10%</div>
            <div className="text-sm">Starting extraction from Gmail...</div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-accent/30 rounded-md">
            <div className="font-mono text-sm font-bold w-12">20%</div>
            <div className="text-sm">Extracting newsletters from Gmail...</div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-accent/30 rounded-md">
            <div className="font-mono text-sm font-bold w-12">90%</div>
            <div className="text-sm">Loading extraction results...</div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-accent/30 rounded-md">
            <div className="font-mono text-sm font-bold w-12">100%</div>
            <div className="text-sm">Extraction complete!</div>
          </div>
        </div>
      </Card>

      {/* Technical Details */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">How It Works</h2>
        <div className="space-y-3 text-sm">
          <div>
            <h3 className="font-semibold mb-1">Frontend (React)</h3>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
              <li>Polls backend every 2 seconds for status updates</li>
              <li>Updates progress bar and message in real-time</li>
              <li>Uses AbortController to handle fetch cancellations</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Backend (FastAPI)</h3>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
              <li>Runs extraction in background thread pool</li>
              <li>Updates progress in PostgreSQL database</li>
              <li>Handles blocking subprocess.run() operations safely</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Database</h3>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
              <li>Stores extraction status, progress %, and progress message</li>
              <li>Enables progress tracking across server restarts</li>
              <li>Allows multiple users to run extractions simultaneously</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Navigation */}
      <div className="flex gap-4">
        <Link href="/newsletters" className="flex-1">
          <Button variant="outline" className="w-full">
            Go to Real Extraction →
          </Button>
        </Link>
      </div>
    </div>
  );
}
