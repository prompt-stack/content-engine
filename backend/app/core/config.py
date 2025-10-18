from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    API_PORT: int = 8765

    # Database (optional - only needed if using auth features)
    POSTGRES_PORT: int = 5433
    DATABASE_URL: str = "sqlite:///./content_engine.db"

    # Redis
    REDIS_PORT: int = 6380
    REDIS_URL: str = "redis://localhost:6380/0"

    # Authentication (optional - only needed if using auth features)
    JWT_SECRET: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Key Authentication (for cost control)
    API_SECRET_KEY: str = ""  # Set this in production to require API key

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3456",
        # Vercel deployments handled by regex in main.py
    ]

    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # Search API
    TAVILY_API_KEY: str = ""

    # Google Gmail API
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # Clerk Authentication
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_SECRET_KEY: str = ""

    # Rate Limiting (requests per month)
    RATE_LIMIT_FREE: int = 100
    RATE_LIMIT_STARTER: int = 1000
    RATE_LIMIT_PRO: int = 10000
    RATE_LIMIT_BUSINESS: int = 50000

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Feature Flags
    ENABLE_BETTING_EXTRACTOR: bool = False
    ENABLE_EMAIL_EXTRACTOR: bool = True
    ENABLE_EXTRACTORS: bool = True  # Disable all extractors (for cost control)
    ENABLE_LLM: bool = True  # Disable LLM endpoints (for cost control)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)

    @property
    def has_deepseek(self) -> bool:
        return bool(self.DEEPSEEK_API_KEY)

    @property
    def has_gmail(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def default_llm_provider(self) -> str:
        """Return first available LLM provider, prefer DeepSeek for cost."""
        if self.has_deepseek:
            return "deepseek"
        if self.has_openai:
            return "openai"
        if self.has_anthropic:
            return "anthropic"
        if self.has_gemini:
            return "gemini"
        return "demo"


# Global settings instance
settings = Settings()