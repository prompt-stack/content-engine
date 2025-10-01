# 🏗️ Frontend Architecture - Content Engine

**Component Hierarchy**: Primitives → Composed → Features → Pages

---

## 📋 Architecture Pattern

### Your Pattern (Excellent!) ✅

```
primitives/     # Base UI elements (no imports from our code)
    ↓
composed/       # Made of primitives
    ↓
features/       # Made of primitives + composed
    ↓
pages/          # Made of features (in app/ directory)
```

**Rules**:
1. **Primitives** = Pure UI, no business logic, no local imports
2. **Composed** = Combine primitives, still generic
3. **Features** = Business logic, use composed + primitives
4. **Pages** = Orchestrate features, route-level components

---

## 🎯 Recommended Structure for Content Engine

### Directory Layout

```
content-engine/frontend/
├── app/                          # Next.js App Router (PAGES)
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── extract/
│   │   └── page.tsx             # Extract page (uses features)
│   ├── process/
│   │   └── page.tsx             # Process page
│   ├── workflows/
│   │   └── page.tsx             # Workflows page
│   └── api/                     # API routes (proxy to backend)
│       ├── extract/
│       │   └── route.ts
│       └── llm/
│           └── route.ts
│
├── src/
│   ├── components/
│   │   ├── primitives/          # Base UI (Shadcn lives here)
│   │   │   ├── ui/              # Shadcn components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── ...
│   │   │   ├── icons/           # Icon components
│   │   │   │   ├── logo.tsx
│   │   │   │   └── spinner.tsx
│   │   │   └── typography/      # Text primitives
│   │   │       ├── heading.tsx
│   │   │       └── text.tsx
│   │   │
│   │   ├── composed/            # Combinations of primitives
│   │   │   ├── empty-state.tsx  # Card + Icon + Text
│   │   │   ├── loading-state.tsx # Spinner + Text
│   │   │   ├── error-state.tsx  # Card + Alert + Text
│   │   │   ├── form-field.tsx   # Label + Input + Error
│   │   │   ├── modal.tsx        # Dialog + Card + Button
│   │   │   └── navbar.tsx       # Nav + Buttons + Logo
│   │   │
│   │   └── features/            # Business logic components
│   │       ├── extract/
│   │       │   ├── extract-form.tsx
│   │       │   ├── extract-result.tsx
│   │       │   ├── platform-selector.tsx
│   │       │   └── url-validator.tsx
│   │       ├── llm/
│   │       │   ├── llm-processor.tsx
│   │       │   ├── provider-selector.tsx
│   │       │   ├── task-selector.tsx
│   │       │   └── result-viewer.tsx
│   │       ├── media/
│   │       │   ├── image-generator.tsx
│   │       │   ├── image-gallery.tsx
│   │       │   └── prompt-editor.tsx
│   │       ├── search/
│   │       │   ├── search-bar.tsx
│   │       │   ├── search-results.tsx
│   │       │   └── search-filters.tsx
│   │       └── workflow/
│   │           ├── workflow-builder.tsx
│   │           ├── workflow-steps.tsx
│   │           └── workflow-runner.tsx
│   │
│   ├── lib/                     # Utilities & API client
│   │   ├── api.ts              # API client
│   │   ├── utils.ts            # Helper functions
│   │   └── constants.ts        # Constants
│   │
│   ├── types/                   # TypeScript types
│   │   ├── api.ts              # API response types
│   │   ├── components.ts       # Component prop types
│   │   └── index.ts
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── use-extract.ts
│   │   ├── use-llm.ts
│   │   └── use-workflow.ts
│   │
│   └── styles/                  # Global styles
│       └── globals.css
│
├── public/                      # Static assets
│   ├── images/
│   └── icons/
│
└── config files
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    └── next.config.js
```

---

## 🎨 Component Examples by Layer

### 1. Primitives (Base UI - No Local Imports)

#### src/components/primitives/ui/button.tsx (Shadcn)
```typescript
// ✅ NO imports from our code
// ✅ Pure UI component
// ✅ Reusable everywhere

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'rounded-lg font-medium transition-colors',
          {
            'bg-primary text-white hover:bg-primary/90': variant === 'primary',
            'bg-secondary text-gray-900 hover:bg-secondary/80': variant === 'secondary',
            'bg-transparent hover:bg-gray-100': variant === 'ghost',
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-base': size === 'md',
            'px-6 py-3 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      />
    );
  }
);
```

#### src/components/primitives/ui/card.tsx (Shadcn)
```typescript
// ✅ NO imports from our code
// ✅ Pure UI component

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        className
      )}
      {...props}
    />
  )
);

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
  )
);

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
);
```

#### src/components/primitives/icons/spinner.tsx
```typescript
// ✅ NO imports from our code
// ✅ Pure UI component

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
```

---

### 2. Composed (Made of Primitives)

#### src/components/composed/loading-state.tsx
```typescript
// ✅ Imports ONLY from primitives
// ✅ No business logic
// ✅ Generic, reusable

import { Card, CardContent } from '@/components/primitives/ui/card';
import { Spinner } from '@/components/primitives/icons/spinner';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <Card className="p-8">
      <CardContent className="flex flex-col items-center justify-center space-y-4">
        <Spinner className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}
```

#### src/components/composed/empty-state.tsx
```typescript
// ✅ Imports ONLY from primitives
// ✅ No business logic

import { Card, CardContent, CardHeader } from '@/components/primitives/ui/card';
import { Button } from '@/components/primitives/ui/button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="p-8">
      <CardContent className="flex flex-col items-center justify-center space-y-4 text-center">
        {icon && <div className="text-4xl text-muted-foreground">{icon}</div>}
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground mt-2">{description}</p>
        </div>
        {action && (
          <Button variant="primary" onClick={action.onClick}>
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
```

#### src/components/composed/form-field.tsx
```typescript
// ✅ Imports ONLY from primitives
// ✅ Generic form field pattern

import { Input } from '@/components/primitives/ui/input';
import { Label } from '@/components/primitives/ui/label';

interface FormFieldProps {
  label: string;
  id: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}

export function FormField({ label, id, error, hint, required, children }: FormFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      {children}
      {error && <p className="text-sm text-destructive">{error}</p>}
      {hint && !error && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}
```

---

### 3. Features (Business Logic - Uses Primitives + Composed)

#### src/components/features/extract/extract-form.tsx
```typescript
// ✅ Imports from primitives + composed
// ✅ Contains business logic (extraction)
// ✅ Uses API

'use client';

import { useState } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Input } from '@/components/primitives/ui/input';
import { Card, CardHeader, CardContent } from '@/components/primitives/ui/card';
import { FormField } from '@/components/composed/form-field';
import { LoadingState } from '@/components/composed/loading-state';
import { api } from '@/lib/api';

interface ExtractFormProps {
  onSuccess: (data: any) => void;
}

export function ExtractForm({ onSuccess }: ExtractFormProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await api.extract.auto(url);
      onSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Extracting content..." />;
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-bold">Extract Content</h2>
        <p className="text-muted-foreground">
          Paste a TikTok, YouTube, or Reddit URL
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            label="URL"
            id="url"
            error={error}
            hint="Supports TikTok, YouTube, Reddit, and article URLs"
            required
          >
            <Input
              id="url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://tiktok.com/..."
            />
          </FormField>

          <Button type="submit" variant="primary" disabled={!url}>
            Extract Content
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

#### src/components/features/llm/llm-processor.tsx
```typescript
// ✅ Business logic for LLM processing
// ✅ Uses primitives + composed

'use client';

import { useState } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Card, CardHeader, CardContent } from '@/components/primitives/ui/card';
import { Select } from '@/components/primitives/ui/select';
import { Textarea } from '@/components/primitives/ui/textarea';
import { LoadingState } from '@/components/composed/loading-state';
import { api } from '@/lib/api';

interface LLMProcessorProps {
  initialContent?: string;
  onSuccess: (result: any) => void;
}

export function LLMProcessor({ initialContent = '', onSuccess }: LLMProcessorProps) {
  const [content, setContent] = useState(initialContent);
  const [task, setTask] = useState<'summarize' | 'extract_key_points' | 'generate_tags'>('summarize');
  const [provider, setProvider] = useState<'deepseek' | 'openai' | 'anthropic'>('deepseek');
  const [loading, setLoading] = useState(false);

  const handleProcess = async () => {
    setLoading(true);
    try {
      const result = await api.llm.processContent(content, task, provider);
      onSuccess(result);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message={`Processing with ${provider}...`} />;
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-2xl font-bold">AI Processing</h2>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Select value={task} onValueChange={setTask}>
            <option value="summarize">Summarize</option>
            <option value="extract_key_points">Key Points</option>
            <option value="generate_tags">Generate Tags</option>
          </Select>

          <Select value={provider} onValueChange={setProvider}>
            <option value="deepseek">DeepSeek (Cheapest)</option>
            <option value="openai">OpenAI (GPT-4o)</option>
            <option value="anthropic">Claude (Best)</option>
          </Select>
        </div>

        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={10}
          placeholder="Paste content to process..."
        />

        <Button onClick={handleProcess} variant="primary" disabled={!content}>
          Process with AI
        </Button>
      </CardContent>
    </Card>
  );
}
```

---

### 4. Pages (in app/ - Orchestrate Features)

#### app/extract/page.tsx
```typescript
// ✅ Page-level component
// ✅ Orchestrates features
// ✅ Manages route state

'use client';

import { useState } from 'react';
import { ExtractForm } from '@/components/features/extract/extract-form';
import { ExtractResult } from '@/components/features/extract/extract-result';
import { EmptyState } from '@/components/composed/empty-state';

export default function ExtractPage() {
  const [result, setResult] = useState(null);

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-4xl font-bold">Content Extraction</h1>
        <p className="text-muted-foreground mt-2">
          Extract content from social media and web articles
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <ExtractForm onSuccess={setResult} />

        {result ? (
          <ExtractResult data={result} />
        ) : (
          <EmptyState
            icon="📄"
            title="No content extracted yet"
            description="Enter a URL to get started"
          />
        )}
      </div>
    </div>
  );
}
```

---

## 🎯 Integration with Shadcn UI

### Shadcn Components = Primitives ✅

```bash
# Install Shadcn
npx shadcn-ui@latest init

# Add components (these go in src/components/primitives/ui/)
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add select
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
```

**Result**:
```
src/components/primitives/ui/
├── button.tsx          # ✅ Shadcn primitive
├── card.tsx            # ✅ Shadcn primitive
├── input.tsx           # ✅ Shadcn primitive
└── ...
```

**All Shadcn components = Primitives** (no imports from our code)

---

## 📋 Component Layer Rules

### Primitives ✅
- ❌ NO imports from `@/components/` (except utils)
- ✅ Pure UI components
- ✅ Fully reusable
- ✅ No business logic
- ✅ No API calls
- **Example**: Button, Card, Input, Spinner

### Composed ✅
- ✅ Imports ONLY from `primitives/`
- ✅ Combination patterns
- ✅ Still generic
- ✅ No business logic
- ✅ No API calls
- **Example**: LoadingState, EmptyState, FormField

### Features ✅
- ✅ Imports from `primitives/` + `composed/`
- ✅ Business logic allowed
- ✅ API calls allowed
- ✅ Domain-specific
- ✅ Reusable within domain
- **Example**: ExtractForm, LLMProcessor, ImageGenerator

### Pages ✅
- ✅ Imports from `features/` (primarily)
- ✅ Can import `composed/` + `primitives/`
- ✅ Route-level components
- ✅ Orchestrate features
- ✅ Manage page state
- **Example**: ExtractPage, WorkflowPage, DashboardPage

---

## 🚀 Summary

**Your pattern is perfect!** ✅

**Integration with Shadcn**:
- Shadcn UI → `primitives/ui/`
- Your custom primitives → `primitives/icons/`, `primitives/typography/`
- Build composed from primitives
- Build features from composed + primitives
- Build pages from features

**Clean, scalable, maintainable!** 🎉

Want me to help set up this structure?