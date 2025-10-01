"""
Reddit Poster
Post to subreddits

API: https://www.reddit.com/dev/api/
Auth: OAuth 2.0
"""

import logging
from typing import Dict, Any, Optional
import praw
from app.services.social.base import BaseSocialPoster, AuthenticationError, PostingError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedditPoster(BaseSocialPoster):
    """
    Reddit posting service

    Features:
    - Text posts (self posts)
    - Link posts
    - Subreddit submission
    """

    PLATFORM_NAME = "reddit"
    CHARACTER_LIMIT = None  # No hard limit on Reddit text posts

    supports_markdown = True
    supports_links = True

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize Reddit poster

        Credentials (from .env or passed in):
        - REDDIT_CLIENT_ID
        - REDDIT_CLIENT_SECRET
        - REDDIT_USER_AGENT
        - REDDIT_USERNAME (optional)
        - REDDIT_PASSWORD (optional)
        """
        super().__init__(credentials)

        self.client_id = self.credentials.get('client_id') or settings.REDDIT_CLIENT_ID
        self.client_secret = self.credentials.get('client_secret') or settings.REDDIT_CLIENT_SECRET
        self.user_agent = self.credentials.get('user_agent') or settings.REDDIT_USER_AGENT
        self.username = self.credentials.get('username') or getattr(settings, 'REDDIT_USERNAME', None)
        self.password = self.credentials.get('password') or getattr(settings, 'REDDIT_PASSWORD', None)

        if not all([self.client_id, self.client_secret, self.user_agent]):
            raise AuthenticationError("Reddit API credentials not configured")

    def authenticate(self) -> None:
        """Authenticate with Reddit API"""
        try:
            if self.username and self.password:
                # Username/password auth (for script apps)
                self.client = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent,
                    username=self.username,
                    password=self.password
                )
            else:
                # App-only auth (read-only or will need OAuth flow)
                self.client = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )

            # Verify authentication
            if self.username:
                me = self.client.user.me()
                logger.info(f"Authenticated with Reddit as: u/{me.name}")
            else:
                logger.info("Authenticated with Reddit (app-only mode)")

        except Exception as e:
            logger.error(f"Reddit authentication failed: {e}")
            raise AuthenticationError(f"Reddit auth failed: {str(e)}") from e

    def _post_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Post to Reddit

        Args:
            content: Post text (for self posts) or URL (for link posts)
            subreddit: Subreddit name (required)
            title: Post title (required)
            is_self: True for text post, False for link post
            flair_id: Optional flair ID
            send_replies: Whether to send reply notifications (default True)

        Returns:
            {
                "id": "post_id",
                "url": "https://reddit.com/r/subreddit/...",
                "title": "post title"
            }
        """
        subreddit_name = kwargs.get('subreddit')
        title = kwargs.get('title')
        is_self = kwargs.get('is_self', True)
        flair_id = kwargs.get('flair_id')
        send_replies = kwargs.get('send_replies', True)

        if not subreddit_name:
            raise ValueError("subreddit is required")
        if not title:
            raise ValueError("title is required")

        try:
            subreddit = self.client.subreddit(subreddit_name)

            if is_self:
                # Text post
                submission = subreddit.submit(
                    title=title,
                    selftext=content,
                    flair_id=flair_id,
                    send_replies=send_replies
                )
            else:
                # Link post (content is the URL)
                submission = subreddit.submit(
                    title=title,
                    url=content,
                    flair_id=flair_id,
                    send_replies=send_replies
                )

            return {
                "id": submission.id,
                "url": f"https://reddit.com{submission.permalink}",
                "title": title,
                "subreddit": subreddit_name,
                "platform": "reddit"
            }

        except praw.exceptions.RedditAPIException as e:
            # Check for rate limiting
            if "RATELIMIT" in str(e):
                raise RateLimitError("Reddit rate limit hit") from e
            else:
                raise PostingError(f"Reddit API error: {e}") from e
        except Exception as e:
            raise PostingError(f"Failed to post to Reddit: {e}") from e

    def validate_content(self, content: str, **kwargs) -> None:
        """Validate Reddit post"""
        super().validate_content(content, **kwargs)

        title = kwargs.get('title')
        if not title or not title.strip():
            raise ValueError("Reddit post requires a title")

        if len(title) > 300:
            raise ValueError(f"Reddit title max 300 chars (got {len(title)})")

        subreddit = kwargs.get('subreddit')
        if not subreddit:
            raise ValueError("Subreddit is required")

    def get_character_limit(self) -> Optional[int]:
        """Reddit has no character limit for text posts"""
        return None

    def format_content(self, content: str, use_markdown: bool = True) -> str:
        """
        Format content for Reddit

        Args:
            content: Raw content
            use_markdown: Keep markdown formatting

        Returns:
            Formatted post
        """
        # Reddit supports full markdown, so minimal formatting needed
        return content.strip()

    def post_text(self, subreddit: str, title: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Post text to subreddit (convenience method)

        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            text: Post text (markdown supported)
            **kwargs: Additional options

        Returns:
            Post response
        """
        return self.post(
            content=text,
            subreddit=subreddit,
            title=title,
            is_self=True,
            **kwargs
        )

    def post_link(self, subreddit: str, title: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Post link to subreddit (convenience method)

        Args:
            subreddit: Subreddit name (without r/)
            title: Post title
            url: URL to share
            **kwargs: Additional options

        Returns:
            Post response
        """
        return self.post(
            content=url,
            subreddit=subreddit,
            title=title,
            is_self=False,
            **kwargs
        )