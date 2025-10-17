#!/usr/bin/env python3
from gmail_extractor import GmailExtractor
import re

extractor = GmailExtractor()
newsletters = extractor.search_newsletters(days_back=7, max_results=30)

# Find Alpha Signal
for newsletter in newsletters:
    if 'alphasignal' in newsletter.get('sender_email', ''):
        print(f"Subject: {newsletter['subject']}")
        print(f"Sender: {newsletter['sender_email']}\n")

        body_html = newsletter.get('body_html', '')
        link_pattern = r'href=["\']([^"\']+)["\']'
        raw_links = re.findall(link_pattern, body_html)

        print(f"Total links found: {len(raw_links)}\n")
        print("All unique links:")
        seen = set()
        for i, link in enumerate(raw_links, 1):
            if link not in seen and not any(x in link.lower() for x in ['unsubscribe', 'preferences', 'mailto:', '.png', '.jpg', '.gif', '.svg']):
                seen.add(link)
                print(f"{i}. {link}")
        break
