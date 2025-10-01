# 🚀 Frontend Setup Guide - Content Engine

**Status**: Ready to initialize with component architecture pattern

---

## 🎯 Architecture Pattern

Your proven component pattern:

```
primitives/     # No local imports (Shadcn UI components)
    ↓
composed/       # Made of primitives
    ↓
features/       # Made of primitives + composed + business logic
    ↓
pages/          # Made of features (lives in app/)
```

**Import Rules**:
- ✅ Primitives: NO local imports (external only: React, Radix, etc.)
- ✅ Composed: Import ONLY from primitives
- ✅ Features: Import from primitives + composed
- ✅ Pages: Import from features (orchestration only)

---

## 📁 Final Directory Structure

```
frontend/
├── app/                          # Next.js 14 App Router (PAGES LAYER)
│   ├── page.tsx                  # Homepage
│   ├── extract/
│   │   └── page.tsx              # /extract page
│   ├── process/
│   │   └── page.tsx              # /process page
│   ├── generate/
│   │   └── page.tsx              # /generate page
│   ├── search/
│   │   └── page.tsx              # /search page
│   ├── layout.tsx                # Root layout
│   ├── globals.css               # Global styles
│   └── api/                      # API routes (proxy to backend)
│       ├── extract/route.ts
│       ├── llm/route.ts
│       ├── media/route.ts
│       └── search/route.ts
│
├── src/
│   ├── components/
│   │   ├── primitives/          # PRIMITIVES LAYER
│   │   │   ├── ui/              # Shadcn components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── textarea.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── alert.tsx
│   │   │   │   └── progress.tsx
│   │   │   └── icons/           # Icon components
│   │   │       ├── spinner.tsx
│   │   │       └── index.ts
│   │   │
│   │   ├── composed/            # COMPOSED LAYER
│   │   │   ├── loading-state.tsx
│   │   │   ├── empty-state.tsx
│   │   │   ├── error-state.tsx
│   │   │   ├── form-field.tsx
│   │   │   ├── result-card.tsx
│   │   │   └── status-badge.tsx
│   │   │
│   │   └── features/            # FEATURES LAYER
│   │       ├── extract/
│   │       │   ├── extract-form.tsx
│   │       │   ├── platform-selector.tsx
│   │       │   └── extracted-content-view.tsx
│   │       ├── llm/
│   │       │   ├── llm-processor.tsx
│   │       │   ├── provider-selector.tsx
│   │       │   └── output-view.tsx
│   │       ├── media/
│   │       │   ├── image-generator.tsx
│   │       │   └── image-gallery.tsx
│   │       └── search/
│   │           ├── search-form.tsx
│   │           └── search-results.tsx
│   │
│   ├── lib/
│   │   ├── api.ts               # API client (calls backend)
│   │   ├── utils.ts             # cn() utility
│   │   └── types.ts             # TypeScript types
│   │
│   └── hooks/                   # React hooks
│       ├── use-api.ts
│       └── use-toast.ts
│
├── public/                      # Static assets
│   ├── favicon.ico
│   └── images/
│
├── .env.local                   # Environment variables
├── .gitignore
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── components.json              # Shadcn config
└── postcss.config.js
```

---

## 🔧 Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Shadcn UI (in primitives/ui/)
- **State**: React hooks (useState, useEffect)
- **API Client**: Fetch API
- **Deployment**: Vercel (recommended)

---

## 📦 Installation Steps

### Step 1: Initialize Next.js 14 Project

```bash
cd /Users/hoff/My\ Drive/tools/data-processing/content-engine/frontend

# Create Next.js app (will merge with existing dirs)
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"

# Answer prompts:
# ✔ Would you like to use ESLint? … Yes
# ✔ Would you like to use Turbopack? … No
# ✔ Would you like to customize the default import alias? … No
```

### Step 2: Install Shadcn UI

```bash
# Initialize Shadcn
npx shadcn-ui@latest init

# Answer prompts:
# ✔ Which style? › Default
# ✔ Which color? › Slate
# ✔ Would you like to use CSS variables? › Yes

# Install base components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add select
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add progress
```

**IMPORTANT**: Shadcn will create `src/components/ui/` - we need to move this to `src/components/primitives/ui/`

```bash
# Move Shadcn components to primitives
mkdir -p src/components/primitives
mv src/components/ui src/components/primitives/ui

# Update components.json to point to new location
```

### Step 3: Create Architecture Directories

```bash
# Create component layer directories
mkdir -p src/components/primitives/icons
mkdir -p src/components/composed
mkdir -p src/components/features/extract
mkdir -p src/components/features/llm
mkdir -p src/components/features/media
mkdir -p src/components/features/search

# Create lib and hooks
mkdir -p src/lib
mkdir -p src/hooks

# Create app directories
mkdir -p app/extract
mkdir -p app/process
mkdir -p app/generate
mkdir -p app/search
mkdir -p app/api/extract
mkdir -p app/api/llm
mkdir -p app/api/media
mkdir -p app/api/search
```

### Step 4: Update Import Paths

Since we moved Shadcn to `primitives/ui/`, update `components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components/primitives/ui",
    "utils": "@/lib/utils"
  }
}
```

---

## 🎨 Layer Examples

### Primitives (No Local Imports)

```typescript
// src/components/primitives/ui/button.tsx (Shadcn)
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
```

### Composed (Imports Only Primitives)

```typescript
// src/components/composed/loading-state.tsx
import { Card, CardContent } from '@/components/primitives/ui/card';
import { Spinner } from '@/components/primitives/icons/spinner';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-6">
        <Spinner className="h-5 w-5 animate-spin" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}
```

### Features (Imports Primitives + Composed + Business Logic)

```typescript
// src/components/features/extract/extract-form.tsx
import { useState } from 'react';
import { Button } from '@/components/primitives/ui/button';
import { Input } from '@/components/primitives/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/primitives/ui/card';
import { LoadingState } from '@/components/composed/loading-state';
import { ErrorState } from '@/components/composed/error-state';
import { api } from '@/lib/api';

export function ExtractForm({ onSuccess }: { onSuccess: (data: any) => void }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await api.extract.auto(url);
      onSuccess(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract content');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingState message="Extracting content..." />;
  if (error) return <ErrorState message={error} onRetry={() => setError(null)} />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extract Content</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="url"
            placeholder="Paste TikTok, YouTube, or Reddit URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <Button type="submit" disabled={!url}>
            Extract
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

### Pages (Imports Features Only)

```typescript
// app/extract/page.tsx
'use client';

import { useState } from 'react';
import { ExtractForm } from '@/components/features/extract/extract-form';
import { ExtractedContentView } from '@/components/features/extract/extracted-content-view';

export default function ExtractPage() {
  const [extractedData, setExtractedData] = useState<any>(null);

  return (
    <div className="container mx-auto py-8 space-y-6">
      <h1 className="text-4xl font-bold">Content Extractor</h1>

      <ExtractForm onSuccess={setExtractedData} />

      {extractedData && <ExtractedContentView data={extractedData} />}
    </div>
  );
}
```

---

## 🔗 API Client

```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9765';

export const api = {
  // Extractors
  extract: {
    tiktok: async (url: string) => {
      const res = await fetch(`${API_BASE}/api/extract/tiktok`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!res.ok) throw new Error('Extraction failed');
      return res.json();
    },

    youtube: async (url: string) => {
      const res = await fetch(`${API_BASE}/api/extract/youtube`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!res.ok) throw new Error('Extraction failed');
      return res.json();
    },

    auto: async (url: string) => {
      const res = await fetch(`${API_BASE}/api/extract/auto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      if (!res.ok) throw new Error('Extraction failed');
      return res.json();
    },
  },

  // LLM
  llm: {
    generate: async (prompt: string, provider = 'deepseek') => {
      const res = await fetch(`${API_BASE}/api/llm/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, provider })
      });
      if (!res.ok) throw new Error('Generation failed');
      return res.json();
    },

    processContent: async (content: string, task = 'summarize', provider = 'deepseek') => {
      const res = await fetch(`${API_BASE}/api/llm/process-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, task, provider })
      });
      if (!res.ok) throw new Error('Processing failed');
      return res.json();
    },
  },

  // Media
  media: {
    generateImage: async (prompt: string, provider = 'openai') => {
      const res = await fetch(`${API_BASE}/api/media/generate-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, provider })
      });
      if (!res.ok) throw new Error('Image generation failed');
      return res.json();
    },
  },

  // Search
  search: {
    search: async (query: string, max_results = 10) => {
      const res = await fetch(`${API_BASE}/api/search/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results })
      });
      if (!res.ok) throw new Error('Search failed');
      return res.json();
    },
  }
};
```

---

## ⚙️ Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:9765
```

---

## 🚀 Development

```bash
# Start backend first
cd ../backend
docker-compose up

# In another terminal, start frontend
cd /Users/hoff/My\ Drive/tools/data-processing/content-engine/frontend
npm run dev
```

Visit: http://localhost:3000

---

## 🎯 Build Order (Recommended)

### Day 1: Setup + First Feature
1. ✅ Initialize Next.js + Shadcn
2. ✅ Create directory structure
3. ✅ Create API client
4. ✅ Build extract feature (form + view)
5. ✅ Create extract page
6. ✅ Test end-to-end

### Day 2: LLM + Media Features
1. Build LLM processor feature
2. Build image generator feature
3. Create process page
4. Create generate page
5. Test workflows

### Day 3: Search + Complete Pipeline
1. Build search feature
2. Create search page
3. Build complete workflow component
4. Polish UI/UX
5. Add error handling

---

## 📊 Component Checklist

### Primitives (Shadcn)
- [ ] button
- [ ] card
- [ ] input
- [ ] textarea
- [ ] select
- [ ] badge
- [ ] alert
- [ ] progress
- [ ] spinner icon

### Composed
- [ ] loading-state
- [ ] empty-state
- [ ] error-state
- [ ] form-field
- [ ] result-card

### Features
- [ ] extract-form
- [ ] extracted-content-view
- [ ] llm-processor
- [ ] output-view
- [ ] image-generator
- [ ] image-gallery
- [ ] search-form
- [ ] search-results

### Pages
- [ ] / (homepage)
- [ ] /extract
- [ ] /process
- [ ] /generate
- [ ] /search

---

## 🎯 Next Steps

Run the initialization:

```bash
cd /Users/hoff/My\ Drive/tools/data-processing/content-engine/frontend

# 1. Initialize Next.js
npx create-next-app@latest . --typescript --tailwind --app --src-dir

# 2. Install Shadcn
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input textarea select badge alert progress

# 3. Reorganize for architecture pattern
mkdir -p src/components/primitives
mv src/components/ui src/components/primitives/ui

# 4. Create remaining directories
mkdir -p src/components/composed
mkdir -p src/components/features/{extract,llm,media,search}
mkdir -p src/lib src/hooks
mkdir -p app/{extract,process,generate,search}

# 5. Start building!
npm run dev
```

Ready to build! 🚀