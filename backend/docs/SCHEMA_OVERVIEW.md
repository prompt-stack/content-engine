# Schema Overview - Content Engine MVP

**STATUS: ✅ PRODUCTION READY** (2025-10-15)

## 📊 Complete Data Model (5 Tables, 41 Columns)

```
┌─────────────────────────────────────────────┐
│  users (22 columns)                         │
│  Owner account with Google OAuth            │
└────┬───────────────────────┬────────────────┘
     │                       │
     │ CASCADE DELETE        │ CASCADE DELETE
     │                       │
     ▼                       ▼
┌──────────────────┐   ┌─────────────────────────┐
│  extractions (5) │   │ newsletter_config (5)   │
│  Pipeline runs   │   │ User settings (JSONB)   │
└────┬─────────────┘   └─────────────────────────┘
     │ CASCADE DELETE
     ▼
┌──────────────────┐
│ email_content (5)│
│  Newsletters     │
└────┬─────────────┘
     │ CASCADE DELETE
     ▼
┌──────────────────┐
│extracted_links(4)│
│ URLs from emails │
└──────────────────┘
```

## 🔗 Relationships

### Hierarchical (Parent → Children)
```sql
users (1) ──► extractions (N)
  ├─ ON DELETE CASCADE
  └─ Index: ix_extractions_user_id

extractions (1) ──► email_content (N)
  ├─ ON DELETE CASCADE
  └─ Index: ix_email_content_extraction_id

email_content (1) ──► extracted_links (N)
  ├─ ON DELETE CASCADE
  └─ Index: ix_extracted_links_content_id
```

### Parallel (User-Specific Configuration)
```sql
users (1) ──► newsletter_config (1)
  ├─ ON DELETE CASCADE
  ├─ UNIQUE constraint on user_id
  └─ Index: ix_newsletter_config_user_id
```

## 📋 Table Summary

| Table | Columns | Role | Sample Row Count |
|-------|---------|------|------------------|
| **users** | 22 | Owner account with OAuth | 1 (you) |
| **newsletter_config** | 5 | Per-user filtering rules | 1 (your config) |
| **extractions** | 5 | Pipeline execution sessions | ~50/month |
| **email_content** | 5 | Newsletters per extraction | ~250/month |
| **extracted_links** | 4 | URLs per newsletter | ~3000/month |

**Total Schema Size:** 41 columns across 5 tables

---

## 🗄️ Table Details

### Table 1: `users` (22 columns)

**Purpose:** Authentication and account management

```sql
CREATE TABLE users (
    -- Core Identity (3)
    id SERIAL PRIMARY KEY,
    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(1024) NOT NULL,

    -- Account Status (3)
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    is_verified BOOLEAN NOT NULL DEFAULT false,

    -- Role & Tier (2)
    role ENUM('USER', 'ADMIN', 'SUPERADMIN', 'OWNER') NOT NULL DEFAULT 'USER',
    tier ENUM('FREE', 'STARTER', 'PRO', 'BUSINESS', 'OWNER') NOT NULL DEFAULT 'FREE',

    -- Usage Tracking (2)
    requests_this_month INTEGER NOT NULL DEFAULT 0,
    requests_reset_at TIMESTAMP,

    -- OAuth (4) ✨ NEW
    oauth_provider VARCHAR(50),        -- "google", "github", etc.
    google_id VARCHAR(255) UNIQUE,     -- Google OAuth subject ID
    google_email VARCHAR(320),         -- Email from Google
    google_picture VARCHAR(512),       -- Profile picture URL

    -- Social Platform Flags (6)
    twitter_connected BOOLEAN NOT NULL DEFAULT false,
    linkedin_connected BOOLEAN NOT NULL DEFAULT false,
    reddit_connected BOOLEAN NOT NULL DEFAULT false,
    youtube_connected BOOLEAN NOT NULL DEFAULT false,
    facebook_connected BOOLEAN NOT NULL DEFAULT false,
    instagram_connected BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps (2)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE UNIQUE INDEX ix_users_google_id ON users(google_id);
```

**Example Data (Your OWNER Account):**
```sql
INSERT INTO users (id, email, role, tier, is_active, is_superuser, is_verified)
VALUES (
    1,
    'you@example.com',
    'OWNER',           -- ← Unlimited access
    'OWNER',           -- ← No rate limits
    true,
    true,
    true
);
```

**Referenced By:**
- `extractions.user_id` (CASCADE)
- `newsletter_config.user_id` (CASCADE)

---

### Table 2: `extractions` (5 columns) ✨ Updated

**Purpose:** One pipeline execution (extract newsletters from Gmail)

```sql
CREATE TABLE extractions (
    -- Core Identity (1)
    id VARCHAR(50) PRIMARY KEY,        -- "20251015_163702" (timestamp)

    -- Ownership (1) ✨ NEW
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Execution Context (2)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    days_back INTEGER,                 -- How many days to look back
    max_results INTEGER                -- Max newsletters to process
);

CREATE INDEX ix_extractions_created_at ON extractions(created_at);
CREATE INDEX ix_extractions_user_id ON extractions(user_id);
```

**Before (Phase 0):**
```sql
extractions (
    id,               -- ✅
    created_at,       -- ✅
    days_back,        -- ✅
    max_results       -- ✅
)
-- No user ownership
```

**After (Phase 1):**
```sql
extractions (
    id,               -- ✅
    user_id,          -- ✨ NEW - ties to owner
    created_at,       -- ✅
    days_back,        -- ✅
    max_results       -- ✅
)
```

**Example Data:**
```sql
-- Your extraction from Oct 15, 2025
INSERT INTO extractions (id, user_id, created_at, days_back, max_results)
VALUES (
    '20251015_163702',
    1,                 -- ← Your user ID
    '2025-10-15 16:37:02',
    7,
    30
);
```

**Referenced By:**
- `email_content.extraction_id` (CASCADE)

---

### Table 3: `email_content` (5 columns)

**Purpose:** One newsletter email from an extraction

```sql
CREATE TABLE email_content (
    -- Core Identity (2)
    id SERIAL PRIMARY KEY,
    extraction_id VARCHAR(50) NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,

    -- Newsletter Metadata (3)
    subject VARCHAR(1024) NOT NULL,    -- "🔥 Alibaba unveils Qwen3-VL..."
    sender VARCHAR(256) NOT NULL,      -- "news@alphasignal.ai"
    date VARCHAR(100) NOT NULL         -- "Wed, 15 Oct 2025 17:03:08 +0000"
);

CREATE INDEX ix_email_content_extraction_id ON email_content(extraction_id);
CREATE INDEX ix_email_content_sender ON email_content(sender);
```

**Example Data:**
```sql
INSERT INTO email_content (id, extraction_id, subject, sender, date)
VALUES (
    1,
    '20251015_163702',
    '🔥 Alibaba unveils compact Qwen3-VL models that rival GPT-5 Nano',
    'news@alphasignal.ai',
    'Wed, 15 Oct 2025 17:03:08 +0000'
);
```

**Referenced By:**
- `extracted_links.content_id` (CASCADE)

---

### Table 4: `extracted_links` (4 columns)

**Purpose:** One URL extracted from a newsletter

```sql
CREATE TABLE extracted_links (
    -- Core Identity (2)
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES email_content(id) ON DELETE CASCADE,

    -- URL Data (2)
    url TEXT NOT NULL,                 -- Final resolved URL
    original_url TEXT                  -- Tracking/redirect URL (if different)
);

CREATE INDEX ix_extracted_links_content_id ON extracted_links(content_id);
```

**Example Data:**
```sql
INSERT INTO extracted_links (id, content_id, url, original_url)
VALUES (
    1,
    1,
    'https://huggingface.co/collections/Qwen/qwen3-vl-68d2a7c1b8a8afce4ebd2dbe',
    'https://app.alphasignal.ai/c?uid=1CMu2MCSvWZouF4ld&cid=05be88743bf5d704&lid=vhqNakjKI4qFG0eX'
);
```

**Why Store Both URLs?**
- `url` = Clean link for content extraction
- `original_url` = Attribution/tracking (curator gets credit)

---

### Table 5: `newsletter_config` (5 columns)

**Purpose:** Per-user configuration (filtering rules, sources, settings)

```sql
CREATE TABLE newsletter_config (
    -- Core Identity (2)
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Configuration (1)
    config_data JSON NOT NULL,         -- Full config as JSON

    -- Timestamps (2)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ix_newsletter_config_user_id ON newsletter_config(user_id);
```

**Example Data:**
```sql
INSERT INTO newsletter_config (id, user_id, config_data, created_at, updated_at)
VALUES (
    1,
    1,  -- Your user ID
    '{
      "newsletters": {
        "enabled": true,
        "sources": [
          {"name": "AlphaSignal", "email": "news@alphasignal.ai", "enabled": true}
        ]
      },
      "content_filtering": {
        "whitelist_domains": ["github.com", "arxiv.org", "huggingface.co"],
        "blacklist_domains": ["typeform.com", "surveymonkey.com"],
        "curator_domains": ["alphasignal.ai", "therundown.ai"],
        "content_indicators": ["/blog/", "/article/", "/2025/"]
      }
    }'::json,
    NOW(),
    NOW()
);
```

---

## 📈 Query Examples

### Get all YOUR extractions with stats
```sql
SELECT
    e.id,
    e.created_at,
    COUNT(DISTINCT ec.id) as newsletter_count,
    COUNT(el.id) as total_links
FROM extractions e
LEFT JOIN email_content ec ON e.extraction_id = ec.extraction_id
LEFT JOIN extracted_links el ON ec.id = el.content_id
WHERE e.user_id = 1  -- You
GROUP BY e.id, e.created_at
ORDER BY e.created_at DESC;
```

### Get all links from AlphaSignal (across all extractions)
```sql
SELECT
    e.id as extraction_id,
    e.created_at,
    ec.subject,
    el.url
FROM extracted_links el
JOIN email_content ec ON el.content_id = ec.id
JOIN extractions e ON ec.extraction_id = e.id
WHERE e.user_id = 1
  AND ec.sender = 'news@alphasignal.ai'
ORDER BY e.created_at DESC;
```

### Delete an entire extraction (CASCADE)
```sql
-- This automatically deletes:
-- - All email_content rows for this extraction
-- - All extracted_links for those newsletters
DELETE FROM extractions WHERE id = '20251015_163702';
```

### Get your config
```sql
SELECT config_data
FROM newsletter_config
WHERE user_id = 1;
```

---

## 🔄 Migration History

### Migration 1: Initial Extraction Models
**File:** `0a3d2a7ef13b_add_newsletter_extraction_models.py`
**Date:** 2025-10-15

**Created:**
- `extractions` (4 columns: id, created_at, days_back, max_results)
- `email_content` (5 columns: id, extraction_id, subject, sender, date)
- `extracted_links` (4 columns: id, content_id, url, original_url)

**Purpose:** Enable database persistence for newsletter extractions

---

### Migration 2: Add Newsletter Config Table
**File:** `405f9211eb0a_add_newsletter_config_table.py`
**Date:** 2025-10-15

**Created:**
- `newsletter_config` (5 columns: id, user_id, config_data, created_at, updated_at)

**Purpose:** Persist configuration across Railway restarts (ephemeral filesystem fix)

---

### Migration 3: Add User Authentication ✨ Current
**File:** `ac4b2ff42914_add_user_authentication_user_id_to_.py`
**Date:** 2025-10-15

**Added to `extractions`:**
- `user_id INTEGER` FK → users.id (CASCADE)

**Added to `users`:**
- `oauth_provider VARCHAR(50)`
- `google_id VARCHAR(255)` (UNIQUE)
- `google_email VARCHAR(320)`
- `google_picture VARCHAR(512)`

**Purpose:** Tie extractions to authenticated users, enable Google OAuth

---

## ✅ CASCADE Delete Behavior

Understanding the cascade is critical for data management:

### Scenario 1: Delete User (You)
```sql
DELETE FROM users WHERE id = 1;
```

**Cascades:**
1. ✅ All `extractions` for user_id=1 deleted
2. ✅ All `email_content` for those extractions deleted
3. ✅ All `extracted_links` for those newsletters deleted
4. ✅ `newsletter_config` for user_id=1 deleted

**Result:** Complete data wipe (be careful!)

---

### Scenario 2: Delete Extraction
```sql
DELETE FROM extractions WHERE id = '20251015_163702';
```

**Cascades:**
1. ✅ All `email_content` for extraction_id='20251015_163702' deleted
2. ✅ All `extracted_links` for those newsletters deleted

**NOT Affected:**
- ❌ User account (stays)
- ❌ Other extractions (stay)
- ❌ Newsletter config (stays)

---

### Scenario 3: Delete Newsletter
```sql
DELETE FROM email_content WHERE id = 1;
```

**Cascades:**
1. ✅ All `extracted_links` for content_id=1 deleted

**NOT Affected:**
- ❌ Extraction (stays)
- ❌ Other newsletters from same extraction (stay)

---

## 🎯 Storage Estimates

**Per Month (Typical Usage):**
- 1 extraction/day × 30 days = 30 extractions
- 5 newsletters/extraction × 30 = 150 email_content rows
- 60 links/extraction × 30 = 1,800 extracted_links rows

**Database Size:**
- Extractions: 30 rows × 100 bytes = 3 KB
- Email Content: 150 rows × 1 KB = 150 KB
- Extracted Links: 1,800 rows × 3 KB = 5.4 MB
- **Total/Month:** ~5.5 MB

**Annual:** ~66 MB (easily fits in any database tier)

---

## 🚀 API Integration

### Extraction Endpoints
- `POST /api/newsletters/extract` - Create extraction (ties to authenticated user)
- `GET /api/newsletters/extractions` - List user's extractions

### Config Endpoints
- `GET /api/newsletters/config` - Get user's config
- `PUT /api/newsletters/config` - Update user's config

### Auth Endpoints (Future)
- `POST /api/auth/google` - Google OAuth login
- `GET /api/auth/me` - Get current user

---

## 📚 Related Documentation

- **SCHEMA_DATA_MAPPING.md** - Detailed examples with real data
- **NEWSLETTER_CONFIG_DATABASE.md** - Config table specifics
- **ENV_SETUP.md** - Local vs Railway environment setup
- **Migration Files** - `alembic/versions/`

---

## ✅ Production Readiness Checklist

- [x] All foreign keys have CASCADE delete
- [x] All tables indexed appropriately
- [x] User authentication ready (OAuth fields)
- [x] Config persists across deployments
- [x] Extractions tied to users
- [x] Query patterns optimized
- [x] Migration history documented
- [ ] User account created (run `create_owner_user.py`)
- [ ] Google OAuth configured
- [ ] Frontend authentication integrated

**Schema Status:** Production Ready for Single-User MVP 🎉
