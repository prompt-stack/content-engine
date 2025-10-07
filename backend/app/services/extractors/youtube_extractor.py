"""YouTube Transcript Extractor - Uses yt-dlp with YouTube API fallback."""

import re
import json
import asyncio
import tempfile
import os
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
        Uses youtube-transcript-api first (works better on cloud),
        falls back to yt-dlp if that fails.

        Args:
            url: YouTube video URL

        Returns:
            Standardized content dict with transcript
        """
        video_id = self._extract_video_id(url)

        # Try youtube-transcript-api first (more reliable on cloud)
        try:
            return await self._extract_via_transcript_api(video_id, url)
        except Exception as transcript_error:
            # If transcript API fails, try yt-dlp as fallback
            try:
                await self._check_ytdlp()
                video_info = await self._get_video_info(url)
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
                        "description": video_info.get("description", "")[:500],
                        "method": "yt-dlp-fallback",
                    },
                )

            except Exception as ytdlp_error:
                # Both methods failed
                raise ExtractionError(
                    message=f"Failed to extract YouTube content. Transcript API: {str(transcript_error)[:100]}. yt-dlp: {str(ytdlp_error)[:100]}",
                    platform=self.platform,
                    url=url,
                    original_error=transcript_error,
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
            # Update yt-dlp in the background to ensure we have the latest version
            # This helps with YouTube's frequent changes
            await asyncio.create_subprocess_exec(
                "yt-dlp", "-U",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
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
        # Use multiple player clients as fallback strategy
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--extractor-args", "youtube:player_client=android_creator,android,web",
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
            # Use android_creator client which has better subtitle access
            process = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--write-auto-sub",
                "--sub-lang",
                "en",
                "--convert-subs",
                "srt",
                "--skip-download",
                "--no-check-certificates",
                "--extractor-args", "youtube:player_client=android_creator,android,web",
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

    async def _extract_via_transcript_api(self, video_id: str, url: str) -> Dict[str, Any]:
        """
        Extract using SupaData API first (cloud-friendly, designed for this),
        fallback to youtube-transcript-api library.
        """
        import httpx

        # Try SupaData API first if key is available
        supadata_key = os.getenv("SUPA_DATA_API")
        if supadata_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        "https://api.supadata.ai/v1/youtube/transcript",
                        params={"url": url, "text": "true"},
                        headers={"x-api-key": supadata_key}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        transcript_text = data.get("content", "")

                        if transcript_text:
                            # Get metadata using yt-dlp or httpx
                            video_info = await self._get_video_metadata(url, video_id)
                            content = self._format_with_transcript(video_info, transcript_text)

                            return self._standardize_output(
                                url=url,
                                title=video_info['title'],
                                author=video_info['uploader'],
                                content=content,
                                metadata={
                                    "video_id": video_id,
                                    "duration": video_info.get("duration"),
                                    "view_count": video_info.get("view_count"),
                                    "upload_date": video_info.get("upload_date"),
                                    "channel": video_info.get("channel"),
                                    "has_transcript": True,
                                    "description": video_info.get("description", "")[:500],
                                    "method": "supadata",
                                    "transcript_lang": data.get("lang"),
                                },
                            )
            except Exception as e:
                # SupaData failed, continue to fallback
                pass

        # Fallback to youtube-transcript-api
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # Run in thread pool since library is synchronous
            def get_transcript_sync():
                api = YouTubeTranscriptApi()
                transcript_list = api.list(video_id)
                transcript = transcript_list.find_transcript(['en'])
                return transcript.fetch()

            # Run synchronous code in thread pool
            loop = asyncio.get_event_loop()
            text_data = await loop.run_in_executor(None, get_transcript_sync)

            # Combine transcript text
            transcript_text = ' '.join([entry.text for entry in text_data])

            # Get video metadata
            video_info = await self._get_video_metadata(url, video_id)

            content = self._format_with_transcript(video_info, transcript_text)

            return self._standardize_output(
                url=url,
                title=video_info.get('title', 'YouTube Video'),
                author=video_info.get('uploader', 'Unknown'),
                content=content,
                metadata={
                    "video_id": video_id,
                    "duration": video_info.get("duration"),
                    "view_count": video_info.get("view_count"),
                    "upload_date": video_info.get("upload_date"),
                    "channel": video_info.get("channel"),
                    "has_transcript": True,
                    "description": video_info.get("description", "")[:500],
                    "method": "transcript-api",
                },
            )

        except Exception as e:
            raise RuntimeError(f"Transcript API error: {str(e)}")

    async def _extract_via_youtube_api(self, video_id: str, url: str) -> Dict[str, Any]:
        """
        Fallback method using YouTube Data API v3.
        Requires YOUTUBE_API_KEY environment variable.
        """
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not set. Cannot use YouTube API fallback.")

        try:
            from googleapiclient.discovery import build

            # Build YouTube API client
            youtube = build('youtube', 'v3', developerKey=api_key)

            # Get video details
            video_response = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()

            if not video_response.get('items'):
                raise ValueError(f"Video {video_id} not found")

            video_data = video_response['items'][0]
            snippet = video_data['snippet']
            statistics = video_data.get('statistics', {})

            # Try to get captions
            captions_response = youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()

            transcript = ""
            has_transcript = False

            # Check if captions are available
            if captions_response.get('items'):
                # Find English caption
                for caption in captions_response['items']:
                    if caption['snippet']['language'] == 'en':
                        # Note: Downloading caption content requires OAuth
                        # For now, we'll just note that captions exist
                        has_transcript = True
                        transcript = "[Captions available but require OAuth to download. Video has English captions.]"
                        break

            # Parse duration from ISO 8601 format
            duration_str = video_data['contentDetails']['duration']
            duration_seconds = self._parse_iso_duration(duration_str)

            video_info = {
                'title': snippet['title'],
                'uploader': snippet['channelTitle'],
                'channel': snippet['channelTitle'],
                'description': snippet['description'],
                'duration': duration_seconds,
                'view_count': int(statistics.get('viewCount', 0)),
                'upload_date': snippet['publishedAt'][:10].replace('-', ''),
                'webpage_url': url,
            }

            if has_transcript and transcript:
                content = self._format_with_transcript(video_info, transcript)
            else:
                content = self._format_no_transcript(video_info)

            return self._standardize_output(
                url=url,
                title=video_info['title'],
                author=video_info['uploader'],
                content=content,
                metadata={
                    "video_id": video_id,
                    "duration": duration_seconds,
                    "view_count": video_info['view_count'],
                    "upload_date": video_info['upload_date'],
                    "channel": video_info['channel'],
                    "has_transcript": has_transcript,
                    "description": video_info['description'][:500],
                    "method": "youtube-api",
                },
            )

        except ImportError:
            raise ValueError("google-api-python-client not installed")
        except Exception as e:
            raise RuntimeError(f"YouTube API error: {str(e)}")

    def _parse_iso_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration (e.g., PT1H2M10S) to seconds."""
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    async def _get_video_metadata(self, url: str, video_id: str) -> Dict[str, Any]:
        """
        Get video metadata. Try yt-dlp first, fallback to basic scraping.
        """
        import httpx
        import re

        # Try yt-dlp first
        try:
            await self._check_ytdlp()
            return await self._get_video_info(url)
        except:
            # Fallback: scrape basic info from page
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    title_match = re.search(r'<title>(.+?)</title>', response.text)
                    title = title_match.group(1).replace(' - YouTube', '') if title_match else f"YouTube Video {video_id}"

                    return {
                        'title': title,
                        'uploader': 'Unknown',
                        'channel': 'Unknown',
                        'description': '',
                        'duration': None,
                        'view_count': 0,
                        'upload_date': '',
                        'webpage_url': url,
                    }
            except:
                # Last resort fallback
                return {
                    'title': f"YouTube Video {video_id}",
                    'uploader': 'Unknown',
                    'channel': 'Unknown',
                    'description': '',
                    'duration': None,
                    'view_count': 0,
                    'upload_date': '',
                    'webpage_url': url,
                }