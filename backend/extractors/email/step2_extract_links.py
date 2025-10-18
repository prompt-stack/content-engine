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
from bs4 import BeautifulSoup


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


def find_context_for_link(link_elem) -> str:
    """
    Multi-level context extraction for a link element.

    Tries multiple strategies to find meaningful context:
    1. Link text itself (headline in link)
    2. Following sibling paragraphs (description after headline)
    3. Parent container text (description around link)

    Args:
        link_elem: BeautifulSoup link element

    Returns:
        Context string or None
    """
    # Skip patterns (buttons, navigation, etc.)
    SKIP_PATTERNS = [
        "TRY NOW", "LEARN MORE", "START SECURE AUTH", "SUBSCRIBE",
        "GET STARTED", "SIGN UP", "VIEW ALL", "READ MORE", "CLICK HERE",
        "READ ONLINE", "UNSUBSCRIBE", "ADVERTISE", "TWITTER", "LINKEDIN",
        "FACEBOOK", "INSTAGRAM", "SHARE", "FORWARD"
    ]

    def is_meaningful(text: str) -> bool:
        """Check if text is meaningful context (not a button/nav)."""
        if not text or len(text) < 15:
            return False
        if text.upper() in SKIP_PATTERNS:
            return False
        if text.isupper() and len(text) < 50:  # All-caps short text = button
            return False
        return True

    # LEVEL 1: Link text itself (headline)
    link_text = link_elem.get_text(strip=True)

    # LEVEL 2: Following sibling paragraphs (TheRundown pattern)
    # Look for description in next few siblings
    description = None
    current = link_elem

    # Navigate up to find a container (h4, div, tr, etc.)
    for _ in range(5):  # Check up to 5 parent levels
        parent = current.parent
        if not parent:
            break
        current = parent

        # Check siblings at each level (for nested table structures)
        for sibling in parent.find_next_siblings(limit=5):
            # Look in paragraphs and table cells
            desc_elems = sibling.find_all(['p', 'div', 'td'], limit=5)
            for elem in desc_elems:
                elem_text = elem.get_text(strip=True)
                # Look for description patterns
                if elem_text and len(elem_text) > 50:
                    # Clean up: remove "The Rundown:" prefix, etc.
                    if 'The Rundown:' in elem_text:
                        elem_text = elem_text.split('The Rundown:', 1)[1].strip()
                    if 'The details:' in elem_text:
                        elem_text = elem_text.split('The details:', 1)[1].strip()

                    # Extract first 200 chars
                    desc = elem_text[:200]
                    if is_meaningful(desc):
                        description = desc
                        break
            if description:
                break
        if description:
            break

    # LEVEL 3: Parent container text (inline description)
    if not description:
        parent = link_elem.parent
        if parent:
            # Get parent text excluding the link text
            parent_text = parent.get_text(strip=True)
            if link_text in parent_text:
                # Remove link text to get surrounding context
                parent_text = parent_text.replace(link_text, '', 1).strip()
                if is_meaningful(parent_text):
                    description = parent_text[:200]

    # Combine headline + description
    if is_meaningful(link_text):
        if description:
            # Format: "Headline - Description..."
            combined = f"{link_text} - {description}"
            return combined[:300]  # Limit total length
        else:
            return link_text
    elif description:
        return description

    return None


def extract_links_with_context(html_content: str) -> List[Dict]:
    """
    Extract links WITH curator descriptions from HTML

    Uses multi-level context extraction to find both headlines and descriptions.
    Works across different newsletter formats (TheRundown, AlphaSignal, etc.)

    Args:
        html_content: Raw HTML string

    Returns:
        List of dicts with 'url' and 'curator_description' keys
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    enriched_links = []
    seen_urls = set()  # Avoid duplicates

    for a in soup.find_all('a', href=True):
        url = html.unescape(a['href'])

        # Skip duplicate URLs
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Extract context using multi-level strategy
        context = find_context_for_link(a)

        enriched_links.append({
            "url": url,
            "curator_description": context
        })

    return enriched_links


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

        # Extract links WITH curator descriptions
        enriched_links = extract_links_with_context(html_content)
        link_count = len(enriched_links)
        total_links += link_count

        # Count how many have meaningful descriptions
        with_context_count = sum(1 for link in enriched_links if link['curator_description'])

        print(f"      Extracted: {link_count} links ({with_context_count} with curator descriptions)")
        print()

        # Store results
        results.append({
            "newsletter_index": index,
            "newsletter_subject": subject,
            "newsletter_sender": sender,
            "newsletter_date": newsletter['date'],
            "html_file": html_file,
            "links": enriched_links,
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
