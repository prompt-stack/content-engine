# Environment Configuration

This project supports modular environment configuration for easy switching between local development and production (Railway) databases.

## Files

- **`.env`** - Currently active environment (auto-generated, do not edit directly)
- **`.env.local`** - Local development configuration (uses local PostgreSQL)
- **`.env.railway`** - Production configuration (uses Railway PostgreSQL)

## Quick Start

### Switch to Local Development
```bash
./use-local.sh
```
- Uses local PostgreSQL database (`localhost:7654`)
- Perfect for development and testing
- Data stays on your machine

### Switch to Railway Production
```bash
./use-railway.sh
```
- Uses Railway PostgreSQL database
- Allows testing production database locally
- **⚠️ Warning:** Extractions will save to production!

## Environment Differences

| Feature | Local | Railway |
|---------|-------|---------|
| Database | `localhost:7654` | `postgres.railway.internal:5432` |
| Environment | `development` | `production` |
| Debug Mode | `true` | `false` |
| Purpose | Dev & Testing | Prod Testing |

## Syncing API Keys

If you update API keys in `.env`, sync them to both environment files:
```bash
./sync-keys.sh
```

## Typical Workflow

### Development (default)
```bash
# Switch to local environment
./use-local.sh

# Start local backend
python3.11 -m uvicorn app.main:app --reload --port 9765

# Run extractions (saves to local DB)
curl -X POST http://localhost:9765/api/newsletters/extract \
  -H "Content-Type: application/json" \
  -d '{"days_back": 1, "max_results": 5}'
```

### Testing with Production Database
```bash
# Switch to Railway environment  
./use-railway.sh

# Start local backend (connects to Railway DB)
python3.11 -m uvicorn app.main:app --reload --port 9765

# Run extractions (saves to Railway DB!)
curl -X POST http://localhost:9765/api/newsletters/extract \
  -H "Content-Type: application/json" \
  -d '{"days_back": 1, "max_results": 5}'

# View results on Railway
curl https://content-engine-production.up.railway.app/api/newsletters/extractions
```

### Switching Back
```bash
# Always switch back to local when done testing
./use-local.sh
```

## Railway Deployment

Railway automatically uses environment variables set in the Railway dashboard:
- `DATABASE_URL` is automatically set to use Railway's PostgreSQL
- No need to manually switch environments on Railway

## Security Notes

- ✅ `.env.local` and `.env.railway` are git-ignored
- ✅ Never commit actual API keys or database credentials
- ✅ Railway credentials are stored only in Railway dashboard
- ⚠️ Be careful when using Railway environment - you're touching production data!
