# Newsletter Extraction Database Migration Plan

## Executive Summary

We're migrating newsletter extraction data from **file-based storage** (JSON files in `extractors/email/output/`) to **PostgreSQL database storage** to support Railway deployment and enable better querying/filtering capabilities.

---

## Current State Analysis

### File-Based Storage (Current)
```
extractors/email/output/
├── extraction_20251015_162827/
│   ├── filtered_articles.json          # Newsletter data with article links
│   └── config_used.json                # Extraction metadata
└── extraction_20251015_143052/
    ├── filtered_articles.json
    └── config_used.json
```

**filtered_articles.json structure:**
```json
[
  {
    "newsletter_subject": "AI Weekly Digest",
    "newsletter_sender": "hello@aiweekly.co",
    "newsletter_date": "2025-10-15T10:30:00",
    "articles": [
      {
        "url": "https://example.com/article",
        "original_url": "https://track.newsletter.co/click?..."
      }
    ]
  }
]
```

**config_used.json structure:**
```json
{
  "created_at": "2025-10-15T16:28:27",
  "days_back": 7,
  "max_results": 30,
  "senders": ["@therundown.ai", "@alphasignal.ai"]
}
```

### Frontend Expectations (Current)
```typescript
interface Extraction {
  id: string;                    // "20251015_162827"
  filename: string;              // "extraction_20251015_162827"
  newsletters: Newsletter[];
  newsletter_count: number;
  total_links: number;
  created_at?: string;
  days_back?: number;
  max_results?: number;
  senders?: string[];
}

interface Newsletter {
  newsletter_subject: string;
  newsletter_sender: string;
  newsletter_date: string;
  links: ResolvedLink[];         // NOTE: Backend calls this "articles"
  link_count: number;
}

interface ResolvedLink {
  url: string;
  original_url?: string;
}
```

---

## Naming Convention Analysis

### ⚠️ Naming Conflicts to Resolve

#### **Conflict #1: "Newsletter" Model Exists**
- **Existing Model**: `Newsletter` in `app/models/content.py` (lines 73-92)
  - Purpose: Newsletter **digest generation** from multiple content sources
  - Fields: `title`, `digest`, `source_count`, `user_id`
- **New Requirement**: Model for newsletter **email extraction**
  - Purpose: Store extracted newsletter emails and their article links
  - Fields: `subject`, `sender`, `date`, `links`

**Resolution**: Use `NewsletterEmail` or `ExtractedNewsletter` for the new model to avoid conflict

#### **Conflict #2: Frontend "links" vs Backend "articles"**
- **Frontend expects**: `newsletter.links[]`
- **Backend JSON uses**: `newsletter.articles[]`
- **Current workaround**: API transforms `articles` → `links` at response time

**Resolution**: Database should use `article_links` (clear, unambiguous) and API layer handles transformation

### Naming Convention Standards

| Layer | Convention | Example |
|-------|-----------|---------|
| **Database Tables** | `snake_case` (plural) | `extractions`, `newsletter_emails`, `article_links` |
| **Database Columns** | `snake_case` | `newsletter_subject`, `created_at`, `original_url` |
| **Python Models** | `PascalCase` | `Extraction`, `NewsletterEmail`, `ArticleLink` |
| **Python Fields** | `snake_case` | `newsletter_subject`, `created_at`, `original_url` |
| **TypeScript Interfaces** | `PascalCase` | `Extraction`, `Newsletter`, `ResolvedLink` |
| **TypeScript Properties** | `camelCase` | `newsletterSubject`, `createdAt`, `originalUrl` |
| **API JSON Keys** | `snake_case` | `newsletter_subject`, `created_at`, `original_url` |

---

## Proposed Database Schema

### Table 1: `extractions`
**Purpose**: Represents a single run of the email extraction pipeline

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(50) | PRIMARY KEY | Timestamp-based ID (e.g., "20251015_162827") |
| `created_at` | TIMESTAMP | NOT NULL, INDEX | When extraction was run |
| `days_back` | INTEGER | NULLABLE | Number of days searched (e.g., 7) |
| `max_results` | INTEGER | NULLABLE | Max newsletters extracted (e.g., 30) |
| `config` | JSONB | DEFAULT '{}' | Full config snapshot |

**Indexes**:
- Primary: `id`
- Secondary: `created_at DESC` (for listing recent extractions)

**Relationships**:
- One-to-Many with `newsletter_emails`

---

### Table 2: `newsletter_emails`
**Purpose**: Individual newsletter email within an extraction

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `extraction_id` | VARCHAR(50) | FK → extractions(id), NOT NULL, INDEX | Parent extraction |
| `subject` | VARCHAR(1024) | NOT NULL | Email subject line |
| `sender` | VARCHAR(256) | NOT NULL, INDEX | Email sender (e.g., "hello@aiweekly.co") |
| `date` | VARCHAR(100) | NOT NULL | Email date (ISO 8601 string) |

**Indexes**:
- Primary: `id`
- Foreign Key: `extraction_id` (with CASCADE DELETE)
- Secondary: `sender` (for filtering by sender)

**Relationships**:
- Many-to-One with `extractions`
- One-to-Many with `article_links`

**Why not use TIMESTAMP for date?**
- Email dates come in various formats from Gmail API
- Storing as string preserves original format
- Frontend already handles date formatting

---

### Table 3: `article_links`
**Purpose**: Article link extracted and resolved from a newsletter

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `newsletter_id` | INTEGER | FK → newsletter_emails(id), NOT NULL, INDEX | Parent newsletter |
| `url` | TEXT | NOT NULL | Resolved final article URL |
| `original_url` | TEXT | NULLABLE | Original tracking/redirect URL |

**Indexes**:
- Primary: `id`
- Foreign Key: `newsletter_id` (with CASCADE DELETE)

**Relationships**:
- Many-to-One with `newsletter_emails`

---

## SQLAlchemy Model Design

### Model 1: `Extraction`
```python
class Extraction(Base):
    """Newsletter extraction session."""
    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    days_back: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_results: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    newsletters: Mapped[list["NewsletterEmail"]] = relationship(
        "NewsletterEmail",
        back_populates="extraction",
        cascade="all, delete-orphan",
        lazy="joined"  # Eager load newsletters when querying extractions
    )
```

**Design Decisions**:
- ✅ `id` is string (timestamp format) - matches existing file naming
- ✅ `created_at` is indexed - supports `ORDER BY created_at DESC` for listing
- ✅ `config` is JSON - flexible storage for extraction parameters
- ✅ `cascade="all, delete-orphan"` - deleting extraction deletes all newsletters and links

---

### Model 2: `NewsletterEmail`
```python
class NewsletterEmail(Base):
    """Individual newsletter email within an extraction."""
    __tablename__ = "newsletter_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subject: Mapped[str] = mapped_column(String(1024), nullable=False)
    sender: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    extraction: Mapped["Extraction"] = relationship("Extraction", back_populates="newsletters")
    links: Mapped[list["ArticleLink"]] = relationship(
        "ArticleLink",
        back_populates="newsletter",
        cascade="all, delete-orphan",
        lazy="joined"
    )
```

**Design Decisions**:
- ✅ Named `NewsletterEmail` to avoid conflict with existing `Newsletter` model
- ✅ `sender` is indexed - supports filtering by sender (e.g., "@therundown.ai")
- ✅ `date` is string - preserves original format from Gmail API
- ✅ `ondelete="CASCADE"` - deleting extraction deletes all child newsletters

---

### Model 3: `ArticleLink`
```python
class ArticleLink(Base):
    """Article link extracted from a newsletter."""
    __tablename__ = "article_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    newsletter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("newsletter_emails.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    original_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    newsletter: Mapped["NewsletterEmail"] = relationship("NewsletterEmail", back_populates="links")
```

**Design Decisions**:
- ✅ Named `ArticleLink` (singular) - clear, unambiguous
- ✅ `url` is TEXT - no length limit for URLs
- ✅ `original_url` is optional - not all links have tracking URLs
- ✅ `ondelete="CASCADE"` - deleting newsletter deletes all links

---

## Migration Strategy

### Phase 1: Schema Creation (This Migration)
**File**: `alembic/versions/001_add_newsletter_extraction_models.py`

**Operations**:
1. Create `extractions` table
2. Create `newsletter_emails` table with FK to `extractions`
3. Create `article_links` table with FK to `newsletter_emails`
4. Create indexes on `created_at`, `sender`, foreign keys

**Rollback Plan**:
- Drop tables in reverse order: `article_links` → `newsletter_emails` → `extractions`

**Generated SQL** (preview):
```sql
-- Up migration
CREATE TABLE extractions (
    id VARCHAR(50) NOT NULL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    days_back INTEGER,
    max_results INTEGER,
    config JSON DEFAULT '{}'
);

CREATE INDEX idx_extractions_created_at ON extractions (created_at DESC);

CREATE TABLE newsletter_emails (
    id SERIAL PRIMARY KEY,
    extraction_id VARCHAR(50) NOT NULL REFERENCES extractions(id) ON DELETE CASCADE,
    subject VARCHAR(1024) NOT NULL,
    sender VARCHAR(256) NOT NULL,
    date VARCHAR(100) NOT NULL
);

CREATE INDEX idx_newsletter_emails_extraction_id ON newsletter_emails (extraction_id);
CREATE INDEX idx_newsletter_emails_sender ON newsletter_emails (sender);

CREATE TABLE article_links (
    id SERIAL PRIMARY KEY,
    newsletter_id INTEGER NOT NULL REFERENCES newsletter_emails(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    original_url TEXT
);

CREATE INDEX idx_article_links_newsletter_id ON article_links (newsletter_id);

-- Down migration
DROP TABLE article_links;
DROP TABLE newsletter_emails;
DROP TABLE extractions;
```

---

### Phase 2: Data Migration (Optional - If Preserving Existing Data)
**File**: `alembic/versions/002_migrate_existing_extractions.py`

**Operations**:
1. Scan `extractors/email/output/extraction_*/` directories
2. Load `filtered_articles.json` and `config_used.json`
3. Insert into database:
   - Create `Extraction` record
   - For each newsletter: Create `NewsletterEmail` record
   - For each link: Create `ArticleLink` record

**Python Script** (data migration):
```python
import json
from pathlib import Path
from datetime import datetime

def upgrade():
    # Get database connection
    connection = op.get_bind()

    # Scan output directory
    output_dir = Path(__file__).parent.parent.parent / "extractors" / "email" / "output"
    extraction_dirs = sorted(output_dir.glob("extraction_*"))

    for extraction_dir in extraction_dirs:
        extraction_id = extraction_dir.name.replace("extraction_", "")

        # Load files
        filtered_file = extraction_dir / "filtered_articles.json"
        config_file = extraction_dir / "config_used.json"

        if not filtered_file.exists():
            continue

        with open(filtered_file) as f:
            newsletters_data = json.load(f)

        config = {}
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

        # Insert extraction
        connection.execute(
            "INSERT INTO extractions (id, created_at, days_back, max_results, config) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                extraction_id,
                datetime.fromisoformat(config.get('created_at')),
                config.get('days_back'),
                config.get('max_results'),
                json.dumps(config)
            )
        )

        # Insert newsletters and links
        for newsletter_data in newsletters_data:
            result = connection.execute(
                "INSERT INTO newsletter_emails (extraction_id, subject, sender, date) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (
                    extraction_id,
                    newsletter_data['newsletter_subject'],
                    newsletter_data['newsletter_sender'],
                    newsletter_data['newsletter_date']
                )
            )
            newsletter_id = result.fetchone()[0]

            # Insert links
            for article in newsletter_data.get('articles', []):
                connection.execute(
                    "INSERT INTO article_links (newsletter_id, url, original_url) "
                    "VALUES (%s, %s, %s)",
                    (
                        newsletter_id,
                        article['url'],
                        article.get('original_url')
                    )
                )

def downgrade():
    # Truncate tables (data migration is one-way)
    connection = op.get_bind()
    connection.execute("TRUNCATE article_links, newsletter_emails, extractions CASCADE")
```

**Decision**: Do we need this?
- ✅ **Yes** if you want to preserve existing extractions in database
- ❌ **No** if starting fresh (old extractions stay in files for reference)

---

### Phase 3: API Layer Update
**File**: `app/api/endpoints/newsletters.py`

**Changes Required**:

#### 1. Add Database Dependencies
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_session
from app.models import Extraction, NewsletterEmail, ArticleLink
from sqlalchemy import select
from sqlalchemy.orm import selectinload
```

#### 2. Update `/resolve` Endpoint (Save to DB)
```python
@router.post("/resolve", response_model=dict)
async def resolve_links(
    request: NewsletterExtractRequest,
    db: AsyncSession = Depends(get_async_session)  # Add DB dependency
):
    # ... existing pipeline.py execution code ...

    # NEW: Save to database
    extraction = Extraction(
        id=extraction_id,
        created_at=datetime.fromisoformat(config.get('created_at')),
        days_back=request.days_back,
        max_results=request.max_results,
        config=config
    )
    db.add(extraction)

    for newsletter_data in newsletters_data:
        newsletter = NewsletterEmail(
            extraction_id=extraction_id,
            subject=newsletter_data['newsletter_subject'],
            sender=newsletter_data['newsletter_sender'],
            date=newsletter_data['newsletter_date']
        )
        db.add(newsletter)
        await db.flush()  # Get newsletter.id

        for article in newsletter_data.get('articles', []):
            link = ArticleLink(
                newsletter_id=newsletter.id,
                url=article['url'],
                original_url=article.get('original_url')
            )
            db.add(link)

    await db.commit()

    # Transform for frontend (articles → links)
    for newsletter in newsletters_data:
        newsletter['links'] = newsletter.pop('articles')
        newsletter['link_count'] = len(newsletter['links'])

    return {
        "status": "success",
        "id": extraction_id,
        "newsletters": newsletters_data,
        ...
    }
```

#### 3. Update `/resolved` Endpoint (Load from DB)
```python
@router.get("/resolved", response_model=List[dict])
async def list_resolved_links(db: AsyncSession = Depends(get_async_session)):
    # Query with eager loading
    stmt = (
        select(Extraction)
        .options(
            selectinload(Extraction.newsletters)
            .selectinload(NewsletterEmail.links)
        )
        .order_by(Extraction.created_at.desc())
    )
    result = await db.execute(stmt)
    extractions = result.scalars().all()

    # Transform to frontend format
    response = []
    for extraction in extractions:
        newsletters_data = []
        total_links = 0

        for newsletter in extraction.newsletters:
            links = [
                {
                    'url': link.url,
                    'original_url': link.original_url
                }
                for link in newsletter.links
            ]

            newsletters_data.append({
                'newsletter_subject': newsletter.subject,
                'newsletter_sender': newsletter.sender,
                'newsletter_date': newsletter.date,
                'links': links,  # Transform to frontend expectation
                'link_count': len(links)
            })
            total_links += len(links)

        response.append({
            'id': extraction.id,
            'filename': f"extraction_{extraction.id}",
            'newsletters': newsletters_data,
            'newsletter_count': len(newsletters_data),
            'total_links': total_links,
            'created_at': extraction.created_at.isoformat(),
            'days_back': extraction.days_back,
            'max_results': extraction.max_results
        })

    return response
```

---

## API Response Transformation

### Backend → Frontend Field Mapping

| Backend (DB/Model) | API JSON Response | Frontend (TypeScript) |
|--------------------|-------------------|-----------------------|
| `NewsletterEmail.subject` | `newsletter_subject` | `newsletter_subject` |
| `NewsletterEmail.sender` | `newsletter_sender` | `newsletter_sender` |
| `NewsletterEmail.date` | `newsletter_date` | `newsletter_date` |
| `ArticleLink.url` | `url` | `url` |
| `ArticleLink.original_url` | `original_url` | `original_url` |
| `NewsletterEmail.links` | **`links`** | `links` |
| _(computed)_ | `link_count` | `link_count` |

**Key Transformation**:
```python
# Backend model has: newsletter.links (relationship to ArticleLink)
# Frontend expects: newsletter.links (array of {url, original_url})

# API transforms:
newsletter_data = {
    'newsletter_subject': newsletter.subject,
    'links': [{'url': link.url, 'original_url': link.original_url} for link in newsletter.links],
    'link_count': len(newsletter.links)
}
```

---

## Testing Strategy

### Unit Tests
**File**: `tests/test_newsletter_extraction_models.py`

```python
async def test_create_extraction_with_newsletters():
    """Test creating extraction with nested newsletters and links."""
    extraction = Extraction(
        id="20251015_120000",
        days_back=7,
        max_results=30
    )

    newsletter = NewsletterEmail(
        extraction_id=extraction.id,
        subject="Test Newsletter",
        sender="test@example.com",
        date="2025-10-15T12:00:00"
    )
    extraction.newsletters.append(newsletter)

    link = ArticleLink(
        newsletter_id=newsletter.id,
        url="https://example.com/article",
        original_url="https://track.example.com/click"
    )
    newsletter.links.append(link)

    db.add(extraction)
    await db.commit()

    # Verify cascade loading
    stmt = select(Extraction).where(Extraction.id == "20251015_120000")
    result = await db.execute(stmt)
    loaded = result.scalar_one()

    assert len(loaded.newsletters) == 1
    assert len(loaded.newsletters[0].links) == 1
```

### Integration Tests
**File**: `tests/test_newsletter_api.py`

```python
async def test_resolve_endpoint_saves_to_database(client, db):
    """Test /resolve endpoint saves extraction to database."""
    response = await client.post("/api/newsletters/resolve", json={
        "days_back": 1,
        "max_results": 5
    })

    assert response.status_code == 200
    data = response.json()
    extraction_id = data['id']

    # Verify database
    stmt = select(Extraction).where(Extraction.id == extraction_id)
    result = await db.execute(stmt)
    extraction = result.scalar_one()

    assert extraction.days_back == 1
    assert extraction.max_results == 5
    assert len(extraction.newsletters) > 0

async def test_resolved_endpoint_loads_from_database(client, db):
    """Test /resolved endpoint returns data from database."""
    # Create test data
    extraction = Extraction(id="test_123", days_back=7)
    newsletter = NewsletterEmail(
        extraction_id="test_123",
        subject="Test",
        sender="test@example.com",
        date="2025-10-15"
    )
    link = ArticleLink(
        newsletter_id=newsletter.id,
        url="https://example.com"
    )
    newsletter.links.append(link)
    extraction.newsletters.append(newsletter)
    db.add(extraction)
    await db.commit()

    # Query API
    response = await client.get("/api/newsletters/resolved")
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    assert data[0]['id'] == "test_123"
    assert data[0]['newsletters'][0]['newsletter_subject'] == "Test"
    assert data[0]['newsletters'][0]['links'][0]['url'] == "https://example.com"
```

---

## Deployment Checklist

### Local Development
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify tables created: `psql -d content_engine -c "\dt"`
- [ ] Test API endpoints with Postman/curl
- [ ] Verify frontend still works
- [ ] Run unit tests: `pytest tests/test_newsletter_extraction_models.py`
- [ ] Run integration tests: `pytest tests/test_newsletter_api.py`

### Railway Production
- [ ] Add PostgreSQL service to Railway project
- [ ] Set `DATABASE_URL` environment variable
- [ ] Update Dockerfile to run migrations on startup:
  ```dockerfile
  CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
  ```
- [ ] Or add to `railway.json`:
  ```json
  {
    "deploy": {
      "startCommand": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    }
  }
  ```
- [ ] Deploy and monitor logs
- [ ] Test extraction via frontend on production URL
- [ ] Verify data persists across deployments

---

## Rollback Plan

### If Migration Fails
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

### If API Changes Break Frontend
- Keep file-based fallback temporarily
- Add feature flag: `ENABLE_DB_STORAGE=true/false`
- API checks flag and uses DB or files accordingly

### If Production Issues
- Railway: Rollback to previous deployment
- Database: Run `alembic downgrade -1` via Railway CLI
- Emergency: Drop tables and redeploy without migration

---

## Future Enhancements

### Phase 4: Advanced Features (Post-MVP)
1. **User Association**: Add `user_id` to `extractions` table for multi-user support
2. **Full-Text Search**: Add GIN index on `newsletter_emails.subject` for search
3. **Link Deduplication**: Track unique URLs across extractions
4. **Analytics**: Add `article_links.click_count`, `article_links.extracted_at`
5. **Soft Deletes**: Add `deleted_at` for archiving instead of hard deletes
6. **Pagination**: Add cursor-based pagination for large extraction lists
7. **Filtering**: Support query params like `?sender=@therundown.ai&days_back=7`

---

## Decision Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Use `NewsletterEmail` instead of `Newsletter` | Avoid conflict with existing `Newsletter` model for digest generation | 2025-10-15 |
| Use `ArticleLink` instead of `Link` | More descriptive, avoids potential conflicts | 2025-10-15 |
| Store email date as string | Preserve original format from Gmail API, frontend handles formatting | 2025-10-15 |
| Use async SQLAlchemy | Matches existing app architecture | 2025-10-15 |
| Eager load relationships with `selectinload` | Reduce N+1 queries when loading extractions | 2025-10-15 |
| Keep API JSON keys as `snake_case` | Consistency with existing API responses | 2025-10-15 |
| Transform `articles` → `links` in API layer | Keep backend clear, frontend gets expected format | 2025-10-15 |

---

## Questions for Review

1. ✅ **Naming**: Is `NewsletterEmail` clear enough, or prefer `ExtractedNewsletter`?
2. ✅ **Data Migration**: Should we migrate existing JSON files to database (Phase 2)?
3. ✅ **Dual Storage**: Keep writing to files + database temporarily for safety?
4. ⚠️ **User Association**: Add `user_id` now or later? (Currently anonymous extractions)
5. ⚠️ **Retention Policy**: Auto-delete extractions older than X days?
6. ⚠️ **File Cleanup**: After successful DB save, delete JSON files or keep as backup?

---

## Next Steps

1. Review this plan with team
2. Approve naming conventions
3. Run Phase 1 migration (schema creation)
4. Update API endpoints
5. Test locally
6. Deploy to Railway
7. Monitor for issues
8. Consider Phase 2 (data migration) if needed
