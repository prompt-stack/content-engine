#!/usr/bin/env python3
"""
STEP 4: Filter URLs to keep only valid article content

Input: extraction_TIMESTAMP/resolved_links.json
Output: extraction_TIMESTAMP/filtered_articles.json
        extraction_TIMESTAMP/filtered_articles.txt (human-readable)
        extraction_TIMESTAMP/article_urls.txt (URLs only)
        extraction_TIMESTAMP/rejected.json (rejected URLs with reasons)
        extraction_TIMESTAMP/rejected.txt (human-readable rejected list)
"""

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict


def load_config() -> Dict:
    """Load configuration from config.json"""
    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def is_content_url(url: str, config: Dict = None) -> bool:
    """
    Check if FINAL destination URL is actual content

    Args:
        url: Resolved URL to validate
        config: Configuration dict (loads from config.json if None)

    Returns:
        True if URL appears to be article content
    """
    if not url:
        return False

    # Load config if not provided
    if config is None:
        config = load_config()

    # Get filtering config with defaults
    filtering = config.get('content_filtering', {})

    # Blacklist (surveys, forms)
    blacklist_domains = filtering.get('blacklist_domains', ['typeform.com', 'mailchi.mp', 'surveymonkey.com'])

    # Newsletter curator domains (circular reference)
    curator_domains = filtering.get('curator_domains', ['alphasignal.ai', 'therundown.ai', 'rundown.ai'])

    # Content indicators (path patterns)
    content_indicators = filtering.get('content_indicators', [
        '/blog/', '/article/', '/news/', '/post/', '/story/',
        '/2024/', '/2025/', '/2026/',
        '/p/', '/thread/', '/status/',
        '/watch?v=', '/v/',
        '/guides/', '/guide/',
        '/collections/',
        '/resources/'
    ])

    # Whitelist (always accept these domains)
    whitelist_domains = filtering.get('whitelist_domains', [
        'techcrunch.com', 'theverge.com', 'wired.com', 'arstechnica.com',
        'reuters.com', 'bloomberg.com', 'wsj.com', 'nytimes.com',
        'medium.com', 'substack.com', 'dev.to', 'hackernoon.com',
        'github.com', 'arxiv.org', 'papers.withgoogle.com',
        'huggingface.co', 'blog.google', 'github.blog',
        'techcommunity.microsoft.com', 'aistudio.google.com',
        'microsoft.ai', 'openai.com', 'platform.openai.com',
        'warp.dev', 'graphite.io'
    ])

    url_lower = url.lower()

    # Parse domain and path
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        path = parsed.path.lower()  # Keep slashes for content indicator matching
        path_stripped = path.strip('/')  # For other checks
        full_url = f"{domain}/{path_stripped}"

        # Exclude blacklisted domains (surveys, forms)
        if any(blacklist in domain for blacklist in blacklist_domains):
            return False

        # Exclude newsletter curator domains (circular reference)
        for curator in curator_domains:
            if curator in domain:
                # AlphaSignal: allow nothing except maybe specific post paths in future
                if 'alphasignal.ai' in domain:
                    if not path_stripped or path_stripped in ['', '/', 'index.html'] or '?idref' in url or '/email/' in path:
                        return False
                # The Rundown: block ALL their domains/subdomains (they're the curator, not the content)
                elif 'rundown.ai' in domain or 'therundown.ai' in domain:
                    return False

        # Exclude auth/login pages (not content)
        # Note: Removed '/welcome' from patterns as it's too broad (blocks aistudio.google.com/welcome)
        auth_patterns = ['/signin', '/login', '/identifier', '/signup', '/register']
        auth_domains = ['accounts.google.com', 'login.microsoft.com', 'auth.']
        if any(auth in domain for auth in auth_domains):
            return False
        if any(auth in path for auth in auth_patterns):  # Keep path with slashes for pattern matching
            return False

        # Exclude app stores
        if 'apps.apple.com' in domain or 'play.google.com' in domain:
            return False

        # Exclude social media profiles/pages (not content)
        if 'linkedin.com/school/' in full_url or 'linkedin.com/company/' in full_url:
            return False
        if 'youtube.com/channel/' in full_url or 'youtube.com/user/' in full_url:
            return False

        # Exclude account/settings pages
        account_keywords = ['mail_preferences', 'account/settings', 'user/profile']
        if any(keyword in path_stripped for keyword in account_keywords):
            return False

        # GitHub: only actual repos (must have at least user/repo)
        if 'github.com' in domain and path_stripped.count('/') < 1:
            return False

        # Twitter/X: only specific tweets, not profiles
        if ('x.com' in domain or 'twitter.com' in domain):
            if '/status/' not in path:  # Keep path with slashes for pattern matching
                return False

        # Medium/Substack: need specific post paths
        if 'medium.com' in domain and not any(p in path for p in ['/@', '/p/']):  # Keep path with slashes
            return False
        if 'substack.com' in domain and '/p/' not in path:  # Keep path with slashes
            return False

        # Check for content indicators (loaded from config)
        has_content_indicator = any(indicator in path for indicator in content_indicators)

        # Check if domain is whitelisted (loaded from config)
        is_whitelisted = any(whitelist in domain for whitelist in whitelist_domains)

        # Educational/training platforms (hardcoded patterns)
        educational_domains = ['academy.', 'learn.', 'training.']
        is_educational = any(edu in domain for edu in educational_domains)

        # Accept if it's whitelisted OR educational OR has content indicators
        if is_whitelisted or is_educational or has_content_indicator:
            return True

        # Otherwise reject (likely homepage, company page, etc)
        return False

    except:
        return False


def filter_content_from_file(extraction_dir: Path):
    """
    Step 4: Filter URLs to keep only valid article content

    Args:
        extraction_dir: Path to extraction_TIMESTAMP directory

    Returns:
        Path to filtered_articles.json
    """
    print("="*80)
    print("STEP 4: FILTER CONTENT")
    print("="*80)
    print(f"\n📁 Extraction directory: {extraction_dir.name}\n")

    # Load config for filtering
    config = load_config()

    # Load resolved links
    links_file = extraction_dir / "resolved_links.json"
    if not links_file.exists():
        print(f"❌ Error: {links_file} not found")
        print("   Run step3_resolve_redirects.py first")
        return None

    with open(links_file, 'r', encoding='utf-8') as f:
        resolved_data = json.load(f)

    print(f"📧 Found {len(resolved_data)} newsletters\n")

    # Filter content for each newsletter
    results = []
    rejected_results = []
    total_resolved = 0
    total_valid = 0
    total_rejected = 0

    for newsletter_data in resolved_data:
        index = newsletter_data['newsletter_index']
        subject = newsletter_data['newsletter_subject']
        sender = newsletter_data['newsletter_sender']
        links = newsletter_data['links']

        print(f"{index:3d}. {subject[:60]}")
        print(f"      From: {sender}")
        print(f"      Resolved: {len(links)} links")

        # Filter to valid content URLs
        valid_articles = []
        rejected_links = []
        seen_urls = set()  # Deduplicate

        for link_info in links:
            total_resolved += 1

            # Only process successfully resolved links
            if link_info.get('status') != 'success':
                rejected_links.append({
                    "url": link_info.get('resolved_url') or link_info.get('original_url'),
                    "original_url": link_info.get('original_url'),
                    "reason": f"Resolution failed: {link_info.get('status')}"
                })
                total_rejected += 1
                continue

            resolved_url = link_info.get('resolved_url')
            if not resolved_url:
                rejected_links.append({
                    "url": link_info.get('original_url'),
                    "original_url": link_info.get('original_url'),
                    "reason": "No resolved URL"
                })
                total_rejected += 1
                continue

            # Check if it's valid content (pass config for filtering)
            if is_content_url(resolved_url, config):
                # Deduplicate
                if resolved_url not in seen_urls:
                    seen_urls.add(resolved_url)
                    valid_articles.append({
                        "url": resolved_url,
                        "original_url": link_info.get('original_url'),
                        "is_redirect": link_info.get('is_redirect', False)
                    })
                    total_valid += 1
            else:
                # Determine rejection reason
                from urllib.parse import urlparse
                parsed = urlparse(resolved_url)
                domain = parsed.netloc.lower().replace('www.', '')

                reason = "Did not match content criteria"
                if 'typeform.com' in domain:
                    reason = "Survey/form site"
                elif 'rundown.ai' in domain or 'therundown.ai' in domain:
                    reason = "Newsletter curator origin (not curated content)"
                elif 'alphasignal.ai' in domain:
                    reason = "Newsletter curator homepage"
                elif 'accounts.google.com' in domain or 'login.microsoft.com' in domain:
                    reason = "Auth/login page"

                rejected_links.append({
                    "url": resolved_url,
                    "original_url": link_info.get('original_url'),
                    "reason": reason
                })
                total_rejected += 1

        print(f"      Valid articles: {len(valid_articles)}")
        print(f"      Rejected: {len(rejected_links)}")
        print()

        # Store results (only if we have valid articles)
        if valid_articles:
            results.append({
                "newsletter_index": index,
                "newsletter_subject": subject,
                "newsletter_sender": sender,
                "newsletter_date": newsletter_data['newsletter_date'],
                "html_file": newsletter_data['html_file'],
                "articles": valid_articles,
                "article_count": len(valid_articles)
            })

        # Store rejected links (always, for debugging)
        if rejected_links:
            rejected_results.append({
                "newsletter_index": index,
                "newsletter_subject": subject,
                "newsletter_sender": sender,
                "newsletter_date": newsletter_data['newsletter_date'],
                "html_file": newsletter_data['html_file'],
                "rejected": rejected_links,
                "rejected_count": len(rejected_links)
            })

    # Save filtered articles (JSON)
    output_file = extraction_dir / "filtered_articles.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save human-readable format (TXT)
    txt_file = extraction_dir / "filtered_articles.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Filtered Newsletter Articles\n")
        f.write(f"Total: {len(results)} newsletters, {total_valid} articles\n")
        f.write("=" * 80 + "\n\n")

        for newsletter in results:
            f.write(f"📧 {newsletter['newsletter_subject']}\n")
            f.write(f"   From: {newsletter['newsletter_sender']}\n")
            f.write(f"   Date: {newsletter['newsletter_date']}\n")
            f.write(f"   Articles ({newsletter['article_count']}):\n\n")

            for article in newsletter['articles']:
                f.write(f"   • {article['url']}\n")

            f.write("\n" + "-" * 80 + "\n\n")

    # Save URLs only (for batch extraction)
    urls_file = extraction_dir / "article_urls.txt"
    with open(urls_file, 'w', encoding='utf-8') as f:
        for newsletter in results:
            for article in newsletter['articles']:
                f.write(f"{article['url']}\n")

    # Save rejected URLs (for debugging and improving filter)
    rejected_file = extraction_dir / "rejected.json"
    with open(rejected_file, 'w', encoding='utf-8') as f:
        json.dump(rejected_results, f, indent=2, ensure_ascii=False)

    # Save rejected URLs (human-readable)
    rejected_txt_file = extraction_dir / "rejected.txt"
    with open(rejected_txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Rejected URLs\n")
        f.write(f"Total: {len(rejected_results)} newsletters, {total_rejected} rejected\n")
        f.write("=" * 80 + "\n\n")

        for newsletter in rejected_results:
            f.write(f"📧 {newsletter['newsletter_subject']}\n")
            f.write(f"   From: {newsletter['newsletter_sender']}\n")
            f.write(f"   Date: {newsletter['newsletter_date']}\n")
            f.write(f"   Rejected ({newsletter['rejected_count']}):\n\n")

            for rejected in newsletter['rejected']:
                f.write(f"   ✗ {rejected['url']}\n")
                f.write(f"     Reason: {rejected['reason']}\n\n")

            f.write("-" * 80 + "\n\n")

    print("="*80)
    print("STEP 4 COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Newsletters processed: {len(resolved_data)}")
    print(f"   Newsletters with articles: {len(results)}")
    print(f"   Total resolved links: {total_resolved}")
    print(f"   Valid articles: {total_valid}")
    print(f"   Rejected (junk/homepage/etc): {total_rejected}")
    print()
    print(f"📂 Files created:")
    print(f"   • filtered_articles.json - Full data with newsletter context")
    print(f"   • filtered_articles.txt - Human-readable format")
    print(f"   • article_urls.txt - Just URLs (for batch extraction)")
    print(f"   • rejected.json - Rejected URLs with reasons")
    print(f"   • rejected.txt - Human-readable rejected list")
    print()
    print(f"🚀 Next step:")
    print(f"   python3.11 batch_extract.py --input {output_file}")
    print()

    return output_file


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Step 4: Filter URLs to keep only valid article content',
        epilog='''
Examples:
  # Process specific extraction
  python3.11 step4_filter_content.py extraction_20251015_131800

  # Process latest extraction
  python3.11 step4_filter_content.py latest
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'extraction_dir',
        help='Extraction directory name (or "latest" for most recent)'
    )

    args = parser.parse_args()

    # Find extraction directory
    output_dir = Path(__file__).parent / "output"

    if args.extraction_dir == 'latest':
        # Find most recent extraction_* directory
        extraction_dirs = sorted(output_dir.glob('extraction_*'), reverse=True)
        if not extraction_dirs:
            print("❌ No extraction directories found in output/")
            sys.exit(1)
        extraction_dir = extraction_dirs[0]
    else:
        extraction_dir = output_dir / args.extraction_dir
        if not extraction_dir.exists():
            print(f"❌ Directory not found: {extraction_dir}")
            sys.exit(1)

    filter_content_from_file(extraction_dir)
