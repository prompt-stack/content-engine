"""Content Engine API - Main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title="Content Engine API",
    description="AI-powered content extraction and processing platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from app.api.endpoints import extractors, llm, media, search, prompts

app.include_router(extractors.router, prefix="/api/extract", tags=["extractors"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])