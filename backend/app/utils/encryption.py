"""Token encryption utilities for secure storage of OAuth tokens."""

import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


class TokenEncryption:
    """Handle encryption and decryption of OAuth tokens."""

    def __init__(self):
        """Initialize encryption with key from settings."""
        # Derive a proper Fernet key from the encryption key in settings
        key = settings.GOOGLE_TOKEN_ENCRYPTION_KEY.encode()

        # Use PBKDF2HMAC to derive a proper 32-byte key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'google_oauth_token_salt',  # Static salt for deterministic key
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))

        self.cipher = Fernet(derived_key)

    def encrypt_token(self, token_data: Dict[str, Any]) -> str:
        """
        Encrypt token data for storage.

        Args:
            token_data: Dictionary containing token, refresh_token, expiry, etc.

        Returns:
            Encrypted token as base64 string
        """
        # Convert dict to JSON string
        json_str = json.dumps(token_data)

        # Encrypt
        encrypted = self.cipher.encrypt(json_str.encode())

        # Return as base64 string
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_token(self, encrypted_token: str) -> Dict[str, Any]:
        """
        Decrypt token data from storage.

        Args:
            encrypted_token: Base64 encrypted token string

        Returns:
            Dictionary containing token data

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode from base64
            encrypted = base64.urlsafe_b64decode(encrypted_token.encode())

            # Decrypt
            decrypted = self.cipher.decrypt(encrypted)

            # Parse JSON
            return json.loads(decrypted.decode())

        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {str(e)}")

    def rotate_encryption(self, old_encrypted: str, new_key: str) -> str:
        """
        Re-encrypt a token with a new encryption key.

        Args:
            old_encrypted: Token encrypted with old key
            new_key: New encryption key

        Returns:
            Token encrypted with new key
        """
        # Decrypt with current key
        token_data = self.decrypt_token(old_encrypted)

        # Create new cipher with new key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'google_oauth_token_salt',
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(new_key.encode()))
        new_cipher = Fernet(derived_key)

        # Encrypt with new key
        json_str = json.dumps(token_data)
        encrypted = new_cipher.encrypt(json_str.encode())

        return base64.urlsafe_b64encode(encrypted).decode()


# Global instance
token_encryption = TokenEncryption()
