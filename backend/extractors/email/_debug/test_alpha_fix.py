#!/usr/bin/env python3
"""Test if Alpha Signal link extraction is fixed"""
import json

# Load the old data
with open('output/resolved_links_20251015_122105.json', 'r') as f:
    old_data = json.load(f)

# Find Alpha Signal
for newsletter in old_data:
    if 'alphasignal' in newsletter['newsletter_sender']:
        print(f"OLD RESULT:")
        print(f"Newsletter: {newsletter['newsletter_subject']}")
        print(f"Links found: {newsletter['link_count']}")
        print(f"\nLinks:")
        for i, link in enumerate(newsletter['links'], 1):
            print(f"{i}. {link['url']}")

print(f"\n" + "="*80)
print(f"EXPECTED: Should find at least:")
print(f"1. github.com/karpathy/nanochat")
print(f"2. arxiv.org/abs/2506.10943")
print(f"3. Plus any other article links from tracking link resolution")
print(f"\nThe fix prioritizes direct links (github, arxiv) BEFORE tracking links,")
print(f"so they won't be skipped by the 30-link limit.")
