# Port Configuration

## Default Ports (Non-Standard to Avoid Conflicts)

Content Engine uses **non-standard ports** by default to avoid conflicts with other services:

| Service    | Default Port | Standard Port | Why Different? |
|------------|--------------|---------------|----------------|
| FastAPI    | **8765**     | 8000          | Avoid conflicts with other APIs |
| PostgreSQL | **5433**     | 5432          | Avoid conflicts with local Postgres |
| Redis      | **6380**     | 6379          | Avoid conflicts with local Redis |

## How to Change Ports

### Option 1: Edit Root `.env` File (Recommended)

Edit `/.env` in the project root:

```bash
# content-engine/.env
API_PORT=8765        # Change to any available port
POSTGRES_PORT=5433   # Change to any available port
REDIS_PORT=6380      # Change to any available port
```

### Option 2: Environment Variables

```bash
# Set before running docker-compose
export API_PORT=9000
export POSTGRES_PORT=5434
export REDIS_PORT=6381

docker-compose up -d
```

### Option 3: Inline with docker-compose

```bash
API_PORT=9000 POSTGRES_PORT=5434 REDIS_PORT=6381 docker-compose up -d
```

## Backend Configuration

The backend also needs to know these ports. Edit `backend/.env`:

```bash
# backend/.env
API_PORT=8765
POSTGRES_PORT=5433
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/content_engine
REDIS_PORT=6380
REDIS_URL=redis://localhost:6380/0
```

**Important**: The `DATABASE_URL` and `REDIS_URL` must match the ports in root `.env`.

## Port Conflicts?

If you get an error like:
```
Error: bind: address already in use
```

Someone is using that port. Check what's running:

```bash
# Check what's on port 8765
lsof -i :8765

# Check what's on port 5433
lsof -i :5433

# Check what's on port 6380
lsof -i :6380
```

Then either:
1. Stop the conflicting service
2. Change to a different port in `.env`

## Production Deployment

For production (Railway, Render, etc.), the platform assigns ports automatically via:
- `PORT` environment variable (for the API)
- Database connection strings (Neon, etc.)

Your app will use these automatically in production.

## Accessing Services

After starting with `docker-compose up -d`:

```bash
# API health check
curl http://localhost:8765/health

# API documentation
open http://localhost:8765/docs

# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5433/content_engine

# Connect to Redis
redis-cli -p 6380
```

## Summary

✅ **All ports are configurable via environment variables**
✅ **No hardcoded ports in code**
✅ **Easy to change if conflicts occur**
✅ **Works seamlessly in Docker and production**