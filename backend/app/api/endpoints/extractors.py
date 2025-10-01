"""Content extraction API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.extractors.reddit_extractor import RedditExtractor
from app.services.extractors.tiktok_extractor import TikTokExtractor
from app.services.extractors.youtube_extractor import YouTubeExtractor
from app.services.extractors.article_extractor import ArticleExtractor
from app.services.extractors.base import PlatformDetector, ExtractionError

router = APIRouter()


class ExtractRequest(BaseModel):
    """Request model for content extraction."""
    url: HttpUrl
    max_comments: int = 20


class ExtractResponse(BaseModel):
    """Response model for content extraction."""
    platform: str
    url: str
    title: str
    author: str
    content: str
    metadata: dict
    extracted_at: str


@router.post("/reddit", response_model=ExtractResponse)
async def extract_reddit(request: ExtractRequest):
    """
    Extract content from a Reddit post.

    - **url**: Reddit post URL
    - **max_comments**: Maximum number of top-level comments (default: 20)
    """
    try:
        extractor = RedditExtractor()
        result = await extractor.extract(str(request.url), max_comments=request.max_comments)
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/tiktok", response_model=ExtractResponse)
async def extract_tiktok(request: ExtractRequest):
    """
    Extract transcript from a TikTok video.

    - **url**: TikTok video URL (supports short links like vm.tiktok.com)
    """
    try:
        extractor = TikTokExtractor()
        result = await extractor.extract(str(request.url))
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/youtube", response_model=ExtractResponse)
async def extract_youtube(request: ExtractRequest):
    """
    Extract transcript from a YouTube video.

    - **url**: YouTube video URL (supports various formats)
    """
    try:
        extractor = YouTubeExtractor()
        result = await extractor.extract(str(request.url))
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/article", response_model=ExtractResponse)
async def extract_article(request: ExtractRequest):
    """
    Extract content from any article or web page.

    - **url**: Article/webpage URL
    """
    try:
        extractor = ArticleExtractor()
        result = await extractor.extract(str(request.url))
        return result
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/auto", response_model=ExtractResponse)
async def extract_auto(request: ExtractRequest):
    """
    Automatically detect platform and extract content.

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
            result = await extractor.extract(url, max_comments=request.max_comments)
            return result
        elif platform == "tiktok":
            extractor = TikTokExtractor()
            result = await extractor.extract(url)
            return result
        elif platform == "youtube":
            extractor = YouTubeExtractor()
            result = await extractor.extract(url)
            return result
        elif platform == "article":
            extractor = ArticleExtractor()
            result = await extractor.extract(url)
            return result
        else:
            raise HTTPException(status_code=501, detail=f"Extractor for {platform} not yet implemented")

    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")