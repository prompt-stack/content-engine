"""
Tavily Search Service for Content Engine
AI-powered web search API for content research and enrichment

Features:
- Advanced search depth (AI-optimized results)
- Structured search results (not raw HTML)
- Context-aware queries
- Specialized content research methods

Updated: September 2025
"""

import httpx
from typing import List, Dict, Any, Optional, Literal
from app.core.config import settings


class TavilyService:
    """
    Tavily AI-powered search service

    Use cases:
    - Content research and fact-checking
    - Context enrichment for extracted content
    - Trend analysis and market research
    - Source discovery
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"

        if not self.api_key:
            raise ValueError("Tavily API key not configured. Set TAVILY_API_KEY in .env")

    async def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "advanced",
        max_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a Tavily search

        Args:
            query: Search query
            search_depth: "basic" (faster) or "advanced" (more accurate, AI-optimized)
            max_results: Maximum number of results (1-20)
            include_domains: List of domains to include (e.g., ["reddit.com", "twitter.com"])
            exclude_domains: List of domains to exclude
            include_answer: Include AI-generated answer summary
            include_raw_content: Include full page content
            include_images: Include related images

        Returns:
            List of search results with title, url, content, score
        """
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content,
                "include_images": include_images
            }

            if include_domains:
                payload["include_domains"] = include_domains
            if exclude_domains:
                payload["exclude_domains"] = exclude_domains

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data.get("results", [])

        except httpx.HTTPStatusError as e:
            raise Exception(f"Tavily API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Tavily search failed: {str(e)}")

    async def search_content_context(
        self,
        content_summary: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for additional context about extracted content

        Use case: After extracting a TikTok/YouTube video, find related articles,
        discussions, or background information to enrich the content.

        Args:
            content_summary: Summary of the content to research
            max_results: Number of results

        Returns:
            List of contextual sources
        """
        query = f"background information context about: {content_summary}"
        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True
        )

    async def search_trending_topics(
        self,
        topic: str,
        platforms: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for trending content on specific platforms

        Args:
            topic: Topic to search
            platforms: List of platforms (e.g., ["reddit", "twitter", "tiktok"])
            max_results: Number of results

        Returns:
            List of trending content
        """
        platform_domains = {
            "reddit": "reddit.com",
            "twitter": "twitter.com",
            "tiktok": "tiktok.com",
            "youtube": "youtube.com",
            "medium": "medium.com",
            "substack": "substack.com"
        }

        include_domains = None
        if platforms:
            include_domains = [platform_domains.get(p.lower(), p) for p in platforms]

        query = f"trending recent viral popular: {topic}"
        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=include_domains
        )

    async def search_fact_check(
        self,
        claim: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for fact-checking sources about a claim

        Args:
            claim: Claim to fact-check
            max_results: Number of results

        Returns:
            Dict with results and AI answer
        """
        query = f"fact check verify sources: {claim}"
        results = await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            exclude_domains=["pinterest.com", "instagram.com"]  # Exclude social image sites
        )

        return {
            "claim": claim,
            "sources": results,
            "total_sources": len(results)
        }

    async def search_news(
        self,
        topic: str,
        recency: Literal["24h", "7d", "30d"] = "7d",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for recent news articles

        Args:
            topic: News topic
            recency: Time range (24h, 7d, 30d)
            max_results: Number of results

        Returns:
            List of news articles
        """
        recency_terms = {
            "24h": "today latest breaking",
            "7d": "this week recent",
            "30d": "this month recent news"
        }

        query = f"{recency_terms[recency]} {topic}"

        # Focus on news domains
        news_domains = [
            "reuters.com", "apnews.com", "bbc.com", "theguardian.com",
            "nytimes.com", "wsj.com", "bloomberg.com", "techcrunch.com"
        ]

        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=news_domains
        )

    async def search_research_sources(
        self,
        research_topic: str,
        academic: bool = False,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for research sources and references

        Args:
            research_topic: Topic to research
            academic: Focus on academic sources
            max_results: Number of results

        Returns:
            List of research sources
        """
        if academic:
            query = f"research study paper academic scholarly: {research_topic}"
            include_domains = [
                "scholar.google.com", "arxiv.org", "jstor.org",
                "sciencedirect.com", "springer.com", "nature.com"
            ]
        else:
            query = f"research analysis report study: {research_topic}"
            include_domains = None

        return await self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=include_domains,
            include_answer=True
        )


# Factory function for dependency injection
def get_tavily_service() -> TavilyService:
    """Get Tavily service instance"""
    return TavilyService()