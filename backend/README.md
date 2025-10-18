# Content Engine – Backend

FastAPI application that powers the Prompt Stack content engine. This backend is responsible for extracting content, processing it with LLMs, storing results, and serving authenticated API endpoints for the frontend.

## Directory Map

| Path | Description |
|------|-------------|
| `app/` | FastAPI source code (endpoints, services, models, auth helpers). |
| `alembic/`, `alembic.ini` | Database migrations and Alembic configuration. |
| `config/` | Example configuration snippets and archived settings. |
| `docs/` | Backend-specific documentation (schema mapping, shortcut setup, etc.). |
| `extractors/` | Legacy Node/JS helpers used by some extractors (TikTok, newsletter pipeline). |
| `scripts/` | Operational utilities (owner promotion, social credential manager, etc.). |
| `tests/` | Automated pytest suites. Stand-alone smoke scripts also live in the repo root (see below). |
| `use-local.sh`, `use-railway.sh` | Convenience scripts for swapping `.env` between local and Railway deployments. |
| `Dockerfile`, `requirements.txt` | Container build definition and Python dependencies. |

### Stand-alone test scripts

```
test_all_endpoints.py       # Smoke test hitting key APIs
test_auth_integration.py    # Clerk auth integration checks
test_config_api.py          # Newsletter config API coverage
test_mvp_schema_simple.py   # Legacy schema sanity test
test_tier1_protections.sh   # Shell-based security checks
```

These scripts pre-date the `tests/` package but are still useful for manual regression runs.

## Authentication

All endpoints consume Clerk JWTs via `app.core.clerk`. The old helper module `app.api.deps` remains only for backwards compatibility and emits deprecation warnings. Always depend on:

```python
from app.core.clerk import get_current_user_from_clerk
from app.models.user import User

@router.get("/example")
async def example(user: User = Depends(get_current_user_from_clerk)):
    ...
```

## Environment Configuration

1. Copy `.env.local` → `.env` for local development (`./use-local.sh` does this automatically).
2. Populate provider keys (OpenAI, Anthropic, Gemini, DeepSeek, Tavily) plus Clerk keys.
3. For Railway deployments set the same variables via the project dashboard (including `REDIS_URL` if rate limiting should be active).

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start API locally (after running use-local.sh)
python3 -m uvicorn app.main:app --reload --port 9765

# Run migrations
alembic upgrade head

# Run automated tests
pytest
```

## Documentation

- `docs/SCHEMA_OVERVIEW.md` – Database schema reference
- `docs/SCHEMA_DATA_MAPPING.md` – Newsletter extraction mapping
- `docs/NEWSLETTER_CONFIG_DATABASE.md` – Config schema details
- `docs/IOS_SHORTCUT_SETUP.md` and `docs/shortcut-setup.html` – iOS Shortcut instructions

For full-stack authentication details see `../docs/AUTH-INTEGRATION.md` in the repository root.
