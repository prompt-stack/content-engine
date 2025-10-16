"""Shared rate limiter instance for the application."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create a single limiter instance that will be shared across the app
limiter = Limiter(key_func=get_remote_address)
