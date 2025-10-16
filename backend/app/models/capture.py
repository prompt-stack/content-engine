"""Capture model for direct content input."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Capture(Base):
    """
    Captured content model.

    Stores content directly provided by users (e.g., via iOS Shortcut).
    No URL extraction needed - content is already in hand.
    """

    __tablename__ = "captures"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User relationship (CASCADE delete when user deleted)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata (flexible JSONB field)
    # Example: {"source": "chatgpt", "timestamp": "...", "device": "iPhone"}
    # Note: renamed from 'metadata' to 'meta' because 'metadata' is reserved in SQLAlchemy
    meta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default="NOW()",
        index=True
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="captures")
