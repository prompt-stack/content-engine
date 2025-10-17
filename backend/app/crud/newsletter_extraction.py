"""CRUD operations for newsletter extraction data."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.newsletter_extraction import Extraction, EmailContent, ExtractedLink, NewsletterConfig, ExtractionStatus


async def create_pending_extraction(
    db: AsyncSession,
    extraction_id: str,
    days_back: Optional[int] = None,
    max_results: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Extraction:
    """
    Create a pending extraction (no content yet).

    Used for background jobs - creates the extraction record immediately,
    content is added later when the job completes.

    Args:
        db: Database session
        extraction_id: Unique ID for extraction (e.g., "20251015_163702")
        days_back: Days back parameter from extraction
        max_results: Max results parameter from extraction
        user_id: User ID who owns this extraction

    Returns:
        Created Extraction instance in pending state
    """
    extraction = Extraction(
        id=extraction_id,
        user_id=user_id,
        created_at=datetime.utcnow(),
        days_back=days_back,
        max_results=max_results,
        status=ExtractionStatus.PENDING.value,
        progress=0,
        progress_message="Queued for extraction"
    )
    db.add(extraction)
    await db.commit()
    await db.refresh(extraction)
    return extraction


async def update_extraction_progress(
    db: AsyncSession,
    extraction_id: str,
    progress: int,
    progress_message: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[Extraction]:
    """
    Update extraction progress and optionally status.

    Args:
        db: Database session
        extraction_id: Extraction ID to update
        progress: Progress percentage (0-100)
        progress_message: Optional progress message
        status: Optional status update

    Returns:
        Updated Extraction instance or None if not found
    """
    extraction = await db.get(Extraction, extraction_id)
    if not extraction:
        return None

    extraction.progress = progress
    if progress_message:
        extraction.progress_message = progress_message
    if status:
        extraction.status = status

    await db.commit()
    await db.refresh(extraction)
    return extraction


async def complete_extraction(
    db: AsyncSession,
    extraction_id: str,
    newsletters_data: List[dict],
) -> Optional[Extraction]:
    """
    Mark extraction as complete and add content.

    Args:
        db: Database session
        extraction_id: Extraction ID to complete
        newsletters_data: List of newsletter dicts from pipeline

    Returns:
        Updated Extraction instance or None if not found
    """
    extraction = await db.get(Extraction, extraction_id)
    if not extraction:
        return None

    # Update status
    extraction.status = ExtractionStatus.COMPLETED.value
    extraction.progress = 100
    extraction.progress_message = "Extraction complete"
    extraction.completed_at = datetime.utcnow()

    # Add content items
    for newsletter in newsletters_data:
        email_content = EmailContent(
            extraction_id=extraction_id,
            subject=newsletter.get('newsletter_subject', ''),
            sender=newsletter.get('newsletter_sender', ''),
            date=newsletter.get('newsletter_date', ''),
        )
        db.add(email_content)
        await db.flush()  # Get the email_content.id

        # Create links
        links = newsletter.get('links', newsletter.get('articles', []))
        for link_data in links:
            link = ExtractedLink(
                content_id=email_content.id,
                url=link_data.get('url', ''),
                original_url=link_data.get('original_url'),
                curator_description=link_data.get('curator_description'),
            )
            db.add(link)

    await db.commit()
    await db.refresh(extraction)
    return extraction


async def fail_extraction(
    db: AsyncSession,
    extraction_id: str,
    error_message: str
) -> Optional[Extraction]:
    """
    Mark extraction as failed.

    Args:
        db: Database session
        extraction_id: Extraction ID to fail
        error_message: Error message

    Returns:
        Updated Extraction instance or None if not found
    """
    extraction = await db.get(Extraction, extraction_id)
    if not extraction:
        return None

    extraction.status = ExtractionStatus.FAILED.value
    extraction.error_message = error_message
    extraction.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(extraction)
    return extraction


async def create_extraction(
    db: AsyncSession,
    extraction_id: str,
    newsletters_data: List[dict],
    days_back: Optional[int] = None,
    max_results: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Extraction:
    """
    Create a new extraction with its email content and links.

    Args:
        db: Database session
        extraction_id: Unique ID for extraction (e.g., "20251015_163702")
        newsletters_data: List of newsletter dicts from pipeline
        days_back: Days back parameter from extraction
        max_results: Max results parameter from extraction
        user_id: User ID who owns this extraction

    Returns:
        Created Extraction instance with all relationships
    """
    # Create extraction
    extraction = Extraction(
        id=extraction_id,
        user_id=user_id,
        created_at=datetime.utcnow(),
        days_back=days_back,
        max_results=max_results,
    )
    db.add(extraction)

    # Create email content items
    for newsletter in newsletters_data:
        # Create email content
        email_content = EmailContent(
            extraction_id=extraction_id,
            subject=newsletter.get('newsletter_subject', ''),
            sender=newsletter.get('newsletter_sender', ''),
            date=newsletter.get('newsletter_date', ''),
        )
        db.add(email_content)
        await db.flush()  # Get the email_content.id

        # Create links
        links = newsletter.get('links', newsletter.get('articles', []))
        for link_data in links:
            link = ExtractedLink(
                content_id=email_content.id,
                url=link_data.get('url', ''),
                original_url=link_data.get('original_url'),
                curator_description=link_data.get('curator_description'),
            )
            db.add(link)

    await db.commit()
    await db.refresh(extraction)

    return extraction


async def get_extraction(db: AsyncSession, extraction_id: str) -> Optional[Extraction]:
    """Get a single extraction by ID with all relationships loaded."""
    result = await db.execute(
        select(Extraction)
        .where(Extraction.id == extraction_id)
        .options(
            selectinload(Extraction.content_items).selectinload(EmailContent.links)
        )
    )
    return result.scalar_one_or_none()


async def get_all_extractions(
    db: AsyncSession,
    user_id: Optional[int] = None
) -> List[Extraction]:
    """
    Get all extractions ordered by created_at DESC with all relationships loaded.

    Args:
        db: Database session
        user_id: Optional user ID to filter extractions (None = all extractions)

    Returns:
        List of Extraction instances
    """
    query = select(Extraction).options(
        selectinload(Extraction.content_items).selectinload(EmailContent.links)
    )

    # Filter by user_id if provided
    if user_id is not None:
        query = query.where(Extraction.user_id == user_id)

    query = query.order_by(Extraction.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_extraction(db: AsyncSession, extraction_id: str) -> bool:
    """
    Delete an extraction and all related data (cascade).

    Returns:
        True if deleted, False if not found
    """
    extraction = await db.get(Extraction, extraction_id)
    if not extraction:
        return False

    await db.delete(extraction)
    await db.commit()
    return True


# =============================================================================
# NEWSLETTER CONFIG CRUD OPERATIONS
# =============================================================================

async def get_config(
    db: AsyncSession,
    user_id: Optional[int] = None
) -> Optional[dict]:
    """
    Get newsletter configuration from database.

    Args:
        db: Database session
        user_id: User ID (None = system default config)

    Returns:
        Config data as dict, or None if not found
    """
    result = await db.execute(
        select(NewsletterConfig)
        .where(NewsletterConfig.user_id == user_id)
    )
    config_row = result.scalar_one_or_none()

    if config_row:
        return config_row.config_data
    return None


async def upsert_config(
    db: AsyncSession,
    config_data: dict,
    user_id: Optional[int] = None
) -> NewsletterConfig:
    """
    Create or update newsletter configuration.

    Args:
        db: Database session
        config_data: Full config dictionary
        user_id: User ID (None = system default config)

    Returns:
        Created or updated NewsletterConfig instance
    """
    # Try to get existing config
    result = await db.execute(
        select(NewsletterConfig)
        .where(NewsletterConfig.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        existing.config_data = config_data
        existing.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Create new
        new_config = NewsletterConfig(
            user_id=user_id,
            config_data=config_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)
        return new_config
