'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/primitives/ui/button';
import { Input } from '@/components/primitives/ui/input';
import { Card } from '@/components/primitives/ui/card';
import { api } from '@/lib/api';

interface ContentFiltering {
  description: string;
  whitelist_domains: string[];
  blacklist_domains: string[];
  curator_domains: string[];
  content_indicators: string[];
}

interface Config {
  content_filtering: ContentFiltering;
  [key: string]: any;
}

export default function NewsletterConfigPage() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testUrl, setTestUrl] = useState('');
  const [testResult, setTestResult] = useState<{url: string; is_valid: boolean; reason: string} | null>(null);
  const [testingUrl, setTestingUrl] = useState(false);

  // New domain inputs
  const [newWhitelist, setNewWhitelist] = useState('');
  const [newBlacklist, setNewBlacklist] = useState('');
  const [newCurator, setNewCurator] = useState('');
  const [newIndicator, setNewIndicator] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.newsletters.config();
      setConfig(data);
    } catch (error) {
      console.error('Failed to load config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    setSaving(true);
    try {
      await api.newsletters.updateConfig(config);
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save config:', error);
      alert(error instanceof Error ? error.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const testUrlFiltering = async () => {
    if (!testUrl.trim()) return;

    setTestingUrl(true);
    setTestResult(null);

    try {
      const data = await api.newsletters.testUrl(testUrl);
      setTestResult(data);
    } catch (error) {
      console.error('Failed to test URL:', error);
    } finally {
      setTestingUrl(false);
    }
  };

  const addDomain = (type: keyof ContentFiltering, value: string, setter: (val: string) => void) => {
    if (!config || !value.trim()) return;

    const domain = value.trim().toLowerCase();
    const list = config.content_filtering[type];

    if (Array.isArray(list) && !list.includes(domain)) {
      setConfig({
        ...config,
        content_filtering: {
          ...config.content_filtering,
          [type]: [...list, domain],
        },
      });
      setter('');
    }
  };

  const removeDomain = (type: keyof ContentFiltering, domain: string) => {
    if (!config) return;

    const list = config.content_filtering[type];

    if (Array.isArray(list)) {
      setConfig({
        ...config,
        content_filtering: {
          ...config.content_filtering,
          [type]: list.filter((d) => d !== domain),
        },
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <p>Loading configuration...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="container mx-auto py-8 px-4">
        <p>Failed to load configuration</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-4 sm:py-8 px-4 max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl sm:text-4xl font-bold">Content Filtering Config</h1>
          <p className="text-muted-foreground mt-2">
            Manage which domains and URLs are accepted or rejected during newsletter extraction
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/newsletters">
            <Button variant="ghost" size="sm">← Back</Button>
          </Link>
          <Button onClick={saveConfig} disabled={saving} size="sm">
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* URL Tester */}
      <Card className="p-6 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <h2 className="text-xl font-semibold mb-4">Test URL Filtering</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Test if a URL would pass the current filtering rules
        </p>
        <div className="flex gap-2 mb-4">
          <Input
            type="url"
            placeholder="https://example.com/article"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && testUrlFiltering()}
            className="flex-1"
          />
          <Button onClick={testUrlFiltering} disabled={testingUrl || !testUrl.trim()}>
            {testingUrl ? 'Testing...' : 'Test URL'}
          </Button>
        </div>
        {testResult && (
          <div className={`p-4 rounded-md ${testResult.is_valid ? 'bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-700' : 'bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-700'}`}>
            <div className="flex items-start gap-2">
              <span className="text-2xl">{testResult.is_valid ? '✅' : '❌'}</span>
              <div className="flex-1">
                <p className="font-semibold">{testResult.is_valid ? 'ACCEPTED' : 'REJECTED'}</p>
                <p className="text-sm mt-1">{testResult.reason}</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Whitelist Domains */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-2">Whitelist Domains</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Domains that are always accepted (e.g., github.com, arxiv.org, techcrunch.com)
        </p>
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="example.com"
            value={newWhitelist}
            onChange={(e) => setNewWhitelist(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addDomain('whitelist_domains', newWhitelist, setNewWhitelist)}
          />
          <Button onClick={() => addDomain('whitelist_domains', newWhitelist, setNewWhitelist)}>
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.content_filtering.whitelist_domains || []).map((domain) => (
            <div key={domain} className="flex items-center gap-2 bg-green-100 dark:bg-green-900 px-3 py-1 rounded-full text-sm">
              <span>{domain}</span>
              <button
                onClick={() => removeDomain('whitelist_domains', domain)}
                className="text-green-700 dark:text-green-300 hover:text-green-900 dark:hover:text-green-100"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Blacklist Domains */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-2">Blacklist Domains</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Domains that are always rejected (e.g., typeform.com, surveymonkey.com)
        </p>
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="example.com"
            value={newBlacklist}
            onChange={(e) => setNewBlacklist(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addDomain('blacklist_domains', newBlacklist, setNewBlacklist)}
          />
          <Button onClick={() => addDomain('blacklist_domains', newBlacklist, setNewBlacklist)}>
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.content_filtering.blacklist_domains || []).map((domain) => (
            <div key={domain} className="flex items-center gap-2 bg-red-100 dark:bg-red-900 px-3 py-1 rounded-full text-sm">
              <span>{domain}</span>
              <button
                onClick={() => removeDomain('blacklist_domains', domain)}
                className="text-red-700 dark:text-red-300 hover:text-red-900 dark:hover:text-red-100"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Curator Domains */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-2">Newsletter Curator Domains</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Newsletter platforms whose own content should be excluded (e.g., rundown.ai, alphasignal.ai)
        </p>
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="example.ai"
            value={newCurator}
            onChange={(e) => setNewCurator(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addDomain('curator_domains', newCurator, setNewCurator)}
          />
          <Button onClick={() => addDomain('curator_domains', newCurator, setNewCurator)}>
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.content_filtering.curator_domains || []).map((domain) => (
            <div key={domain} className="flex items-center gap-2 bg-yellow-100 dark:bg-yellow-900 px-3 py-1 rounded-full text-sm">
              <span>{domain}</span>
              <button
                onClick={() => removeDomain('curator_domains', domain)}
                className="text-yellow-700 dark:text-yellow-300 hover:text-yellow-900 dark:hover:text-yellow-100"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Content Indicators */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-2">Content Indicators</h2>
        <p className="text-sm text-muted-foreground mb-4">
          URL path patterns that indicate content (e.g., /blog/, /article/, /p/, /status/)
        </p>
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="/example/"
            value={newIndicator}
            onChange={(e) => setNewIndicator(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addDomain('content_indicators', newIndicator, setNewIndicator)}
          />
          <Button onClick={() => addDomain('content_indicators', newIndicator, setNewIndicator)}>
            Add
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.content_filtering.content_indicators || []).map((indicator) => (
            <div key={indicator} className="flex items-center gap-2 bg-blue-100 dark:bg-blue-900 px-3 py-1 rounded-full text-sm">
              <span className="font-mono">{indicator}</span>
              <button
                onClick={() => removeDomain('content_indicators', indicator)}
                className="text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Save Button (bottom) */}
      <div className="flex justify-end">
        <Button onClick={saveConfig} disabled={saving} size="lg">
          {saving ? 'Saving...' : 'Save All Changes'}
        </Button>
      </div>
    </div>
  );
}
