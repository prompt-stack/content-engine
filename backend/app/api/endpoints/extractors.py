"""Content extraction API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.limiter import limiter
from app.services.extractors.reddit_extractor import RedditExtractor
from app.services.extractors.tiktok_extractor import TikTokExtractor
from app.services.extractors.youtube_extractor import YouTubeExtractor
from app.services.extractors.article_extractor import ArticleExtractor
from app.services.extractors.base import PlatformDetector, ExtractionError
from app.db.session import get_async_session
from app.crud import capture as crud
from app.api.deps import get_current_active_user, verify_api_key
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
@limiter.limit("5/minute")
async def extract_reddit(
    extract_request: ExtractRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_api_key)
):
    """
    Extract content from a Reddit post and save to vault.

    **Rate Limit:** 5 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **url**: Reddit post URL (supports short links like /r/subreddit/s/xxxxx)
    - **max_comments**: Maximum number of top-level comments (default: 20)
    - **title**: Post title (optional, helps resolve short links if redirect blocked)
    """
    from app.core.config import settings
    if not settings.ENABLE_EXTRACTORS:
        raise HTTPException(
            status_code=503,
            detail="Extractor features are currently disabled for cost control. Please contact administrator."
        )

    try:
        extractor = RedditExtractor()
        result = await extractor.extract(
            str(extract_request.url),
            max_comments=extract_request.max_comments,
            title=extract_request.title
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
@limiter.limit("5/minute")
async def extract_tiktok(
    extract_request: ExtractRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_api_key)
):
    """
    Extract transcript from a TikTok video and save to vault.

    **Rate Limit:** 5 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **url**: TikTok video URL (supports short links like vm.tiktok.com)
    """
    from app.core.config import settings
    if not settings.ENABLE_EXTRACTORS:
        raise HTTPException(status_code=503, detail="Extractor features are currently disabled for cost control. Please contact administrator.")

    try:
        extractor = TikTokExtractor()
        result = await extractor.extract(str(extract_request.url))

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
@limiter.limit("5/minute")
async def extract_youtube(
    extract_request: ExtractRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_api_key)
):
    """
    Extract transcript from a YouTube video and save to vault.

    **Rate Limit:** 5 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **url**: YouTube video URL (supports various formats)
    """
    from app.core.config import settings
    if not settings.ENABLE_EXTRACTORS:
        raise HTTPException(status_code=503, detail="Extractor features are currently disabled for cost control. Please contact administrator.")

    try:
        extractor = YouTubeExtractor()
        result = await extractor.extract(str(extract_request.url))

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
@limiter.limit("5/minute")
async def extract_article(
    extract_request: ExtractRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_api_key)
):
    """
    Extract content from any article or web page and save to vault.

    **Rate Limit:** 5 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **url**: Article/webpage URL
    """
    from app.core.config import settings
    if not settings.ENABLE_EXTRACTORS:
        raise HTTPException(status_code=503, detail="Extractor features are currently disabled for cost control. Please contact administrator.")

    try:
        extractor = ArticleExtractor()
        result = await extractor.extract(str(extract_request.url))

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
@limiter.limit("5/minute")
async def extract_auto(
    extract_request: ExtractRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(verify_api_key)
):
    """
    Automatically detect platform, extract content, and save to vault.

    **Rate Limit:** 5 requests per minute
    **Authentication:** Requires X-API-Key header if API_SECRET_KEY is configured

    - **url**: Content URL (any supported platform)
    """
    import logging
    from app.core.config import settings
    if not settings.ENABLE_EXTRACTORS:
        raise HTTPException(status_code=503, detail="Extractor features are currently disabled for cost control. Please contact administrator.")

    url = str(extract_request.url)

    # Detect platform
    platform = PlatformDetector.detect(url)

    if not platform:
        raise HTTPException(status_code=400, detail="Unsupported URL or platform not detected")

    # Extract content with proper error handling
    result = None
    try:
        if platform == "reddit":
            extractor = RedditExtractor()
            result = await extractor.extract(url, max_comments=extract_request.max_comments, title=extract_request.title)
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

    except ExtractionError as e:
        # Known extraction errors - return 400
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except Exception as e:
        # Log unexpected errors and return 500
        logging.error(f"Unexpected error in auto-detect for {url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    # Save to vault (separate concern from extraction)
    try:
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
    except Exception as db_error:
        # Extraction succeeded but DB save failed - log and return extraction anyway
        logging.error(f"Failed to save to vault: {str(db_error)}")
        result["capture_id"] = None

    return result