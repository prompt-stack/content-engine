"""Newsletter digest API endpoints."""

import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session, async_session_maker
from app.crud import newsletter_extraction as crud
from app.core.clerk import get_current_user_from_clerk
from app.models.user import User
from app.models.newsletter_extraction import ExtractionStatus


router = APIRouter()

# Path to extractors directory
EXTRACTORS_DIR = Path(__file__).parent.parent.parent.parent / "extractors" / "email"
OUTPUT_DIR = EXTRACTORS_DIR / "output"
CONFIG_FILE = EXTRACTORS_DIR / "config.json"


class NewsletterExtractRequest(BaseModel):
    """Request to extract newsletters."""
    days_back: Optional[int] = Field(default=None, ge=1, le=90, description="Days to look back (mutually exclusive with hours_back)")
    hours_back: Optional[float] = Field(default=None, ge=0.1, le=2160, description="Hours to look back (mutually exclusive with days_back)")
    max_results: int = Field(default=30, ge=1, le=100, description="Maximum newsletters to extract")
    senders: Optional[List[str]] = Field(default=None, description="Filter by specific sender emails")


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


# =============================================================================
# BACKGROUND TASK FUNCTIONS
# =============================================================================

async def run_extraction_pipeline(
    extraction_id: str,
    days_back_value: float,
    max_results: int,
    senders: List[str],
    user_id: int
):
    """
    Run the newsletter extraction pipeline in background.

    This is an async function that uses run_in_executor for the blocking subprocess.run()
    call, allowing it to run without blocking the event loop.

    Updates progress in database at key milestones:
    - 10%: Starting extraction from Gmail
    - 20%: Extracting newsletters from Gmail
    - 90%: Loading extraction results
    - 100%: Complete

    Args:
        extraction_id: Unique extraction ID
        days_back_value: Days to look back (supports fractional for hours)
        max_results: Maximum newsletters to extract
        senders: List of sender emails to filter by
        user_id: User ID who owns this extraction
    """
    import asyncio
    import json
    from concurrent.futures import ThreadPoolExecutor
    from app.crud import google_token as google_token_crud

    # Create new database session for background task
    async with async_session_maker() as db:
        token_file = None  # Initialize for cleanup in finally block
        try:
            # Update: Starting
            await crud.update_extraction_progress(
                db=db,
                extraction_id=extraction_id,
                progress=10,
                progress_message="Starting extraction from Gmail...",
                status=ExtractionStatus.PROCESSING.value
            )

            # Get user's decrypted Google OAuth token
            token_data = await google_token_crud.get_decrypted_token(db, user_id)
            if not token_data:
                await crud.fail_extraction(
                    db=db,
                    extraction_id=extraction_id,
                    error_message="No Google account connected. Please connect Gmail in Settings."
                )
                return

            # Save token to extraction directory for pipeline to use
            # This allows the subprocess to access the user's OAuth token
            extraction_dir = OUTPUT_DIR / f"extraction_{extraction_id}"
            extraction_dir.mkdir(parents=True, exist_ok=True)

            token_file = extraction_dir / "user_token.json"
            with open(token_file, 'w') as f:
                json.dump(token_data, f)

            # Build pipeline command
            cmd = [
                "python3.11",
                str(EXTRACTORS_DIR / "pipeline.py"),
                "--days", str(days_back_value),
                "--max", str(max_results),
                "--extraction-id", extraction_id,  # Pass extraction ID to ensure directory names match
                "--token-file", str(token_file)  # Pass token file path
            ]

            # Add senders if provided
            if senders:
                cmd.extend(["--senders"] + senders)

            # Update: Running pipeline
            await crud.update_extraction_progress(
                db=db,
                extraction_id=extraction_id,
                progress=20,
                progress_message="Extracting newsletters from Gmail..."
            )

            # Run pipeline in executor (non-blocking)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    lambda: subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(EXTRACTORS_DIR),
                        timeout=600  # 10 minute timeout
                    )
                )

            # Check if pipeline failed
            if result.returncode != 0:
                error_output = result.stderr or result.stdout or "Pipeline failed with no error message"

                # Check if this was just "no newsletters found" (not an error, just empty result)
                if "No newsletters found" in error_output or "⚠️  No newsletters found" in error_output:
                    # Complete extraction with empty results and helpful message
                    await crud.complete_extraction(
                        db=db,
                        extraction_id=extraction_id,
                        newsletters_data=[]
                    )
                    # Update with helpful message
                    await crud.update_extraction_progress(
                        db=db,
                        extraction_id=extraction_id,
                        progress=100,
                        progress_message="No newsletters found in the specified time range. Try a longer time window or check your sender filters."
                    )
                    return

                # Actual error - fail the extraction
                await crud.fail_extraction(
                    db=db,
                    extraction_id=extraction_id,
                    error_message=error_output
                )
                return

            # Update: Loading results
            await crud.update_extraction_progress(
                db=db,
                extraction_id=extraction_id,
                progress=90,
                progress_message="Loading extraction results..."
            )

            # Find the extraction output directory
            # Pipeline creates: extraction_YYYYMMDD_HHMMSS/
            extraction_dirs = sorted(
                OUTPUT_DIR.glob(f"extraction_{extraction_id}*"),
                reverse=True
            )

            if not extraction_dirs:
                await crud.fail_extraction(
                    db=db,
                    extraction_id=extraction_id,
                    error_message="Extraction completed but output directory not found"
                )
                return

            extraction_dir = extraction_dirs[0]
            filtered_file = extraction_dir / "filtered_articles.json"

            if not filtered_file.exists():
                await crud.fail_extraction(
                    db=db,
                    extraction_id=extraction_id,
                    error_message="Extraction completed but filtered_articles.json not found"
                )
                return

            # Load results
            with open(filtered_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            # Handle different result formats (list or dict with 'newsletters' key)
            if isinstance(results, list):
                newsletters_data = results
            else:
                newsletters_data = results.get('newsletters', [])

            # Complete extraction with results
            await crud.complete_extraction(
                db=db,
                extraction_id=extraction_id,
                newsletters_data=newsletters_data
            )

        except subprocess.TimeoutExpired:
            await crud.fail_extraction(
                db=db,
                extraction_id=extraction_id,
                error_message="Extraction timed out after 10 minutes"
            )
        except Exception as e:
            await crud.fail_extraction(
                db=db,
                extraction_id=extraction_id,
                error_message=f"Unexpected error: {str(e)}"
            )
        finally:
            # Clean up token file for security
            if token_file and token_file.exists():
                try:
                    token_file.unlink()
                except Exception:
                    pass  # Best effort cleanup


# =============================================================================
# EXTRACTION ENDPOINTS
# =============================================================================

@router.post("/extract", response_model=dict)
async def extract_newsletters(
    request: NewsletterExtractRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_from_clerk)
):
    """
    Extract newsletters and links from email sources (ASYNC - returns immediately).

    Creates a pending extraction job and runs the pipeline in the background.
    Use GET /extractions/{extraction_id}/status to poll for progress.

    **Time Range:** Specify either days_back OR hours_back (not both)
    **Senders:** Optional list of email addresses to filter by

    **Returns immediately with extraction_id for status polling**
    """
    try:
        # Validate mutually exclusive time parameters
        if request.days_back and request.hours_back:
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both days_back and hours_back"
            )

        # Calculate days_back (support fractional days for hours)
        if request.hours_back:
            days_back_value = request.hours_back / 24.0
        elif request.days_back:
            days_back_value = float(request.days_back)
        else:
            days_back_value = 7.0  # Default

        # Generate unique extraction ID
        extraction_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create pending extraction in database
        await crud.create_pending_extraction(
            db=db,
            extraction_id=extraction_id,
            days_back=int(days_back_value) if days_back_value == int(days_back_value) else days_back_value,
            max_results=request.max_results,
            user_id=current_user.id
        )

        # Queue background task
        background_tasks.add_task(
            run_extraction_pipeline,
            extraction_id=extraction_id,
            days_back_value=days_back_value,
            max_results=request.max_results,
            senders=request.senders or [],
            user_id=current_user.id
        )

        # Return immediately
        return {
            "status": "pending",
            "extraction_id": extraction_id,
            "message": "Extraction started - use /extractions/{id}/status to poll for progress"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extractions/{extraction_id}/status", response_model=dict)
async def get_extraction_status(
    extraction_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_from_clerk)
):
    """
    Get current status of an extraction job.

    Frontend polls this endpoint every 2 seconds to show progress.

    Returns:
        - status: pending|processing|completed|failed
        - progress: 0-100
        - progress_message: Current step description
        - error_message: Error details if failed
        - newsletters: Full extraction data if completed
    """
    try:
        # Get extraction from database
        extraction = await crud.get_extraction(db, extraction_id)

        if not extraction:
            raise HTTPException(status_code=404, detail="Extraction not found")

        # Check user owns this extraction
        if extraction.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this extraction")

        # Build response
        response = {
            "extraction_id": extraction.id,
            "status": extraction.status,
            "progress": extraction.progress,
            "progress_message": extraction.progress_message,
            "created_at": extraction.created_at.isoformat() if extraction.created_at else None,
            "completed_at": extraction.completed_at.isoformat() if extraction.completed_at else None,
        }

        # Add error message if failed
        if extraction.status == ExtractionStatus.FAILED.value:
            response["error_message"] = extraction.error_message

        # Add full results if completed
        if extraction.status == ExtractionStatus.COMPLETED.value:
            # Transform content_items to match frontend expectations
            newsletters_data = []
            total_links = 0

            for email_content in extraction.content_items:
                newsletter = {
                    'newsletter_subject': email_content.subject,
                    'newsletter_sender': email_content.sender,
                    'newsletter_date': email_content.date,
                    'links': [
                        {
                            'url': link.url,
                            'original_url': link.original_url,
                            'curator_description': link.curator_description
                        }
                        for link in email_content.links
                    ],
                    'link_count': len(email_content.links)
                }
                newsletters_data.append(newsletter)
                total_links += len(email_content.links)

            response["newsletters"] = newsletters_data
            response["newsletter_count"] = len(newsletters_data)
            response["total_links"] = total_links

        return response

    except HTTPException:
        raise
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
async def list_extractions(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_from_clerk)
):
    """
    List all newsletter extractions from database for the authenticated user.

    Returns list of extractions with their newsletters and filtered article links.
    Only returns extractions owned by the authenticated user.
    """
    try:
        # Load all extractions from database for the authenticated user
        extractions = await crud.get_all_extractions(db, user_id=current_user.id)

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
                            'original_url': link.original_url,
                            'curator_description': link.curator_description
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
async def get_email_config(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_from_clerk)
):
    """
    Get the current email extractor configuration for the authenticated user.

    First checks database. If not found, seeds from config.json file.
    This ensures config persists across Railway restarts.
    """
    try:
        # Try to get config from database for this user
        config = await crud.get_config(db, user_id=current_user.id)

        if config:
            # Found in database - return it
            return config

        # Not in database - seed from config.json file
        if not CONFIG_FILE.exists():
            raise HTTPException(status_code=404, detail="Config file not found")

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Save to database for future requests (tied to this user)
        await crud.upsert_config(db, config_data=config, user_id=current_user.id)

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_email_config(
    config: Dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_from_clerk)
):
    """
    Update the email extractor configuration for the authenticated user.

    Saves the updated config to database (persists across Railway restarts).
    """
    try:
        # Validate that content_filtering section exists
        if 'content_filtering' not in config:
            raise HTTPException(
                status_code=400,
                detail="Config must contain 'content_filtering' section"
            )

        # Save to database (tied to this user)
        await crud.upsert_config(db, config_data=config, user_id=current_user.id)

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
