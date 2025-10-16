"""
Direct content capture API endpoints.

Accepts content directly from user (no URL extraction needed).
Primary use case: iOS Shortcut → webhook → database
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.api.deps import get_current_active_user
from app.models.user import User
from app.crud import capture as crud


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class CaptureRequest(BaseModel):
    """Request model for capturing content."""
    title: Optional[str] = None
    content: str
    meta: Optional[Dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "PostgreSQL Indexing Discussion",
                "content": "Long text from ChatGPT conversation...",
                "meta": {
                    "source": "chatgpt",
                    "device": "iPhone",
                    "timestamp": "2025-10-16T14:00:00"
                }
            }
        }


class CaptureResponse(BaseModel):
    """Response model after successful capture."""
    id: int
    title: Optional[str]
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "title": "PostgreSQL Indexing Discussion",
                "created_at": "2025-10-16T14:00:00"
            }
        }


class CaptureDetail(BaseModel):
    """Detailed capture information."""
    id: int
    title: Optional[str]
    content: str
    meta: Optional[Dict]
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "title": "PostgreSQL Indexing Discussion",
                "content": "Full content text...",
                "meta": {"source": "chatgpt"},
                "created_at": "2025-10-16T14:00:00"
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/text", response_model=CaptureResponse)
async def capture_text(
    request: CaptureRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Capture text content directly.

    Use case: iOS Shortcut copying text from ChatGPT or any other source.

    - **title**: Optional title (can be provided by shortcut or left blank)
    - **content**: Required text content
    - **meta**: Optional metadata (source, device, etc.)

    Returns capture ID and creation timestamp.
    """
    capture = await crud.create_capture(
        db=db,
        title=request.title,
        content=request.content,
        meta=request.meta,
        user_id=current_user.id
    )

    return CaptureResponse(
        id=capture.id,
        title=capture.title,
        created_at=capture.created_at.isoformat()
    )


@router.get("/list", response_model=List[CaptureDetail])
async def list_captures(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all captures for the current user (newest first).

    - **limit**: Maximum results (default: 50, max: 100)
    - **offset**: Pagination offset (default: 0)

    Returns list of captures with preview (first 200 chars of content).
    """
    # Enforce max limit
    if limit > 100:
        limit = 100

    captures = await crud.list_captures(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    # Return with content preview for list view
    return [
        CaptureDetail(
            id=c.id,
            title=c.title,
            content=c.content[:200] + "..." if len(c.content) > 200 else c.content,
            meta=c.meta,
            created_at=c.created_at.isoformat()
        )
        for c in captures
    ]


@router.get("/search", response_model=List[CaptureDetail])
async def search_captures(
    q: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search captures by query string.

    Searches in both title and content (case-insensitive).

    - **q**: Search query (required)
    - **limit**: Maximum results (default: 50, max: 100)

    Returns matching captures with content preview.
    """
    # Enforce max limit
    if limit > 100:
        limit = 100

    results = await crud.search_captures(
        db=db,
        query=q,
        user_id=current_user.id,
        limit=limit
    )

    return [
        CaptureDetail(
            id=c.id,
            title=c.title,
            content=c.content[:200] + "..." if len(c.content) > 200 else c.content,
            meta=c.meta,
            created_at=c.created_at.isoformat()
        )
        for c in results
    ]


@router.get("/{capture_id}", response_model=CaptureDetail)
async def get_capture(
    capture_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific capture by ID (full content).

    Returns complete capture with full content (not truncated).
    """
    capture = await crud.get_capture(
        db=db,
        capture_id=capture_id,
        user_id=current_user.id
    )

    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    return CaptureDetail(
        id=capture.id,
        title=capture.title,
        content=capture.content,  # Full content
        meta=capture.meta,
        created_at=capture.created_at.isoformat()
    )


@router.delete("/{capture_id}")
async def delete_capture(
    capture_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a capture.

    Only the owner of the capture can delete it.
    """
    deleted = await crud.delete_capture(
        db=db,
        capture_id=capture_id,
        user_id=current_user.id
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Capture not found")

    return {"status": "deleted", "id": capture_id}


@router.get("/stats/count")
async def get_capture_count(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get total number of captures for current user.

    Useful for displaying stats in UI.
    """
    count = await crud.count_captures(db=db, user_id=current_user.id)

    return {
        "user_id": current_user.id,
        "total_captures": count
    }
