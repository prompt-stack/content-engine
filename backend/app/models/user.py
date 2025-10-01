from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_users.db import SQLAlchemyBaseUserTable
from .base import Base
import enum


class UserTier(str, enum.Enum):
    """User subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    OWNER = "owner"  # NEW: Unrestricted access


class UserRole(str, enum.Enum):
    """User roles for permissions."""
    USER = "user"           # Regular user
    ADMIN = "admin"         # Can manage users
    SUPERADMIN = "superadmin"  # Can manage everything
    OWNER = "owner"         # System owner (you!)


class User(SQLAlchemyBaseUserTable[int], Base):
    """User model with authentication and subscription."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Role system
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,
        nullable=False
    )

    # Subscription
    tier: Mapped[UserTier] = mapped_column(
        SQLEnum(UserTier),
        default=UserTier.FREE,
        nullable=False
    )

    # Usage tracking
    requests_this_month: Mapped[int] = mapped_column(Integer, default=0)
    requests_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Social media OAuth tokens (JSON field would be better, but keeping simple)
    twitter_connected: Mapped[bool] = mapped_column(default=False)
    linkedin_connected: Mapped[bool] = mapped_column(default=False)
    reddit_connected: Mapped[bool] = mapped_column(default=False)
    youtube_connected: Mapped[bool] = mapped_column(default=False)
    facebook_connected: Mapped[bool] = mapped_column(default=False)
    instagram_connected: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    @property
    def rate_limit(self) -> int:
        """Get user's monthly rate limit based on tier."""
        from app.core.config import settings

        # OWNER tier = unlimited
        if self.tier == UserTier.OWNER:
            return 999999999  # Effectively unlimited

        limits = {
            UserTier.FREE: settings.RATE_LIMIT_FREE,
            UserTier.STARTER: settings.RATE_LIMIT_STARTER,
            UserTier.PRO: settings.RATE_LIMIT_PRO,
            UserTier.BUSINESS: settings.RATE_LIMIT_BUSINESS,
        }
        return limits.get(self.tier, settings.RATE_LIMIT_FREE)

    @property
    def has_quota(self) -> bool:
        """Check if user has remaining quota."""
        # OWNER always has quota
        if self.tier == UserTier.OWNER:
            return True
        return self.requests_this_month < self.rate_limit

    @property
    def is_owner(self) -> bool:
        """Check if user is the system owner."""
        return self.role == UserRole.OWNER

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.OWNER]

    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.OWNER]

    @property
    def can_manage_system(self) -> bool:
        """Check if user can manage system settings."""
        return self.role in [UserRole.SUPERADMIN, UserRole.OWNER]

    @property
    def can_bypass_limits(self) -> bool:
        """Check if user can bypass rate limits."""
        return self.role == UserRole.OWNER