"""Article/web page content extractor using Node.js based extractor."""

import asyncio
import json
from typing import Dict, Any
from pathlib import Path
from .base import BaseExtractor, ExtractionError


class ArticleExtractor(BaseExtractor):
    """Extract content from articles and web pages using Node.js extractor."""

    @property
    def platform(self) -> str:
        return "article"

    @property
    def url_patterns(self) -> list[str]:
        return [r"^https?://"]  # Matches any HTTP(S) URL

    async def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract article content using Node.js extractor with table support.

        Args:
            url: Article URL

        Returns:
            Standardized content dict

        Raises:
            ExtractionError: If extraction fails
        """
        try:
            # Get path to the Node.js extractor
            backend_root = Path(__file__).parent.parent.parent.parent
            extractor_path = backend_root / "extractors" / "article" / "article-extractor.js"

            if not extractor_path.exists():
                raise ExtractionError("Article extractor script not found", self.platform, url)

            # Run the Node.js extractor with larger buffer limits
            # TODO: Fix buffer truncation issue for large outputs (>8KB)
            # Currently working: Direct node execution and outputs <8KB
            # Issue: Python subprocess appears to truncate at 8192 bytes despite limit parameter
            process = await asyncio.create_subprocess_exec(
                "node",
                str(extractor_path),
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=10 * 1024 * 1024,  # 10MB buffer limit
            )

            # Read output with explicit buffer handling
            stdout_data = await process.stdout.read()
            stderr_data = await process.stderr.read()
            await process.wait()

            if process.returncode != 0:
                error_msg = stderr_data.decode() if stderr_data else "Unknown error"
                raise ExtractionError(f"Article extraction failed: {error_msg}", self.platform, url)

            # Parse the JSON output
            result = json.loads(stdout_data.decode())

            if not result.get('success'):
                raise ExtractionError(f"Article extraction failed: {result.get('error')}", self.platform, url)

            # Calculate word count from content
            word_count = len(result['content'].split()) if result.get('content') else 0

            return self._standardize_output(
                url=result.get('url', url),
                title=result.get('title', 'Untitled'),
                author=result.get('author', 'Unknown'),
                content=result.get('content', ''),
                metadata={
                    'siteName': result.get('metadata', {}).get('siteName'),
                    'word_count': word_count,
                    'excerpt': result.get('description', ''),
                    'scraped': result.get('metadata', {}).get('scraped'),
                },
            )

        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse article extractor output: {str(e)}", self.platform, url, e)
        except FileNotFoundError:
            raise ExtractionError("Node.js not installed or extractor not found", self.platform, url)
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Article extraction failed: {str(e)}", self.platform, url, e)
