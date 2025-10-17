"""Rate limiter configuration using fastapi-limiter."""

import logging
from typing import Callable
from fastapi import Request
from fastapi_limiter.depends import RateLimiter

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """
    Get the key for rate limiting (client IP address).
    Falls back to a default key if IP cannot be determined.
    """
    # Try to get real IP from headers (for proxies/load balancers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    # Ultimate fallback
    return "unknown"


# Pre-configured rate limiters for common use cases
def limit_10_per_minute() -> Callable:
    """Rate limiter: 10 requests per minute."""
    return RateLimiter(times=10, seconds=60)


def limit_5_per_minute() -> Callable:
    """Rate limiter: 5 requests per minute."""
    return RateLimiter(times=5, seconds=60)


def limit_100_per_hour() -> Callable:
    """Rate limiter: 100 requests per hour."""
    return RateLimiter(times=100, seconds=3600)
