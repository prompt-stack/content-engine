from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, Integer, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum


class Platform(str, enum.Enum):
    """Supported content platforms."""
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    ARTICLE = "article"
    EMAIL = "email"
    BETTING = "betting"


class ProcessingStatus(str, enum.Enum):
    """Content processing status."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Content(Base):
    """Extracted and processed content."""

    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Source
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)

    # Extracted content
    title: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_content_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Processing
    status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # LLM Processing results
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    categories: Mapped[list] = mapped_column(JSON, default=list)

    # Timestamps
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    # user = relationship("User", back_populates="contents")  # Add to User model later


class Newsletter(Base):
    """Newsletter digest generated from multiple content sources."""

    __tablename__ = "newsletters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Digest
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    digest: Mapped[str] = mapped_column(Text, nullable=False)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    source_content_ids: Mapped[list] = mapped_column(JSON, default=list)

    # Metadata
    content_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)