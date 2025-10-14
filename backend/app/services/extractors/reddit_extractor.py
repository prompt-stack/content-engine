"""Reddit Extractor - Uses Python wrapper with short link resolution"""

import subprocess
import json
import tempfile
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseExtractor, ExtractionError
from .url_utils import expand_url, is_mobile_or_shortened_url


class RedditExtractor(BaseExtractor):
    """Extract Reddit posts and comments using Python wrapper with Brave/Tavily fallback."""

    @property
    def platform(self) -> str:
        return "reddit"

    @property
    def url_patterns(self) -> list[str]:
        return [
            r"reddit\.com/r/\w+/comments/\w+",
            r"reddit\.com/s/\w+",  # shortened URLs
            r"redd\.it/\w+",
        ]

    async def extract(self, url: str, max_comments: int = 20, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract Reddit post and comments using Python wrapper with short link resolution.

        Args:
            url: Reddit post URL (supports short links, permalinks)
            max_comments: Maximum number of comments to extract (default: 20)
            title: Post title (optional, helps resolve short links if redirect fails)

        Returns:
            Standardized content dict with post and comments
        """
        try:
            # Get path to the Python wrapper (extract.py)
            backend_root = Path(__file__).parent.parent.parent.parent
            extractor_dir = backend_root / "extractors" / "reddit"
            python_wrapper = extractor_dir / "extract.py"

            if not python_wrapper.exists():
                raise ExtractionError("Reddit Python wrapper not found", "reddit", url)

            # Add the extractor dir to Python path so it can import url_resolver
            sys.path.insert(0, str(extractor_dir))

            try:
                # Import and use the updated extract function
                from extractors.reddit.extract import extract_reddit

                # Call the Python wrapper with title parameter
                result = extract_reddit(url, title=title)

                if not result.get('success'):
                    error_msg = result.get('error', 'Unknown error')
                    raise ExtractionError(f"Reddit extraction failed: {error_msg}", "reddit", url)

                # Return standardized output
                return self._standardize_output(
                    url=result.get('url', url),
                    title=result.get('title', 'Reddit Post'),
                    author=result.get('author', ''),
                    content=result.get('content', ''),
                    metadata=result.get('metadata', {})
                )

            finally:
                # Clean up sys.path
                if str(extractor_dir) in sys.path:
                    sys.path.remove(str(extractor_dir))

        except ImportError as e:
            raise ExtractionError(f"Failed to import Reddit extractor: {str(e)}", "reddit", url)
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Reddit extraction failed: {str(e)}", "reddit", url)