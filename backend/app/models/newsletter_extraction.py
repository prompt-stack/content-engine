"""Database models for content extraction and link aggregation.

Minimal Phase 0-1 Schema:
- Start with 10 essential columns across 3 tables
- Can add more via migrations when features require them
- Designed to support future content sources: Reddit share-to-email, web forms, API

Future-proof naming:
- EmailContent (not NewsletterEmail) - supports any email type
- ExtractedLink (not ArticleLink) - supports any link type
"""

from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum


class ExtractionStatus(str, enum.Enum):
    """Status of an extraction job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Extraction(Base):
    """Extraction session - one pipeline run.

    Represents a single execution of the content extraction pipeline.
    Currently: Gmail newsletters
    Future: Direct email, Reddit share-to-email, web forms, API
    """
    __tablename__ = "extractions"

    # Core fields
    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "20251015_162827"
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for backwards compatibility with existing data
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    days_back: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Gmail-specific param
    max_results: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Gmail-specific param

    # Background job tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=ExtractionStatus.PENDING.value,
        nullable=False,
        index=True
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0-100
    progress_message: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Current step
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For failed jobs

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    content_items: Mapped[list["EmailContent"]] = relationship(
        "EmailContent",
        back_populates="extraction",
        cascade="all, delete-orphan",
        lazy="joined"
    )


class EmailContent(Base):
    """Content container - newsletter, plain email, social share, etc.

    Generic container for any email-based content that contains links.
    Currently: TheRundown.ai newsletters, AlphaSignal newsletters
    Future: Reddit share-to-email, personal link submissions, RSS-to-email
    """
    __tablename__ = "email_content"

    # Core fields (5 columns)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subject: Mapped[str] = mapped_column(String(1024), nullable=False)
    sender: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(100), nullable=False)  # Store as ISO string

    # Relationships
    extraction: Mapped["Extraction"] = relationship("Extraction", back_populates="content_items")
    links: Mapped[list["ExtractedLink"]] = relationship(
        "ExtractedLink",
        back_populates="content",
        cascade="all, delete-orphan",
        lazy="joined"
    )


class ExtractedLink(Base):
    """Extracted link - the core asset.

    Stores clean, resolved URLs from any content source.
    These links feed into article/YouTube/Reddit extractors → LLM processing.
    """
    __tablename__ = "extracted_links"

    # Core fields (5 columns)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("email_content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)  # Resolved final URL
    original_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Original tracking/redirect URL
    curator_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Newsletter curator's article description

    # Relationships
    content: Mapped["EmailContent"] = relationship("EmailContent", back_populates="links")


class NewsletterConfig(Base):
    """Newsletter extractor configuration tied to a user.

    Stores filtering rules, source preferences, and extraction settings.
    Each user can have their own configuration.
    Falls back to config.json if no user-specific config exists.
    """
    __tablename__ = "newsletter_config"

    # Core fields (5 columns)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for now (single-user mode)
        unique=True,  # One config per user
        index=True
    )
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Entire config as JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
