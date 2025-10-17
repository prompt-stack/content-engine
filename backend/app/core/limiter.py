"""
Rate limiter configuration using fastapi-limiter.

Note: RateLimiter instances are created directly in endpoint dependencies.
Example: dependencies=[Depends(RateLimiter(times=10, seconds=60))]

This file is kept for documentation purposes.
"""

# Rate limiting is now configured directly in endpoints using:
# from fastapi_limiter.depends import RateLimiter
# dependencies=[Depends(RateLimiter(times=N, seconds=M))]

# Common rate limits used in the API:
# - LLM endpoints: 10 requests/minute
# - Extractor endpoints: 5 requests/minute
# - Other endpoints: As needed
