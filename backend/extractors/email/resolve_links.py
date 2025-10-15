#!/usr/bin/env python3
"""
Newsletter Link Resolver - Follow tracking URLs to get real article links
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict, Optional
from gmail_extractor import GmailExtractor


def is_obvious_junk(url: str) -> bool:
    """Check if URL is obviously junk (unsubscribe, preferences, etc) - check BEFORE resolving"""
    url_lower = url.lower()

    junk_keywords = [
        'unsubscribe',
        'preferences',
        'settings',
        'privacy-policy',
        'terms-of-service',
        'mailto:',
        'tel:',
        '/cdn-cgi/',
        'favicon',
        '.png',
        '.jpg',
        '.gif',
        '.svg',
        '.ico',
        'mail_preferences',
        'email_preferences',
    ]

    for keyword in junk_keywords:
        if keyword in url_lower:
            return True

    return False


# Import the config-based filtering from step4
# This ensures we use the same filtering logic that's configurable via the frontend
try:
    from step4_filter_content import is_content_url as config_based_filter
    USE_CONFIG_FILTER = True
except ImportError:
    USE_CONFIG_FILTER = False

    def config_based_filter(url: str, config: Dict = None) -> bool:
        """Fallback filter if step4 not available"""
        return True  # Accept all if filter not available


def resolve_redirect(url: str, max_hops: int = 5) -> Optional[str]:
    """
    Follow redirects to get final destination URL

    Args:
        url: Starting URL (tracking link)
        max_hops: Maximum number of redirects to follow

    Returns:
        Final destination URL or None if failed
    """
    try:
        # Use HEAD request to avoid downloading content
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
        )

        # Get final URL after all redirects
        final_url = response.url

        # If HEAD didn't work, try GET
        if response.status_code >= 400:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=10,
                stream=True,  # Don't download body
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
            )
            final_url = response.url

        return final_url if final_url != url else url

    except requests.exceptions.Timeout:
        print(f"    ⏱️  Timeout resolving: {url[:80]}...")
        return None
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error resolving: {url[:80]}... ({str(e)[:50]})")
        return None
    except Exception as e:
        print(f"    ❌ Unexpected error: {str(e)[:50]}")
        return None


def load_config() -> Dict:
    """Load configuration from config.json"""
    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_enabled_senders_from_config() -> List[str]:
    """Extract enabled newsletter sender emails from config"""
    config = load_config()
    if not config:
        return []

    sources = config.get('newsletters', {}).get('sources', [])
    enabled_senders = [
        source['email']
        for source in sources
        if source.get('enabled', False)
    ]
    return enabled_senders


def extract_and_resolve_links(days_back: int = 7, max_results: int = 30, senders: List[str] = None):
    """
    Extract newsletters and resolve all links to real article URLs

    Args:
        days_back: Number of days to look back
        max_results: Maximum number of newsletters
        senders: List of sender emails/domains to filter (e.g., ['@therundown.ai', '@alphasignal.ai'])
    """
    if senders:
        print(f"📧 Extracting newsletters from: {', '.join(senders)}")
        print(f"   Looking back {days_back} days...\n")
    else:
        print(f"📧 Extracting ALL newsletters from last {days_back} days...\n")

    # Load config for filtering
    config = load_config()

    # Extract newsletters
    extractor = GmailExtractor()
    newsletters = extractor.search_newsletters(
        days_back=days_back,
        max_results=max_results,
        sender_filter=senders
    )

    if not newsletters:
        print("ℹ️  No newsletters found")
        return

    print(f"✅ Found {len(newsletters)} newsletters\n")

    # Process each newsletter
    resolved_articles = []
    total_links = 0
    resolved_count = 0

    for i, newsletter in enumerate(newsletters, 1):
        subject = newsletter.get('subject', 'Untitled')
        sender = newsletter.get('sender_email', 'Unknown')
        date = newsletter.get('date', 'Unknown')
        body_html = newsletter.get('body_html', '')

        print(f"{i}. {subject[:60]}")
        print(f"   From: {sender}")

        if not body_html:
            print(f"   ⚠️  No HTML content\n")
            continue

        # Extract all links from HTML
        import re
        import html
        link_pattern = r'href=["\']([^"\']+)["\']'
        raw_links = re.findall(link_pattern, body_html)

        # Decode HTML entities (&amp; -> &, &quot; -> ", etc.)
        raw_links = [html.unescape(link) for link in raw_links]

        # Filter out obvious junk BEFORE resolving
        candidate_links = [link for link in raw_links if not is_obvious_junk(link)]

        # PRIORITIZE: Put direct article links first, tracking links last
        # This ensures we process actual content before hitting our limit
        direct_links = []
        tracking_links = []

        tracking_domains = ['link.', '/c?', '/fb/', '/click/', '/track/', '/redirect/', '/r/']
        for link in candidate_links:
            if any(tracker in link.lower() for tracker in tracking_domains):
                tracking_links.append(link)
            else:
                direct_links.append(link)

        # Process direct links first (more likely to be content)
        prioritized_links = direct_links + tracking_links
        total_links += len(prioritized_links)

        if not prioritized_links:
            print(f"   ℹ️  No links to resolve\n")
            continue

        print(f"   🔗 Found {len(prioritized_links)} links ({len(direct_links)} direct, {len(tracking_links)} tracking)")
        print(f"   🔄 Resolving redirects...")

        # Resolve each link (increased limit since we prioritize better now)
        resolved_links = []
        for link in prioritized_links[:30]:  # Limit to 30 per newsletter
            final_url = resolve_redirect(link)
            # Use config-based filtering for consistency with frontend configuration
            if final_url and config_based_filter(final_url, config):
                # Remove duplicates
                if final_url not in [r['url'] for r in resolved_links]:
                    resolved_links.append({
                        'url': final_url,
                        'original_url': link if link != final_url else None
                    })
                    resolved_count += 1

        if resolved_links:
            resolved_articles.append({
                'newsletter_subject': subject,
                'newsletter_sender': sender,
                'newsletter_date': date,
                'links': resolved_links,
                'link_count': len(resolved_links)
            })
            print(f"   ✅ Resolved {len(resolved_links)} article URLs\n")
        else:
            print(f"   ⚠️  No valid article URLs found\n")

    # Save results
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save as JSON
    json_file = output_dir / f"resolved_links_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(resolved_articles, f, indent=2, ensure_ascii=False)

    # Save as readable text
    txt_file = output_dir / f"resolved_links_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Resolved Newsletter Links - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total: {len(resolved_articles)} newsletters, {resolved_count} article URLs\n")
        f.write("=" * 80 + "\n\n")

        for item in resolved_articles:
            f.write(f"📧 {item['newsletter_subject']}\n")
            f.write(f"   From: {item['newsletter_sender']}\n")
            f.write(f"   Date: {item['newsletter_date']}\n")
            f.write(f"   Articles ({item['link_count']}):\n\n")

            for link in item['links']:
                f.write(f"   • {link['url']}\n")

            f.write("\n" + "-" * 80 + "\n\n")

    # Save URLs only (for batch extraction)
    urls_file = output_dir / f"article_urls_{timestamp}.txt"
    with open(urls_file, 'w', encoding='utf-8') as f:
        for item in resolved_articles:
            for link in item['links']:
                f.write(f"{link['url']}\n")

    # Print summary
    print(f"\n{'='*80}")
    print(f"📊 Summary:\n")
    print(f"  📧 Newsletters processed: {len(newsletters)}")
    print(f"  🔗 Total links found: {total_links}")
    print(f"  ✅ Article URLs resolved: {resolved_count}")
    print(f"  📄 Newsletters with articles: {len(resolved_articles)}\n")

    print(f"📂 Files saved:")
    print(f"   • {txt_file.name} - Readable format with context")
    print(f"   • {json_file.name} - JSON data with newsletter context")
    print(f"   • {urls_file.name} - Just URLs (reference)\n")
    print(f"📍 Location: {output_dir.absolute()}\n")

    print(f"🚀 Next step: Batch extract these articles through content-engine")
    print(f"   python3.11 batch_extract.py --input {json_file}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Resolve newsletter tracking links to real article URLs',
        epilog='''
Examples:
  # Use config file settings (enabled newsletters, default days)
  python3.11 resolve_links.py

  # Use config with custom days
  python3.11 resolve_links.py --days 3

  # Override config with specific senders
  python3.11 resolve_links.py --senders @therundown.ai @alphasignal.ai

  # Get all newsletters (ignore config)
  python3.11 resolve_links.py --days 7 --max 100
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--days', type=int, help='Days to look back (default: from config or 7)')
    parser.add_argument('--max', type=int, help='Maximum newsletters (default: from config or 30)')
    parser.add_argument(
        '--senders',
        nargs='+',
        help='Filter by sender emails (default: enabled newsletters from config)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config()
    config_settings = config.get('settings', {})

    # Use command-line args if provided, otherwise use config, otherwise use hardcoded defaults
    days_back = args.days if args.days is not None else config_settings.get('default_days_back', 7)
    max_results = args.max if args.max is not None else config_settings.get('max_results', 30)

    # For senders: if command-line provided, use those; otherwise use enabled from config
    senders = args.senders if args.senders else get_enabled_senders_from_config()

    if senders:
        print(f"📋 Using newsletters from config.json:")
        for sender in senders:
            print(f"   • {sender}")
        print()

    extract_and_resolve_links(
        days_back=days_back,
        max_results=max_results,
        senders=senders
    )
