#!/usr/bin/env python3
"""
STEP 2: Extract links from raw HTML files

Input: extraction_TIMESTAMP/raw_html/*.html
Output: extraction_TIMESTAMP/extracted_links.json
        [
          {
            "newsletter_index": 1,
            "newsletter_subject": "...",
            "raw_links": ["url1", "url2", ...],
            "decoded_links": ["url1", "url2", ...],
            "link_count": 45
          }
        ]
"""

import json
import re
import html
from pathlib import Path
from typing import List, Dict


def extract_links_from_html(html_content: str) -> List[str]:
    """
    Extract all href links from HTML and decode entities

    Args:
        html_content: Raw HTML string

    Returns:
        List of decoded URLs
    """
    # Extract all href="..." patterns
    link_pattern = r'href=["\']([^"\']+)["\']'
    raw_links = re.findall(link_pattern, html_content)

    # Decode HTML entities (&amp; → &, &quot; → ", etc.)
    decoded_links = [html.unescape(link) for link in raw_links]

    return decoded_links


def extract_links_from_directory(extraction_dir: Path):
    """
    Step 2: Extract links from all raw HTML files

    Args:
        extraction_dir: Path to extraction_TIMESTAMP directory

    Returns:
        Path to extracted_links.json
    """
    print("="*80)
    print("STEP 2: EXTRACT LINKS FROM HTML")
    print("="*80)
    print(f"\n📁 Extraction directory: {extraction_dir.name}\n")

    # Load newsletters metadata
    metadata_file = extraction_dir / "newsletters.json"
    if not metadata_file.exists():
        print(f"❌ Error: {metadata_file} not found")
        print("   Run step1_extract_gmail.py first")
        return None

    with open(metadata_file, 'r', encoding='utf-8') as f:
        newsletters_metadata = json.load(f)

    print(f"📧 Found {len(newsletters_metadata)} newsletters\n")

    # Extract links from each newsletter
    raw_html_dir = extraction_dir / "raw_html"
    results = []
    total_links = 0

    for newsletter in newsletters_metadata:
        index = newsletter['index']
        html_file = newsletter['html_file']
        subject = newsletter['subject']
        sender = newsletter['sender']

        print(f"{index:3d}. {subject[:60]}")
        print(f"      From: {sender}")

        # Read raw HTML
        html_path = raw_html_dir / html_file
        if not html_path.exists():
            print(f"      ⚠️  HTML file not found: {html_file}")
            print()
            continue

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Extract links
        decoded_links = extract_links_from_html(html_content)
        link_count = len(decoded_links)
        total_links += link_count

        print(f"      Extracted: {link_count} links (decoded HTML entities)")
        print()

        # Store results
        results.append({
            "newsletter_index": index,
            "newsletter_subject": subject,
            "newsletter_sender": sender,
            "newsletter_date": newsletter['date'],
            "html_file": html_file,
            "links": decoded_links,
            "link_count": link_count
        })

    # Save extracted links
    output_file = extraction_dir / "extracted_links.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("="*80)
    print("STEP 2 COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Newsletters processed: {len(results)}")
    print(f"   Total links extracted: {total_links}")
    print(f"   Average per newsletter: {total_links // len(results) if results else 0}")
    print()
    print(f"📂 File created:")
    print(f"   • extracted_links.json - All links from all newsletters")
    print()
    print(f"🚀 Next step:")
    print(f"   python3.11 step3_resolve_redirects.py {extraction_dir.name}")
    print()

    return output_file


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Step 2: Extract links from raw HTML files',
        epilog='''
Examples:
  # Process specific extraction
  python3.11 step2_extract_links.py extraction_20251015_131800

  # Process latest extraction
  python3.11 step2_extract_links.py latest
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

    extract_links_from_directory(extraction_dir)
