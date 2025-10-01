"""YouTube Transcript Extractor - Uses yt-dlp to extract video transcripts."""

import re
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseExtractor, ExtractionError


class YouTubeExtractor(BaseExtractor):
    """Extract YouTube video transcripts using yt-dlp."""

    @property
    def platform(self) -> str:
        return "youtube"

    @property
    def url_patterns(self) -> list[str]:
        return [
            r"youtube\.com/watch\?v=[\w-]+",
            r"youtu\.be/[\w-]+",
            r"youtube\.com/embed/[\w-]+",
            r"youtube\.com/v/[\w-]+",
            r"youtube\.com/shorts/[\w-]+",
        ]

    async def extract(self, url: str) -> Dict[str, Any]:
        """
        Extract YouTube video transcript.

        Args:
            url: YouTube video URL

        Returns:
            Standardized content dict with transcript
        """
        try:
            # Check if yt-dlp is installed
            await self._check_ytdlp()

            # Extract video ID
            video_id = self._extract_video_id(url)

            # Get video info
            video_info = await self._get_video_info(url)

            # Try to get transcript
            transcript = await self._get_transcript(url, video_id)

            if transcript:
                content = self._format_with_transcript(video_info, transcript)
                has_transcript = True
            else:
                content = self._format_no_transcript(video_info)
                has_transcript = False

            return self._standardize_output(
                url=video_info.get("webpage_url", url),
                title=video_info.get("title", "YouTube Video"),
                author=video_info.get("uploader", "Unknown"),
                content=content,
                metadata={
                    "video_id": video_id,
                    "duration": video_info.get("duration"),
                    "view_count": video_info.get("view_count"),
                    "upload_date": video_info.get("upload_date"),
                    "channel": video_info.get("channel"),
                    "has_transcript": has_transcript,
                    "description": video_info.get("description", "")[:500],  # Truncate long descriptions
                },
            )

        except Exception as e:
            raise ExtractionError(
                message=f"Failed to extract YouTube content: {str(e)}",
                platform=self.platform,
                url=url,
                original_error=e,
            )

    async def _check_ytdlp(self) -> None:
        """Check if yt-dlp is installed."""
        try:
            process = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            if process.returncode != 0:
                raise FileNotFoundError()
        except FileNotFoundError:
            raise ValueError(
                "yt-dlp is not installed. Install with: pip install yt-dlp "
                "or brew install yt-dlp (macOS)"
            )

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Check if it's already just a video ID
        if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
            return url

        raise ValueError("Invalid YouTube URL or video ID")

    async def _get_video_info(self, url: str) -> Dict[str, Any]:
        """Get video metadata using yt-dlp."""
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")

        return json.loads(stdout.decode())

    async def _get_transcript(self, url: str, video_id: str) -> Optional[str]:
        """Download and parse transcript using yt-dlp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Try to download subtitles (prefer auto-generated English)
            process = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--write-auto-sub",
                "--sub-lang",
                "en",
                "--convert-subs",
                "srt",
                "--skip-download",
                "--paths",
                str(temp_path),
                "--output",
                video_id,
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.communicate()

            # Find subtitle file
            possible_files = [
                f"{video_id}.en.srt",
                f"{video_id}.en-US.srt",
                f"{video_id}.en-GB.srt",
                f"{video_id}.srt",
            ]

            subtitle_path = None
            for filename in possible_files:
                file_path = temp_path / filename
                if file_path.exists():
                    subtitle_path = file_path
                    break

            # If specific file not found, try to find any .srt file
            if not subtitle_path:
                srt_files = list(temp_path.glob("*.srt"))
                if srt_files:
                    subtitle_path = srt_files[0]

            if subtitle_path:
                return self._parse_srt(subtitle_path.read_text(encoding="utf-8"))

            return None

    def _parse_srt(self, srt_content: str) -> str:
        """Parse SRT subtitle file to plain text."""
        lines = []

        for line in srt_content.split("\n"):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip subtitle numbers (digits only)
            if re.match(r"^\d+$", line):
                continue

            # Skip timestamp lines
            if "-->" in line:
                continue

            # This is text content
            lines.append(line)

        # Join with spaces and clean up
        text = " ".join(lines)
        text = re.sub(r"\s+", " ", text)  # Normalize whitespace
        return text.strip()

    def _format_with_transcript(self, video_info: Dict[str, Any], transcript: str) -> str:
        """Format content with transcript."""
        return f"""YouTube Video Transcript

Title: {video_info.get('title', 'Unknown')}
Channel: {video_info.get('uploader', 'Unknown')}
Duration: {self._format_duration(video_info.get('duration'))}
Views: {video_info.get('view_count', 0):,}

Description:
{video_info.get('description', 'No description')[:500]}

---

Transcript:
{transcript}"""

    def _format_no_transcript(self, video_info: Dict[str, Any]) -> str:
        """Format content when no transcript is available."""
        return f"""YouTube Video (No Transcript Available)

Title: {video_info.get('title', 'Unknown')}
Channel: {video_info.get('uploader', 'Unknown')}
Duration: {self._format_duration(video_info.get('duration'))}
Views: {video_info.get('view_count', 0):,}

Description:
{video_info.get('description', 'No description')[:500]}

This video doesn't have captions/subtitles available.
You may need to watch the video to understand the content."""

    def _format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in seconds to human-readable format."""
        if not seconds:
            return "Unknown"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"