# Newsletter Article Extractor

Extract article links from newsletter emails, resolve tracking URLs, and prepare for content extraction.

---

## Quick Start

```bash
# 1. Extract and resolve links from specific newsletters
python3.11 resolve_links.py --days 7 --senders @therundown.ai @alphasignal.ai

# 2. Extract content from resolved links
python3.11 batch_extract.py --input output/resolved_links_TIMESTAMP.json

# 3. View results in RSS feed
open http://localhost:3456/newsletters/feed
```

---

## Directory Structure

```
email/
├── 📄 PRODUCTION FILES
│   ├── gmail_extractor.py       Gmail API integration
│   ├── resolve_links.py         Main pipeline (extract → filter → resolve)
│   └── batch_extract.py         Content extraction via API
│
├── 🗂️ CONFIGURATION
│   ├── credentials.json         Gmail OAuth credentials (not in git)
│   ├── token.pickle             Auth token (not in git)
│   ├── config.json              App configuration
│   └── manage_config.py         Config management utility
│
├── 📚 DOCUMENTATION
│   ├── README.md                     This file
│   ├── PIPELINE_DOCUMENTATION.md     Complete pipeline breakdown
│   └── FILTERING_EXPLAINED.md        Filtering logic with examples
│
├── 🗄️ DIRECTORIES
│   ├── output/                  Extracted data
│   │   ├── raw_html/            Raw newsletter HTML
│   │   ├── resolved_links_*.json    Resolved article links
│   │   ├── resolved_links_*.txt     Human-readable format
│   │   └── extracted_articles/      Full article content
│   │
│   ├── _debug/                  Debug & test scripts
│   ├── _archive/                Deprecated code
│   └── _old_backup/             Old backup files
```

---

## Pipeline Overview

### 1. Gmail → Extract Newsletters
```python
extractor = GmailExtractor()
newsletters = extractor.search_newsletters(
    days_back=7,
    sender_filter=['@therundown.ai']
)
```
**Output:** List of newsletters with HTML content

---

### 2. HTML → Extract Links
```python
# Find all href="..." in HTML
links = re.findall(r'href=["\']([^"\']+)["\']', html)

# Decode HTML entities (&amp; → &)
links = [html.unescape(link) for link in links]
```
**Output:** Decoded URLs from newsletter

---

### 3. Filter Junk
```python
# Remove unsubscribe, mailto:, images, etc.
links = [link for link in links if not is_obvious_junk(link)]
```
**Output:** Candidate article links

---

### 4. Prioritize
```python
# Separate direct links from tracking links
direct_links = [...]  # github.com, arxiv.org, news sites
tracking_links = [...] # link.domain.com, /c?uid=...

# Process direct links first
prioritized = direct_links + tracking_links
```
**Output:** Ordered list (articles first)

---

### 5. Resolve Redirects
```python
# Follow tracking links to final destination
final_url = requests.head(tracking_url, allow_redirects=True).url
```
**Output:** Real article URLs

---

### 6. Validate Content
```python
# Check if final URL is actual content
if is_content_url(final_url):
    keep_link()
```
**Checks:**
- ❌ Homepages
- ❌ Social media profiles
- ❌ Sponsor/ad pages
- ✅ Articles with content indicators
- ✅ Known news domains

---

### 7. Save Results
**Three file formats:**
1. `resolved_links_*.json` - Full data with context
2. `resolved_links_*.txt` - Human-readable
3. `article_urls_*.txt` - Just URLs

---

## Usage Examples

### Basic: Get all newsletters
```bash
python3.11 resolve_links.py --days 7
```

### Filtered: Specific newsletters only
```bash
python3.11 resolve_links.py --days 7 --senders @therundown.ai @alphasignal.ai
```

### Limited: Fewer results
```bash
python3.11 resolve_links.py --days 3 --max 5
```

### Extract content from resolved links
```bash
python3.11 batch_extract.py --input output/resolved_links_20251015_123456.json
```

---

## File Sizes & Performance

### Code Files
- `gmail_extractor.py` - 18K (Gmail API wrapper)
- `resolve_links.py` - 14K (main pipeline)
- `batch_extract.py` - 10K (content extraction)

### Performance
- **Speed:** 30-60 seconds per newsletter
- **Bottleneck:** HTTP redirects (30 links × 1s each)
- **Rate limits:** 30 links processed per newsletter

### Output Files
- **JSON:** ~1-50KB per newsletter (depends on link count)
- **TXT:** Human-readable version
- **HTML:** Raw newsletter (50-150KB)

---

## Understanding the Filters

Read `FILTERING_EXPLAINED.md` for detailed walkthrough with real examples.

### Key Concepts

1. **HTML Entity Decoding**
   ```
   BROKEN:  url?id=123&amp;ref=email
   FIXED:   url?id=123&ref=email
   ```
   Without decoding, `&amp;` breaks URL parameters.

2. **Direct vs Tracking Links**
   - Direct: `github.com/user/repo` (process first)
   - Tracking: `link.site.com/xyz` (needs redirect)

3. **Content Validation**
   - ✅ `techcrunch.com/2025/10/15/article` (article)
   - ❌ `techcrunch.com` (homepage)
   - ✅ `twitter.com/user/status/123` (tweet)
   - ❌ `twitter.com/user` (profile)

4. **Domain-Specific Rules**
   - GitHub: Must have user/repo
   - Twitter: Must have /status/ (tweet)
   - Medium: Must have /@author or /p/post

---

## Common Issues

### Issue: Few articles found
**Cause:** Most tracking links redirect to non-content (homepage, sponsor)
**Solution:** This is expected! Newsletters have many junk links.

### Issue: Missing articles
**Cause:** Filters too strict
**Solution:** Check `FILTERING_EXPLAINED.md`, adjust `is_content_url()`

### Issue: Duplicates
**Cause:** Same article linked multiple times
**Solution:** Already handled by deduplication (lines 314-319)

### Issue: Timeout errors
**Cause:** Slow redirects or network issues
**Solution:** Increase timeout in `resolve_redirect()` function

---

## Testing & Debugging

### View extraction flow
```bash
python3.11 _debug/show_extraction_flow.py
```
Shows step-by-step: extract → decode → filter → prioritize

### View raw HTML
```bash
python3.11 _debug/show_raw_html.py
```
Saves newsletter HTML to `output/raw_html/`

### Test specific sender
```bash
python3.11 _debug/debug_alpha_links.py
```
Debug Alpha Signal link extraction

### Test connection
```bash
python3.11 _debug/test_connection.py
```
Verify Gmail API authentication

---

## Configuration

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials
4. Download as `credentials.json`
5. First run will open browser for auth
6. Token saved to `token.pickle`

### Newsletter Filters

Edit `resolve_links.py` to customize:

**Add news domains** (line 155):
```python
news_domains = [
    'techcrunch.com',
    'yourcustomsite.com',  # Add here
]
```

**Add content indicators** (line 145):
```python
content_indicators = [
    '/blog/',
    '/your-pattern/',  # Add here
]
```

**Adjust tracking domains** (line 288):
```python
tracking_domains = [
    'link.',
    'yourdomain.com/track/',  # Add here
]
```

---

## Architecture Decisions

### Why separate files?
- `gmail_extractor.py` - Reusable Gmail API wrapper
- `resolve_links.py` - Pure link processing logic
- `batch_extract.py` - Content extraction (separate concern)

### Why prioritize direct links?
- More likely to be articles
- 30-link limit per newsletter
- Avoids wasting time on tracking redirects

### Why decode HTML entities?
- `&amp;` in URLs breaks query parameters
- Must decode BEFORE filtering
- Standard HTML encoding issue

### Why validate final URL?
- Tracking links often redirect to:
  - Homepage (not article)
  - Sponsor page (ad)
  - Social profile (not content)
- Must check destination, not source

---

## Next Steps

### Short Term
1. ✅ Organize code (DONE)
2. ✅ Document pipeline (DONE)
3. ⏳ Add unit tests
4. ⏳ Split resolve_links.py into modules

### Long Term
1. Frontend integration (RSS feed viewer)
2. Database storage for history
3. ML-based content detection
4. Parallel processing for speed

---

## Resources

- **Gmail API Docs:** https://developers.google.com/gmail/api
- **OAuth2 Guide:** https://developers.google.com/identity/protocols/oauth2
- **Regex Tester:** https://regex101.com/
- **URL Parser:** https://www.urlparser.io/

---

## Support

Issues? Check:
1. `PIPELINE_DOCUMENTATION.md` - Complete pipeline breakdown
2. `FILTERING_EXPLAINED.md` - Filtering logic with examples
3. `_debug/` scripts - Test individual components

---

## Summary

This pipeline extracts **real article links** from newsletter emails by:

1. 📧 Connecting to Gmail
2. 🔍 Finding href links in HTML
3. 🔧 Decoding HTML entities
4. 🚮 Filtering junk
5. ⚡ Prioritizing direct links
6. 🔄 Resolving tracking redirects
7. ✅ Validating final content
8. 💾 Saving with context

Result: Clean list of article URLs organized by newsletter, ready for content extraction!
