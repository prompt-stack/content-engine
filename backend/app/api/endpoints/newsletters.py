"""Newsletter digest API endpoints."""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.crud import newsletter_extraction as crud


router = APIRouter()

# Path to extractors directory
EXTRACTORS_DIR = Path(__file__).parent.parent.parent.parent / "extractors" / "email"
OUTPUT_DIR = EXTRACTORS_DIR / "output"
CONFIG_FILE = EXTRACTORS_DIR / "config.json"


class NewsletterExtractRequest(BaseModel):
    """Request to extract newsletters."""
    days_back: int = Field(default=7, ge=1, le=90, description="Days to look back")
    max_results: int = Field(default=30, ge=1, le=100, description="Maximum newsletters to extract")


class NewsletterSummary(BaseModel):
    """Summary of a newsletter."""
    subject: str
    sender: str
    date: str
    article_count: int


class DigestSummary(BaseModel):
    """Summary of a digest."""
    id: str
    timestamp: str
    newsletter_count: int
    total_articles: int
    successful: int
    failed: int
    newsletters: List[NewsletterSummary]


class ArticleInfo(BaseModel):
    """Article information."""
    title: str
    url: str
    file: str


class NewsletterDetail(BaseModel):
    """Detailed newsletter with articles."""
    subject: str
    sender: str
    date: str
    total_links: int
    successful: int
    failed: int
    articles: List[ArticleInfo]


class DigestDetail(BaseModel):
    """Detailed digest."""
    id: str
    timestamp: str
    newsletter_count: int
    total_articles: int
    successful: int
    failed: int
    newsletters: List[NewsletterDetail]


@router.post("/extract", response_model=dict)
async def extract_newsletters(
    request: NewsletterExtractRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Extract newsletters and links from email sources.

    Runs the complete pipeline (Steps 1-4) and returns filtered article links.
    Also saves the extraction to the database.
    """
    try:
        # Run pipeline.py which does everything: extract → parse → resolve → filter
        result = subprocess.run(
            [
                "python3.11",
                str(EXTRACTORS_DIR / "pipeline.py"),
                "--days", str(request.days_back),
                "--max", str(request.max_results)
            ],
            capture_output=True,
            text=True,
            cwd=str(EXTRACTORS_DIR)
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed: {result.stderr}"
            )

        # Find the latest extraction directory
        extraction_dirs = sorted(OUTPUT_DIR.glob("extraction_*"), reverse=True)
        if not extraction_dirs:
            raise HTTPException(
                status_code=404,
                detail="No extraction found"
            )

        extraction_dir = extraction_dirs[0]
        filtered_file = extraction_dir / "filtered_articles.json"

        if not filtered_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Filtered articles file not found"
            )

        # Extract ID from directory name
        extraction_id = extraction_dir.name.replace("extraction_", "")

        # Load the filtered articles (contains newsletters with valid links only)
        with open(filtered_file, 'r') as f:
            newsletters_data = json.load(f)

        # Save to database
        await crud.create_extraction(
            db=db,
            extraction_id=extraction_id,
            newsletters_data=newsletters_data,
            days_back=request.days_back,
            max_results=request.max_results
        )

        # Transform data to match frontend expectations
        for newsletter in newsletters_data:
            # Rename 'articles' to 'links' for frontend compatibility
            if 'articles' in newsletter:
                newsletter['links'] = newsletter.pop('articles')

            # Add link_count field
            newsletter['link_count'] = len(newsletter.get('links', []))

        return {
            "status": "success",
            "id": extraction_id,
            "message": "Extraction complete",
            "newsletters": newsletters_data,
            "days_back": request.days_back,
            "max_results": request.max_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/{resolved_id}", response_model=dict)
async def extract_content(
    resolved_id: str,
    background_tasks: BackgroundTasks
):
    """
    Extract content from a resolved links file.

    This is step 2 - runs batch extraction on previously resolved links.
    """
    try:
        resolved_file = OUTPUT_DIR / f"resolved_links_{resolved_id}.json"

        if not resolved_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Resolved links file not found"
            )

        # Run batch_extract.py in background with the resolved links
        def run_batch_extract():
            subprocess.run(
                [
                    "python3.11",
                    str(EXTRACTORS_DIR / "batch_extract.py"),
                    "--input", str(resolved_file),
                    "--delay", "1.5"
                ],
                cwd=str(EXTRACTORS_DIR)
            )

        background_tasks.add_task(run_batch_extract)

        # Return job info
        return {
            "status": "processing",
            "message": "Content extraction started in background",
            "resolved_id": resolved_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extractions", response_model=List[dict])
async def list_extractions(db: AsyncSession = Depends(get_async_session)):
    """
    List all newsletter extractions from database.

    Returns list of extractions with their newsletters and filtered article links.
    """
    try:
        # Load all extractions from database
        extractions = await crud.get_all_extractions(db)

        result = []
        for extraction in extractions:
            # Transform database models to API response format
            newsletters_data = []
            total_links = 0

            for email_content in extraction.content_items:
                # Transform to match frontend expectations
                newsletter = {
                    'newsletter_subject': email_content.subject,
                    'newsletter_sender': email_content.sender,
                    'newsletter_date': email_content.date,
                    'links': [
                        {
                            'url': link.url,
                            'original_url': link.original_url
                        }
                        for link in email_content.links
                    ],
                    'link_count': len(email_content.links)
                }
                newsletters_data.append(newsletter)
                total_links += len(email_content.links)

            result.append({
                'id': extraction.id,
                'filename': f"extraction_{extraction.id}",
                'newsletters': newsletters_data,
                'newsletter_count': len(newsletters_data),
                'total_links': total_links,
                'created_at': extraction.created_at.isoformat() if extraction.created_at else None,
                'days_back': extraction.days_back,
                'max_results': extraction.max_results,
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digests", response_model=List[DigestSummary])
async def list_digests():
    """
    List all available newsletter digests.

    Returns summaries sorted by timestamp (newest first).
    """
    try:
        digest_dirs = sorted(
            OUTPUT_DIR.glob("newsletter_digest_*"),
            reverse=True
        )

        digests = []

        for digest_dir in digest_dirs:
            manifest_file = digest_dir / "manifest.json"
            if not manifest_file.exists():
                continue

            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Extract ID from directory name (timestamp)
            digest_id = digest_dir.name.replace("newsletter_digest_", "")

            # Create newsletter summaries
            newsletter_summaries = []
            for newsletter in manifest.get('newsletters', []):
                newsletter_summaries.append(NewsletterSummary(
                    subject=newsletter['newsletter_subject'],
                    sender=newsletter['newsletter_sender'],
                    date=newsletter['newsletter_date'],
                    article_count=newsletter['successful']
                ))

            digests.append(DigestSummary(
                id=digest_id,
                timestamp=manifest['timestamp'],
                newsletter_count=manifest['total_newsletters'],
                total_articles=manifest['total_links'],
                successful=manifest['total_successful'],
                failed=manifest['total_failed'],
                newsletters=newsletter_summaries
            ))

        return digests

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digests/{digest_id}", response_model=DigestDetail)
async def get_digest(digest_id: str):
    """
    Get detailed information about a specific digest.

    Includes all newsletters with their extracted articles.
    """
    try:
        digest_dir = OUTPUT_DIR / f"newsletter_digest_{digest_id}"
        manifest_file = digest_dir / "manifest.json"

        if not manifest_file.exists():
            raise HTTPException(status_code=404, detail="Digest not found")

        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        # Build detailed newsletter information
        newsletter_details = []
        for newsletter in manifest.get('newsletters', []):
            articles = []
            for article in newsletter.get('articles', []):
                articles.append(ArticleInfo(
                    title=article['title'],
                    url=article['url'],
                    file=article['file']
                ))

            newsletter_details.append(NewsletterDetail(
                subject=newsletter['newsletter_subject'],
                sender=newsletter['newsletter_sender'],
                date=newsletter['newsletter_date'],
                total_links=newsletter['total_links'],
                successful=newsletter['successful'],
                failed=newsletter['failed'],
                articles=articles
            ))

        return DigestDetail(
            id=digest_id,
            timestamp=manifest['timestamp'],
            newsletter_count=manifest['total_newsletters'],
            total_articles=manifest['total_links'],
            successful=manifest['total_successful'],
            failed=manifest['total_failed'],
            newsletters=newsletter_details
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digests/{digest_id}/article/{filename}")
async def get_article_content(digest_id: str, filename: str):
    """
    Get the markdown content of a specific article.
    """
    try:
        digest_dir = OUTPUT_DIR / f"newsletter_digest_{digest_id}"
        article_file = digest_dir / filename

        if not article_file.exists():
            raise HTTPException(status_code=404, detail="Article not found")

        with open(article_file, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "filename": filename,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digests/{digest_id}/markdown")
async def get_digest_markdown(digest_id: str):
    """
    Get the complete digest as markdown.
    """
    try:
        digest_dir = OUTPUT_DIR / f"newsletter_digest_{digest_id}"
        digest_file = digest_dir / "digest.md"

        if not digest_file.exists():
            raise HTTPException(status_code=404, detail="Digest markdown not found")

        with open(digest_file, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "digest_id": digest_id,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EMAIL EXTRACTOR CONFIGURATION ENDPOINTS
# =============================================================================

class ContentFilteringConfig(BaseModel):
    """Content filtering configuration."""
    description: str = "Control which domains/URLs to always accept or reject"
    whitelist_domains: List[str] = Field(default_factory=list)
    blacklist_domains: List[str] = Field(default_factory=list)
    curator_domains: List[str] = Field(default_factory=list)
    content_indicators: List[str] = Field(default_factory=list)


class EmailExtractorConfig(BaseModel):
    """Email extractor configuration."""
    content_filtering: ContentFilteringConfig


class TestURLRequest(BaseModel):
    """Request to test a URL against filtering rules."""
    url: str = Field(..., description="URL to test")


class TestURLResponse(BaseModel):
    """Response from URL filtering test."""
    url: str
    is_valid: bool
    reason: str


@router.get("/config", response_model=Dict)
async def get_email_config():
    """
    Get the current email extractor configuration.

    Returns the config.json content from the email extractor directory.
    """
    try:
        if not CONFIG_FILE.exists():
            raise HTTPException(status_code=404, detail="Config file not found")

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_email_config(config: Dict):
    """
    Update the email extractor configuration.

    Saves the updated config to config.json.
    """
    try:
        # Validate that content_filtering section exists
        if 'content_filtering' not in config:
            raise HTTPException(
                status_code=400,
                detail="Config must contain 'content_filtering' section"
            )

        # Write to config file
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": "Configuration updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/test-url", response_model=TestURLResponse)
async def test_url_filtering(request: TestURLRequest):
    """
    Test if a URL would pass the current filtering rules.

    This helps users understand why certain URLs are being filtered.
    """
    try:
        # Import the filtering function from step4
        import sys
        sys.path.insert(0, str(EXTRACTORS_DIR))
        from step4_filter_content import is_content_url, load_config

        # Load current config
        config = load_config()

        # Test the URL
        is_valid = is_content_url(request.url, config)

        # Determine reason
        if is_valid:
            reason = "URL matches content criteria and would be accepted"
        else:
            from urllib.parse import urlparse
            parsed = urlparse(request.url)
            domain = parsed.netloc.lower().replace('www.', '')

            # Check against filters to give specific reason
            filtering = config.get('content_filtering', {})
            blacklist = filtering.get('blacklist_domains', [])
            curators = filtering.get('curator_domains', [])

            if any(bl in domain for bl in blacklist):
                reason = "Domain is in blacklist (survey/form site)"
            elif any(cur in domain for cur in curators):
                reason = "Domain is a newsletter curator (circular reference)"
            else:
                reason = "URL does not match content criteria (not in whitelist and no content indicators)"

        return TestURLResponse(
            url=request.url,
            is_valid=is_valid,
            reason=reason
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
