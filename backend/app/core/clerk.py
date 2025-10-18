"""Clerk authentication utilities for FastAPI."""

import jwt
import requests
from typing import Optional, Dict, Any
from functools import lru_cache
from fastapi import HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_async_session
from app.models.user import User, UserRole, UserTier


@lru_cache(maxsize=1)
def get_clerk_jwks() -> Dict[str, Any]:
    """
    Fetch Clerk's JSON Web Key Set (JWKS) for JWT verification.

    Cached to avoid repeated requests.
    """
    # Extract domain from publishable key
    # Format: pk_test_xxx or pk_live_xxx
    if not hasattr(settings, 'CLERK_PUBLISHABLE_KEY'):
        raise ValueError("CLERK_PUBLISHABLE_KEY not set in environment")

    # Clerk JWKS URL is always at this endpoint
    # The domain comes from your Clerk instance
    jwks_url = "https://cute-mayfly-11.clerk.accounts.dev/.well-known/jwks.json"

    response = requests.get(jwks_url, timeout=5)
    response.raise_for_status()
    return response.json()


def verify_clerk_token(token: str) -> Dict[str, Any]:
    """
    Verify a Clerk JWT token and return the payload.

    Args:
        token: The JWT token from Authorization header

    Returns:
        Dict containing user claims (sub, email, etc.)

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Get JWKS from Clerk
        jwks = get_clerk_jwks()

        # Decode the token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')

        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token: missing kid")

        # Find the matching key in JWKS
        signing_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not signing_key:
            raise HTTPException(status_code=401, detail="Invalid token: key not found")

        # Verify and decode the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=['RS256'],
            options={"verify_aud": False}  # Clerk doesn't use aud claim
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch JWKS: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token verification failed: {str(e)}")


async def get_current_clerk_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from Clerk JWT.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_clerk_user)):
            return {"user_id": user["sub"]}

    Args:
        authorization: Authorization header with "Bearer {token}"

    Returns:
        User claims from verified JWT

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please sign in."
        )

    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header. Expected 'Bearer {token}'"
        )

    token = parts[1]
    return verify_clerk_token(token)


async def get_optional_clerk_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for optional authentication.

    Returns user if authenticated, None otherwise.
    """
    if not authorization:
        return None

    try:
        return await get_current_clerk_user(authorization)
    except HTTPException:
        return None


async def get_or_create_user(
    clerk_claims: Dict[str, Any],
    db: AsyncSession
) -> User:
    """
    Get or create a User in the database from Clerk claims.

    Just-In-Time (JIT) user provisioning:
    - If user exists (by clerk_user_id), return it
    - If not, create new User record

    Args:
        clerk_claims: Verified JWT claims from Clerk
        db: Database session

    Returns:
        User: Database User object
    """
    clerk_user_id = clerk_claims.get("sub")  # Clerk user ID
    email = clerk_claims.get("email", clerk_claims.get("email_addresses", [{}])[0].get("email_address"))

    if not clerk_user_id:
        raise HTTPException(status_code=400, detail="Invalid Clerk token: missing user ID")

    # Try to find existing user
    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # User exists, return it
        return user

    # User doesn't exist, create new one
    new_user = User(
        clerk_user_id=clerk_user_id,
        email=email or f"{clerk_user_id}@clerk.placeholder",
        hashed_password="",  # Clerk handles auth, no password needed
        is_active=True,
        is_verified=True,  # Clerk handles verification
        is_superuser=False,
        role=UserRole.USER,
        tier=UserTier.FREE,
        oauth_provider="clerk",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def get_current_user_from_clerk(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    FastAPI dependency to get current DATABASE User from Clerk JWT.

    This is the main dependency to use in your endpoints!

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user_from_clerk)):
            return {"user_id": user.id, "email": user.email}

    Flow:
        1. Verify Clerk JWT token
        2. Get or create User in database
        3. Return database User object

    Args:
        authorization: Authorization header with "Bearer {token}"
        db: Database session

    Returns:
        User: Database User object (ORM model)

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    # Verify Clerk token and get claims
    clerk_claims = await get_current_clerk_user(authorization)

    # Get or create database user
    user = await get_or_create_user(clerk_claims, db)

    return user
