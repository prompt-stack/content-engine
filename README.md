# Content Engine

**Full-stack AI-powered content processing platform** for extracting, processing, and synthesizing information from social media platforms. Built with modern production-ready architecture and deployed at scale.

🚀 **Live Demo**: [Content Engine](https://content-engine-frontend-green.vercel.app)
📚 **Documentation**: [Prompt Stack](https://prompt-stack.github.io)
🔧 **Backend API**: [Railway Deployment](https://content-engine-production.up.railway.app/docs)

## What It Does

Content Engine extracts content from platforms like YouTube, Twitter, TikTok, and Articles, processes it with multiple LLM providers, and stores it in a searchable vault. It's designed for research, content synthesis, and knowledge management workflows.

**Real-world use**: This platform powers the content on [Prompt Stack](https://prompt-stack.github.io), demonstrating end-to-end AI-assisted content workflows.

## Key Features

- **Multi-Platform Extraction**: YouTube (transcripts + metadata), Twitter, TikTok, Articles, Email, Newsletters
- **Multi-Provider LLM Integration**: OpenAI GPT-4, Anthropic Claude, Google Gemini, DeepSeek (cost-optimized default)
- **Content Vault**: Store, organize, and search extracted content with metadata
- **Newsletter Pipeline**: Automated extraction and digest generation from newsletters
- **Prompt Management**: Save and reuse prompts for consistent processing
- **Production-Ready Auth**: Clerk JWT authentication with JIT user provisioning
- **Rate Limiting**: Redis-backed rate limiting (10 req/min for LLM endpoints)
- **Type-Safe API**: OpenAPI documentation with Pydantic models
- **Async Architecture**: Built on FastAPI for high performance

## Tech Stack

### Backend (FastAPI)
- **Framework**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with Alembic migrations
- **Authentication**: Clerk JWT with JIT user provisioning
- **LLM Providers**: OpenAI, Anthropic Claude, Google Gemini, DeepSeek
- **Rate Limiting**: Redis + FastAPILimiter
- **Deployment**: Railway (auto-deployment from GitHub)
- **API Docs**: OpenAPI/Swagger at `/docs`

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: Shadcn UI component library
- **Authentication**: Clerk React SDK
- **Deployment**: Vercel (auto-deployment from GitHub)

## Deployment

**Backend** on Railway: `https://content-engine-production.up.railway.app`
**Frontend** on Vercel: `https://content-engine-frontend-green.vercel.app`

Both services auto-deploy from the `main` branch on GitHub push.

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

## Architecture

Content Engine follows a clean architecture pattern:

1. **Extractors** (`backend/app/services/extractors/`) - Platform-specific content extraction
2. **LLM Service** (`backend/app/services/llm/`) - Multi-provider LLM integration
3. **Processors** (`backend/app/services/processors/`) - Content processing workflows
4. **API Layer** (`backend/app/api/`) - RESTful endpoints with authentication
5. **Frontend** (`frontend/app/`) - Next.js pages with protected routes

Key architectural decisions:
- **BaseExtractor pattern** for consistent extraction workflows
- **Fallback hierarchy**: Primary API → Library → CLI tool → Scraping
- **Async throughout** for performance
- **Type safety** with Pydantic models
- **Standardized responses** for all API endpoints

## Local Development

```bash
# Clone the repository
git clone https://github.com/prompt-stack/content-engine.git
cd content-engine

# Start services (uses custom ports to avoid conflicts)
docker-compose up -d

# Access the application
# - Frontend:     http://localhost:3456
# - Backend API:  http://localhost:9765
# - API docs:     http://localhost:9765/docs
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and patterns
- **[Auth Integration](docs/AUTH-INTEGRATION.md)** - Clerk authentication setup
- **[CORS Configuration](docs/CORS-CONFIGURATION.md)** - Cross-origin setup
- **[Development Guide](docs/DEVELOPMENT.md)** - Local development setup

## Contributing

This is an open-source project built with AI-assisted development. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Links

- **GitHub**: [prompt-stack/content-engine](https://github.com/prompt-stack/content-engine)
- **Portfolio**: [Prompt Stack](https://prompt-stack.github.io)
- **Organization**: [prompt-stack](https://github.com/prompt-stack)

---

**Built with AI-assisted development.** The code is real, the deployments work, and the patterns are actionable. That's the point.