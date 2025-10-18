#!/usr/bin/env python3
"""
NEWSLETTER EXTRACTION PIPELINE

Runs all 4 steps in sequence:
1. Extract from Gmail → raw HTML
2. Extract links from HTML
3. Resolve redirects
4. Filter content

Usage:
  python3.11 pipeline.py              # Use config.json settings
  python3.11 pipeline.py --days 3     # Override days
"""

import sys
from pathlib import Path
from step1_extract_gmail import extract_from_gmail
from step2_extract_links import extract_links_from_directory
from step3_resolve_redirects import resolve_links_from_file
from step4_filter_content import filter_content_from_file


def run_pipeline(days_back=None, senders=None, max_results=None, max_links_per_newsletter=30, extraction_id=None, token_file=None):
    """
    Run complete newsletter extraction pipeline

    Args:
        days_back: Days to look back (None = use config)
        senders: List of sender emails (None = use config)
        max_results: Max newsletters (None = use config)
        max_links_per_newsletter: Limit processing per newsletter
        extraction_id: Pre-generated extraction ID (None = generate new)
        token_file: Path to user's OAuth token JSON file (None = use legacy token)

    Returns:
        Path to extraction directory
    """
    print("\n" + "="*80)
    print(" "*20 + "NEWSLETTER EXTRACTION PIPELINE")
    print("="*80 + "\n")

    # STEP 1: Extract from Gmail
    extraction_dir = extract_from_gmail(
        days_back=days_back,
        senders=senders,
        max_results=max_results,
        extraction_id=extraction_id,
        token_file=token_file
    )

    if not extraction_dir:
        print("\n❌ Pipeline failed at Step 1 (Gmail extraction)")
        sys.exit(1)

    # STEP 2: Extract links from HTML
    print("\n" + "─"*80 + "\n")
    links_file = extract_links_from_directory(extraction_dir)

    if not links_file:
        print("\n❌ Pipeline failed at Step 2 (Link extraction)")
        sys.exit(1)

    # STEP 3: Resolve redirects
    print("\n" + "─"*80 + "\n")
    resolved_file = resolve_links_from_file(
        extraction_dir,
        max_links_per_newsletter=max_links_per_newsletter
    )

    if not resolved_file:
        print("\n❌ Pipeline failed at Step 3 (Redirect resolution)")
        sys.exit(1)

    # STEP 4: Filter content
    print("\n" + "─"*80 + "\n")
    filtered_file = filter_content_from_file(extraction_dir)

    if not filtered_file:
        print("\n❌ Pipeline failed at Step 4 (Content filtering)")
        sys.exit(1)

    # Success!
    print("\n" + "="*80)
    print(" "*20 + "PIPELINE COMPLETE! ✅")
    print("="*80 + "\n")
    print(f"📁 Extraction directory: {extraction_dir}\n")
    print("📂 Files created:")
    print(f"   • config_used.json - Parameters for this run")
    print(f"   • newsletters.json - Newsletter metadata")
    print(f"   • raw_html/ - Raw HTML files")
    print(f"   • extracted_links.json - All extracted links")
    print(f"   • resolved_links.json - Resolved redirects")
    print(f"   • filtered_articles.json - Valid articles only")
    print(f"   • filtered_articles.txt - Human-readable")
    print(f"   • article_urls.txt - URLs for batch extraction")
    print()
    print("🚀 Next step:")
    print(f"   python3.11 batch_extract.py --input {filtered_file}")
    print()

    return extraction_dir


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Run complete newsletter extraction pipeline',
        epilog='''
Examples:
  # Use config.json settings
  python3.11 pipeline.py

  # Override days back
  python3.11 pipeline.py --days 3

  # Override senders
  python3.11 pipeline.py --senders @therundown.ai @alphasignal.ai

  # Override link limit
  python3.11 pipeline.py --max-links 50
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--days', type=float, help='Days to look back (supports fractional days for hours)')
    parser.add_argument('--max', type=int, help='Maximum newsletters')
    parser.add_argument('--senders', nargs='+', help='Filter by sender emails')
    parser.add_argument(
        '--max-links',
        type=int,
        default=30,
        help='Max links per newsletter (default: 30)'
    )
    parser.add_argument('--extraction-id', type=str, help='Pre-generated extraction ID')
    parser.add_argument('--token-file', type=str, help='Path to user OAuth token JSON file')

    args = parser.parse_args()

    run_pipeline(
        days_back=args.days,
        senders=args.senders,
        max_results=args.max,
        max_links_per_newsletter=args.max_links,
        extraction_id=args.extraction_id,
        token_file=args.token_file
    )
