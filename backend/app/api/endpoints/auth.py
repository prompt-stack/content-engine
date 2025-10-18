"""Authentication endpoints."""

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clerk import get_current_user_from_clerk
from app.core.config import settings
from app.models.user import User
from app.db.session import get_async_session
from app.services.google_oauth import google_oauth
from app.services.oauth_state import oauth_state_store
from app.crud import google_token as google_token_crud
from app.crud import user as user_crud

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    user: User = Depends(get_current_user_from_clerk)
):
    """
    Get current authenticated user information.

    This endpoint demonstrates JIT user provisioning:
    - First time: Creates user in database
    - Subsequent times: Returns existing user

    Returns:
        User info including database ID, email, role, tier
    """
    return {
        "id": user.id,
        "clerk_user_id": user.clerk_user_id,
        "email": user.email,
        "role": user.role.value,
        "tier": user.tier.value,
        "is_verified": user.is_verified,
        "requests_this_month": user.requests_this_month,
        "created_at": user.created_at.isoformat(),
    }


# ========== Google OAuth Endpoints ==========

@router.get("/google/start")
async def start_google_oauth(
    user: User = Depends(get_current_user_from_clerk)
):
    """
    Start Google OAuth flow for Gmail access.

    Returns:
        Authorization URL to redirect user to
    """
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state with user ID for callback
    oauth_state_store.store_state(state, user.id)

    # Get authorization URL
    auth_url = google_oauth.get_authorization_url(state)

    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Handle Google OAuth callback and store tokens.

    This endpoint is called by Google after user authorizes.
    Note: This endpoint does NOT require Clerk auth since it's called by Google's redirect.
    """
    try:
        # Retrieve user ID from state token
        user_id = oauth_state_store.get_user_id(state)
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired state token. Please try connecting again."
            )

        # Verify user exists
        user = await user_crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Exchange code for tokens
        token_data = google_oauth.exchange_code_for_token(code, state)

        # Extract expiry
        expires_at = None
        if token_data.get("expiry"):
            expires_at = datetime.fromisoformat(token_data["expiry"])

        # Store encrypted tokens in database
        await google_token_crud.create_or_update_token(
            db=db,
            user_id=user.id,
            token_data=token_data,
            scopes=",".join(token_data.get("scopes", [])),
            google_email=token_data.get("email"),
            google_user_id=token_data.get("user_id"),
            expires_at=expires_at
        )

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings?google_connected=true",
            status_code=302
        )

    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend error page
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/settings?google_error=true&message={str(e)}",
            status_code=302
        )


@router.get("/google/status")
async def get_google_oauth_status(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user_from_clerk)
):
    """
    Check if user has connected their Google account.

    Returns:
        Connection status and details
    """
    google_token = await google_token_crud.get_token_by_user(db, user.id)

    if not google_token:
        return {
            "connected": False,
            "email": None,
            "expires_at": None
        }

    return {
        "connected": True,
        "email": google_token.google_email,
        "expires_at": google_token.expires_at.isoformat() if google_token.expires_at else None,
        "is_expired": google_token.is_expired
    }


@router.delete("/google/disconnect")
async def disconnect_google_oauth(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user_from_clerk)
):
    """
    Disconnect Google account and delete tokens.

    Returns:
        Success status
    """
    deleted = await google_token_crud.delete_token(db, user.id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="No Google account connected"
        )

    return {
        "success": True,
        "message": "Google account disconnected successfully"
    }
