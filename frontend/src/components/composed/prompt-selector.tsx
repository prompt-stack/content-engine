'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Textarea } from '@/components/primitives/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/primitives/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/primitives/ui/card';
import { api } from '@/lib/api';
import type { Prompt, PromptCategory } from '@/lib/types';

interface PromptSelectorProps {
  content: string;
  onProcess: (promptText: string, promptName: string) => void;
  loading?: boolean;
}

export function PromptSelector({ content, onProcess, loading = false }: PromptSelectorProps) {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [categories, setCategories] = useState<PromptCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPromptId, setSelectedPromptId] = useState<string>('');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [mode, setMode] = useState<'template' | 'custom'>('template');
  const [error, setError] = useState<string | null>(null);

  // Load prompts and categories on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [allPrompts, allCategories] = await Promise.all([
          api.prompts.list(),
          api.prompts.categories(),
        ]);
        setPrompts(allPrompts);
        setCategories(allCategories);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load prompts');
      }
    };
    loadData();
  }, []);

  // Filter prompts by category
  const filteredPrompts = selectedCategory === 'all'
    ? prompts
    : prompts.filter(p => p.category.toLowerCase() === categories.find(c => c.id === selectedCategory)?.name.toLowerCase());

  // Get selected prompt details
  const selectedPrompt = prompts.find(p => p.id === selectedPromptId);

  const handleProcess = async () => {
    if (mode === 'custom') {
      if (!customPrompt.trim()) {
        setError('Please enter a custom prompt');
        return;
      }
      // For custom prompts, just use the content directly in the prompt
      const fullPrompt = customPrompt.replace('{content}', content);
      onProcess(fullPrompt, 'Custom Prompt');
    } else {
      if (!selectedPromptId) {
        setError('Please select a prompt');
        return;
      }
      try {
        // Render the prompt with content variable
        const response = await api.prompts.render({
          prompt_id: selectedPromptId,
          variables: { content },
        });
        onProcess(response.rendered_prompt, selectedPrompt?.name || 'Prompt');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to render prompt');
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Processing</CardTitle>
        <CardDescription>
          Choose a prompt template or write your own
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Toggle */}
        <div className="flex gap-2">
          <Button
            variant={mode === 'template' ? 'default' : 'outline'}
            onClick={() => setMode('template')}
            size="sm"
          >
            📋 Templates
          </Button>
          <Button
            variant={mode === 'custom' ? 'default' : 'outline'}
            onClick={() => setMode('custom')}
            size="sm"
          >
            ✏️ Custom
          </Button>
        </div>

        {/* Template Mode */}
        {mode === 'template' && (
          <div className="space-y-3">
            {/* Category Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Prompt Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Prompt Template</label>
              <Select value={selectedPromptId} onValueChange={setSelectedPromptId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a prompt..." />
                </SelectTrigger>
                <SelectContent>
                  {filteredPrompts.map((prompt) => (
                    <SelectItem key={prompt.id} value={prompt.id}>
                      {prompt.icon} {prompt.name} - {prompt.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Prompt Preview */}
            {selectedPrompt && (
              <div className="p-3 bg-muted rounded-md text-sm">
                <p className="font-semibold mb-1">Preview:</p>
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {selectedPrompt.template}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Est. tokens: {selectedPrompt.estimated_tokens} • Format: {selectedPrompt.output_format}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Custom Mode */}
        {mode === 'custom' && (
          <div>
            <label className="text-sm font-medium mb-2 block">Custom Prompt</label>
            <Textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Enter your custom prompt here. Use {content} to reference the extracted content."
              className="min-h-[150px]"
            />
            <p className="text-xs text-muted-foreground mt-2">
              Tip: Use {'{content}'} in your prompt to insert the extracted content
            </p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive rounded-md text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Process Button */}
        <Button
          onClick={handleProcess}
          disabled={loading || (mode === 'template' && !selectedPromptId) || (mode === 'custom' && !customPrompt.trim())}
          className="w-full"
        >
          {loading ? '⏳ Processing...' : '✨ Process with AI'}
        </Button>
      </CardContent>
    </Card>
  );
}
