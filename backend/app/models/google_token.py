from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User


class GoogleToken(Base):
    """Store encrypted Google OAuth tokens per user for Gmail access."""

    __tablename__ = "google_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One Google token per user
        index=True
    )

    # Encrypted token data (JSON encrypted as string)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)

    # OAuth scopes granted
    scopes: Mapped[str] = mapped_column(Text, nullable=False)  # Comma-separated scopes

    # Google user info
    google_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    google_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Token expiry info (for display purposes, actual expiry is in encrypted token)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="google_token")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def __repr__(self) -> str:
        return f"<GoogleToken(user_id={self.user_id}, email={self.google_email}, expired={self.is_expired})>"
