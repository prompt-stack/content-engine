"""Google OAuth helper for web-based authentication."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleOAuthHelper:
    """Handle Google OAuth web flow for Gmail API access."""

    # Gmail API scopes
    SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
    ]

    def __init__(self):
        """Initialize OAuth helper with settings."""
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google OAuth credentials not configured")

    def get_authorization_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: Random state string for CSRF protection

        Returns:
            Authorization URL for user to visit
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Request refresh token
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent to get refresh token
        )

        return authorization_url

    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            state: State string for verification

        Returns:
            Dictionary containing token data

        Raises:
            Exception: If token exchange fails
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
            state=state,
            redirect_uri=self.redirect_uri
        )

        # Exchange code for token
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Get user info
        user_info = self._get_user_info(credentials)

        # Build token data
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "email": user_info.get("email"),
            "user_id": user_info.get("id"),
            "picture": user_info.get("picture"),
        }

        return token_data

    def refresh_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh an expired access token.

        Args:
            token_data: Dictionary containing token information

        Returns:
            Updated token data

        Raises:
            Exception: If refresh fails
        """
        credentials = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )

        # Import here to avoid circular dependency
        from google.auth.transport.requests import Request

        # Refresh the token
        credentials.refresh(Request())

        # Update token data
        token_data["token"] = credentials.token
        if credentials.expiry:
            token_data["expiry"] = credentials.expiry.isoformat()

        return token_data

    def _get_user_info(self, credentials: Credentials) -> Dict[str, str]:
        """
        Get user info from Google.

        Args:
            credentials: Google OAuth credentials

        Returns:
            Dictionary with user info (email, id, picture)
        """
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {}

    def get_credentials_from_token_data(self, token_data: Dict[str, Any]) -> Credentials:
        """
        Convert token data dictionary to Google Credentials object.

        Args:
            token_data: Dictionary containing token information

        Returns:
            Google Credentials object
        """
        expiry = None
        if token_data.get("expiry"):
            expiry = datetime.fromisoformat(token_data["expiry"])

        return Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", self.client_id),
            client_secret=token_data.get("client_secret", self.client_secret),
            scopes=token_data.get("scopes", self.SCOPES),
            expiry=expiry
        )

    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if token is expired.

        Args:
            token_data: Dictionary containing token information

        Returns:
            True if token is expired, False otherwise
        """
        if not token_data.get("expiry"):
            return False

        expiry = datetime.fromisoformat(token_data["expiry"])
        # Add 5-minute buffer
        return datetime.utcnow() >= (expiry - timedelta(minutes=5))


# Global instance
google_oauth = GoogleOAuthHelper()
