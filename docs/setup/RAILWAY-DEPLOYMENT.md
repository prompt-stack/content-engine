# Railway Deployment Guide

## Step 1: Create Service from GitHub

1. In your Railway project, click **"New Service"**
2. Select **"GitHub Repo"**
3. Choose **`prompt-stack/content-engine`**
4. Railway will auto-detect the Dockerfile

## Step 2: Configure Environment Variables

Click on **Variables** tab and add these:

### Required Variables:
```
ENVIRONMENT=production
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=...
```

### Optional (but suggested) Variables:
Railway already detected these from your `.env` - you can ignore them:
- `API_PORT=9765` (Railway uses dynamic PORT)
- `POSTGRES_PORT=7654` (only needed if you add PostgreSQL service)
- `REDIS_PORT=8765` (only needed if you add Redis service)

### CORS Configuration:
```
CORS_ORIGINS=["*"]
```

Or for production (after deploying frontend):
```
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

## Step 3: Deploy Settings

Railway will automatically:
- ✅ Detect `backend/Dockerfile`
- ✅ Set PORT dynamically
- ✅ Run health checks on `/health`
- ✅ Build and deploy on every git push

## Step 4: Get Your Backend URL

Once deployed, Railway will give you a URL like:
```
https://content-engine-production.up.railway.app
```

**Copy this URL** - you'll need it for the frontend Vercel deployment.

## Step 5: Test the Backend

Visit these endpoints to verify:
- `https://your-railway-url.up.railway.app/` - Should show API info
- `https://your-railway-url.up.railway.app/health` - Should show healthy status
- `https://your-railway-url.up.railway.app/docs` - FastAPI Swagger docs

## Next: Deploy Frontend to Vercel

Once backend is live, we'll deploy the frontend and set:
```
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```
