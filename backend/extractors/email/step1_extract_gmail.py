#!/usr/bin/env python3
"""
STEP 1: Extract newsletters from Gmail and save raw HTML

Input: Config file (days_back, senders)
Output: extraction_TIMESTAMP/
        ├── config_used.json
        ├── newsletters.json (metadata)
        └── raw_html/
            ├── newsletter_001.html
            ├── newsletter_002.html
            └── ...
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from gmail_extractor import GmailExtractor


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


def extract_from_gmail(days_back: int = None, senders: List[str] = None, max_results: int = None):
    """
    Step 1: Extract newsletters from Gmail and save raw HTML

    Args:
        days_back: Days to look back (default: from config)
        senders: List of sender emails (default: from config)
        max_results: Max newsletters (default: from config)

    Returns:
        Path to extraction directory
    """
    # Load config
    config = load_config()
    config_settings = config.get('settings', {})

    # Use parameters or fall back to config
    days_back = days_back if days_back is not None else config_settings.get('default_days_back', 7)
    max_results = max_results if max_results is not None else config_settings.get('max_results', 100)
    senders = senders if senders else get_enabled_senders_from_config()

    print("="*80)
    print("STEP 1: EXTRACT FROM GMAIL")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   Days back: {days_back}")
    print(f"   Max results: {max_results}")
    print(f"   Senders: {', '.join(senders) if senders else 'ALL'}\n")

    # Create extraction directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    extraction_dir = Path(__file__).parent / "output" / f"extraction_{timestamp}"
    extraction_dir.mkdir(parents=True, exist_ok=True)

    raw_html_dir = extraction_dir / "raw_html"
    raw_html_dir.mkdir(exist_ok=True)

    print(f"📁 Extraction directory: {extraction_dir.name}\n")

    # Save config used for this extraction
    config_used = {
        "timestamp": timestamp,
        "days_back": days_back,
        "max_results": max_results,
        "senders": senders,
        "created_at": datetime.now().isoformat()
    }

    config_file = extraction_dir / "config_used.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_used, f, indent=2, ensure_ascii=False)

    print("✅ Saved config_used.json\n")

    # Extract from Gmail
    print("📧 Connecting to Gmail...\n")
    extractor = GmailExtractor()
    newsletters = extractor.search_newsletters(
        days_back=days_back,
        max_results=max_results,
        sender_filter=senders
    )

    if not newsletters:
        print("⚠️  No newsletters found")
        return None

    print(f"\n✅ Found {len(newsletters)} newsletters\n")

    # Save raw HTML for each newsletter
    newsletters_metadata = []

    for i, newsletter in enumerate(newsletters, 1):
        subject = newsletter.get('subject', 'Untitled')
        sender = newsletter.get('sender_email', 'Unknown')
        date = newsletter.get('date', 'Unknown')
        body_html = newsletter.get('body_html', '')

        print(f"{i:3d}. {subject[:60]}")
        print(f"      From: {sender}")
        print(f"      Date: {date}")

        # Save raw HTML
        html_filename = f"newsletter_{i:03d}.html"
        html_path = raw_html_dir / html_filename

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(body_html)

        print(f"      Saved: {html_filename}")
        print()

        # Store metadata (without full HTML to keep file size down)
        newsletters_metadata.append({
            "index": i,
            "html_file": html_filename,
            "subject": subject,
            "sender": sender,
            "date": date,
            "html_size": len(body_html)
        })

    # Save newsletters metadata
    metadata_file = extraction_dir / "newsletters.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(newsletters_metadata, f, indent=2, ensure_ascii=False)

    print("="*80)
    print("STEP 1 COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   Newsletters extracted: {len(newsletters)}")
    print(f"   Raw HTML saved: {len(newsletters)} files")
    print(f"   Location: {extraction_dir}")
    print()
    print(f"📂 Files created:")
    print(f"   • config_used.json - Parameters for this extraction")
    print(f"   • newsletters.json - Newsletter metadata")
    print(f"   • raw_html/ - {len(newsletters)} HTML files")
    print()
    print(f"🚀 Next step:")
    print(f"   python3.11 step2_extract_links.py {extraction_dir.name}")
    print()

    return extraction_dir


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Step 1: Extract newsletters from Gmail and save raw HTML',
        epilog='''
Examples:
  # Use config.json settings
  python3.11 step1_extract_gmail.py

  # Override days back
  python3.11 step1_extract_gmail.py --days 3

  # Override senders
  python3.11 step1_extract_gmail.py --senders @therundown.ai @alphasignal.ai
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--days', type=int, help='Days to look back')
    parser.add_argument('--max', type=int, help='Maximum newsletters')
    parser.add_argument('--senders', nargs='+', help='Filter by sender emails')

    args = parser.parse_args()

    extract_from_gmail(
        days_back=args.days,
        senders=args.senders,
        max_results=args.max
    )
