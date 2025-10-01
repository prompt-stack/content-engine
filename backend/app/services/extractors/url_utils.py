"""URL utility functions for extractors"""

import httpx
from typing import Optional


async def expand_url(url: str, timeout: int = 10) -> str:
    """
    Expand shortened/mobile URLs by following redirects.

    Args:
        url: URL to expand (can be shortened like t.co, bit.ly, or mobile links)
        timeout: Request timeout in seconds

    Returns:
        Expanded full URL
    """
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            # Use HEAD request to avoid downloading content
            response = await client.head(url)
            return str(response.url)
    except Exception:
        # If expansion fails, return original URL
        return url


def is_mobile_or_shortened_url(url: str) -> bool:
    """Check if URL is a mobile or shortened link that needs expansion."""
    mobile_patterns = [
        '/t/',  # TikTok mobile
        '/s/',  # Reddit mobile
        'vm.tiktok.com',  # TikTok short link
        'vt.tiktok.com',  # TikTok short link
        'redd.it',  # Reddit short link
        'youtu.be',  # YouTube short link
        't.co',  # Twitter short link
        'bit.ly',  # Bitly
        'tinyurl.com',  # TinyURL
    ]

    return any(pattern in url for pattern in mobile_patterns)