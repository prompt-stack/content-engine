"""Reddit Extractor - Uses Node.js based extractor"""

import subprocess
import json
import tempfile
import os
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from .base import BaseExtractor, ExtractionError
from .url_utils import expand_url, is_mobile_or_shortened_url


class RedditExtractor(BaseExtractor):
    """Extract Reddit posts and comments using Node.js extractor."""

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

    async def extract(self, url: str, max_comments: int = 20) -> Dict[str, Any]:
        """
        Extract Reddit post and comments.

        Args:
            url: Reddit post URL (supports mobile/shortened URLs)
            max_comments: Maximum number of comments to extract (default: 20)

        Returns:
            Standardized content dict with post and comments
        """
        try:
            # Expand mobile/shortened URLs
            if is_mobile_or_shortened_url(url):
                url = await expand_url(url)
            # Get path to the Node.js extractor
            backend_root = Path(__file__).parent.parent.parent.parent
            extractor_dir = backend_root / "extractors" / "reddit"
            extractor_path = extractor_dir / "reddit-extractor.js"

            if not extractor_path.exists():
                raise ExtractionError("Reddit extractor script not found", "reddit", url)

            # Create a temp file for output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as f:
                temp_file = f.name

            try:
                # Run the Node.js extractor
                result = subprocess.run(
                    ["node", str(extractor_path), url, temp_file],
                    capture_output=True,
                    text=True,
                    cwd=str(extractor_dir),
                    timeout=30
                )

                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout
                    raise ExtractionError(f"Failed to extract Reddit content: {error_msg}", "reddit", url)

                # Read the extracted content
                with open(temp_file, 'r') as f:
                    content = f.read()

                # Parse metadata from content
                title = "Reddit Post"
                author = ""
                subreddit = ""
                score = 0
                comments_count = 0

                # Extract title
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()

                # Extract author
                author_match = re.search(r'\*\*Posted by\*\*\s+(u/[\w-]+)', content)
                if author_match:
                    author = author_match.group(1)

                # Extract subreddit
                sub_match = re.search(r'\*\*Subreddit:\*\*\s+r/([\w-]+)', content)
                if sub_match:
                    subreddit = sub_match.group(1)

                # Extract score
                score_match = re.search(r'\*\*Score:\*\*\s+(\d+)', content)
                if score_match:
                    score = int(score_match.group(1))

                # Extract comment count
                comments_match = re.search(r'\*\*Comments:\*\*\s+(\d+)', content)
                if comments_match:
                    comments_count = int(comments_match.group(1))

                return self._standardize_output(
                    url=url,
                    title=title,
                    author=author,
                    content=content,
                    metadata={
                        'subreddit': subreddit,
                        'score': score,
                        'comments': comments_count,
                        'platform': 'reddit'
                    }
                )

            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

        except subprocess.TimeoutExpired:
            raise ExtractionError("Reddit extraction timed out after 30 seconds", "reddit", url)
        except FileNotFoundError:
            raise ExtractionError("Node.js not installed or extractor not found", "reddit", url)
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Reddit extraction failed: {str(e)}", "reddit", url)