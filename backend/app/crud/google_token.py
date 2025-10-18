"""CRUD operations for Google OAuth tokens."""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.google_token import GoogleToken
from app.utils.encryption import token_encryption


async def create_or_update_token(
    db: AsyncSession,
    user_id: int,
    token_data: Dict[str, Any],
    scopes: str,
    google_email: Optional[str] = None,
    google_user_id: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> GoogleToken:
    """
    Create or update a Google token for a user.

    Args:
        db: Database session
        user_id: User ID
        token_data: Dictionary containing OAuth token data
        scopes: Comma-separated scopes
        google_email: User's Gmail address
        google_user_id: Google user ID
        expires_at: Token expiry datetime

    Returns:
        GoogleToken instance
    """
    try:
        # Encrypt the token data
        encrypted_token = token_encryption.encrypt_token(token_data)

        # Check if token already exists
        existing_token = await get_token_by_user(db, user_id)

        if existing_token:
            # Update existing token
            existing_token.encrypted_token = encrypted_token
            existing_token.scopes = scopes
            existing_token.google_email = google_email
            existing_token.google_user_id = google_user_id
            existing_token.expires_at = expires_at
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token
            existing_token = GoogleToken(
                user_id=user_id,
                encrypted_token=encrypted_token,
                scopes=scopes,
                google_email=google_email,
                google_user_id=google_user_id,
                expires_at=expires_at
            )
            db.add(existing_token)

        await db.commit()
        await db.refresh(existing_token)
        return existing_token

    except Exception as e:
        await db.rollback()
        raise


async def get_token_by_user(
    db: AsyncSession,
    user_id: int
) -> Optional[GoogleToken]:
    """
    Get Google token for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        GoogleToken if found, None otherwise
    """
    result = await db.execute(
        select(GoogleToken).where(GoogleToken.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_decrypted_token(
    db: AsyncSession,
    user_id: int
) -> Optional[Dict[str, Any]]:
    """
    Get decrypted token data for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Decrypted token data dictionary, or None if not found
    """
    google_token = await get_token_by_user(db, user_id)

    if not google_token:
        return None

    try:
        return token_encryption.decrypt_token(google_token.encrypted_token)
    except Exception as e:
        # Token decryption failed, likely corrupted
        return None


async def delete_token(
    db: AsyncSession,
    user_id: int
) -> bool:
    """
    Delete Google token for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        True if deleted, False if not found
    """
    try:
        google_token = await get_token_by_user(db, user_id)

        if not google_token:
            return False

        await db.delete(google_token)
        await db.commit()
        return True

    except Exception as e:
        await db.rollback()
        raise


async def has_valid_token(
    db: AsyncSession,
    user_id: int
) -> bool:
    """
    Check if user has a valid (non-expired) Google token.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        True if valid token exists, False otherwise
    """
    google_token = await get_token_by_user(db, user_id)

    if not google_token:
        return False

    # Check if token is expired
    if google_token.expires_at and datetime.utcnow() >= google_token.expires_at:
        return False

    return True
