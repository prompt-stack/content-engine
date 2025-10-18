# Database Schema Documentation

## Table Overview

The Content Engine uses 8 core tables organized around user authentication, content capture, newsletter extraction, and content processing.

---

## 1. USERS

**Purpose:** Central authentication and user management table

**Used In:**
- `app/models/user.py` - User model definition
- `app/api/deps.py` - Authentication dependencies
- `app/crud/capture.py` - Capture ownership
- All API endpoints requiring authentication

**User Flows:**
1. **MVP Mode (Current):** Auto-creates OWNER user on first request
2. **Future:** OAuth login via Google, GitHub
3. **Future:** Social platform connections (Twitter, Reddit, etc.)

**Key Features:**
- **Tiered system:** FREE, STARTER, PRO, BUSINESS, OWNER
- **Role-based access:** USER, ADMIN, SUPERADMIN, OWNER
- **Rate limiting:** `requests_this_month` tracks API usage
- **OAuth ready:** Google fields present, others prepared

**Indexes:**
- `email` (unique)
- `google_id` (unique)

---

## 2. CAPTURES

**Purpose:** Direct content storage from iOS Shortcuts and manual input

**Used In:**
- `app/models/capture.py` - Capture model
- `app/crud/capture.py` - CRUD operations
- `app/api/endpoints/capture.py` - REST API
- `frontend/src/components/features/vault/` - Vault UI

**User Flows:**
1. **iOS Shortcut:** Share ChatGPT conversation → POST to `/api/capture/text`
2. **Manual Input:** Paste content in web UI → Save to vault
3. **View Vault:** Browse all saved captures at `/vault`

**Key Features:**
- Flexible `meta` JSONB field for any metadata (device, source, timestamp)
- Title is optional but indexed for search
- Cascades on user deletion

**Indexes:**
- `user_id`
- `created_at` (for chronological listing)
- `title` (for search)

**Example Data:**
```json
{
  "id": 14,
  "title": "iOS Capture",
  "content": "AI's Climate Problem Is Real...",
  "meta": {
    "device": "iPhone",
    "source": "chatgpt"
  },
  "created_at": "2025-10-16T22:44:04"
}
```

---

## 3. EXTRACTIONS

**Purpose:** Newsletter extraction session tracking

**Used In:**
- `app/models/newsletter_extraction.py` - Extraction model
- `backend/extractors/email/resolve_links.py` - Gmail extractor
- `app/api/endpoints/newsletters.py` - REST API
- `frontend/src/app/newsletters/` - Newsletter feed UI

**User Flows:**
1. **Run Extraction:** `python resolve_links.py --days 3 --max 10`
2. **View Extractions:** GET `/api/newsletters/extractions`
3. **Browse Links:** Navigate newsletter feed UI

**Key Features:**
- String ID format: `YYYYMMDD_HHMMSS` (e.g., `20251016_163356`)
- Stores Gmail-specific params (`days_back`, `max_results`)
- Future-proof: Can add params for other sources

**Indexes:**
- `created_at`
- `user_id`

**Example Data:**
```json
{
  "id": "20251016_163356",
  "user_id": 1,
  "days_back": 3,
  "max_results": 10,
  "created_at": "2025-10-16T16:33:56"
}
```

---

## 4. EMAIL_CONTENT

**Purpose:** Individual emails extracted from Gmail

**Used In:**
- `app/models/newsletter_extraction.py` - EmailContent model
- `backend/extractors/email/resolve_links.py` - Email parser
- `app/crud/newsletter_extraction.py` - CRUD operations

**User Flows:**
1. Gmail extractor fetches emails matching criteria
2. Parses subject, sender, date
3. Stores as EMAIL_CONTENT record
4. Extracts links → EXTRACTED_LINKS

**Key Features:**
- One extraction can have multiple emails
- Sender indexed for filtering by source
- Date stored as ISO string for flexibility

**Indexes:**
- `extraction_id`
- `sender`

**Example Data:**
```json
{
  "id": 1,
  "extraction_id": "20251016_163356",
  "subject": "The Rundown AI: Today's Top Stories",
  "sender": "crew@therundown.ai",
  "date": "2025-10-16T09:00:00"
}
```

---

## 5. EXTRACTED_LINKS

**Purpose:** Clean, resolved URLs from newsletters

**Used In:**
- `app/models/newsletter_extraction.py` - ExtractedLink model
- `backend/extractors/email/resolve_links.py` - Link resolver
- `app/crud/newsletter_extraction.py` - Link aggregation

**User Flows:**
1. Extract raw links from email HTML
2. Resolve tracking URLs → final destination
3. Store both original and resolved URLs
4. Display in newsletter feed
5. **Future:** Feed into article/video extractors

**Key Features:**
- Tracks original tracking URLs (for debugging)
- Stores final resolved URL (for extraction)
- Cascades when email deleted

**Indexes:**
- `content_id`

**Example Data:**
```json
{
  "id": 42,
  "content_id": 1,
  "original_url": "https://therundown.ai/link/XYZ123",
  "url": "https://techcrunch.com/2025/10/16/ai-breakthrough"
}
```

---

## 6. NEWSLETTER_CONFIG

**Purpose:** Per-user extractor configuration

**Used In:**
- `app/models/newsletter_extraction.py` - NewsletterConfig model
- `app/api/endpoints/newsletters.py` - Config API
- `backend/extractors/email/resolve_links.py` - Config loading
- `frontend/src/app/newsletters/config/` - Config UI

**User Flows:**
1. **View Config:** GET `/api/newsletters/config`
2. **Edit Filters:** Update whitelist/blacklist domains
3. **Save:** POST `/api/newsletters/config`
4. **Run Extraction:** Uses saved config

**Key Features:**
- One config per user (unique constraint)
- Falls back to `config.json` if no user config
- Stores entire config as JSON for flexibility

**Example Data:**
```json
{
  "id": 1,
  "user_id": 1,
  "config_data": {
    "sources": {
      "gmail_newsletters": {
        "enabled": true,
        "default_days": 3,
        "default_max": 10,
        "senders": ["@therundown.ai", "@alphasignal.ai"]
      }
    },
    "content_filtering": {
      "whitelist_domains": ["techcrunch.com", "bloomberg.com"],
      "blacklist_domains": ["ads.google.com"]
    }
  },
  "created_at": "2025-10-15T12:00:00",
  "updated_at": "2025-10-16T14:30:00"
}
```

---

## 7. CONTENTS (Future Feature)

**Purpose:** Extracted content from social platforms and articles

**Used In:**
- `app/models/content.py` - Content model
- **NOT ACTIVELY USED YET**

**Planned User Flows:**
1. Submit URL via extract form
2. Platform auto-detected (YouTube, Reddit, TikTok, Article)
3. Content extracted and stored
4. LLM processes content → summary, entities, sentiment
5. Display in content feed

**Key Features:**
- Multi-platform support (6 platforms)
- Status tracking (PENDING → EXTRACTING → PROCESSING → COMPLETED/FAILED)
- LLM processing results stored inline
- **NOTE:** Contains typo `content_content_metadata` (should be `content_metadata`)

**Indexes:**
- `url`

**Status:** Not implemented in current flows

---

## 8. NEWSLETTERS (Future Feature)

**Purpose:** LLM-generated newsletter digests

**Used In:**
- `app/models/content.py` - Newsletter model
- **NOT ACTIVELY USED YET**

**Planned User Flows:**
1. Select multiple CONTENTS
2. Generate digest via LLM
3. Store as NEWSLETTER
4. Email to user (future)

**Key Features:**
- Links back to source content IDs
- Tracks source count
- Stores generation metadata

**Status:** Not implemented in current flows

---

## Relationship Summary

```
USER
├── CAPTURES (1:many) - Direct content storage
├── EXTRACTIONS (1:many) - Newsletter extraction sessions
│   └── EMAIL_CONTENT (1:many) - Individual emails
│       └── EXTRACTED_LINKS (1:many) - Resolved URLs
├── NEWSLETTER_CONFIG (1:1) - User-specific extraction config
├── CONTENTS (1:many) - Platform content [FUTURE]
└── NEWSLETTERS (1:many) - Generated digests [FUTURE]
```

---

## Active Tables (Current MVP)

| Table | Status | API Endpoints | Frontend Pages |
|-------|--------|---------------|----------------|
| USERS | ✅ Active | `/api/capture/*`, `/health` | All pages |
| CAPTURES | ✅ Active | `/api/capture/*` | `/vault` |
| EXTRACTIONS | ✅ Active | `/api/newsletters/extractions` | `/newsletters` |
| EMAIL_CONTENT | ✅ Active | `/api/newsletters/extractions` | `/newsletters` |
| EXTRACTED_LINKS | ✅ Active | `/api/newsletters/extractions` | `/newsletters` |
| NEWSLETTER_CONFIG | ✅ Active | `/api/newsletters/config` | `/newsletters/config` |
| CONTENTS | ⏳ Planned | Not implemented | Not implemented |
| NEWSLETTERS | ⏳ Planned | Not implemented | Not implemented |

---

## Migration History

1. **`0a3d2a7ef13b`** - Initial schema (all 8 tables)
2. **`405f9211eb0a`** - Add NEWSLETTER_CONFIG table
3. **`ac4b2ff42914`** - Add user_id to EXTRACTIONS + Google OAuth fields
4. **`8d3e0fed9597`** - Add CAPTURES table
5. **`a27f6d4becae`** - Rename `metadata` → `meta` in CAPTURES
6. **`f7a91c41953b`** - Add index to CAPTURES.title

---

## Database Connections

**Local Development:**
- PostgreSQL: `localhost:5433`
- Database: `content_vault`
- Migrations: `alembic upgrade head`

**Production (Railway):**
- PostgreSQL: Internal Railway network
- Redis: Internal Railway network (for rate limiting)
- Auto-deployed via GitHub push
