#!/usr/bin/env python3
"""
Newsletter Article Extraction Pipeline

Purpose: Extracts article links from email newsletters, resolves tracking redirects,
fetches metadata, and creates organized outputs for content repurposing.

Key Features:
- Concurrent processing with bounded semaphores for performance
- URL canonicalization and tracking parameter stripping
- Smart redirect resolution for wrapped/tracked links
- Domain-based and keyword categorization
- Filters out newsletter platform marketing and survey links

Usage:
    python src/extract_articles.py --days 7
    python src/extract_articles.py --days 30 --output custom_output

Output:
    - articles.json: Structured JSON with all extracted articles
    - articles_digest.md: Markdown digest organized by category
"""

import asyncio
import aiohttp
import json
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode
from pathlib import Path
import sys
import argparse

# Import from same backend directory
from gmail_extractor import GmailNewsletterExtractor
from database import ArticleDatabase

# Concurrency control
SEM = asyncio.Semaphore(32)

# Load source names dynamically from config
def load_source_names():
    """Load newsletter source names from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    source_map = {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Load enabled sources
        for source in config.get('newsletters', {}).get('sources', []):
            if source.get('enabled', True):
                email = source.get('email', '')
                name = source.get('name', email.split('@')[0])
                source_map[email] = name
                
        # Also load additional sources if enabled
        for source in config.get('newsletters', {}).get('additional_sources', []):
            if source.get('enabled', False):
                email = source.get('email', '')
                name = source.get('name', email.split('@')[0])
                # Support domain-based matching
                source_map[email] = name
                
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        # Fall back to some defaults
        source_map = {
            'news@alphasignal.ai': 'AlphaSignal',
            'crew@technews.therundown.ai': 'The Rundown Tech',
            'news@daily.therundown.ai': 'The Rundown AI'
        }
    
    return source_map

# Load source names on startup
SOURCE_NAMES = load_source_names()

def get_newsletter_source_name(sender_email):
    """Get friendly name for newsletter source"""
    # First check exact email match
    if sender_email in SOURCE_NAMES:
        return SOURCE_NAMES[sender_email]
    
    # Check domain-based matching
    if '@' in sender_email:
        domain = sender_email.split('@')[-1]
        for email_key, name in SOURCE_NAMES.items():
            # If the config has a domain entry (no @), match it
            if '@' not in email_key and domain == email_key:
                return name
    
    # Fall back to email prefix
    return sender_email.split('@')[0] if '@' in sender_email else sender_email

# Tracking parameters to strip
TRACKER_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "mc_cid", "mc_eid", "fbclid", "gclid", "ref", "source"
}

# Domains that need params preserved
KEEP_PARAMS_FOR = {"bloomberg.com", "wsj.com", "ft.com"}

# Known wrapper/redirect domains
WRAPPER_HOSTS = (
    "beehiiv.com", "mailchi.mp", "list-manage.com", "t.co", "lnkd.in",
    "urldefense.com", "bit.ly", "tinyurl.com", "ow.ly", "buff.ly",
    "link.mail.beehiiv.com", "clicks.beehiiv.com"
)

# Categorization priors by domain
CAT_PRIORS = {
    "AI/ML": {
        "openai.com", "anthropic.com", "deepmind.google", "huggingface.co",
        "arxiv.org", "papers.nips.cc", "mlconf.com", "nvidia.com"
    },
    "Business": {
        "bloomberg.com", "reuters.com", "ft.com", "wsj.com", "businessinsider.com",
        "fortune.com", "forbes.com", "economist.com", "cnbc.com"
    },
    "Technology": {
        "theverge.com", "wired.com", "arstechnica.com", "techcrunch.com",
        "engadget.com", "9to5mac.com", "macrumors.com", "anandtech.com"
    }
}

# Keywords for categorization
CATEGORY_KEYWORDS = {
    "AI/ML": {
        "ai", "ml", "gpt", "claude", "llm", "diffusion", "dataset", "fine-tune",
        "token", "neural", "transformer", "bert", "machine learning", "artificial intelligence"
    },
    "Business": {
        "market", "earnings", "deal", "acquire", "valuation", "funding", "revenue",
        "ipo", "merger", "stock", "investor", "venture", "capital"
    },
    "Technology": {
        "software", "app", "startup", "api", "cloud", "infra", "devops", "release",
        "hardware", "chip", "processor", "mobile", "platform"
    }
}


def _backoff_sleep(i, base=0.4):
    """Calculate exponential backoff with jitter"""
    return base * (2 ** i) + random.random() * 0.2


async def with_semaphore(coro, *args, **kwargs):
    """Execute coroutine with semaphore for concurrency control"""
    async with SEM:
        return await coro(*args, **kwargs)


async def retry(fn, *args, tries=3, **kwargs):
    """Retry a function with exponential backoff"""
    for i in range(tries):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            if i == tries - 1:
                raise
            await asyncio.sleep(_backoff_sleep(i))


def canonical_url(url: str) -> str:
    """Canonicalize URL: lowercase host, strip trackers, remove fragment"""
    if not url:
        return url
    
    try:
        sp = urlsplit(url)
        if sp.scheme not in {"http", "https"}:
            return url
        
        host = sp.netloc.lower()
        
        # Strip tracking parameters unless domain requires them
        q = dict(parse_qsl(sp.query, keep_blank_values=True))
        if host not in KEEP_PARAMS_FOR:
            q = {k: v for k, v in q.items() if k not in TRACKER_PARAMS}
        
        # Rebuild URL without fragment
        return urlunsplit((sp.scheme, host, sp.path, urlencode(q, doseq=True), ""))
    except:
        return url


def is_excluded(url: str) -> bool:
    """Check if URL should be excluded"""
    if not url:
        return True
        
    lower = url.lower()
    
    # Protocol exclusions
    if lower.startswith(("mailto:", "javascript:", "data:", "file:", "about:")):
        return True
    
    # Pattern exclusions
    bad_patterns = (
        'unsubscribe', 'preferences', 'update-preferences', '/unsub', '/optout',
        'list-manage.com', 'manage.com', 'email-preferences',
        # Newsletter platform's own marketing/tracking
        'alphasignal.ai/?idref=', 'therundown.ai/?ref=', 'therundown.ai/subscribe',
        'alphasignal.ai/subscribe', 'alphasignal.ai/?ref=',
        # Newsletter platform's own social media
        'facebook.com/therundown', 'twitter.com/therundown', 'instagram.com/therundown',
        'facebook.com/alphasignal', 'twitter.com/alphasignal', 'instagram.com/alphasignal',
        'linkedin.com/company/', 'youtube.com/c/', 'youtube.com/channel/',
        # Surveys and forms
        'docs.google.com/forms', 'forms.gle', 'surveymonkey.com', 'typeform.com',
        'qualtrics.com', 'airtable.com/shr'
    )
    
    return any(pattern in lower for pattern in bad_patterns)


def extract_links_from_newsletter(newsletter):
    """Extract all links from newsletter HTML"""
    html_content = newsletter.get('body_html', '')
    if not html_content:
        return []
    
    # Find all href links
    href_pattern = r'href=[\'"]?([^\'" >]+)'
    links = re.findall(href_pattern, html_content, re.IGNORECASE)
    
    # Find plain URLs in text
    url_pattern = r'https?://[^\s<>"\']+(?:[^\s<>"\'])*'
    text_links = re.findall(url_pattern, html_content)
    
    # Combine and deduplicate
    all_links = set(links + text_links)
    return [canonical_url(link) for link in all_links if link]


async def resolve_redirect(session: aiohttp.ClientSession, url: str, timeout=10) -> str:
    """Resolve redirects, handle wrappers, return final URL"""
    if not url:
        return None
    
    url = canonical_url(url)
    final = url
    
    try:
        # Try HEAD first (faster)
        try:
            async with session.head(url, allow_redirects=True, timeout=timeout) as resp:
                final = str(resp.url)
        except:
            # Fallback to GET if HEAD fails
            async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
                final = str(resp.url)
        
        # If still a wrapper, chase once more with GET
        if any(host in final for host in WRAPPER_HOSTS):
            async with session.get(final, allow_redirects=True, timeout=timeout) as resp:
                final = str(resp.url)
        
        return canonical_url(final)
    except Exception:
        return url  # Return original if resolution fails


async def _read_capped(resp, cap=512*1024):
    """Read response with size cap to prevent huge downloads"""
    chunks, total = [], 0
    async for chunk in resp.content.iter_chunked(8192):
        chunks.append(chunk)
        total += len(chunk)
        if total >= cap:
            break
    return b"".join(chunks).decode(errors="ignore")


async def fetch_article_metadata(session: aiohttp.ClientSession, url: str) -> dict:
    """Fetch and parse article metadata"""
    meta = {
        'url': url,
        'domain': urlparse(url).netloc.replace('www.', ''),
        'fetch_status': 'pending'
    }
    
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status >= 400:
                meta['fetch_status'] = 'failed'
                meta['error'] = f'HTTP {resp.status}'
                return meta
            
            html = await _read_capped(resp)
            meta['fetch_status'] = 'success'
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                meta['title'] = title_match.group(1).strip()
            
            # Extract meta tags (prefer OG tags)
            meta_patterns = {
                'og_title': r'<meta\s+(?:property|name)=["\']og:title["\']\s+content=["\'](.*?)["\']',
                'description': r'<meta\s+(?:property|name)=["\'](?:og:)?description["\']\s+content=["\'](.*?)["\']',
                'author': r'<meta\s+(?:property|name)=["\'](?:article:)?author["\']\s+content=["\'](.*?)["\']',
                'published_date': r'<meta\s+(?:property|name)=["\']article:published_time["\']\s+content=["\'](.*?)["\']',
            }
            
            for key, pattern in meta_patterns.items():
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    meta[key] = match.group(1).strip()
            
    except asyncio.TimeoutError:
        meta['fetch_status'] = 'timeout'
    except Exception as e:
        meta['fetch_status'] = 'failed'
        meta['error'] = type(e).__name__
    
    return meta


def categorize_article(metadata, newsletter_subject=''):
    """Categorize article based on domain, content, and keywords"""
    domain = (metadata.get('domain', '') or '').lower()
    title = (metadata.get('og_title') or metadata.get('title') or '').lower()
    subject = (newsletter_subject or '').lower()
    path = urlparse(metadata.get('url', '')).path.lower()
    
    # Check domain priors first
    for cat, domains in CAT_PRIORS.items():
        if any(d in domain for d in domains):
            return cat
    
    # Score by keywords
    text = " ".join([title, subject, path])
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[cat] += 1
    
    # Return highest scoring category
    if any(scores.values()):
        return max(scores, key=scores.get)
    
    return "General"


async def process_newsletter_batch(newsletters):
    """Process newsletters with full concurrency"""
    results = []
    
    # Create session with proper configuration
    conn = aiohttp.TCPConnector(limit=64, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=20, connect=5, sock_read=12)
    headers = {"User-Agent": "NewsletterExtractor/2.0 (Compatible)"}
    
    async with aiohttp.ClientSession(connector=conn, timeout=timeout, headers=headers) as session:
        for newsletter in newsletters:
            print(f"\n📧 Processing: {newsletter.get('subject', '')[:60]}...")
            
            # Extract and filter links
            links = extract_links_from_newsletter(newsletter)
            links = [link for link in links if not is_excluded(link)][:50]  # Cap at 50
            
            print(f"  Found {len(links)} potential article links")
            
            # Resolve redirects concurrently
            resolve_tasks = [
                with_semaphore(retry, resolve_redirect, session, link)
                for link in links
            ]
            resolved = await asyncio.gather(*resolve_tasks, return_exceptions=True)
            
            # Filter and dedupe resolved URLs
            seen = set()
            unique_urls = []
            for url in resolved:
                if isinstance(url, str) and url:
                    canonical = canonical_url(url)
                    if canonical not in seen and not is_excluded(canonical):
                        seen.add(canonical)
                        unique_urls.append(canonical)
            
            # Fetch metadata concurrently
            meta_tasks = [
                with_semaphore(retry, fetch_article_metadata, session, url)
                for url in unique_urls
            ]
            metas = await asyncio.gather(*meta_tasks, return_exceptions=True)
            
            # Process successful fetches
            articles = []
            for meta in metas:
                if not isinstance(meta, dict):
                    continue
                if meta.get('fetch_status') != 'success':
                    continue
                if not (meta.get('title') or meta.get('og_title')):
                    continue
                
                # Add categorization and source info
                meta['category'] = categorize_article(meta, newsletter.get('subject'))
                meta['source_newsletter'] = newsletter.get('subject')
                meta['newsletter_date'] = newsletter.get('date')
                
                articles.append(meta)
                title = meta.get('og_title') or meta.get('title', 'Unknown')
                print(f"  📄 {title[:70]}...")
            
            results.append({
                'newsletter': {
                    'subject': newsletter.get('subject'),
                    'sender': newsletter.get('sender_email'),
                    'date': newsletter.get('date')
                },
                'articles': articles
            })
    
    return results


def create_digest(data, output_file='output/articles_digest.md'):
    """Create markdown digest from extracted articles"""
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Gather all articles
    all_articles = []
    for newsletter_data in data:
        all_articles.extend(newsletter_data['articles'])
    
    # Group by category
    categorized = {}
    for article in all_articles:
        category = article.get('category', 'Uncategorized')
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(article)
    
    # Create digest
    with open(output_file, 'w') as f:
        f.write(f"# 📰 Newsletter Articles Digest\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total Articles Extracted:** {len(all_articles)}\n\n")
        
        # Table of contents
        f.write("## 📋 Categories\n\n")
        for category, articles in sorted(categorized.items()):
            f.write(f"- **{category}**: {len(articles)} articles\n")
        f.write("\n---\n\n")
        
        # Articles by category
        for category, articles in sorted(categorized.items()):
            f.write(f"## 📂 {category} ({len(articles)} articles)\n\n")
            
            for article in articles:
                title = article.get('og_title') or article.get('title', 'Untitled')
                f.write(f"### {title}\n\n")
                
                f.write(f"**Source:** {article.get('domain', 'Unknown')}\n")
                
                if article.get('author'):
                    f.write(f"**Author:** {article['author']}\n")
                
                if article.get('published_date'):
                    f.write(f"**Published:** {article['published_date']}\n")
                
                f.write(f"**From Newsletter:** {article.get('source_newsletter', 'Unknown')} ")
                f.write(f"({article.get('newsletter_date', 'Unknown date')})\n\n")
                
                if article.get('description'):
                    f.write(f"**Summary:** {article['description']}\n\n")
                
                f.write(f"**Link:** {article['url']}\n\n")
                f.write("---\n\n")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Extract articles from newsletters')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back')
    parser.add_argument('--output', default='output', help='Output directory')
    parser.add_argument('--use-db', action='store_true', help='Store articles in database')
    args = parser.parse_args()
    
    print("🚀 Initializing optimized extractor with concurrent processing...")
    
    # Initialize Gmail extractor
    extractor = GmailNewsletterExtractor()
    
    # Initialize database if requested
    db = None
    if args.use_db:
        print("📊 Using database for storage...")
        db = ArticleDatabase()
    
    # Get configured sources
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            newsletters = config.get('newsletters', {})
            sources = [s for s in newsletters.get('sources', []) if s.get('enabled', True)]
    except FileNotFoundError:
        print("❌ config.json not found")
        return
    
    if not sources:
        print("❌ No enabled sources in config")
        return
    
    print(f"\n📋 Extracting from {len(sources)} sources:")
    for source in sources:
        print(f"  • {source['name']} ({source['email']})")
    
    # Fetch newsletters
    print(f"\n🔍 Searching last {args.days} days...")
    
    # Build search query for sources
    emails = [s['email'] for s in sources]
    after_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y/%m/%d')
    
    from_clause = ' OR '.join([f'from:{email}' for email in emails])
    query = f'after:{after_date} AND ({from_clause})'
    
    print(f"🔍 Searching with query: {query}")
    newsletters = extractor.search_newsletters(query=query)
    
    if not newsletters:
        print("❌ No newsletters found")
        return
    
    print(f"✅ Found {len(newsletters)} newsletters")
    
    # Process newsletters with concurrency
    print("\n🔄 Processing newsletters with concurrent extraction...")
    results = await process_newsletter_batch(newsletters)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_file = output_dir / 'articles.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Saved to {json_file}")
    
    # Create digest
    digest_file = output_dir / 'articles_digest.md'
    create_digest(results, digest_file)
    print(f"📝 Created digest at {digest_file}")
    
    # Stats
    total_articles = sum(len(r['articles']) for r in results)
    
    # Save to database if requested
    if db:
        print("\n💾 Saving to database...")
        total_added = 0
        total_skipped = 0
        
        for newsletter_data in results:
            newsletter_info = newsletter_data['newsletter']
            for article in newsletter_data['articles']:
                # Prepare article for database
                db_article = {
                    'url': article.get('url'),
                    'domain': article.get('domain'),
                    'title': article.get('title') or article.get('og_title'),
                    'description': article.get('description') or article.get('og_description'),
                    'category': article.get('category'),
                    'source': get_newsletter_source_name(newsletter_info.get('sender', '')),
                    'newsletter_subject': newsletter_info.get('subject'),
                    'newsletter_sender': newsletter_info.get('sender'),
                    'newsletter_date': newsletter_info.get('date'),
                    'extracted_at': datetime.now().isoformat(),
                    'fetch_status': article.get('fetch_status'),
                    'og_title': article.get('og_title'),
                    'og_description': article.get('og_description'),
                    'og_image': article.get('og_image'),
                    'meta_keywords': article.get('keywords')
                }
                
                if db.insert_article(db_article):
                    total_added += 1
                else:
                    total_skipped += 1
        
        # Log extraction
        db.log_extraction(
            days_back=args.days,
            newsletters_processed=len(newsletters),
            articles_found=total_articles,
            articles_added=total_added,
            duplicates_skipped=total_skipped
        )
        
        print(f"  • Articles added to DB: {total_added}")
        print(f"  • Duplicates skipped: {total_skipped}")
        
        # Show DB stats
        stats = db.get_stats()
        print(f"\n📊 Database stats:")
        print(f"  • Total articles stored: {stats['total_articles']}")
        
        db.close()
    print(f"\n✅ Complete!")
    print(f"  • Newsletters processed: {len(newsletters)}")
    print(f"  • Articles extracted: {total_articles}")


if __name__ == "__main__":
    asyncio.run(main())