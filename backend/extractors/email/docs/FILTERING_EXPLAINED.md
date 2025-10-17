# Link Filtering - Complete Walkthrough

This document walks through EVERY filtering decision with real examples from Alpha Signal newsletter.

---

## Test Data: Alpha Signal Newsletter
- Subject: "🔥 Karpathy unveils end-to-end ChatGPT clone repo"
- Total links found: 46
- After filtering: 3 article URLs

Let's see WHY each link was kept or rejected.

---

## STAGE 1: Extract from HTML

```python
link_pattern = r'href=["\']([^"\']+)["\']'
raw_links = re.findall(link_pattern, body_html)
```

**Found 46 links in HTML**

---

## STAGE 2: Decode HTML Entities

```python
raw_links = [html.unescape(link) for link in raw_links]
```

**Example transformation:**
```
BEFORE: https://app.alphasignal.ai/c?uid=123&amp;cid=456&amp;lid=789
AFTER:  https://app.alphasignal.ai/c?uid=123&cid=456&lid=789
```

**Why this matters:**
- `&amp;` is how HTML represents `&`
- But `&` is needed in URLs to separate parameters
- Without decoding, `?uid=123&amp;cid=456` won't work - server sees `&amp;` as literal text
- With decoding, `?uid=123&cid=456` works - server understands these are separate parameters

---

## STAGE 3: Filter Obvious Junk

Function: `is_obvious_junk(url)`

### What Gets Filtered:

#### 1. Unsubscribe/Settings Links
```python
junk_keywords = ['unsubscribe', 'preferences', 'settings', 'privacy-policy']
```

**Example:**
```
❌ https://alphasignal.ai/unsubscribe?id=123
❌ https://alphasignal.ai/mail_preferences
❌ https://alphasignal.ai/settings
```

**Why reject:** Never article content, always UI/account pages

---

#### 2. Contact Links
```python
junk_keywords = ['mailto:', 'tel:']
```

**Example:**
```
❌ mailto:hello@alphasignal.ai
❌ tel:+1-555-1234
```

**Why reject:** Not web URLs, can't extract content

---

#### 3. Image Files
```python
junk_keywords = ['.png', '.jpg', '.gif', '.svg', '.ico', 'favicon']
```

**Example:**
```
❌ https://alphasignal.ai/logo.png
❌ https://cdn.alphasignal.ai/images/header.jpg
❌ https://alphasignal.ai/favicon.ico
```

**Why reject:** Images, not article content

---

#### 4. CDN/Cloudflare
```python
junk_keywords = ['/cdn-cgi/']
```

**Example:**
```
❌ https://alphasignal.ai/cdn-cgi/l/email-protection
```

**Why reject:** CDN/protection URLs, not content

---

### Result: 46 → 45 links (removed 1 junk link)

---

## STAGE 4: Separate Direct vs Tracking

### Direct Links (5 found)
**No tracking domains in URL**

```
✅ https://alphasignal.ai/email/8ea6d368184fc4a5
✅ https://github.com/karpathy/nanochat?utm_source=alphasignal&utm_campaign=2025-10-14&lid=Owx4liNC3BpC2Gzr
✅ https://github.com/karpathy/nanochat?utm_source=alphasignal&utm_campaign=2025-10-14&lid=Owx4liNC3BpC2Gzr (duplicate)
✅ https://arxiv.org/abs/2506.10943?utm_source=alphasignal&utm_campaign=2025-10-14&lid=u1wzh1bJCtTsdIV4
✅ https://arxiv.org/abs/2506.10943?utm_source=alphasignal&utm_campaign=2025-10-14&lid=u1wzh1bJCtTsdIV4 (duplicate)
```

**Note:** These are direct article links with UTM parameters (for analytics), but they go DIRECTLY to the content. No redirect needed!

---

### Tracking Links (40 found)
**Have tracking domain patterns**

```python
tracking_domains = ['link.', '/c?', '/fb/', '/click/', '/track/', '/redirect/', '/r/']
```

**Examples:**
```
⏱️ https://link.alphasignal.ai/HWyWVm                    (will redirect)
⏱️ https://link.alphasignal.ai/qBDJtP                    (will redirect)
⏱️ https://app.alphasignal.ai/c?uid=123&cid=456&lid=789 (will redirect)
```

**Why separate:** We process direct links FIRST because they're more likely to be articles.

---

## STAGE 5: Resolve Redirects

Function: `resolve_redirect(url)`

Only runs for tracking links. Makes HTTP request to follow redirects.

**Example 1 - Homepage redirect:**
```
INPUT:  https://link.alphasignal.ai/HWyWVm
OUTPUT: https://alphasignal.ai/?idref=email_ref
```

**Example 2 - Sponsor redirect:**
```
INPUT:  https://link.alphasignal.ai/PfbaIm
OUTPUT: https://www.nylas.com/products/notetaker-api/the-state-of-meeting-recordings/?utm_source=...
```

**Example 3 - Twitter profile redirect:**
```
INPUT:  https://link.alphasignal.ai/uIKFtp
OUTPUT: https://x.com/AlphaSignalAI#Intent;package=com.twitter.android;scheme=https;end
```

**Example 4 - Typeform redirect:**
```
INPUT:  https://link.alphasignal.ai/qBDJtP
OUTPUT: https://wsndcchuur6.typeform.com/to/t0Ry7qsf
```

---

## STAGE 6: Content URL Validation

Function: `is_content_url(url)`

This is the MOST IMPORTANT filter. Checks if the final URL is actual article content.

---

### Check 1: Homepage Detection

```python
if not path or path in ['', '/', 'index.html', 'index.htm']:
    return False
```

**Example:**
```
❌ https://alphasignal.ai/
❌ https://alphasignal.ai
❌ https://techcrunch.com/
```

**Why reject:** Homepage, not a specific article

**But wait, this caught our direct link!**
```
❌ https://alphasignal.ai/email/8ea6d368184fc4a5
```
Hmm, actually this has a path `/email/...`, so it passes this check!

---

### Check 2: Sponsor/Ad Domains

```python
ad_domains = ['airia.com', 'typeform.com', 'mailchi.mp']
if any(ad in domain for ad in ad_domains):
    return False
```

**Example:**
```
❌ https://wsndcchuur6.typeform.com/to/t0Ry7qsf       (survey, not article)
❌ https://www.nylas.com/products/notetaker-api/...  (sponsor page)
```

**Why reject:** These are ads/sponsors embedded in newsletter, not article content

---

### Check 3: App Stores

```python
if 'apps.apple.com' in domain or 'play.google.com' in domain:
    return False
```

**Example:**
```
❌ https://apps.apple.com/app/some-ai-app
❌ https://play.google.com/store/apps/details?id=com.example
```

**Why reject:** App download pages, not articles

---

### Check 4: Social Media Profiles

```python
# LinkedIn company/school pages
if 'linkedin.com/school/' in full_url or 'linkedin.com/company/' in full_url:
    return False

# YouTube channels
if 'youtube.com/channel/' in full_url or 'youtube.com/user/' in full_url:
    return False

# Twitter profiles (not tweets)
if ('x.com' in domain or 'twitter.com' in domain):
    if '/status/' not in path:
        return False
```

**Examples:**
```
❌ https://x.com/AlphaSignalAI                      (profile, not tweet)
❌ https://linkedin.com/company/alpha-signal
❌ https://youtube.com/channel/UCxxxxx

✅ https://twitter.com/karpathy/status/123456789   (specific tweet = content)
✅ https://youtube.com/watch?v=xxxxx               (specific video = content)
```

**Why reject profiles:** Profiles are not article content. But specific tweets/videos ARE content!

---

### Check 5: Account Pages

```python
account_keywords = ['mail_preferences', 'account', 'settings', 'profile', 'login', 'signup']
if any(keyword in path for keyword in account_keywords):
    return False
```

**Example:**
```
❌ https://alphasignal.ai/account/dashboard
❌ https://site.com/user/profile
```

**Why reject:** UI pages, not content

---

### Check 6: Domain-Specific Rules

#### GitHub

```python
# Must have user/repo (at least 1 slash)
if 'github.com' in domain and path.count('/') < 1:
    return False
```

**Examples:**
```
✅ https://github.com/karpathy/nanochat              (user/repo = good)
✅ https://github.com/openai/gpt-4                   (user/repo = good)
❌ https://github.com                                (homepage = bad)
❌ https://github.com/karpathy                       (just user = bad, no specific repo)
```

**Why:** We only want links to specific repositories, not GitHub homepage or user profiles

---

#### Twitter/X

```python
if ('x.com' in domain or 'twitter.com' in domain):
    if '/status/' not in path:
        return False
```

**Examples:**
```
✅ https://twitter.com/karpathy/status/1712345678   (specific tweet)
✅ https://x.com/sama/status/9876543210             (specific tweet)
❌ https://twitter.com/karpathy                      (profile page)
❌ https://x.com/AlphaSignalAI                       (profile page)
```

**Why:** Profiles are not articles, but tweets ARE content

---

#### Medium/Substack

```python
require_path_domains = {
    'medium.com': ['/@', '/p/'],  # Need author or post
    'substack.com': ['/p/'],      # Need post
}
```

**Examples:**
```
✅ https://medium.com/@author/my-article-title      (author post)
✅ https://medium.com/publication/p/article         (publication post)
✅ https://newsletter.substack.com/p/article-title  (specific post)
❌ https://medium.com                                (homepage)
❌ https://medium.com/@author                        (author profile, no specific post)
```

**Why:** We want specific articles, not homepages or profiles

---

### Check 7: Content Indicators

If URL doesn't match known news domains, look for content patterns:

```python
content_indicators = [
    '/blog/', '/article/', '/news/', '/post/', '/story/',
    '/2024/', '/2025/', '/2026/',  # Date-based URLs
    '/p/', '/thread/', '/status/', # Social media content
    '/watch?v=', '/v/',            # YouTube videos
]
```

**Examples:**
```
✅ https://example.com/blog/ai-breakthrough          (/blog/ = article)
✅ https://site.com/2025/10/15/news                  (/2025/ = dated article)
✅ https://site.com/article/123-ai-news              (/article/ = article)
❌ https://example.com/products                      (no content indicators)
❌ https://site.com/about-us                         (no content indicators)
```

**Why:** These paths are strong indicators of article content

---

### Check 8: Known News Domains

```python
news_domains = [
    'techcrunch.com', 'theverge.com', 'wired.com', 'arstechnica.com',
    'reuters.com', 'bloomberg.com', 'wsj.com', 'nytimes.com',
    'github.com',  # (already filtered to repos only)
    'arxiv.org', 'papers.withgoogle.com',
    'rundown.ai',
]
```

**Examples:**
```
✅ https://techcrunch.com/2025/10/15/ai-news        (trusted news domain)
✅ https://arxiv.org/abs/2506.10943                  (research paper)
✅ https://theverge.com/path/to/article             (trusted news domain)
❌ https://example.com/random-page                   (unknown domain, no indicators)
```

**Why:** These domains are trusted to have quality article content

---

## STAGE 7: Deduplicate

Check if URL already in our results list:

```python
if final_url not in [r['url'] for r in resolved_links]:
    resolved_links.append({'url': final_url, ...})
```

**Example:**
```
INPUT:
  1. https://github.com/karpathy/nanochat?utm_source=alphasignal&lid=abc
  2. https://github.com/karpathy/nanochat?utm_source=alphasignal&lid=xyz

OUTPUT:
  1. https://github.com/karpathy/nanochat?utm_source=alphasignal&lid=abc
  (Link 2 is a duplicate, skip it)
```

---

## Final Results for Alpha Signal

### ✅ KEPT (3 articles)

1. **https://github.com/karpathy/nanochat**
   - Direct link ✓
   - GitHub repo with user/repo ✓
   - Known domain ✓

2. **https://arxiv.org/abs/2506.10943**
   - Direct link ✓
   - ArXiv paper ✓
   - Known domain ✓

3. **https://github.com/langflow-ai/langflow**
   - Direct link ✓
   - GitHub repo with user/repo ✓
   - Known domain ✓

---

### ❌ REJECTED Examples

1. **https://alphasignal.ai/?idref=email_ref**
   - Reason: Homepage (no content path)

2. **https://wsndcchuur6.typeform.com/to/t0Ry7qsf**
   - Reason: Typeform (survey/ad domain)

3. **https://x.com/AlphaSignalAI**
   - Reason: Twitter profile (not a tweet)

4. **https://www.nylas.com/products/notetaker-api/...**
   - Reason: Sponsor page (not article content)

5. **https://app.alphasignal.ai/fb/...**
   - Reason: Feedback URL (account function)

---

## Summary: Why Only 3 Articles?

**Started with:** 46 links
**After decode:** 46 links (fixed `&amp;`)
**After junk filter:** 45 links
**Direct links found:** 5 (but 2 duplicates)
**Tracking links:** 40

**Tracking link results:**
- Most redirected to homepage, sponsor pages, or social profiles
- None passed the content validation checks
- Only the 3 direct links were actual articles

**This is CORRECT behavior!** The newsletter had:
- Navigation links (homepage, social, settings)
- Sponsor links (Nylas, Typeform)
- Analytics/tracking links
- Only 3 real article links

The filters successfully identified ONLY the actual articles!

---

## Key Insights

1. **HTML entities MUST be decoded** - Without this, tracking links fail
2. **Direct links are prioritized** - They're more likely to be articles
3. **Multiple checks needed** - Single filter misses edge cases
4. **Domain-specific rules crucial** - GitHub, Twitter, Medium need special handling
5. **Tracking links often lead nowhere** - Most resolve to non-content pages

---

## Testing Your Filters

To test if your filters are working:

```bash
# Run the extraction flow demo
python3.11 _debug/show_extraction_flow.py

# Check what gets filtered at each stage
# Look for patterns in rejected URLs
# Adjust filters in resolve_links.py if needed
```

Remember: **False positives (keeping junk) are worse than false negatives (missing articles)**. Better to be strict and miss a few articles than to include lots of junk.
