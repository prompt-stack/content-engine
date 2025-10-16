"""Content extraction API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.extractors.reddit_extractor import RedditExtractor
from app.services.extractors.tiktok_extractor import TikTokExtractor
from app.services.extractors.youtube_extractor import YouTubeExtractor
from app.services.extractors.article_extractor import ArticleExtractor
from app.services.extractors.base import PlatformDetector, ExtractionError
from app.db.session import get_async_session
from app.crud import capture as crud
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


class ExtractRequest(BaseModel):
    """Request model for content extraction."""
    url: HttpUrl
    max_comments: int = 20
    title: str | None = None  # Optional title for Reddit short links


class ExtractResponse(BaseModel):
    """Response model for content extraction."""
    platform: str
    url: str
    title: str
    author: str
    content: str
    metadata: dict
    extracted_at: str
    capture_id: int | None = None  # Added capture_id


@router.post("/reddit", response_model=ExtractResponse)
async def extract_reddit(
    request: ExtractRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract content from a Reddit post and save to vault.

    - **url**: Reddit post URL (supports short links like /r/subreddit/s/xxxxx)
    - **max_comments**: Maximum number of top-level comments (default: 20)
    - **title**: Post title (optional, helps resolve short links if redirect blocked)
    """
    try:
        extractor = RedditExtractor()
        result = await extractor.extract(
            str(request.url),
            max_comments=request.max_comments,
            title=request.title
        )

        # Save to vault
        capture = await crud.create_capture(
            db=db,
            title=result.get("title"),
            content=result.get("content", ""),
            meta={
                "platform": result.get("platform"),
                "url": result.get("url"),
                "author": result.get("author"),
                "source": "extractor",
                **result.get("metadata", {})
            },
            user_id=current_user.id
        )

        result["capture_id"] = capture.id
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/tiktok", response_model=ExtractResponse)
async def extract_tiktok(
    request: ExtractRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract transcript from a TikTok video and save to vault.

    - **url**: TikTok video URL (supports short links like vm.tiktok.com)
    """
    try:
        extractor = TikTokExtractor()
        result = await extractor.extract(str(request.url))

        # Save to vault
        capture = await crud.create_capture(
            db=db,
            title=result.get("title"),
            content=result.get("content", ""),
            meta={
                "platform": result.get("platform"),
                "url": result.get("url"),
                "author": result.get("author"),
                "source": "extractor",
                **result.get("metadata", {})
            },
            user_id=current_user.id
        )

        result["capture_id"] = capture.id
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/youtube", response_model=ExtractResponse)
async def extract_youtube(
    request: ExtractRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract transcript from a YouTube video and save to vault.

    - **url**: YouTube video URL (supports various formats)
    """
    try:
        extractor = YouTubeExtractor()
        result = await extractor.extract(str(request.url))

        # Save to vault
        capture = await crud.create_capture(
            db=db,
            title=result.get("title"),
            content=result.get("content", ""),
            meta={
                "platform": result.get("platform"),
                "url": result.get("url"),
                "author": result.get("author"),
                "source": "extractor",
                **result.get("metadata", {})
            },
            user_id=current_user.id
        )

        result["capture_id"] = capture.id
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/article", response_model=ExtractResponse)
async def extract_article(
    request: ExtractRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract content from any article or web page and save to vault.

    - **url**: Article/webpage URL
    """
    try:
        extractor = ArticleExtractor()
        result = await extractor.extract(str(request.url))

        # Save to vault
        capture = await crud.create_capture(
            db=db,
            title=result.get("title"),
            content=result.get("content", ""),
            meta={
                "platform": result.get("platform"),
                "url": result.get("url"),
                "author": result.get("author"),
                "source": "extractor",
                **result.get("metadata", {})
            },
            user_id=current_user.id
        )

        result["capture_id"] = capture.id
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/auto", response_model=ExtractResponse)
async def extract_auto(
    request: ExtractRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Automatically detect platform, extract content, and save to vault.

    - **url**: Content URL (any supported platform)
    """
    url = str(request.url)

    # Detect platform
    platform = PlatformDetector.detect(url)

    if not platform:
        raise HTTPException(status_code=400, detail="Unsupported URL or platform not detected")

    # Route to appropriate extractor
    try:
        if platform == "reddit":
            extractor = RedditExtractor()
            result = await extractor.extract(url, max_comments=request.max_comments, title=request.title)
        elif platform == "tiktok":
            extractor = TikTokExtractor()
            result = await extractor.extract(url)
        elif platform == "youtube":
            extractor = YouTubeExtractor()
            result = await extractor.extract(url)
        elif platform == "article":
            extractor = ArticleExtractor()
            result = await extractor.extract(url)
        else:
            raise HTTPException(status_code=501, detail=f"Extractor for {platform} not yet implemented")

        # Save to vault
        capture = await crud.create_capture(
            db=db,
            title=result.get("title"),
            content=result.get("content", ""),
            meta={
                "platform": result.get("platform"),
                "url": result.get("url"),
                "author": result.get("author"),
                "source": "extractor",
                **result.get("metadata", {})
            },
            user_id=current_user.id
        )

        result["capture_id"] = capture.id
        return result

    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")