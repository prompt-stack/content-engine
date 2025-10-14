#!/usr/bin/env python3
"""
Reddit URL Resolver
Resolves Reddit short links to canonical permalinks using Brave Search API
"""

import os
import re
import requests
from typing import Optional


def extract_subreddit_from_short_link(url: str) -> Optional[str]:
    """
    Extract subreddit name from Reddit short link

    Args:
        url: Reddit short link like https://www.reddit.com/r/Conservative/s/QeYXyYfV9X

    Returns:
        Subreddit name (e.g., "Conservative") or None if not found
    """
    match = re.search(r'/r/([^/]+)/s/', url)
    return match.group(1) if match else None


def resolve_reddit_short_link(title: str, subreddit: str, api_key: Optional[str] = None) -> str:
    """
    Resolve Reddit short link to canonical permalink using search APIs (Brave + Tavily fallback)

    Args:
        title: Post title (verbatim)
        subreddit: Subreddit name (without r/ prefix)
        api_key: Brave API key (defaults to BRAVE_API_KEY env var)

    Returns:
        Canonical permalink URL

    Raises:
        ValueError: If no permalink found or API error
    """
    # Normalize title
    title = title.strip()
    # Replace fancy quotes with ASCII
    title = title.replace('\u2018', "'").replace('\u2019', "'")
    title = title.replace('\u201c', '"').replace('\u201d', '"')

    permalink_pattern = re.compile(
        r'^https://(www\.)?reddit\.com/r/[^/]+/comments/[a-z0-9]+/',
        re.IGNORECASE
    )

    # Try Brave Search first
    try:
        brave_key = api_key or os.getenv('BRAVE_API_KEY')
        if brave_key:
            query = f'"{title}" site:reddit.com/r/{subreddit}'
            response = requests.get(
                'https://api.search.brave.com/res/v1/web/search',
                params={'q': query},
                headers={'X-Subscription-Token': brave_key, 'Accept': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            results = response.json().get('web', {}).get('results', [])

            for result in results[:5]:
                url = result.get('url', '')
                if permalink_pattern.match(url):
                    return url.split('?')[0].rstrip('/')
    except Exception as e:
        print(f"⚠️  Brave Search failed: {e}")

    # Fallback to Tavily
    try:
        tavily_key = os.getenv('TAVILY_API_KEY')
        if tavily_key:
            query = f'{title} site:reddit.com/r/{subreddit}'
            response = requests.post(
                'https://api.tavily.com/search',
                json={
                    'api_key': tavily_key,
                    'query': query,
                    'search_depth': 'basic',
                    'max_results': 5
                },
                timeout=10
            )
            response.raise_for_status()
            results = response.json().get('results', [])

            for result in results:
                url = result.get('url', '')
                if permalink_pattern.match(url):
                    return url.split('?')[0].rstrip('/')
    except Exception as e:
        print(f"⚠️  Tavily Search failed: {e}")

    raise ValueError(
        f'No permalink found for "{title}" in r/{subreddit}. '
        f'Both Brave and Tavily search failed. The post might be too recent to be indexed.'
    )


def is_short_link(url: str) -> bool:
    """Check if URL is a Reddit short link"""
    return bool(re.search(r'/r/[^/]+/s/', url))


def is_canonical_permalink(url: str) -> bool:
    """Check if URL is already a canonical Reddit permalink"""
    pattern = r'^https://(www\.)?reddit\.com/r/[^/]+/comments/[a-z0-9]+/'
    return bool(re.match(pattern, url, re.IGNORECASE))


# Test if running directly
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python url_resolver.py <title> <subreddit>")
        print("\nExample:")
        print('  python url_resolver.py "Happy Columbus Day" Conservative')
        sys.exit(1)

    title = sys.argv[1]
    subreddit = sys.argv[2]

    try:
        permalink = resolve_reddit_short_link(title, subreddit)
        print(f"\n✅ Found permalink:")
        print(f"   {permalink}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
