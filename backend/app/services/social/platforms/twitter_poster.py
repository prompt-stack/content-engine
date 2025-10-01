"""
Twitter (X) Poster
Post tweets and threads to Twitter/X

API: https://developer.twitter.com/en/docs/twitter-api
Auth: OAuth 2.0 with PKCE
"""

import logging
from typing import Dict, Any, Optional, List
import tweepy
from app.services.social.base import BaseSocialPoster, AuthenticationError, PostingError, RateLimitError
from app.core.config import settings

logger = logging.getLogger(__name__)


class TwitterPoster(BaseSocialPoster):
    """
    Twitter/X posting service

    Features:
    - Single tweets (280 characters)
    - Threads (multiple tweets)
    - Media attachments (images, videos)
    - Reply tweets
    """

    PLATFORM_NAME = "twitter"
    CHARACTER_LIMIT = 280
    MAX_MEDIA_PER_TWEET = 4

    supports_images = True
    supports_videos = True
    supports_threads = True

    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize Twitter poster

        Credentials (from .env or passed in):
        - TWITTER_API_KEY
        - TWITTER_API_SECRET
        - TWITTER_ACCESS_TOKEN
        - TWITTER_ACCESS_SECRET
        """
        super().__init__(credentials)

        self.api_key = self.credentials.get('api_key') or settings.TWITTER_API_KEY
        self.api_secret = self.credentials.get('api_secret') or settings.TWITTER_API_SECRET
        self.access_token = self.credentials.get('access_token') or settings.TWITTER_ACCESS_TOKEN
        self.access_secret = self.credentials.get('access_secret') or settings.TWITTER_ACCESS_SECRET

        if not all([self.api_key, self.api_secret]):
            raise AuthenticationError("Twitter API credentials not configured")

    def authenticate(self) -> None:
        """
        Authenticate with Twitter API using OAuth 1.0a

        For now using API keys (simpler).
        TODO: Implement OAuth 2.0 with PKCE for user auth
        """
        try:
            # Create API client with credentials
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)

            if self.access_token and self.access_secret:
                # Use existing access tokens
                auth.set_access_token(self.access_token, self.access_secret)
            else:
                # Need user authorization (OAuth flow)
                raise AuthenticationError(
                    "Twitter access tokens not configured. "
                    "Please set TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET"
                )

            # Create API v2 client
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            # Verify credentials
            me = self.client.get_me()
            logger.info(f"Authenticated as Twitter user: @{me.data.username}")

        except tweepy.TweepyException as e:
            logger.error(f"Twitter authentication failed: {e}")
            raise AuthenticationError(f"Twitter auth failed: {str(e)}") from e

    def _post_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Post a tweet

        Args:
            content: Tweet text (max 280 chars)
            media_ids: List of uploaded media IDs
            reply_to: Tweet ID to reply to
            quote_tweet_id: Tweet ID to quote

        Returns:
            {
                "id": "tweet_id",
                "url": "https://twitter.com/user/status/id",
                "text": "posted text"
            }
        """
        media_ids = kwargs.get('media_ids')
        reply_to = kwargs.get('reply_to')
        quote_tweet_id = kwargs.get('quote_tweet_id')

        try:
            response = self.client.create_tweet(
                text=content,
                media_ids=media_ids,
                in_reply_to_tweet_id=reply_to,
                quote_tweet_id=quote_tweet_id
            )

            tweet_id = response.data['id']

            # Get username for URL
            me = self.client.get_me()
            username = me.data.username
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"

            return {
                "id": tweet_id,
                "url": tweet_url,
                "text": content,
                "platform": "twitter"
            }

        except tweepy.TooManyRequests as e:
            raise RateLimitError("Twitter rate limit hit") from e
        except tweepy.Forbidden as e:
            raise AuthenticationError(f"Twitter auth error: {e}") from e
        except tweepy.TweepyException as e:
            raise PostingError(f"Failed to post tweet: {e}") from e

    def post_thread(self, tweets: List[str], media_ids_list: Optional[List[List[str]]] = None) -> List[Dict[str, Any]]:
        """
        Post a Twitter thread

        Args:
            tweets: List of tweet texts
            media_ids_list: Optional list of media IDs per tweet

        Returns:
            List of tweet responses
        """
        if not tweets:
            raise ValueError("Thread must contain at least one tweet")

        if media_ids_list and len(media_ids_list) != len(tweets):
            raise ValueError("media_ids_list must match tweets length")

        results = []
        reply_to = None

        for i, tweet_text in enumerate(tweets):
            media_ids = media_ids_list[i] if media_ids_list else None

            result = self.post(
                tweet_text,
                media_ids=media_ids,
                reply_to=reply_to
            )

            results.append(result)
            reply_to = result['id']  # Next tweet replies to this one

        return results

    def validate_content(self, content: str, **kwargs) -> None:
        """Validate tweet content"""
        super().validate_content(content, **kwargs)

        if len(content) > self.CHARACTER_LIMIT:
            raise ValueError(
                f"Tweet exceeds {self.CHARACTER_LIMIT} characters "
                f"(got {len(content)}). Consider using post_thread()."
            )

        media_ids = kwargs.get('media_ids', [])
        if media_ids and len(media_ids) > self.MAX_MEDIA_PER_TWEET:
            raise ValueError(
                f"Twitter allows max {self.MAX_MEDIA_PER_TWEET} media per tweet "
                f"(got {len(media_ids)})"
            )

    def get_character_limit(self) -> int:
        """Get Twitter character limit"""
        return self.CHARACTER_LIMIT

    def format_content(self, content: str, add_thread_numbers: bool = False, thread_index: int = 0, thread_total: int = 1) -> str:
        """
        Format content for Twitter

        Args:
            content: Raw content
            add_thread_numbers: Add (1/3) style numbering
            thread_index: Current thread position (0-indexed)
            thread_total: Total tweets in thread

        Returns:
            Formatted tweet text
        """
        formatted = content.strip()

        # Add thread numbers if requested
        if add_thread_numbers and thread_total > 1:
            thread_suffix = f" ({thread_index + 1}/{thread_total})"
            max_length = self.CHARACTER_LIMIT - len(thread_suffix)

            if len(formatted) > max_length:
                formatted = formatted[:max_length - 3] + "..."

            formatted += thread_suffix

        # Ensure under character limit
        if len(formatted) > self.CHARACTER_LIMIT:
            formatted = formatted[:self.CHARACTER_LIMIT - 3] + "..."

        return formatted

    @staticmethod
    def split_into_thread(long_text: str, max_length: int = 270) -> List[str]:
        """
        Split long text into tweet-sized chunks for threading

        Args:
            long_text: Text to split
            max_length: Max chars per tweet (leave room for thread numbers)

        Returns:
            List of tweet texts
        """
        if len(long_text) <= max_length:
            return [long_text]

        # Split by paragraphs first
        paragraphs = long_text.split('\n\n')
        tweets = []
        current_tweet = ""

        for para in paragraphs:
            # If paragraph fits in current tweet
            if len(current_tweet) + len(para) + 2 <= max_length:
                current_tweet += para + "\n\n"
            # If paragraph fits in new tweet
            elif len(para) <= max_length:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = para + "\n\n"
            # If paragraph too long, split by sentences
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                    current_tweet = ""

                sentences = para.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    if not sentence.endswith('.'):
                        sentence += '.'

                    if len(current_tweet) + len(sentence) + 1 <= max_length:
                        current_tweet += sentence + " "
                    else:
                        if current_tweet:
                            tweets.append(current_tweet.strip())
                        current_tweet = sentence + " "

        if current_tweet:
            tweets.append(current_tweet.strip())

        return tweets