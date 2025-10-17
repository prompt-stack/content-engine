"""CRUD operations for captures."""

from typing import List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.capture import Capture


async def create_capture(
    db: AsyncSession,
    title: Optional[str],
    content: str,
    meta: Optional[dict],
    user_id: int
) -> Capture:
    """
    Create a new capture.

    Args:
        db: Database session
        title: Optional title for the capture
        content: The actual text content (required)
        meta: Optional metadata dict
        user_id: User ID who owns this capture

    Returns:
        Created Capture instance
    """
    try:
        capture = Capture(
            user_id=user_id,
            title=title,
            content=content,
            meta=meta or {}
        )
        db.add(capture)
        await db.commit()
        await db.refresh(capture)
        return capture
    except Exception as e:
        await db.rollback()
        raise


async def get_capture(
    db: AsyncSession,
    capture_id: int,
    user_id: int
) -> Optional[Capture]:
    """
    Get a single capture by ID (user-scoped).

    Args:
        db: Database session
        capture_id: ID of the capture
        user_id: User ID (for security - can only access own captures)

    Returns:
        Capture if found and belongs to user, None otherwise
    """
    result = await db.execute(
        select(Capture)
        .where(Capture.id == capture_id)
        .where(Capture.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_captures(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Capture]:
    """
    List captures for a user (newest first, paginated).

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum results to return
        offset: Pagination offset

    Returns:
        List of Capture instances
    """
    result = await db.execute(
        select(Capture)
        .where(Capture.user_id == user_id)
        .order_by(Capture.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def search_captures(
    db: AsyncSession,
    query: str,
    user_id: int,
    limit: int = 50
) -> List[Capture]:
    """
    Simple search in captures (title or content contains query).

    Args:
        db: Database session
        query: Search query string
        user_id: User ID
        limit: Maximum results to return

    Returns:
        List of matching Capture instances
    """
    search_pattern = f"%{query}%"

    result = await db.execute(
        select(Capture)
        .where(Capture.user_id == user_id)
        .where(
            or_(
                Capture.title.ilike(search_pattern),
                Capture.content.ilike(search_pattern)
            )
        )
        .order_by(Capture.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_capture(
    db: AsyncSession,
    capture_id: int,
    user_id: int
) -> bool:
    """
    Delete a capture (user-scoped).

    Args:
        db: Database session
        capture_id: ID of capture to delete
        user_id: User ID (for security)

    Returns:
        True if deleted, False if not found or doesn't belong to user
    """
    try:
        capture = await get_capture(db, capture_id, user_id)
        if not capture:
            return False

        await db.delete(capture)
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        raise


async def count_captures(
    db: AsyncSession,
    user_id: int
) -> int:
    """
    Count total captures for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Total number of captures
    """
    result = await db.execute(
        select(func.count(Capture.id))
        .where(Capture.user_id == user_id)
    )
    return result.scalar_one()
