# Newsletter Link Extraction Pipeline

## Overview
This pipeline extracts article links from newsletter emails in Gmail, resolves tracking URLs, and filters to only keep real article content.

---

## Directory Structure

```
email/
├── Core Files (Production)
│   ├── gmail_extractor.py      (18K) - Gmail API integration
│   ├── resolve_links.py         (14K) - Main pipeline: extract & resolve links
│   └── batch_extract.py         (10K) - Pass resolved links to content-engine
│
├── Utilities
│   ├── manage_config.py         (6.6K) - Config management
│   └── test_connection.py       (2.1K) - Test Gmail connection
│
├── Debug/Testing (Can be cleaned up)
│   ├── debug_alpha_links.py     (949B)
│   ├── debug_alpha_tracking.py  (1.8K)
│   ├── show_extraction_flow.py  (3.2K)
│   ├── show_raw_html.py         (1.2K)
│   └── test_alpha_fix.py        (946B)
│
├── Deprecated (Should be archived)
│   ├── extract_links.py         (6.0K) - Old version
│   ├── extract_simple.py        (3.6K) - Old version
│   └── extract.py               (3.5K) - Old version
│
└── output/
    ├── raw_html/                - Newsletter HTML files
    ├── resolved_links_*.json    - Resolved article links (with context)
    ├── resolved_links_*.txt     - Human-readable format
    └── article_urls_*.txt       - Just URLs (for reference)
```

---

## Pipeline Stages

### STAGE 1: Gmail Extraction
**File:** `gmail_extractor.py`
**Input:** Gmail credentials, search parameters
**Output:** List of newsletter dictionaries with HTML

**What it does:**
1. Authenticates with Gmail API (OAuth2)
2. Searches for newsletters matching criteria
3. Fetches full email content (headers + HTML body)
4. Returns structured data

**Search filters:**
- Date range (days_back)
- Sender filter (specific domains/emails)
- Newsletter indicators (list headers, unsubscribe links)

---

### STAGE 2: Link Extraction
**File:** `resolve_links.py` (Lines 271-278)
**Input:** Newsletter HTML
**Output:** List of all href URLs

**What it does:**
1. **EXTRACT** - Find all `href="..."` patterns using regex
   ```python
   link_pattern = r'href=["\']([^"\']+)["\']'
   raw_links = re.findall(link_pattern, body_html)
   ```

2. **DECODE** - Fix HTML entities
   ```python
   raw_links = [html.unescape(link) for link in raw_links]
   ```
   - `&amp;` → `&`
   - `&quot;` → `"`
   - `&lt;` → `<`

**Example:**
```
BEFORE: https://track.com?id=123&amp;ref=email
AFTER:  https://track.com?id=123&ref=email
```

---

### STAGE 3: Filter Obvious Junk
**File:** `resolve_links.py` (Function: `is_obvious_junk()`)
**Input:** List of decoded URLs
**Output:** Filtered list (junk removed)

**What gets filtered out:**
- Unsubscribe links
- Preference/settings pages
- mailto: and tel: links
- Image files (.png, .jpg, .gif, .svg)
- Favicons
- CDN URLs (/cdn-cgi/)
- Email preference pages

**Why:** These are never article content, so we skip them early to save time.

---

### STAGE 4: Separate & Prioritize
**File:** `resolve_links.py` (Lines 283-296)
**Input:** Filtered candidate links
**Output:** Two lists: direct_links (first) + tracking_links (second)

**Direct links** (processed FIRST):
- github.com/user/repo
- arxiv.org/abs/12345
- techcrunch.com/article
- News site URLs

**Tracking links** (processed SECOND):
- link.alphasignal.ai/*
- app.newsletter.com/c?uid=...
- track.example.com/click?id=...

**Why prioritize?**
- Direct links are more likely to be articles
- We have a 30-link limit per newsletter
- By processing direct links first, we get the important articles before hitting the limit

---

### STAGE 5: Resolve Redirects
**File:** `resolve_links.py` (Function: `resolve_redirect()`)
**Input:** Tracking URL
**Output:** Final destination URL after following redirects

**How it works:**
1. Make HTTP HEAD request (doesn't download content, just headers)
2. Follow all redirects automatically
3. Get final destination URL
4. If HEAD fails, try GET (some servers don't support HEAD)
5. Timeout after 10 seconds

**Example:**
```
INPUT:  https://link.alphasignal.ai/xyz123
OUTPUT: https://techcrunch.com/2025/10/14/ai-breakthrough
```

---

### STAGE 6: Content URL Validation
**File:** `resolve_links.py` (Function: `is_content_url()`)
**Input:** Final destination URL (after redirect)
**Output:** True/False - is this real content?

**Checks performed:**

#### ❌ Reject if:
1. **Homepage only** - No path after domain (example.com/)
2. **Sponsor/Ad domains** - airia.com, typeform.com, mailchi.mp
3. **App stores** - apps.apple.com, play.google.com
4. **Social media profiles** - twitter.com/username (no /status/)
5. **Account pages** - /account, /settings, /profile, /login
6. **Company pages** - linkedin.com/company/, youtube.com/channel/

#### ✅ Accept if:
1. **Known news domains**:
   - techcrunch.com, theverge.com, wired.com
   - reuters.com, bloomberg.com, nytimes.com
   - github.com (repos only), arxiv.org

2. **Has content indicators in path**:
   - /blog/, /article/, /news/, /post/, /story/
   - /2024/, /2025/ (date-based URLs)
   - /p/ (Medium/Substack posts)
   - /status/ (tweets)
   - /watch?v= (YouTube videos)

3. **Special domain rules**:
   - GitHub: Must have user/repo (at least 1 slash in path)
   - Twitter: Must have /status/ (actual tweet, not profile)
   - Medium: Must have /@author or /p/post

**Example checks:**
```
✅ github.com/karpathy/nanochat          - Has user/repo
❌ github.com                             - Just homepage
✅ twitter.com/user/status/123           - Specific tweet
❌ twitter.com/user                       - Profile page
✅ techcrunch.com/2025/10/14/article    - News site with date
❌ techcrunch.com                         - Homepage
```

---

### STAGE 7: Deduplicate
**File:** `resolve_links.py` (Lines 308-320)
**Input:** List of validated article URLs
**Output:** Unique list (duplicates removed)

**How:**
- Check if URL already in resolved_links list
- If duplicate, skip it
- If unique, add to list

**Why duplicates happen:**
- Same article linked multiple times in newsletter
- Different tracking links → same final URL
- Newsletter navigation repeats links

---

### STAGE 8: Save Results
**File:** `resolve_links.py` (Lines 330-362)
**Input:** List of resolved articles with newsletter context
**Output:** 3 files

**Files created:**
1. **resolved_links_TIMESTAMP.json** - Full data with context
   ```json
   [
     {
       "newsletter_subject": "🔥 AI News",
       "newsletter_sender": "news@ai.com",
       "newsletter_date": "Oct 15, 2025",
       "links": [
         {"url": "https://...", "original_url": "https://track..."}
       ],
       "link_count": 10
     }
   ]
   ```

2. **resolved_links_TIMESTAMP.txt** - Human-readable
   ```
   📧 🔥 AI News
      From: news@ai.com
      Date: Oct 15, 2025
      Articles (10):

      • https://article1.com
      • https://article2.com
   ```

3. **article_urls_TIMESTAMP.txt** - Just URLs (one per line)
   ```
   https://article1.com
   https://article2.com
   ```

---

## Pipeline Flow Diagram

```
Gmail → Extract HTML → Find hrefs → Decode entities
                                         ↓
                               Filter obvious junk
                                         ↓
                        Separate: Direct | Tracking
                                         ↓
                        Prioritize: Direct FIRST
                                         ↓
                              Resolve redirects
                                         ↓
                         Check: Is content URL?
                                         ↓
                              Remove duplicates
                                         ↓
                           Save with context
```

---

## Usage Examples

### 1. Get all newsletters (last 7 days)
```bash
python3.11 resolve_links.py --days 7
```

### 2. Get specific newsletters only
```bash
python3.11 resolve_links.py --days 7 --senders @therundown.ai @alphasignal.ai
```

### 3. Extract content from resolved links
```bash
python3.11 batch_extract.py --input output/resolved_links_20251015_123456.json
```

---

## Performance Characteristics

**Speed:**
- ~30-60 seconds per newsletter (depends on link count)
- Bottleneck: HTTP requests to resolve tracking links
- 10-second timeout per link

**Limits:**
- 30 links processed per newsletter (to avoid rate limits)
- Direct links processed first (most important)

**Rate limiting:**
- Gmail API: 250 quota units per user per second
- HTTP redirects: No built-in rate limit, but timeout protects

---

## Common Issues & Solutions

### Issue: Few articles found
**Cause:** Tracking links not resolving or timing out
**Solution:** Check network connection, increase timeout

### Issue: Wrong articles extracted
**Cause:** Content filters too strict/loose
**Solution:** Adjust `is_content_url()` checks

### Issue: HTML entities breaking links
**Cause:** Missing `html.unescape()`
**Solution:** Already fixed in line 278

### Issue: Duplicate articles
**Cause:** Same URL from different tracking links
**Solution:** Deduplication in place (lines 314-319)

---

## File Size Guidelines

- **gmail_extractor.py**: 18K (Gmail API wrapper - good)
- **resolve_links.py**: 14K (main pipeline - could split into modules)
- **batch_extract.py**: 10K (content extraction - good)

**Recommendation:** Consider splitting resolve_links.py into:
- `link_extractor.py` - Extract & decode
- `link_filter.py` - All filtering functions
- `link_resolver.py` - Redirect resolution
- `pipeline.py` - Orchestration

---

## Next Steps

1. **Cleanup** - Move deprecated files to _archive/
2. **Refactor** - Split resolve_links.py into modules
3. **Testing** - Add unit tests for each stage
4. **Documentation** - Add docstrings to all functions
5. **Frontend** - Integrate with RSS feed viewer
