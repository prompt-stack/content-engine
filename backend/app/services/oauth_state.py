"""OAuth state management for tracking user sessions during OAuth flows."""

from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OAuthStateStore:
    """
    Simple in-memory store for OAuth state parameters.

    Maps state tokens to user IDs for the OAuth callback flow.
    In production, this should use Redis or similar persistent store.
    """

    def __init__(self):
        """Initialize the state store."""
        # state -> (user_id, created_at)
        self._store: Dict[str, tuple[int, datetime]] = {}

    def store_state(self, state: str, user_id: int) -> None:
        """
        Store state parameter with associated user ID.

        Args:
            state: OAuth state token
            user_id: User ID to associate with this state
        """
        self._store[state] = (user_id, datetime.utcnow())
        logger.info(f"Stored OAuth state for user {user_id}")

    def get_user_id(self, state: str) -> Optional[int]:
        """
        Retrieve user ID for a given state token.

        Args:
            state: OAuth state token

        Returns:
            User ID if found and not expired, None otherwise
        """
        if state not in self._store:
            logger.warning(f"State token not found: {state[:10]}...")
            return None

        user_id, created_at = self._store[state]

        # Check if state is expired (15 minutes)
        if datetime.utcnow() - created_at > timedelta(minutes=15):
            logger.warning(f"State token expired for user {user_id}")
            del self._store[state]
            return None

        # Clean up after successful retrieval
        del self._store[state]
        logger.info(f"Retrieved user {user_id} from OAuth state")
        return user_id

    def cleanup_expired(self) -> None:
        """Remove expired state tokens (older than 15 minutes)."""
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        expired_keys = [
            state for state, (_, created_at) in self._store.items()
            if created_at < cutoff
        ]
        for key in expired_keys:
            del self._store[key]
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired OAuth state tokens")


# Global instance
oauth_state_store = OAuthStateStore()
