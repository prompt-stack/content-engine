#!/usr/bin/env python3
"""Show raw HTML pulled from Gmail"""
from gmail_extractor import GmailExtractor
from pathlib import Path

extractor = GmailExtractor()
newsletters = extractor.search_newsletters(days_back=3, max_results=5)

output_dir = Path(__file__).parent / "output" / "raw_html"
output_dir.mkdir(exist_ok=True, parents=True)

print(f"📧 Found {len(newsletters)} newsletters\n")

for i, newsletter in enumerate(newsletters, 1):
    subject = newsletter.get('subject', 'Untitled')
    sender = newsletter.get('sender_email', 'Unknown')
    body_html = newsletter.get('body_html', '')

    print(f"{i}. {subject[:60]}")
    print(f"   From: {sender}")
    print(f"   HTML size: {len(body_html):,} characters")

    # Save raw HTML to file
    safe_name = subject[:50].replace('/', '_').replace(':', '_')
    filename = f"newsletter_{i}_{safe_name}.html"
    filepath = output_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(body_html)

    print(f"   Saved to: {filepath}")

    # Show first 500 chars
    print(f"\n   First 500 chars:")
    print(f"   {'-'*70}")
    print(f"   {body_html[:500]}")
    print(f"   {'-'*70}\n")

print(f"\n📂 All raw HTML files saved to: {output_dir.absolute()}")
