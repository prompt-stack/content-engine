#!/usr/bin/env python3
"""
Show the complete link extraction flow from raw HTML
"""
from gmail_extractor import GmailExtractor
import re
import html

print("="*80)
print("STEP 1: Get Raw HTML from Gmail")
print("="*80)

extractor = GmailExtractor()
newsletters = extractor.search_newsletters(days_back=3, max_results=1, sender_filter=['@alphasignal.ai'])

if not newsletters:
    print("No newsletters found!")
    exit()

newsletter = newsletters[0]
print(f"\n📧 Newsletter: {newsletter['subject']}")
print(f"   From: {newsletter['sender_email']}")
print(f"   HTML size: {len(newsletter['body_html']):,} characters")
print(f"\n   First 200 chars of raw HTML:")
print(f"   {'-'*70}")
print(f"   {newsletter['body_html'][:200]}")
print(f"   {'-'*70}")

print("\n" + "="*80)
print("STEP 2: Extract ALL href links using regex")
print("="*80)

body_html = newsletter['body_html']
link_pattern = r'href=["\']([^"\']+)["\']'
raw_links = re.findall(link_pattern, body_html)

print(f"\n✅ Found {len(raw_links)} total links in HTML")
print(f"\nFirst 10 raw links (WITH HTML entities like &amp;):")
for i, link in enumerate(raw_links[:10], 1):
    print(f"{i}. {link[:80]}")

print("\n" + "="*80)
print("STEP 3: Decode HTML entities (&amp; -> &)")
print("="*80)

decoded_links = [html.unescape(link) for link in raw_links]

print(f"\nFirst 10 decoded links (HTML entities fixed):")
for i, link in enumerate(decoded_links[:10], 1):
    print(f"{i}. {link[:80]}")

print("\n" + "="*80)
print("STEP 4: Filter out obvious junk")
print("="*80)

def is_obvious_junk(url: str) -> bool:
    url_lower = url.lower()
    junk_keywords = [
        'unsubscribe', 'preferences', 'settings', 'mailto:', 'tel:',
        '.png', '.jpg', '.gif', '.svg', '.ico', 'favicon'
    ]
    return any(keyword in url_lower for keyword in junk_keywords)

candidate_links = [link for link in decoded_links if not is_obvious_junk(link)]

print(f"\n✅ After filtering junk: {len(candidate_links)} candidate links")
print(f"   (Removed {len(decoded_links) - len(candidate_links)} junk links)")

print("\n" + "="*80)
print("STEP 5: Separate direct links from tracking links")
print("="*80)

direct_links = []
tracking_links = []

tracking_domains = ['link.', '/c?', '/fb/', '/click/', '/track/', '/redirect/', '/r/']
for link in candidate_links:
    if any(tracker in link.lower() for tracker in tracking_domains):
        tracking_links.append(link)
    else:
        direct_links.append(link)

print(f"\n📊 Direct article links: {len(direct_links)}")
print(f"📊 Tracking links: {len(tracking_links)}")

print(f"\nDirect links (likely articles - processed FIRST):")
for i, link in enumerate(direct_links[:5], 1):
    print(f"{i}. {link}")

print(f"\nTracking links (need to be resolved - processed SECOND):")
for i, link in enumerate(tracking_links[:5], 1):
    print(f"{i}. {link[:100]}")

print("\n" + "="*80)
print("STEP 6: Would resolve redirects and filter final destinations")
print("="*80)
print("\nThis step:")
print("- Makes HTTP requests to follow tracking links")
print("- Gets final destination URLs")
print("- Filters to only keep actual content (not homepages, profiles, etc.)")
print("- Removes duplicates")
print("\nResult: Clean list of article URLs!")
