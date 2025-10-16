# Schema Data Mapping - Content Engine

**STATUS: ✅ PRODUCTION READY** (2025-10-15)

> 📚 **See [SCHEMA_OVERVIEW.md](./SCHEMA_OVERVIEW.md) for complete schema documentation with all 5 tables, relationships, and migration history.**

This document shows **real data examples** from actual newsletter extractions and how they map to the database.

## Implementation Summary

- **Complete Schema**: 5 tables, 41 columns (users, extractions, email_content, extracted_links, newsletter_config)
- **Migrations Applied**:
  1. `0a3d2a7ef13b` - Initial extraction models (extractions, email_content, extracted_links)
  2. `405f9211eb0a` - Add newsletter_config table
  3. `ac4b2ff42914` - Add user authentication (user_id to extractions, Google OAuth to users)
- **Database**: PostgreSQL 16 (Docker on port 7654, Railway in production)
- **API Endpoints**:
  - `POST /api/newsletters/extract` - Saves to database (tied to authenticated user)
  - `GET /api/newsletters/extractions` - Loads user's extractions from database
  - `GET /api/newsletters/config` - Get user's config from database
  - `PUT /api/newsletters/config` - Update user's config in database
- **CRUD Operations**: `app/crud/newsletter_extraction.py`
- **Tested**: ✅ Multi-extraction workflow with database persistence verified

---

## Real Data Example from `extraction_20251015_163702`

This document shows **exactly** how your current JSON extraction data maps to the implemented minimal database schema.

---

## Source Files

```
extractors/email/output/extraction_20251015_163702/
├── filtered_articles.json    ← Newsletter data with links
└── config_used.json           ← Extraction metadata
```

---

## 📊 Database Schema (Core Extraction Tables)

> 📚 **Full schema with users table:** See [SCHEMA_OVERVIEW.md](./SCHEMA_OVERVIEW.md)

### Table 1: `extractions` (5 columns) ✨ Updated
```sql
CREATE TABLE extractions (
    id VARCHAR(50) PRIMARY KEY,           -- "20251015_163702"
    user_id INTEGER,                      -- ✨ NEW: FK to users.id (your account)
    created_at TIMESTAMP NOT NULL,        -- 2025-10-15 16:37:02
    days_back INTEGER,                    -- 1
    max_results INTEGER,                  -- 30
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_extractions_user_id ON extractions(user_id);
CREATE INDEX ix_extractions_created_at ON extractions(created_at);
```

### Table 2: `email_content` (5 columns)
```sql
CREATE TABLE email_content (
    id SERIAL PRIMARY KEY,                -- Auto-increment
    extraction_id VARCHAR(50) NOT NULL,   -- FK: "20251015_163702"
    subject VARCHAR(1024) NOT NULL,       -- Newsletter subject
    sender VARCHAR(256) NOT NULL,         -- e.g., "news@alphasignal.ai"
    date VARCHAR(100) NOT NULL,           -- ISO string
    FOREIGN KEY (extraction_id) REFERENCES extractions(id) ON DELETE CASCADE
);

CREATE INDEX idx_email_content_extraction_id ON email_content(extraction_id);
CREATE INDEX idx_email_content_sender ON email_content(sender);
```

### Table 3: `extracted_links` (4 columns)
```sql
CREATE TABLE extracted_links (
    id SERIAL PRIMARY KEY,                -- Auto-increment
    content_id INTEGER NOT NULL,          -- FK: email_content.id
    url TEXT NOT NULL,                    -- Final resolved URL
    original_url TEXT,                    -- Tracking URL (if different)
    FOREIGN KEY (content_id) REFERENCES email_content(id) ON DELETE CASCADE
);

CREATE INDEX idx_extracted_links_content_id ON extracted_links(content_id);
```

---

## 🔄 Data Transformation Example

### Input: JSON Files

**`config_used.json`:**
```json
{
  "timestamp": "20251015_163702",
  "days_back": 1,
  "max_results": 30,
  "senders": ["news@alphasignal.ai", "crew@technews.therundown.ai", "news@daily.therundown.ai"],
  "created_at": "2025-10-15T16:37:02.240687"
}
```

**`filtered_articles.json` (Sample - Newsletter 1 of 5):**
```json
{
  "newsletter_index": 1,
  "newsletter_subject": "🔥 Alibaba unveils compact Qwen3-VL models that rival GPT-5 Nano",
  "newsletter_sender": "news@alphasignal.ai",
  "newsletter_date": "Wed, 15 Oct 2025 17:03:08 +0000",
  "articles": [
    {
      "url": "https://huggingface.co/collections/Qwen/qwen3-vl-68d2a7c1b8a8afce4ebd2dbe",
      "original_url": "https://app.alphasignal.ai/c?uid=1CMu2MCSvWZouF4ld&cid=05be88743bf5d704&lid=vhqNakjKI4qFG0eX",
      "is_redirect": true
    },
    {
      "url": "https://x.com/sama/status/1978129344598827128",
      "original_url": "https://app.alphasignal.ai/c?uid=1CMu2MCSvWZouF4ld&cid=05be88743bf5d704&lid=XtQKteFqGon9eQxv",
      "is_redirect": true
    }
    // ... 12 more links
  ],
  "article_count": 14
}
```

---

### Output: Database Rows

#### ✅ Table: `extractions` (1 Row)

| id | user_id | created_at | days_back | max_results |
|----|---------|------------|-----------|-------------|
| `20251015_163702` | `1` | `2025-10-15 16:37:02` | `1` | `30` |

**SQL Insert:**
```sql
INSERT INTO extractions (id, user_id, created_at, days_back, max_results)
VALUES (
    '20251015_163702',
    1,  -- ✨ Your user ID
    '2025-10-15 16:37:02',
    1,
    30
);
```

---

#### ✅ Table: `email_content` (5 Rows - one per newsletter)

| id | extraction_id | subject | sender | date |
|----|---------------|---------|--------|------|
| `1` | `20251015_163702` | `🔥 Alibaba unveils compact Qwen3-VL models...` | `news@alphasignal.ai` | `Wed, 15 Oct 2025 17:03:08 +0000` |
| `2` | `20251015_163702` | `🫣 ChatGPT to go 18+` | `news@daily.therundown.ai` | `Wed, 15 Oct 2025 10:06:54 +0000 (UTC)` |
| `3` | `20251015_163702` | `🔥 Karpathy unveils end-to-end ChatGPT clone repo` | `news@alphasignal.ai` | `Tue, 14 Oct 2025 16:32:22 +0000` |
| `4` | `20251015_163702` | `🪖 Meta and Anduril's AI war helmet` | `crew@technews.therundown.ai` | `Tue, 14 Oct 2025 14:33:42 +0000 (UTC)` |
| `5` | `20251015_163702` | `🔥 OpenAI's AI chip era begins` | `news@daily.therundown.ai` | `Tue, 14 Oct 2025 10:06:22 +0000 (UTC)` |

**SQL Inserts:**
```sql
-- Newsletter 1
INSERT INTO email_content (extraction_id, subject, sender, date)
VALUES (
    '20251015_163702',
    '🔥 Alibaba unveils compact Qwen3-VL models that rival GPT-5 Nano',
    'news@alphasignal.ai',
    'Wed, 15 Oct 2025 17:03:08 +0000'
);

-- Newsletter 2
INSERT INTO email_content (extraction_id, subject, sender, date)
VALUES (
    '20251015_163702',
    '🫣 ChatGPT to go 18+',
    'news@daily.therundown.ai',
    'Wed, 15 Oct 2025 10:06:54 +0000 (UTC)'
);

-- ... (3 more newsletters)
```

---

#### ✅ Table: `extracted_links` (62 Rows total - 14+14+12+13+9 links)

**Sample from Newsletter 1 (content_id = 1):**

| id | content_id | url | original_url |
|----|------------|-----|--------------|
| `1` | `1` | `https://huggingface.co/collections/Qwen/qwen3-vl-68...` | `https://app.alphasignal.ai/c?uid=1CMu2...` |
| `2` | `1` | `https://x.com/sama/status/1978129344598827128` | `https://app.alphasignal.ai/c?uid=1CMu2...` |
| `3` | `1` | `https://github.blog/ai-and-ml/generative-ai/spec-driven-development...` | `https://github.blog/ai-and-ml/generative-ai/spec-driven-development...` |
| ... | `1` | _(10 more links from Newsletter 1)_ | ... |

**Sample from Newsletter 2 (content_id = 2):**

| id | content_id | url | original_url |
|----|------------|-----|--------------|
| `15` | `2` | `https://x.com/sama/status/1978129344598827128` | `https://elinke1c.daily.therundown.ai/ss/c/u001...` |
| `16` | `2` | `https://www.theverge.com/news/799312/openai-chatgpt-erotica...` | `https://elinke1c.daily.therundown.ai/ss/c/u001...` |
| ... | `2` | _(12 more links from Newsletter 2)_ | ... |

**SQL Inserts:**
```sql
-- Links for Newsletter 1
INSERT INTO extracted_links (content_id, url, original_url)
VALUES
    (1, 'https://huggingface.co/collections/Qwen/qwen3-vl-68d2a7c1b8a8afce4ebd2dbe',
        'https://app.alphasignal.ai/c?uid=1CMu2MCSvWZouF4ld&cid=05be88743bf5d704&lid=vhqNakjKI4qFG0eX'),
    (1, 'https://x.com/sama/status/1978129344598827128',
        'https://app.alphasignal.ai/c?uid=1CMu2MCSvWZouF4ld&cid=05be88743bf5d704&lid=XtQKteFqGon9eQxv'),
    (1, 'https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/',
        'https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/');
-- ... (11 more links for Newsletter 1)

-- Links for Newsletter 2
INSERT INTO extracted_links (content_id, url, original_url)
VALUES
    (2, 'https://x.com/sama/status/1978129344598827128',
        'https://elinke1c.daily.therundown.ai/ss/c/u001.6k0_SAz8nrOuu_-LoNX1HfqGVtU0...'),
    (2, 'https://www.theverge.com/news/799312/openai-chatgpt-erotica-sam-altman-verified-adults',
        'https://elinke1c.daily.therundown.ai/ss/c/u001.dSnm3kaGd0BkNqLYPjeMf0JUH4oQ...');
-- ... (12 more links for Newsletter 2)
```

---

## 📈 Summary Statistics for This Extraction

**From Files:**
- **Extraction ID**: `20251015_163702`
- **Parameters**: 1 day back, max 30 results
- **Newsletters Found**: 5
- **Total Article Links**: 62 (14 + 14 + 12 + 13 + 9)
- **Senders**:
  - `news@alphasignal.ai` (2 newsletters, 26 links)
  - `news@daily.therundown.ai` (2 newsletters, 23 links)
  - `crew@technews.therundown.ai` (1 newsletter, 13 links)

**To Database:**
- **1 row** in `extractions` table
- **5 rows** in `email_content` table
- **62 rows** in `extracted_links` table

---

## 🔍 Query Examples

### Get all newsletters from this extraction:
```sql
SELECT
    ec.subject,
    ec.sender,
    ec.date,
    COUNT(el.id) as link_count
FROM email_content ec
LEFT JOIN extracted_links el ON ec.id = el.content_id
WHERE ec.extraction_id = '20251015_163702'
GROUP BY ec.id, ec.subject, ec.sender, ec.date
ORDER BY ec.id;
```

**Result:**
```
subject                                                  | sender                           | date                              | link_count
--------------------------------------------------------|----------------------------------|-----------------------------------|------------
🔥 Alibaba unveils compact Qwen3-VL models...           | news@alphasignal.ai              | Wed, 15 Oct 2025 17:03:08 +0000  | 14
🫣 ChatGPT to go 18+                                     | news@daily.therundown.ai         | Wed, 15 Oct 2025 10:06:54 +0000  | 14
🔥 Karpathy unveils end-to-end ChatGPT clone repo       | news@alphasignal.ai              | Tue, 14 Oct 2025 16:32:22 +0000  | 12
🪖 Meta and Anduril's AI war helmet                      | crew@technews.therundown.ai      | Tue, 14 Oct 2025 14:33:42 +0000  | 13
🔥 OpenAI's AI chip era begins                           | news@daily.therundown.ai         | Tue, 14 Oct 2025 10:06:22 +0000  | 9
```

---

### Get all links from AlphaSignal newsletters:
```sql
SELECT
    ec.subject,
    el.url
FROM extracted_links el
JOIN email_content ec ON el.content_id = ec.id
WHERE ec.sender = 'news@alphasignal.ai'
    AND ec.extraction_id = '20251015_163702';
```

**Result:**
```
subject                                                  | url
--------------------------------------------------------|--------------------------------------------------------
🔥 Alibaba unveils compact Qwen3-VL models...           | https://huggingface.co/collections/Qwen/qwen3-vl-68...
🔥 Alibaba unveils compact Qwen3-VL models...           | https://x.com/sama/status/1978129344598827128
🔥 Alibaba unveils compact Qwen3-VL models...           | https://github.blog/ai-and-ml/generative-ai/spec-...
... (11 more from Newsletter 1)
🔥 Karpathy unveils end-to-end ChatGPT clone repo       | https://github.com/karpathy/nanochat
🔥 Karpathy unveils end-to-end ChatGPT clone repo       | https://arxiv.org/abs/2506.10943
... (10 more from Newsletter 3)
```

---

### List all extractions (for frontend `/extractions` endpoint):
```sql
SELECT
    e.id,
    e.created_at,
    e.days_back,
    e.max_results,
    COUNT(DISTINCT ec.id) as newsletter_count,
    COUNT(el.id) as total_links
FROM extractions e
LEFT JOIN email_content ec ON e.id = ec.extraction_id
LEFT JOIN extracted_links el ON ec.id = el.content_id
GROUP BY e.id, e.created_at, e.days_back, e.max_results
ORDER BY e.created_at DESC;
```

**Result:**
```
id               | created_at           | days_back | max_results | newsletter_count | total_links
-----------------|----------------------|-----------|-------------|------------------|-------------
20251015_163702  | 2025-10-15 16:37:02  | 1         | 30          | 5                | 62
20251015_143052  | 2025-10-15 14:30:52  | 7         | 30          | 12               | 148
... (older extractions)
```

---

## 🎯 Key Observations

### 1. **Tracking URL Resolution**
Many links have different `url` vs `original_url`:

```json
{
  "url": "https://huggingface.co/collections/Qwen/qwen3-vl-68...",  // ← Clean URL
  "original_url": "https://app.alphasignal.ai/c?uid=..."            // ← Tracking URL
}
```

This is **the gold** - you're capturing both the clean link (for your extractors) and the tracking link (for attribution).

### 2. **Same Link, Multiple Newsletters**
Some URLs appear in multiple newsletters:
- `https://x.com/sama/status/1978129344598827128` appears in:
  - Newsletter 1 (AlphaSignal)
  - Newsletter 2 (The Rundown)

Database handles this naturally (separate rows).

### 3. **Email Date Formats Vary**
- AlphaSignal: `"Wed, 15 Oct 2025 17:03:08 +0000"`
- The Rundown: `"Wed, 15 Oct 2025 10:06:54 +0000 (UTC)"`

Storing as `VARCHAR(100)` preserves original format (frontend handles display).

### 4. **Emoji in Subjects**
All subjects have emojis (🔥, 🫣, 🪖). Database stores these fine with UTF-8 encoding.

---

## ✅ What Gets Removed from JSON

These fields exist in the JSON but **won't** be stored in the minimal schema:

```json
{
  "newsletter_index": 1,           // ❌ Not needed (order by id)
  "html_file": "newsletter_001.html",  // ❌ Not needed
  "article_count": 14,             // ❌ Computed (COUNT)
  "is_redirect": true              // ❌ Not needed (can infer from url != original_url)
}
```

**Why?**
- `newsletter_index`: Database auto-increments `id`
- `html_file`: Not used after extraction
- `article_count`: Computed with `COUNT(links)`
- `is_redirect`: Redundant (check if `url != original_url`)

---

## 🚀 API Response Transformation

**Database Query Result:**
```python
extraction = {
    'id': '20251015_163702',
    'created_at': datetime(2025, 10, 15, 16, 37, 2),
    'days_back': 1,
    'max_results': 30,
    'content_items': [
        {
            'id': 1,
            'subject': '🔥 Alibaba unveils compact Qwen3-VL models...',
            'sender': 'news@alphasignal.ai',
            'date': 'Wed, 15 Oct 2025 17:03:08 +0000',
            'links': [
                {'url': 'https://huggingface.co/...', 'original_url': 'https://app.alphasignal.ai/...'},
                {'url': 'https://x.com/sama/...', 'original_url': 'https://app.alphasignal.ai/...'},
            ]
        },
        # ... 4 more newsletters
    ]
}
```

**API JSON Response (Frontend Expects):**
```json
{
  "id": "20251015_163702",
  "created_at": "2025-10-15T16:37:02",
  "days_back": 1,
  "max_results": 30,
  "newsletters": [  // ← Renamed from content_items
    {
      "newsletter_subject": "🔥 Alibaba unveils compact Qwen3-VL models...",
      "newsletter_sender": "news@alphasignal.ai",
      "newsletter_date": "Wed, 15 Oct 2025 17:03:08 +0000",
      "links": [
        {"url": "https://huggingface.co/...", "original_url": "https://app.alphasignal.ai/..."},
        {"url": "https://x.com/sama/...", "original_url": "https://app.alphasignal.ai/..."}
      ],
      "link_count": 14
    }
    // ... 4 more
  ],
  "newsletter_count": 5,
  "total_links": 62
}
```

**Transformation in API:**
```python
# Database: extraction.content_items[0].subject
# API: newsletters[0]['newsletter_subject']

for content in extraction.content_items:
    newsletters.append({
        'newsletter_subject': content.subject,    # ← Transform
        'newsletter_sender': content.sender,      # ← Transform
        'newsletter_date': content.date,          # ← Transform
        'links': [{'url': link.url, 'original_url': link.original_url} for link in content.links],
        'link_count': len(content.links)
    })
```

---

## 📦 Storage Footprint Estimate

**Per Extraction (average):**
- 1 extraction row: ~50 bytes
- 5 newsletter rows: ~5KB (1KB each with subjects/senders)
- 60 article links: ~180KB (3KB each with long tracking URLs)

**Total**: ~185KB per extraction in database

**vs JSON files**: ~200KB (similar)

**Advantage**: Queryable, relational, no ephemeral filesystem issues on Railway.

---

## ✅ Implementation Complete

The minimal 10-column schema has been successfully implemented with:

### Files Created/Modified:
1. **Models**: `app/models/newsletter_extraction.py` (Extraction, EmailContent, ExtractedLink)
2. **CRUD**: `app/crud/newsletter_extraction.py` (create_extraction, get_all_extractions)
3. **Migration**: `alembic/versions/0a3d2a7ef13b_add_newsletter_extraction_models.py`
4. **API**: Updated `app/api/endpoints/newsletters.py`:
   - `/extract` - Now saves to database after pipeline
   - `/extractions` - Now loads from database instead of files

### Verified Database Structure:
```sql
-- ✅ Tables created with correct schema
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('extractions', 'email_content', 'extracted_links')
ORDER BY table_name, ordinal_position;
```

### Test Results:
```
✅ Extraction ID: 20251015_173602
✅ Newsletters: 1 (Alibaba Qwen3-VL models)
✅ Links: 14 (all with tracking URLs resolved)
✅ API Response: Frontend format preserved
✅ Database Storage: All relationships working with CASCADE
```

### Future Enhancements (via Alembic migrations when needed):
- Add `source_type` column to track Gmail vs Reddit vs Web forms
- Add `content_type` column to differentiate newsletter vs plain email
- Add `link_type` column to route to correct extractor (article/YouTube/Reddit)
- Add `metadata` JSON column for source-specific params
- ~~Add `config` JSON column for extraction snapshots~~ → **ADDED** via newsletter_config table

---

## Table 4: `newsletter_config` (5 columns) ✨ NEW

**STATUS: ✅ IMPLEMENTED** (2025-10-15) - Migration: `405f9211eb0a`

### Purpose
Stores persistent newsletter extraction configuration tied to users. Replaces file-based `config.json` for Railway deployments (ephemeral filesystem).

### Schema
```sql
CREATE TABLE newsletter_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE,                  -- FK: users.id (NULL = system default)
    config_data JSONB NOT NULL,              -- Full configuration as JSON
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_newsletter_config_user_id ON newsletter_config(user_id);
```

### Data Example

**Row 1: System Default (Single-User Mode)**
```sql
INSERT INTO newsletter_config (id, user_id, config_data, created_at, updated_at) VALUES (
  1,
  NULL,  -- NULL = system default (no auth required)
  '{
    "newsletters": {
      "enabled": true,
      "sources": [
        {
          "name": "AlphaSignal",
          "email": "news@alphasignal.ai",
          "enabled": true,
          "category": "tech",
          "priority": "high"
        },
        {
          "name": "The Rundown AI",
          "email": "news@daily.therundown.ai",
          "enabled": true,
          "category": "ai",
          "priority": "high"
        }
      ]
    },
    "settings": {
      "default_days_back": 7,
      "max_results": 100,
      "auto_digest": true,
      "extract_links": true
    },
    "content_filtering": {
      "description": "Control which domains/URLs to always accept or reject",
      "whitelist_domains": [
        "techcrunch.com",
        "github.com",
        "arxiv.org",
        "huggingface.co",
        "openai.com"
      ],
      "blacklist_domains": [
        "typeform.com",
        "mailchi.mp",
        "surveymonkey.com"
      ],
      "curator_domains": [
        "alphasignal.ai",
        "therundown.ai"
      ],
      "content_indicators": [
        "/blog/",
        "/article/",
        "/news/",
        "/p/",
        "/2025/",
        "/guides/"
      ]
    }
  }'::jsonb,
  NOW(),
  NOW()
);
```

### Query Examples

**Get system default config:**
```sql
SELECT config_data FROM newsletter_config WHERE user_id IS NULL;
```

**Get whitelist domains:**
```sql
SELECT config_data->'content_filtering'->'whitelist_domains' as whitelist
FROM newsletter_config
WHERE user_id IS NULL;
```

**Check if config exists:**
```sql
SELECT EXISTS(SELECT 1 FROM newsletter_config WHERE user_id IS NULL);
```

**Update config (via API):**
```sql
UPDATE newsletter_config
SET
  config_data = '{...new config...}'::jsonb,
  updated_at = NOW()
WHERE user_id IS NULL;
```

### Why This Table?

**Problem:** Railway's ephemeral filesystem loses config changes on restart.

**Before (File-Based):**
```
User changes config via UI → Saves to config.json → Railway restarts → Changes lost ❌
```

**After (Database):**
```
User changes config via UI → Saves to database → Railway restarts → Changes persist ✅
```

### Workflow

1. **First Request:**
   - Check if `newsletter_config` table has a row with `user_id = NULL`
   - If not, load from `config.json` → Insert into database
   - Return config from database

2. **Subsequent Requests:**
   - Always read from database
   - Updates via `/api/newsletters/config` save to database
   - Changes persist across deployments

3. **Fallback:**
   - If database is empty, fall back to `config.json` (seed data)

### API Integration

**Endpoints:**
- `GET /api/newsletters/config` - Load from database (or seed from file)
- `PUT /api/newsletters/config` - Save to database
- `POST /api/newsletters/config/test-url` - Test filtering rules

**Frontend:**
- Config UI: `http://localhost:3000/newsletters/config`
- Changes save to database via API
- Persistent across Railway restarts

### Multi-User Support (Future)

**Current:**
```
┌────┬─────────┬──────────────────┐
│ id │ user_id │   config_data    │
├────┼─────────┼──────────────────┤
│  1 │  NULL   │ {system config}  │  ← Single user
└────┴─────────┴──────────────────┘
```

**Future (with Auth):**
```
┌────┬─────────┬──────────────────┐
│ id │ user_id │   config_data    │
├────┼─────────┼──────────────────┤
│  1 │  NULL   │ {system config}  │  ← Default
│  2 │    1    │ {user 1 config}  │  ← Custom
│  3 │    2    │ {user 2 config}  │  ← Custom
└────┴─────────┴──────────────────┘
```

Each user can have different:
- Newsletter sources
- Whitelist/blacklist domains
- Content indicators
- Extraction settings

### Files

- **Model**: `app/models/newsletter_extraction.py` (`NewsletterConfig` class)
- **Migration**: `alembic/versions/405f9211eb0a_add_newsletter_config_table.py`
- **Seed**: `seed_newsletter_config.sql`
- **Docs**: `NEWSLETTER_CONFIG_DATABASE.md`
