---
name: "Content Engine Extraction Workflow"
description: "Extract and process content from social media platforms using the Content Engine's standardized workflow and architecture patterns"
version: 1.0.0
---

## Overview
This Skill guides the creation and modification of content extractors for the Content Engine platform. Use this when adding new extractors or modifying existing ones.

## Extractor Architecture

All extractors follow the BaseExtractor pattern located in `backend/app/services/extractors/base.py`:

### Required Properties
- `platform` - Platform identifier (e.g., "youtube", "twitter", "tiktok")
- `url_patterns` - List of regex patterns to match platform URLs

### Required Methods
- `extract(url: str) -> Dict[str, Any]` - Main extraction logic
- `_standardize_output()` - Format results consistently

### Standard Output Format
```python
{
    "url": str,           # Original URL
    "title": str,         # Content title
    "author": str,        # Creator/channel name
    "content": str,       # Main content (markdown formatted)
    "platform": str,      # Platform identifier
    "extracted_at": str,  # ISO timestamp
    "metadata": dict      # Platform-specific data
}
```

## Extraction Strategy Pattern

Follow this fallback hierarchy:
1. **Primary API** - Use official/paid API if available (e.g., SupaData for YouTube)
2. **Library Fallback** - Use Python libraries (e.g., youtube-transcript-api)
3. **CLI Tool Fallback** - Use command-line tools (e.g., yt-dlp)
4. **Scraping (Last Resort)** - Direct HTTP requests with httpx

## File Locations

### Backend Structure
```
backend/app/services/extractors/
├── base.py                    # BaseExtractor class
├── youtube_extractor.py       # Reference implementation
├── article_extractor.py
├── tiktok_extractor.py
└── [new_platform]_extractor.py
```

### API Endpoints
```
backend/app/api/endpoints/extractors.py
```

## Code Style Guidelines

1. **Always use async/await** for I/O operations
2. **Include comprehensive error handling** with ExtractionError
3. **Format output in markdown** for LLM consumption
4. **Add metadata** for platform-specific information
5. **Follow rate limit patterns** - Use `@router` dependencies with RateLimiter

## Environment Variables

Add platform API keys to `.env`:
```
PLATFORM_API_KEY=your-key-here
```

And update `backend/app/core/config.py` Settings class:
```python
PLATFORM_API_KEY: str = ""

@property
def has_platform(self) -> bool:
    return bool(self.PLATFORM_API_KEY)
```

## Testing Workflow

1. **Local testing**: Run extractor directly
2. **API testing**: Test via `/api/extract/{platform}` endpoint
3. **Integration**: Verify with Clerk authentication
4. **Rate limiting**: Confirm rate limits are enforced

## Example: Adding a New Extractor

When asked to add a new platform:
1. Create `backend/app/services/extractors/{platform}_extractor.py`
2. Inherit from BaseExtractor
3. Implement required properties and methods
4. Register in `backend/app/api/endpoints/extractors.py`
5. Add Clerk authentication dependency
6. Update documentation

## Reference Implementation

See `backend/app/services/extractors/youtube_extractor.py` for a complete example with:
- Multi-tier fallback strategy
- SupaData API integration
- Comprehensive error handling
- Markdown formatting
- Metadata extraction
