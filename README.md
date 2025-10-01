# Content Engine

AI-powered content extraction and processing platform. Extract content from multiple platforms (TikTok, YouTube, Reddit, Articles, Email) and process with LLMs (OpenAI, Anthropic, Gemini, DeepSeek).

## Features

- **Multi-Platform Extraction**: TikTok, YouTube, Reddit, Article, Email, Betting
- **LLM Processing**: Summarization, entity extraction, sentiment analysis, categorization
- **Newsletter Pipeline**: Automated newsletter digest generation (killer feature)
- **API-First**: RESTful API with OpenAPI documentation
- **Type-Safe**: Pydantic models throughout
- **Async**: Built on FastAPI for high performance

## Tech Stack

### Backend
- **FastAPI**: Python async web framework
- **SQLAlchemy 2.0**: Async ORM
- **Alembic**: Database migrations
- **FastAPI Users**: JWT + OAuth2 authentication
- **Neon**: Serverless Postgres with pgvector
- **Redis**: Rate limiting + caching
- **Celery**: Background job processing

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Shadcn UI**: Component library

## Quick Start

```bash
# Start development environment
docker-compose up -d

# Services (using non-standard ports to avoid conflicts):
# - Frontend:     http://localhost:3456
# - Backend API:  http://localhost:9765
# - PostgreSQL:   localhost:7654
# - Redis:        localhost:8765
# - API docs:     http://localhost:9765/docs
#
# To change ports, edit backend/.env file
```

## Project Structure

```
content-engine/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Config, security
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   └── services/         # Business logic
│   │       ├── extractors/   # Platform extractors
│   │       ├── llm/          # LLM providers
│   │       └── processors/   # Content processors
│   └── tests/
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   └── lib/                  # Utilities
└── docs/                     # Documentation
```

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## License

TBD