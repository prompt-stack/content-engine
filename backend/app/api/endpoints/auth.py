"""Authentication endpoints."""

from fastapi import APIRouter, Depends
from app.core.clerk import get_current_user_from_clerk
from app.models.user import User

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
