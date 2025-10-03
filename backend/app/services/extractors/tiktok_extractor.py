"""TikTok Extractor - Uses Node.js based extractor"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any
from .base import BaseExtractor, ExtractionError
from .url_utils import expand_url, is_mobile_or_shortened_url
from datetime import datetime


class TikTokExtractor(BaseExtractor):
    """Extract TikTok video content using Node.js extractor."""

    @property
    def platform(self) -> str:
        return "tiktok"

    @property
    def url_patterns(self) -> list[str]:
        return [
            r"tiktok\.com/@[\w.-]+/video/\d+",
            r"vm\.tiktok\.com/\w+",
            r"vt\.tiktok\.com/\w+",
        ]

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract TikTok video transcript and metadata.

        Args:
            url: TikTok video URL (supports mobile/shortened URLs)

        Returns:
            Standardized content dict with transcript and metadata
        """
        try:
            # Expand mobile/shortened URLs
            if is_mobile_or_shortened_url(url):
                url = await expand_url(url)
            # Get path to the Node.js extractor
            backend_root = Path(__file__).parent.parent.parent.parent
            extractor_dir = backend_root / "extractors" / "tiktok"

            # Try extractors in order of preference
            extractor_files = [
                "extract-full-with-comments.js",
                "tiktok-extractor.js"
            ]

            extractor_path = None
            for filename in extractor_files:
                candidate = extractor_dir / filename
                if candidate.exists():
                    extractor_path = candidate
                    break

            if not extractor_path:
                raise ExtractionError("TikTok extractor scripts not found", "tiktok", url)

            # Run the Node.js extractor
            result = subprocess.run(
                ["node", str(extractor_path), url],
                capture_output=True,
                text=True,
                cwd=str(extractor_dir),
                timeout=30
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                if "403" in error_msg or "blocked" in error_msg.lower():
                    raise ExtractionError("TikTok is blocking automated requests", "tiktok", url)
                raise ExtractionError(f"Failed to extract TikTok content: {error_msg}", "tiktok", url)

            # Parse the output (formatted text from extract-full-with-comments.js)
            output = result.stdout.strip()

            # Parse the formatted text output
            lines = output.split('\n')
            title = ""
            creator = ""
            description = ""
            transcript = ""
            views = 0
            likes = 0
            comments = 0
            shares = 0
            duration = 0

            in_transcript = False
            for i, line in enumerate(lines):
                if line.startswith('Title:'):
                    title = line.replace('Title:', '').strip()
                    # Clean title - remove hashtags
                    if '#' in title:
                        title = title.split('#')[0].strip()
                elif line.startswith('Creator:'):
                    creator = line.replace('Creator:', '').strip().lstrip('@')
                elif line.startswith('Views:'):
                    try:
                        views = int(line.replace('Views:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Likes:'):
                    try:
                        likes = int(line.replace('Likes:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Comments:'):
                    try:
                        comments = int(line.replace('Comments:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Shares:'):
                    try:
                        shares = int(line.replace('Shares:', '').replace(',', '').strip())
                    except:
                        pass
                elif line.startswith('Duration:'):
                    try:
                        duration_str = line.replace('Duration:', '').replace('s', '').strip()
                        duration = int(duration_str)
                    except:
                        pass
                elif '📝 Description:' in line:
                    # Next line is description
                    if i + 1 < len(lines):
                        description = lines[i + 1].strip()
                elif '💬 Transcript:' in line:
                    # Everything after this is transcript (until next section)
                    in_transcript = True
                    continue
                elif in_transcript:
                    # Stop at next section markers
                    if line.startswith('👤 Creator Stats:') or line.startswith('💭') or line.startswith('💾'):
                        in_transcript = False
                    elif line.strip():
                        transcript += line + '\n'

            transcript = transcript.strip()

            # Use first line of transcript as title if no title
            if not title and transcript:
                first_line = transcript.split('\n')[0][:100]
                title = first_line + ('...' if len(first_line) >= 100 else '')
            elif not title:
                title = f"TikTok by @{creator}" if creator else "TikTok Video"

            return self._standardize_output(
                url=url,
                title=title,
                author=creator,
                content=transcript,
                metadata={
                    'description': description,
                    'has_transcript': bool(transcript),
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'shares': shares,
                    'duration': duration,
                }
            )

        except subprocess.TimeoutExpired:
            raise ExtractionError("TikTok extraction timed out after 30 seconds", "tiktok", url)
        except FileNotFoundError:
            raise ExtractionError("Node.js not installed or extractor not found", "tiktok", url)
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"TikTok extraction failed: {str(e)}", "tiktok", url)