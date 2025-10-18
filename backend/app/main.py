"""Content Engine API - Main application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    # Startup: Initialize rate limiter with Redis
    try:
        redis_url = settings.REDIS_URL
        if redis_url and redis_url != "memory://":
            logger.info(f"✅ Initializing rate limiter with Redis: {redis_url[:20]}...")
            redis_connection = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await FastAPILimiter.init(redis_connection)
            logger.info("✅ Rate limiter initialized successfully")
        else:
            logger.warning("⚠️  No Redis URL configured, rate limiting will not work properly")
    except Exception as e:
        logger.error(f"❌ Failed to initialize rate limiter: {e}")
        logger.warning("⚠️  Continuing without rate limiting")

    yield

    # Shutdown: Close Redis connection
    try:
        await FastAPILimiter.close()
        logger.info("✅ Rate limiter shut down successfully")
    except:
        pass


# Create FastAPI app with lifespan
app = FastAPI(
    title="Content Engine API",
    description="AI-powered content extraction and processing platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Content Engine API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "features": {
            "openai": settings.has_openai,
            "anthropic": settings.has_anthropic,
            "gemini": settings.has_gemini,
            "deepseek": settings.has_deepseek,
            "gmail": settings.has_gmail,
            "tavily": settings.has_tavily,
            "default_llm": settings.default_llm_provider,
        },
    }


# Include routers
from app.api.endpoints import auth, extractors, llm, media, search, prompts, newsletters, capture

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(extractors.router, prefix="/api/extract", tags=["extractors"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])
app.include_router(newsletters.router, prefix="/api/newsletters", tags=["newsletters"])
app.include_router(capture.router, prefix="/api/capture", tags=["capture"])