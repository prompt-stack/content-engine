"""CRUD operations for newsletter extraction data."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.newsletter_extraction import Extraction, EmailContent, ExtractedLink


async def create_extraction(
    db: AsyncSession,
    extraction_id: str,
    newsletters_data: List[dict],
    days_back: Optional[int] = None,
    max_results: Optional[int] = None,
) -> Extraction:
    """
    Create a new extraction with its email content and links.

    Args:
        db: Database session
        extraction_id: Unique ID for extraction (e.g., "20251015_163702")
        newsletters_data: List of newsletter dicts from pipeline
        days_back: Days back parameter from extraction
        max_results: Max results parameter from extraction

    Returns:
        Created Extraction instance with all relationships
    """
    # Create extraction
    extraction = Extraction(
        id=extraction_id,
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


async def get_all_extractions(db: AsyncSession) -> List[Extraction]:
    """Get all extractions ordered by created_at DESC with all relationships loaded."""
    result = await db.execute(
        select(Extraction)
        .options(
            selectinload(Extraction.content_items).selectinload(EmailContent.links)
        )
        .order_by(Extraction.created_at.desc())
    )
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
