"""Article/web page content extractor using BeautifulSoup."""

import asyncio
from typing import Dict, Any
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseExtractor, ExtractionError


class ArticleExtractor(BaseExtractor):
    """Extract content from articles and web pages."""

    @property
    def platform(self) -> str:
        return "article"

    @property
    def url_patterns(self) -> list[str]:
        return [r"^https?://"]  # Matches any HTTP(S) URL

    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract article content from a web page.

        Args:
            url: Article URL

        Returns:
            Standardized content dict

        Raises:
            ExtractionError: If extraction fails
        """
        try:
            # Fetch the page
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = self._extract_title(soup)

            # Extract author
            author = self._extract_author(soup)

            # Extract main content
            content = self._extract_content(soup)

            # Extract published date
            published_at = self._extract_published_date(soup)

            # Extract metadata
            metadata = {
                "domain": httpx.URL(url).host,
                "word_count": len(content.split()) if content else 0,
                "published_at": published_at,
                "description": self._extract_description(soup),
            }

            return self._standardize_output(
                url=url,
                title=title,
                author=author,
                content=content,
                metadata=metadata,
            )

        except httpx.HTTPStatusError as e:
            raise ExtractionError(
                f"HTTP error {e.response.status_code}",
                self.platform,
                url,
                e
            )
        except httpx.TimeoutException as e:
            raise ExtractionError(
                "Request timeout",
                self.platform,
                url,
                e
            )
        except Exception as e:
            raise ExtractionError(
                f"Failed to extract article: {str(e)}",
                self.platform,
                url,
                e
            )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # Try Twitter title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()

        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try <h1> tag
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()

        return "Untitled Article"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author."""
        # Try meta author tag
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta and author_meta.get('content'):
            return author_meta['content'].strip()

        # Try article:author meta tag
        author_article = soup.find('meta', property='article:author')
        if author_article and author_article.get('content'):
            return author_article['content'].strip()

        # Try common author class names
        author_selectors = [
            'author',
            'byline',
            'article-author',
            'post-author',
        ]
        for selector in author_selectors:
            author_elem = soup.find(class_=selector)
            if author_elem:
                return author_elem.get_text().strip()

        return "Unknown Author"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Remove script, style, nav, and footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Try to find main content container
        content_selectors = [
            ('article', {}),
            ('main', {}),
            ('div', {'class': 'content'}),
            ('div', {'class': 'article'}),
            ('div', {'class': 'post'}),
            ('div', {'id': 'content'}),
            ('div', {'id': 'article'}),
        ]

        content_container = None
        for tag, attrs in content_selectors:
            content_container = soup.find(tag, attrs)
            if content_container:
                break

        # If no specific container found, use body
        if not content_container:
            content_container = soup.find('body')

        if not content_container:
            return ""

        # Extract text from paragraphs
        paragraphs = content_container.find_all('p')
        if paragraphs:
            content = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        else:
            # Fallback to all text
            content = content_container.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())

        return content

    def _extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extract article published date."""
        # Try article:published_time meta tag
        published_meta = soup.find('meta', property='article:published_time')
        if published_meta and published_meta.get('content'):
            return published_meta['content']

        # Try datePublished schema.org
        date_schema = soup.find('meta', attrs={'itemprop': 'datePublished'})
        if date_schema and date_schema.get('content'):
            return date_schema['content']

        # Try time tag with datetime attribute
        time_tag = soup.find('time', datetime=True)
        if time_tag:
            return time_tag['datetime']

        return datetime.utcnow().isoformat()

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract article description/summary."""
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()

        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()

        return ""