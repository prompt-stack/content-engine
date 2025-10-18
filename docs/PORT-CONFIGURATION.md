# Port Configuration (October 2025)

Content Engine supports two common development setups:

1. **Direct uvicorn + local services** (recommended) – API on **9765**, Postgres on **7654** (see `backend/.env.local`).
2. **Docker Compose** – API published as **8765**, Postgres **5433**, Redis **6380** unless overridden.

The table below summarises the defaults:

| Service    | uvicorn (local) | Docker Compose publish | Standard Port | Notes |
|------------|-----------------|------------------------|---------------|-------|
| FastAPI    | 9765            | 8765 (`API_PORT`)      | 8000          | Frontend `.env.local` points to 9765; set `NEXT_PUBLIC_API_URL` accordingly |
| PostgreSQL | 7654            | 5433 (`POSTGRES_PORT`) | 5432          | `use-local.sh` configures `DATABASE_URL` to use 7654 |
| Redis      | 6380            | 6380 (`REDIS_PORT`)    | 6379          | Only required if you enable Redis features |

> **Tip**: The backend never hardcodes ports. All listeners derive from environment variables or Docker runtime values.

---

## Changing Ports

### A. uvicorn / Manual Development

1. Edit `backend/.env.local` (or the live `backend/.env`):
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:7654/content_engine
   ```
   Adjust the host/port as needed.

2. Run uvicorn with the target port: `python3 -m uvicorn app.main:app --reload --port 5000`.

3. Update `frontend/.env.local` so `NEXT_PUBLIC_API_URL` matches the new port.

### B. Docker Compose

`docker-compose.yml` honours the following environment variables:

```bash
export API_PORT=9000
export POSTGRES_PORT=5434
export REDIS_PORT=6381

docker-compose up -d
```

You can also inline them:

```bash
API_PORT=9000 POSTGRES_PORT=5434 docker-compose up backend postgres
```

> Remember to update `DATABASE_URL` / `REDIS_URL` in `backend/.env` so the application connects to the published ports when running outside Docker.

---

## Resolving Port Conflicts

If you encounter `bind: address already in use`:

```bash
lsof -i :9765   # or the port you selected
```

Either stop the conflicting service or choose a new port and update the relevant environment variables.

---

## Production Considerations

- **Railway** assigns the `PORT` automatically. The Docker image listens on `0.0.0.0:8000`, and FastAPI respects Railway’s `PORT` entrypoint during deployment.
- **Database and Redis** connections in production are provided via connection strings (`DATABASE_URL`, `REDIS_URL`); no manual port mapping is necessary.
- The frontend expects `NEXT_PUBLIC_API_URL=https://content-engine-production.up.railway.app` in Vercel.

---

## Quick Reference

```bash
# Health check (uvicorn default)
curl http://localhost:9765/health

# Health check (Docker default)
curl http://localhost:8765/health

# Connect to local Postgres (uvicorn setup)
psql postgresql://postgres:postgres@localhost:7654/content_engine

# Connect to Docker Postgres
psql postgresql://postgres:postgres@localhost:5433/content_engine
```

Make sure the frontend and backend agree on the API URL, especially when switching between Docker and direct uvicorn workflows.
