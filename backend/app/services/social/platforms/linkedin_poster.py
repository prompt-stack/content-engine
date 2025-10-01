"""
LinkedIn Poster
Post updates to LinkedIn personal profile or company pages

API: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/posts-api
Auth: OAuth 2.0
"""

import logging
from typing import Dict, Any, Optional
import requests
from app.services.social.base import BaseSocialPoster, AuthenticationError, PostingError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkedInPoster(BaseSocialPoster):
    """
    LinkedIn posting service

    Features:
    - Personal profile posts (3000 characters)
    - Company page posts
    - Image attachments
    - Article sharing
    """

    PLATFORM_NAME = "linkedin"
    CHARACTER_LIMIT = 3000  # LinkedIn allows 3000 chars
    API_BASE_URL = "https://api.linkedin.com/v2"

    supports_images = True
    supports_videos = False  # Videos require additional upload flow
    supports_articles = True

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize LinkedIn poster

        Credentials (from .env or passed in):
        - LINKEDIN_CLIENT_ID
        - LINKEDIN_CLIENT_SECRET
        - LINKEDIN_ACCESS_TOKEN
        """
        super().__init__(credentials)

        self.client_id = self.credentials.get('client_id') or settings.LINKEDIN_CLIENT_ID
        self.client_secret = self.credentials.get('client_secret') or settings.LINKEDIN_CLIENT_SECRET
        self.access_token = self.credentials.get('access_token') or settings.LINKEDIN_ACCESS_TOKEN

        if not all([self.client_id, self.client_secret]):
            raise AuthenticationError("LinkedIn API credentials not configured")

        self.user_id = None

    def authenticate(self) -> None:
        """
        Authenticate with LinkedIn API

        For now using access token from env.
        TODO: Implement full OAuth 2.0 flow
        """
        if not self.access_token:
            raise AuthenticationError(
                "LinkedIn access token not configured. "
                "Please set LINKEDIN_ACCESS_TOKEN in .env"
            )

        # Verify token and get user ID
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f"{self.API_BASE_URL}/me",
                headers=headers
            )

            if response.status_code == 401:
                raise AuthenticationError("LinkedIn access token invalid or expired")

            response.raise_for_status()
            user_data = response.json()

            self.user_id = user_data['id']
            self.client = True  # Mark as authenticated
            logger.info(f"Authenticated with LinkedIn as user: {self.user_id}")

        except requests.RequestException as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            raise AuthenticationError(f"LinkedIn auth failed: {str(e)}") from e

    def _post_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Post to LinkedIn

        Args:
            content: Post text (max 3000 chars)
            link_url: URL to share
            link_title: Title for link preview
            link_description: Description for link preview
            image_url: URL of image to attach

        Returns:
            {
                "id": "post_id",
                "url": "https://www.linkedin.com/feed/update/urn:li:share:id",
                "text": "posted text"
            }
        """
        if not self.access_token:
            raise AuthenticationError("Not authenticated")

        link_url = kwargs.get('link_url')
        link_title = kwargs.get('link_title')
        link_description = kwargs.get('link_description')
        image_url = kwargs.get('image_url')

        # Build post payload
        author = f"urn:li:person:{self.user_id}"

        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Add link if provided
        if link_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": link_url,
                    "title": {
                        "text": link_title or "Shared Article"
                    },
                    "description": {
                        "text": link_description or ""
                    }
                }
            ]

        # Add image if provided (different flow than articles)
        if image_url and not link_url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            # Note: Image upload requires additional API calls
            # This is simplified - full implementation would upload image first

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            response = requests.post(
                f"{self.API_BASE_URL}/ugcPosts",
                headers=headers,
                json=payload
            )

            if response.status_code == 429:
                raise RateLimitError("LinkedIn rate limit hit")

            if response.status_code == 401:
                raise AuthenticationError("LinkedIn token expired")

            response.raise_for_status()

            # Extract post ID from response header
            post_id = response.headers.get('X-RestLi-Id')
            post_url = f"https://www.linkedin.com/feed/update/{post_id}"

            return {
                "id": post_id,
                "url": post_url,
                "text": content,
                "platform": "linkedin"
            }

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("LinkedIn rate limit exceeded") from e
            elif e.response.status_code == 401:
                raise AuthenticationError("LinkedIn authentication failed") from e
            else:
                raise PostingError(f"Failed to post to LinkedIn: {e}") from e
        except requests.RequestException as e:
            raise PostingError(f"Network error posting to LinkedIn: {e}") from e

    def validate_content(self, content: str, **kwargs) -> None:
        """Validate LinkedIn post content"""
        super().validate_content(content, **kwargs)

        if len(content) > self.CHARACTER_LIMIT:
            raise ValueError(
                f"LinkedIn post exceeds {self.CHARACTER_LIMIT} characters "
                f"(got {len(content)})"
            )

    def get_character_limit(self) -> int:
        """Get LinkedIn character limit"""
        return self.CHARACTER_LIMIT

    def format_content(self, content: str, professional: bool = True) -> str:
        """
        Format content for LinkedIn

        Args:
            content: Raw content
            professional: Apply professional formatting

        Returns:
            Formatted LinkedIn post
        """
        formatted = content.strip()

        if professional:
            # Capitalize first letter if not already
            if formatted and formatted[0].islower():
                formatted = formatted[0].upper() + formatted[1:]

            # Ensure professional tone (basic check)
            # Remove casual emoji spam, keep professional ones
            # This is a simple implementation - could be enhanced with NLP

        # Ensure under character limit
        if len(formatted) > self.CHARACTER_LIMIT:
            formatted = formatted[:self.CHARACTER_LIMIT - 3] + "..."

        return formatted

    def post_article(self, title: str, content: str, link_url: str, link_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Post an article link to LinkedIn

        Args:
            title: Article title
            content: Post commentary about the article
            link_url: URL to the article
            link_description: Optional article description

        Returns:
            Post response
        """
        return self.post(
            content=content,
            link_url=link_url,
            link_title=title,
            link_description=link_description
        )