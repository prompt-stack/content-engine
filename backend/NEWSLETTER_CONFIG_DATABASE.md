# Newsletter Config Database Migration

## What Was Added

### Database Table: `newsletter_config`
```sql
CREATE TABLE newsletter_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_newsletter_config_user_id ON newsletter_config(user_id);
```

### Why Database Instead of File?

**Problem:** Railway's filesystem is ephemeral - config changes via `/newsletters/config` UI were lost on restart.

**Solution:** Store config in PostgreSQL for persistence across deployments.

## Architecture

### Current Workflow (Hybrid Approach)
1. **`config.json`** = Default template (in git, deployed with code)
2. **`newsletter_config` table** = Runtime config (persists across restarts)
3. **API Logic:**
   - First request: Load from `config.json` → Save to database
   - Subsequent requests: Read/write from database
   - Fallback: If database empty, use `config.json`

### Single User Mode (Current)
```
newsletter_config table:
┌────┬─────────┬──────────────────┬────────────┬────────────┐
│ id │ user_id │   config_data    │ created_at │ updated_at │
├────┼─────────┼──────────────────┼────────────┼────────────┤
│  1 │  NULL   │ {...json...}     │ 2025-10-15 │ 2025-10-15 │
└────┴─────────┴──────────────────┴────────────┴────────────┘
```
- `user_id = NULL` → System default config (no auth required)

### Multi-User Mode (Future)
```
newsletter_config table:
┌────┬─────────┬──────────────────┬────────────┬────────────┐
│ id │ user_id │   config_data    │ created_at │ updated_at │
├────┼─────────┼──────────────────┼────────────┼────────────┤
│  1 │  NULL   │ {...json...}     │ 2025-10-15 │ 2025-10-15 │  ← System default
│  2 │    1    │ {...json...}     │ 2025-10-15 │ 2025-10-15 │  ← User 1 config
│  3 │    2    │ {...json...}     │ 2025-10-15 │ 2025-10-15 │  ← User 2 config
└────┴─────────┴──────────────────┴────────────┴────────────┘
```
- Each user can have custom whitelist/blacklist/sources
- Falls back to `user_id=NULL` if user has no config

## Config Data Structure

The `config_data` column stores the entire config as JSON:

```json
{
  "newsletters": {
    "enabled": true,
    "sources": [
      {
        "name": "AlphaSignal",
        "email": "news@alphasignal.ai",
        "enabled": true,
        "category": "tech",
        "priority": "high"
      }
    ]
  },
  "settings": {
    "default_days_back": 7,
    "max_results": 100,
    "auto_digest": true
  },
  "content_filtering": {
    "whitelist_domains": ["github.com", "arxiv.org"],
    "blacklist_domains": ["typeform.com"],
    "curator_domains": ["alphasignal.ai"],
    "content_indicators": ["/blog/", "/article/", "/2025/"]
  }
}
```

## Testing & Seeding

### View Current Config
```bash
# Via API
curl http://localhost:9765/api/newsletters/config | jq .

# Via Railway
curl https://content-engine-production.up.railway.app/api/newsletters/config | jq .

# Via Database
psql -h localhost -p 7654 -U postgres -d content_engine \
  -c "SELECT id, user_id, created_at FROM newsletter_config;"
```

### Seed Config from File
```sql
-- Load default config from config.json into database
INSERT INTO newsletter_config (user_id, config_data, created_at, updated_at)
SELECT 
    NULL as user_id,
    content::jsonb as config_data,
    NOW() as created_at,
    NOW() as updated_at
FROM pg_read_file('/path/to/config.json');
```

Or use the seed file:
```bash
psql -h localhost -p 7654 -U postgres -d content_engine \
  -f seed_newsletter_config.sql
```

### Update Config via UI
1. Go to: http://localhost:3000/newsletters/config
2. Add/remove domains in whitelist/blacklist
3. Click "Save Changes"
4. Config is saved to database (persists across restarts)

### Query Specific Fields
```sql
-- Get whitelist domains
SELECT config_data->'content_filtering'->'whitelist_domains' 
FROM newsletter_config WHERE user_id IS NULL;

-- Get all newsletter sources
SELECT config_data->'newsletters'->'sources' 
FROM newsletter_config WHERE user_id IS NULL;

-- Check if config exists
SELECT EXISTS(SELECT 1 FROM newsletter_config WHERE user_id IS NULL);
```

## Migration History

1. **0a3d2a7ef13b**: Initial extraction models (Extraction, EmailContent, ExtractedLink)
2. **405f9211eb0a**: Add newsletter_config table (current)

## Deployment Workflow

### Local Development
```bash
# Already done ✅
./use-local.sh
alembic upgrade head
```

### Railway Production
```bash
# Push code to GitHub
git add .
git commit -m "Add newsletter config database table"
git push origin main

# Railway auto-deploys and runs migrations via start.sh
# Verify migration ran:
railway logs | grep "add newsletter config table"
```

## Next Steps (To Implement)

- [ ] Update API endpoints (`/api/newsletters/config`) to read/write from database
- [ ] Add seed logic: First request loads from `config.json` → saves to DB
- [ ] Test on Railway: Change config via UI → restart → verify persistence
- [ ] (Future) Add user-specific configs when auth is implemented

## Files Changed

- ✅ `app/models/newsletter_extraction.py` - Added `NewsletterConfig` model
- ✅ `app/models/__init__.py` - Export `NewsletterConfig`
- ✅ `alembic/versions/405f9211eb0a_add_newsletter_config_table.py` - Migration
- ✅ `seed_newsletter_config.sql` - Sample seed data
- ✅ `ENV_SETUP.md` - Environment switching docs
- ⏳ `app/api/endpoints/newsletters.py` - (Next: Update to use database)
- ⏳ `app/crud/newsletter_extraction.py` - (Next: Add config CRUD operations)
