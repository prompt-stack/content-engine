#!/usr/bin/env python3
"""Debug why Alpha Signal tracking links aren't resolving"""
from gmail_extractor import GmailExtractor
from resolve_links import resolve_redirect, is_content_url, is_obvious_junk
import re

extractor = GmailExtractor()
newsletters = extractor.search_newsletters(days_back=3, max_results=30)

# Find Alpha Signal
for newsletter in newsletters:
    if 'alphasignal' in newsletter.get('sender_email', ''):
        print(f"Subject: {newsletter['subject']}\n")

        body_html = newsletter.get('body_html', '')
        link_pattern = r'href=["\']([^"\']+)["\']'
        raw_links = re.findall(link_pattern, body_html)

        # Filter junk
        candidate_links = [link for link in raw_links if not is_obvious_junk(link)]

        # Separate direct vs tracking
        direct_links = []
        tracking_links = []
        tracking_domains = ['link.', '/c?', '/fb/', '/click/', '/track/', '/redirect/', '/r/']

        for link in candidate_links:
            if any(tracker in link.lower() for tracker in tracking_domains):
                tracking_links.append(link)
            else:
                direct_links.append(link)

        print(f"Direct links: {len(direct_links)}")
        print(f"Tracking links: {len(tracking_links)}\n")

        print("=" * 80)
        print("TESTING FIRST 10 TRACKING LINKS:")
        print("=" * 80)

        for i, link in enumerate(tracking_links[:10], 1):
            print(f"\n{i}. Original: {link[:80]}")
            final_url = resolve_redirect(link)
            if final_url:
                print(f"   Resolved: {final_url[:80]}")
                is_content = is_content_url(final_url)
                print(f"   Is content? {is_content}")
                if not is_content:
                    print(f"   WHY NOT CONTENT?")
            else:
                print(f"   ❌ Failed to resolve")

        break
