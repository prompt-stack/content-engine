"""
API dependencies for authentication and database sessions.

⚠️  DEPRECATED: This module is deprecated and should not be used for new endpoints.

Authentication System Migration:
    OLD (Deprecated):  app.api.deps (this file)
    NEW (Use this):    app.core.clerk

All new endpoints should use:
    from app.core.clerk import get_current_user_from_clerk
    from app.models.user import User

    @router.get("/endpoint")
    async def endpoint(user: User = Depends(get_current_user_from_clerk)):
        # Your code here

Why Clerk?
    - Proper JWT authentication with token verification
    - Just-In-Time (JIT) user provisioning
    - No hardcoded users or API keys
    - Secure, scalable, production-ready

Legacy Functions in This File (DO NOT USE):
    - get_current_user()        → Use get_current_user_from_clerk()
    - get_current_active_user() → Use get_current_user_from_clerk() (already checks active)
    - get_optional_user()       → Use get_optional_clerk_user()
    - verify_api_key()          → REMOVED (use Clerk auth only)

See /docs/AUTH-INTEGRATION.md for complete migration guide.
"""

import warnings
from typing import Optional
from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.user import User, UserRole, UserTier


# Show deprecation warning when module is imported
warnings.warn(
    "app.api.deps is deprecated. Use app.core.clerk for authentication. "
    "See /docs/AUTH-INTEGRATION.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    authorization: Optional[str] = Header(None)
) -> User:
    """
    ⚠️  DEPRECATED: Use get_current_user_from_clerk() from app.core.clerk instead.

    Get the current authenticated user.

    For MVP: Returns OWNER user (user_id=1) by default.
    TODO: Implement full authentication with JWT/OAuth tokens.

    Args:
        db: Database session
        authorization: Authorization header (for future token-based auth)

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If user not found or unauthorized
    """
    warnings.warn(
        "get_current_user() is deprecated. Use get_current_user_from_clerk() from app.core.clerk",
        DeprecationWarning,
        stacklevel=2
    )
    # For MVP: Always return OWNER user
    # TODO: Parse authorization header, validate JWT token, get user from token

    result = await db.execute(
        select(User).where(User.email == "owner@contentengine.local")
    )
    user = result.scalar_one_or_none()

    if not user:
        # Auto-create OWNER user if it doesn't exist
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            email="owner@contentengine.local",
            hashed_password=pwd_context.hash("owner123"),
            role=UserRole.OWNER,
            tier=UserTier.OWNER,
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    ⚠️  DEPRECATED: Use get_current_user_from_clerk() from app.core.clerk instead.

    Get the current active user.

    Ensures the user account is active before allowing access.

    Args:
        current_user: The current user from get_current_user

    Returns:
        User: The active user

    Raises:
        HTTPException: If user is not active
    """
    warnings.warn(
        "get_current_active_user() is deprecated. Use get_current_user_from_clerk() from app.core.clerk",
        DeprecationWarning,
        stacklevel=2
    )
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def get_optional_user(
    db: AsyncSession = Depends(get_async_session),
    authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    ⚠️  DEPRECATED: Use get_optional_clerk_user() from app.core.clerk instead.

    Get the current user if authenticated, otherwise return None.

    Useful for endpoints that work with or without authentication.

    Args:
        db: Database session
        authorization: Authorization header

    Returns:
        Optional[User]: The authenticated user or None
    """
    warnings.warn(
        "get_optional_user() is deprecated. Use get_optional_clerk_user() from app.core.clerk",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        return await get_current_user(db, authorization)
    except HTTPException:
        return None


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    ⚠️  DEPRECATED: This function has been REMOVED from all endpoints.
    Use Clerk authentication (get_current_user_from_clerk) instead.

    Verify API key for cost control on expensive endpoints.

    If API_SECRET_KEY is set in environment, this will require
    the X-API-Key header to match it. If not set, allows all requests.

    This is a simple shared secret approach for MVP cost control.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is required but missing or invalid
    """
    warnings.warn(
        "verify_api_key() is deprecated and has been removed from all endpoints. "
        "Use get_current_user_from_clerk() from app.core.clerk for authentication",
        DeprecationWarning,
        stacklevel=2
    )
    from app.core.config import settings

    # If no API_SECRET_KEY is configured, allow all requests (dev mode)
    if not settings.API_SECRET_KEY:
        return True

    # If API_SECRET_KEY is configured, require matching header
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )

    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return True
