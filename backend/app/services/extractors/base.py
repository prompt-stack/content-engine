from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import re


class BaseExtractor(ABC):
    """Base class for all content extractors."""

    @property
    @abstractmethod
    def platform(self) -> str:
        """Platform identifier (e.g., 'tiktok', 'youtube')."""
        pass

    @property
    @abstractmethod
    def url_patterns(self) -> list[str]:
        """Regex patterns that this extractor can handle."""
        pass

    @abstractmethod
    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract content from URL.

        Args:
            url: URL to extract from
            **kwargs: Platform-specific options

        Returns:
            Dict with standardized content structure

        Raises:
            ExtractionError: If extraction fails
        """
        pass

    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        for pattern in self.url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _standardize_output(
        self,
        url: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Standardize extractor output format."""
        return {
            "platform": self.platform,
            "url": url,
            "title": title or "",
            "author": author or "",
            "content": content or "",
            "metadata": metadata or {},
            "extracted_at": datetime.utcnow().isoformat(),
        }


class ExtractionError(Exception):
    """Raised when content extraction fails."""

    def __init__(self, message: str, platform: str, url: str, original_error: Optional[Exception] = None):
        self.message = message
        self.platform = platform
        self.url = url
        self.original_error = original_error
        super().__init__(f"[{platform}] {message}: {url}")


class PlatformDetector:
    """Detect which platform a URL belongs to."""

    _patterns = {
        "tiktok": [r"tiktok\.com/@[\w.-]+/video/\d+", r"vm\.tiktok\.com/\w+", r"vt\.tiktok\.com/\w+", r"tiktok\.com/t/\w+"],
        "youtube": [r"youtube\.com/watch\?v=[\w-]+", r"youtu\.be/[\w-]+"],
        "reddit": [r"reddit\.com/r/[\w-]+/comments/[\w-]+", r"redd\.it/\w+"],
        "article": [r"^https?://"],  # Fallback for any HTTP(S) URL
    }

    @classmethod
    def detect(cls, url: str) -> Optional[str]:
        """Detect platform from URL."""
        for platform, patterns in cls._patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return platform
        return None