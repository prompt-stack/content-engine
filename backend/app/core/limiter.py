"""Shared rate limiter instance for the application."""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

def get_rate_limit_storage_uri():
    """
    Get storage URI for rate limiting.

    Uses Redis in production (for distributed rate limiting across Railway instances),
    falls back to in-memory for local development.
    """
    from app.core.config import settings

    # Use Redis if available (required for production/Railway)
    if settings.REDIS_URL:
        logger.info(f"✅ Rate limiting using Redis: {settings.REDIS_URL}")
        return settings.REDIS_URL

    # Fallback to in-memory (only for local dev)
    logger.warning("⚠️  Using in-memory rate limiting (NOT suitable for production)")
    return "memory://"

# Create a single limiter instance with appropriate storage URI
storage_uri = get_rate_limit_storage_uri()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri
)
