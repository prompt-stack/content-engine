# Deployment Information

## Project IDs

### Railway (Backend + PostgreSQL)
- **Project ID**: `312eead6-31f7-464c-bc93-f491f1a043bc`
- **Production URL**: https://content-engine-production.up.railway.app
- **Dashboard**: https://railway.app/project/312eead6-31f7-464c-bc93-f491f1a043bc
- **Database**: PostgreSQL (hosted on Railway)

### Vercel (Frontend)
- **Project ID**: `prj_QWpqZt8FMMOeGVvpgqeiiYAqCVPJ`
- **Production URL**: https://content-engine-frontend-green.vercel.app/
- **Dashboard**: https://vercel.com/prompt-stacks-projects/content-engine-frontend
- **Team**: prompt-stacks-projects

## GitHub Repository
- **Repo**: https://github.com/prompt-stack/content-engine
- **Auto-Deploy**:
  - Railway: Deploys on push to `main` branch
  - Vercel: Deploys on push to `main` branch

## Environment Variables

### Backend (Railway)
Set via Railway dashboard or CLI

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL` = `https://content-engine-production.up.railway.app`

## Architecture

```
User Browser
    ↓
Vercel (Next.js Frontend)
    ↓
Railway (FastAPI Backend)
    ↓
PostgreSQL (Railway)
```

## Recent Deployments

### Latest Commits
- Backend: `899d186` - Fix CORS to allow Vercel frontend access
- Backend: `044efae` - Add curator_description field to extracted links
- Frontend: `56c0d58` - Update frontend to support curator descriptions

## API Endpoints

### Base URL
`https://content-engine-production.up.railway.app`

### Key Endpoints
- `GET /api/newsletters/extractions` - List all extractions
- `POST /api/newsletters/extract` - Trigger new extraction
- `GET /api/newsletters/extractions/{id}/status` - Check extraction status
- `GET /health` - Health check

## Local Development

### Backend
```bash
cd backend
python3.11 -m uvicorn app.main:app --reload --port 9765
```

### Frontend
```bash
cd frontend
npm run dev
```

## Database Schema

### Tables
1. `extractions` - Extraction sessions
2. `email_content` - Newsletter emails
3. `extracted_links` - Links with curator descriptions
4. `newsletter_config` - User-specific configuration
5. `users` - User accounts

## Monitoring

- Railway Logs: https://railway.app/project/312eead6-31f7-464c-bc93-f491f1a043bc/service
- Vercel Logs: https://vercel.com/prompt-stacks-projects/content-engine-frontend/deployments
