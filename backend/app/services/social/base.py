"""
Base Social Media Poster
Common functionality for all social platforms

Pattern based on youtube-uploader-tool OAuth and retry logic
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SocialPostingError(Exception):
    """Base exception for social posting errors"""
    pass


class AuthenticationError(SocialPostingError):
    """OAuth authentication failed"""
    pass


class PostingError(SocialPostingError):
    """Failed to post content"""
    pass


class RateLimitError(SocialPostingError):
    """Hit API rate limit"""
    pass


class BaseSocialPoster(ABC):
    """
    Base class for all social media platforms

    Implements:
    - OAuth token management (from YouTube uploader pattern)
    - Retry logic with exponential backoff
    - Error handling
    - Token storage
    """

    # Platform name (override in subclass)
    PLATFORM_NAME = "base"

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # Exponential: 2^attempt seconds

    # Token storage
    TOKEN_DIR = Path("config/social_tokens")

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize social poster

        Args:
            credentials: Platform credentials (client_id, client_secret, etc)
        """
        self.credentials = credentials or {}
        self.client = None
        self._ensure_token_dir()

    def _ensure_token_dir(self):
        """Create token storage directory if needed"""
        self.TOKEN_DIR.mkdir(parents=True, exist_ok=True)

    def _get_token_path(self) -> Path:
        """Get path to token file for this platform"""
        return self.TOKEN_DIR / f"{self.PLATFORM_NAME}_oauth.json"

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """Load OAuth token from file (YouTube pattern)"""
        token_path = self._get_token_path()
        if not token_path.exists():
            return None

        try:
            with open(token_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load token for {self.PLATFORM_NAME}: {e}")
            return None

    def _save_token(self, token: Dict[str, Any]):
        """Save OAuth token to file (YouTube pattern)"""
        token_path = self._get_token_path()
        try:
            with open(token_path, 'w') as f:
                json.dump(token, f, indent=2)
            logger.info(f"Token saved for {self.PLATFORM_NAME}")
        except Exception as e:
            logger.error(f"Failed to save token for {self.PLATFORM_NAME}: {e}")
            raise

    @abstractmethod
    def authenticate(self) -> None:
        """
        Authenticate with platform using OAuth

        Subclasses should:
        1. Check for existing token (_load_token)
        2. Refresh if expired
        3. Run OAuth flow if needed
        4. Save token (_save_token)
        """
        raise NotImplementedError

    @abstractmethod
    def _post_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Post content to platform (implement in subclass)

        Args:
            content: Text content to post
            **kwargs: Platform-specific options

        Returns:
            Response with post ID and URL
        """
        raise NotImplementedError

    def post(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Post content with retry logic (YouTube pattern)

        Args:
            content: Text content to post
            **kwargs: Platform-specific options (media, tags, etc)

        Returns:
            Response with post ID and URL

        Raises:
            PostingError: After max retries
            AuthenticationError: If auth fails
        """
        # Ensure authenticated
        if not self.client:
            self.authenticate()

        # Validate content
        self.validate_content(content, **kwargs)

        # Post with retry logic
        retry = 0
        last_error = None

        while retry <= self.MAX_RETRIES:
            try:
                logger.info(f"Posting to {self.PLATFORM_NAME} (attempt {retry + 1}/{self.MAX_RETRIES + 1})")
                result = self._post_content(content, **kwargs)
                logger.info(f"Successfully posted to {self.PLATFORM_NAME}: {result.get('url', result.get('id'))}")
                return result

            except RateLimitError as e:
                # Rate limit hit - wait longer
                if retry < self.MAX_RETRIES:
                    wait_time = 60 * (2 ** retry)  # 60s, 120s, 240s
                    logger.warning(f"Rate limit hit on {self.PLATFORM_NAME}, waiting {wait_time}s")
                    time.sleep(wait_time)
                    retry += 1
                    last_error = e
                else:
                    raise PostingError(f"Rate limit exceeded on {self.PLATFORM_NAME}") from e

            except (ConnectionError, TimeoutError) as e:
                # Network error - retry with backoff
                if retry < self.MAX_RETRIES:
                    wait_time = self.RETRY_DELAY_BASE ** retry
                    logger.warning(f"Network error on {self.PLATFORM_NAME}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    retry += 1
                    last_error = e
                else:
                    raise PostingError(f"Network error after {self.MAX_RETRIES} retries") from e

            except AuthenticationError as e:
                # Auth error - try re-authenticating once
                if retry == 0:
                    logger.warning(f"Auth error on {self.PLATFORM_NAME}, re-authenticating")
                    self.authenticate()
                    retry += 1
                    last_error = e
                else:
                    raise PostingError(f"Authentication failed on {self.PLATFORM_NAME}") from e

            except Exception as e:
                # Unexpected error - fail fast
                logger.error(f"Unexpected error posting to {self.PLATFORM_NAME}: {e}")
                raise PostingError(f"Failed to post to {self.PLATFORM_NAME}: {str(e)}") from e

        # If we get here, all retries failed
        raise PostingError(f"Failed to post to {self.PLATFORM_NAME} after {self.MAX_RETRIES + 1} attempts") from last_error

    def validate_content(self, content: str, **kwargs) -> None:
        """
        Validate content for platform (override in subclass)

        Args:
            content: Text content
            **kwargs: Platform-specific options

        Raises:
            ValueError: If content invalid
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

    @abstractmethod
    def get_character_limit(self) -> Optional[int]:
        """Get character limit for platform (None if unlimited)"""
        raise NotImplementedError

    def format_content(self, content: str, **kwargs) -> str:
        """
        Format content for platform (override for platform-specific formatting)

        Args:
            content: Raw content
            **kwargs: Formatting options

        Returns:
            Formatted content
        """
        # Base implementation: truncate to character limit
        limit = self.get_character_limit()
        if limit and len(content) > limit:
            return content[:limit - 3] + "..."
        return content

    @classmethod
    def get_platform_info(cls) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": cls.PLATFORM_NAME,
            "character_limit": cls.get_character_limit(cls),
            "supports_media": hasattr(cls, "supports_images") and cls.supports_images,
            "requires_oauth": True
        }