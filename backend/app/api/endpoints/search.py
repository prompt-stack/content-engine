"""
Search API Endpoints
AI-powered web search using Tavily
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

from app.services.search.tavily_service import get_tavily_service


router = APIRouter()


# Request Models
class SearchRequest(BaseModel):
    """Basic search request"""
    query: str = Field(..., description="Search query")
    search_depth: Literal["basic", "advanced"] = Field(
        "advanced",
        description="Search depth - 'basic' for speed, 'advanced' for accuracy"
    )
    max_results: int = Field(10, ge=1, le=20, description="Maximum results (1-20)")
    include_domains: Optional[List[str]] = Field(None, description="Domains to include")
    exclude_domains: Optional[List[str]] = Field(None, description="Domains to exclude")
    include_answer: bool = Field(False, description="Include AI-generated answer")
    include_images: bool = Field(False, description="Include related images")


class ContentContextRequest(BaseModel):
    """Research context about content"""
    content_summary: str = Field(..., description="Summary of content to research")
    max_results: int = Field(5, ge=1, le=20, description="Maximum results")


class TrendingTopicsRequest(BaseModel):
    """Search trending topics on platforms"""
    topic: str = Field(..., description="Topic to search")
    platforms: Optional[List[str]] = Field(
        None,
        description="Platforms: reddit, twitter, tiktok, youtube, medium, substack"
    )
    max_results: int = Field(10, ge=1, le=20, description="Maximum results")


class FactCheckRequest(BaseModel):
    """Fact-check a claim"""
    claim: str = Field(..., description="Claim to verify")
    max_results: int = Field(5, ge=1, le=20, description="Maximum results")


class NewsSearchRequest(BaseModel):
    """Search recent news"""
    topic: str = Field(..., description="News topic")
    recency: Literal["24h", "7d", "30d"] = Field("7d", description="Time range")
    max_results: int = Field(10, ge=1, le=20, description="Maximum results")


class ResearchRequest(BaseModel):
    """Research topic with sources"""
    topic: str = Field(..., description="Research topic")
    academic: bool = Field(False, description="Focus on academic sources")
    max_results: int = Field(10, ge=1, le=20, description="Maximum results")


# Response Models
class SearchResult(BaseModel):
    """Single search result"""
    title: str
    url: str
    content: str
    score: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response with results"""
    query: str
    results: List[Dict[str, Any]]
    total_results: int


# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute a general web search using Tavily AI

    **Use Cases:**
    - Content research
    - Background information
    - Trend discovery
    - Source finding

    **Search Depth:**
    - `basic`: Faster, good for quick lookups
    - `advanced`: AI-optimized, more accurate results

    **Domain Filtering:**
    - `include_domains`: Only search these domains
    - `exclude_domains`: Exclude these domains
    """
    try:
        service = get_tavily_service()

        results = await service.search(
            query=request.query,
            search_depth=request.search_depth,
            max_results=request.max_results,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains,
            include_answer=request.include_answer,
            include_images=request.include_images
        )

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/context", response_model=SearchResponse)
async def search_content_context(request: ContentContextRequest):
    """
    Search for additional context about extracted content

    **Use Case:**
    After extracting content from TikTok/YouTube/Reddit, use this endpoint
    to find related articles, discussions, or background information.

    **Example Flow:**
    1. Extract TikTok video → Get transcript
    2. Summarize with LLM → Get summary
    3. Search context → Find related sources
    4. Enrich article with discovered context
    """
    try:
        service = get_tavily_service()

        results = await service.search_content_context(
            content_summary=request.content_summary,
            max_results=request.max_results
        )

        return SearchResponse(
            query=f"Context search: {request.content_summary[:100]}...",
            results=results,
            total_results=len(results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context search failed: {str(e)}")


@router.post("/trending", response_model=SearchResponse)
async def search_trending_topics(request: TrendingTopicsRequest):
    """
    Search for trending content on specific platforms

    **Supported Platforms:**
    - reddit
    - twitter
    - tiktok
    - youtube
    - medium
    - substack

    **Use Cases:**
    - Discover viral content
    - Track trending discussions
    - Monitor platform-specific trends
    - Content inspiration
    """
    try:
        service = get_tavily_service()

        results = await service.search_trending_topics(
            topic=request.topic,
            platforms=request.platforms,
            max_results=request.max_results
        )

        return SearchResponse(
            query=f"Trending: {request.topic}",
            results=results,
            total_results=len(results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trending search failed: {str(e)}")


@router.post("/fact-check")
async def fact_check(request: FactCheckRequest):
    """
    Fact-check a claim by searching verification sources

    **Use Cases:**
    - Verify claims from extracted content
    - Check accuracy of statements
    - Find authoritative sources
    - Content moderation

    **Returns:**
    - Claim being verified
    - List of verification sources
    - AI-generated summary (if available)
    """
    try:
        service = get_tavily_service()

        result = await service.search_fact_check(
            claim=request.claim,
            max_results=request.max_results
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact check failed: {str(e)}")


@router.post("/news", response_model=SearchResponse)
async def search_news(request: NewsSearchRequest):
    """
    Search recent news articles from trusted sources

    **Time Ranges:**
    - `24h`: Today's news (latest, breaking)
    - `7d`: This week's news
    - `30d`: This month's news

    **News Sources:**
    - Reuters, AP News, BBC, The Guardian
    - New York Times, Wall Street Journal
    - Bloomberg, TechCrunch

    **Use Cases:**
    - Stay updated on topics
    - Research current events
    - Content sourcing for newsletters
    """
    try:
        service = get_tavily_service()

        results = await service.search_news(
            topic=request.topic,
            recency=request.recency,
            max_results=request.max_results
        )

        return SearchResponse(
            query=f"News ({request.recency}): {request.topic}",
            results=results,
            total_results=len(results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")


@router.post("/research", response_model=SearchResponse)
async def search_research(request: ResearchRequest):
    """
    Search for research sources and references

    **Academic Mode:**
    - Enabled: Focus on scholarly sources (Google Scholar, arXiv, JSTOR)
    - Disabled: General research articles and reports

    **Use Cases:**
    - Literature review
    - Reference gathering
    - Deep research
    - Academic writing support
    """
    try:
        service = get_tavily_service()

        results = await service.search_research_sources(
            research_topic=request.topic,
            academic=request.academic,
            max_results=request.max_results
        )

        return SearchResponse(
            query=f"Research ({'academic' if request.academic else 'general'}): {request.topic}",
            results=results,
            total_results=len(results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research search failed: {str(e)}")


@router.get("/capabilities")
async def get_search_capabilities():
    """
    Get information about available search capabilities

    Returns:
    - Available endpoints
    - Search types
    - Platform support
    - Use case examples
    """
    return {
        "service": "Tavily AI-Powered Search",
        "endpoints": [
            {
                "path": "/api/search/search",
                "name": "General Search",
                "description": "Execute web search with AI optimization"
            },
            {
                "path": "/api/search/context",
                "name": "Content Context",
                "description": "Find background info about extracted content"
            },
            {
                "path": "/api/search/trending",
                "name": "Trending Topics",
                "description": "Discover viral content on platforms"
            },
            {
                "path": "/api/search/fact-check",
                "name": "Fact Checking",
                "description": "Verify claims with authoritative sources"
            },
            {
                "path": "/api/search/news",
                "name": "News Search",
                "description": "Recent news from trusted sources"
            },
            {
                "path": "/api/search/research",
                "name": "Research Sources",
                "description": "Academic and research references"
            }
        ],
        "platforms": ["reddit", "twitter", "tiktok", "youtube", "medium", "substack"],
        "features": {
            "ai_optimized": True,
            "structured_results": True,
            "domain_filtering": True,
            "answer_generation": True,
            "image_search": True
        },
        "use_cases": [
            "Content enrichment after extraction",
            "Fact-checking extracted claims",
            "Trending topic discovery",
            "Research and reference gathering",
            "News monitoring and sourcing"
        ]
    }