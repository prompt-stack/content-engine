#!/usr/bin/env python3
"""
STEP 3: Resolve redirect links to final destinations

Input: extraction_TIMESTAMP/extracted_links.json
Output: extraction_TIMESTAMP/resolved_links.json
        [
          {
            "newsletter_index": 1,
            "newsletter_subject": "...",
            "links": [
              {
                "original_url": "https://tracking.com/xyz",
                "resolved_url": "https://article.com/final",
                "is_redirect": true,
                "status": "success"
              }
            ]
          }
        ]
"""

import json
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional


def is_obvious_junk(url: str) -> bool:
    """Check if URL is obviously junk (unsubscribe, preferences, etc)"""
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


def resolve_redirect(url: str, timeout: int = 10, retries: int = 2) -> Optional[Dict]:
    """
    Follow redirects to get final destination URL (with retry logic)

    Args:
        url: Starting URL (tracking link)
        timeout: Request timeout in seconds
        retries: Number of retry attempts for failed requests

    Returns:
        Dict with resolution info or None if failed
    """
    last_error = None

    for attempt in range(retries + 1):
        try:
            # Use HEAD request to avoid downloading content
            response = requests.head(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
            )

            final_url = response.url

            # If HEAD didn't work, try GET
            if response.status_code >= 400:
                response = requests.get(
                    url,
                    allow_redirects=True,
                    timeout=timeout,
                    stream=True,  # Don't download body
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsletterBot/1.0)'}
                )
                final_url = response.url

            return {
                "original_url": url,
                "resolved_url": final_url,
                "is_redirect": final_url != url,
                "status_code": response.status_code,
                "status": "success",
                "attempts": attempt + 1
            }

        except requests.exceptions.Timeout as e:
            last_error = {"status": "timeout"}
            if attempt < retries:
                time.sleep(0.5)  # Brief pause before retry
                continue

        except requests.exceptions.RequestException as e:
            last_error = {"status": "error", "error": str(e)[:100]}
            if attempt < retries:
                time.sleep(0.5)
                continue

        except Exception as e:
            last_error = {"status": "error", "error": str(e)[:100]}
            if attempt < retries:
                time.sleep(0.5)
                continue

    # All retries failed, return last error
    return {
        "original_url": url,
        "resolved_url": None,
        "is_redirect": False,
        "attempts": retries + 1,
        **last_error
    }


def resolve_links_from_file(extraction_dir: Path, max_links_per_newsletter: int = 30):
    """
    Step 3: Resolve redirect links to final destinations

    Args:
        extraction_dir: Path to extraction_TIMESTAMP directory
        max_links_per_newsletter: Limit processing to avoid rate limits

    Returns:
        Path to resolved_links.json
    """
    print("="*80)
    print("STEP 3: RESOLVE REDIRECTS")
    print("="*80)
    print(f"\n📁 Extraction directory: {extraction_dir.name}\n")

    # Load extracted links
    links_file = extraction_dir / "extracted_links.json"
    if not links_file.exists():
        print(f"❌ Error: {links_file} not found")
        print("   Run step2_extract_links.py first")
        return None

    with open(links_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)

    print(f"📧 Found {len(extracted_data)} newsletters\n")

    # Resolve links for each newsletter
    results = []
    total_links = 0
    total_resolved = 0
    total_filtered = 0
    total_failed = 0
    total_duplicates = 0

    # Global cache for deduplication across all newsletters
    resolution_cache = {}

    for newsletter_data in extracted_data:
        index = newsletter_data['newsletter_index']
        subject = newsletter_data['newsletter_subject']
        sender = newsletter_data['newsletter_sender']
        links = newsletter_data['links']

        print(f"{index:3d}. {subject[:60]}")
        print(f"      From: {sender}")
        print(f"      Links: {len(links)} total")

        # Filter obvious junk BEFORE resolving
        candidate_links = [link for link in links if not is_obvious_junk(link)]
        filtered_count = len(links) - len(candidate_links)
        total_filtered += filtered_count

        print(f"      Filtered: {filtered_count} junk links")

        # Prioritize direct links over tracking links
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

        # DEDUPLICATION: Find unique links only
        unique_links = []
        seen_in_newsletter = set()
        for link in prioritized_links[:max_links_per_newsletter]:
            if link not in seen_in_newsletter:
                seen_in_newsletter.add(link)
                unique_links.append(link)

        duplicate_count = len(prioritized_links[:max_links_per_newsletter]) - len(unique_links)
        total_duplicates += duplicate_count
        total_links += len(unique_links)

        print(f"      Unique: {len(unique_links)} links ({len(direct_links)} direct, {len(tracking_links)} tracking)")
        if duplicate_count > 0:
            print(f"      Skipped: {duplicate_count} duplicates")

        # Resolve redirects with progress feedback
        resolved_links = []
        for i, link in enumerate(unique_links, 1):
            # Check cache first
            if link in resolution_cache:
                result = resolution_cache[link]
                print(f"      [{i}/{len(unique_links)}] Cached: {link[:50]}...")
            else:
                print(f"      [{i}/{len(unique_links)}] Resolving: {link[:50]}...", end='', flush=True)
                result = resolve_redirect(link)
                resolution_cache[link] = result  # Cache result

                # Progress indicator
                if result['status'] == 'success':
                    print(f" ✓ {result.get('attempts', 1)} attempt(s)")
                else:
                    print(f" ✗ {result['status']}")

            if result:
                resolved_links.append(result)
                if result['status'] == 'success':
                    total_resolved += 1
                else:
                    total_failed += 1

        success_count = len([r for r in resolved_links if r['status'] == 'success'])
        print(f"      Summary: {success_count} successful, {len(resolved_links) - success_count} failed")
        print()

        # Store results
        results.append({
            "newsletter_index": index,
            "newsletter_subject": subject,
            "newsletter_sender": sender,
            "newsletter_date": newsletter_data['newsletter_date'],
            "html_file": newsletter_data['html_file'],
            "links": resolved_links,
            "link_count": len(resolved_links)
        })

    # Save resolved links
    output_file = extraction_dir / "resolved_links.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("="*80)
    print("STEP 3 COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Newsletters processed: {len(results)}")
    print(f"   Total unique links: {total_links}")
    print(f"   Filtered (junk): {total_filtered}")
    print(f"   Skipped (duplicates): {total_duplicates}")
    print(f"   Resolved (success): {total_resolved}")
    print(f"   Failed/timeout: {total_failed}")
    print(f"   Cache hits: {len(resolution_cache) - total_links}")
    print()
    print(f"⚡ Efficiency:")
    if total_links > 0:
        success_rate = (total_resolved / total_links * 100) if total_links else 0
        print(f"   Success rate: {success_rate:.1f}%")
        if total_duplicates > 0:
            print(f"   Time saved by dedup: ~{total_duplicates * 2}s")
    print()
    print(f"📂 File created:")
    print(f"   • resolved_links.json - All links with final destinations")
    print()
    print(f"🚀 Next step:")
    print(f"   python3.11 step4_filter_content.py {extraction_dir.name}")
    print()

    return output_file


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Step 3: Resolve redirect links to final destinations',
        epilog='''
Examples:
  # Process specific extraction
  python3.11 step3_resolve_redirects.py extraction_20251015_131800

  # Process latest extraction
  python3.11 step3_resolve_redirects.py latest

  # Process with custom limit
  python3.11 step3_resolve_redirects.py latest --max 50
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'extraction_dir',
        help='Extraction directory name (or "latest" for most recent)'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=30,
        help='Max links per newsletter (default: 30)'
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

    resolve_links_from_file(extraction_dir, max_links_per_newsletter=args.max)
