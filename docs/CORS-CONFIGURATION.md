# CORS Configuration Guide

## Overview

This document explains how Cross-Origin Resource Sharing (CORS) is configured in the Content Engine project to allow the frontend (hosted on Vercel) to communicate with the backend API (hosted on Railway).

## What is CORS?

CORS is a security feature implemented by web browsers that restricts web pages from making requests to a different domain than the one that served the web page. Our project needs CORS because:

- **Frontend**: `https://content-engine-frontend-green.vercel.app` (Vercel)
- **Backend**: `https://content-engine-production.up.railway.app` (Railway)

Since these are different domains, we need to configure CORS to allow them to communicate.

## Backend Configuration

### Location

The CORS configuration is in `/backend/app/main.py`:

```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

### Configuration Options

1. **`allow_origins`**: List of specific origins allowed to access the API
   - Loaded from `settings.CORS_ORIGINS` environment variable
   - Can specify exact URLs like `https://content-engine-frontend-green.vercel.app`

2. **`allow_origin_regex`**: Pattern-based origin matching
   - Current: `r"https://.*\.vercel\.app"` allows ANY Vercel deployment
   - Useful for preview deployments and development

3. **`allow_credentials`**: Set to `True`
   - Allows cookies and authentication headers to be sent
   - Required for user authentication

4. **`allow_methods`**: Set to `["*"]`
   - Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)

5. **`allow_headers`**: Set to `["*"]`
   - Allows all request headers

6. **`max_age`**: Set to `3600` seconds (1 hour)
   - How long browsers cache the preflight OPTIONS response

### Environment Variables

#### Production (Railway)

Set in Railway dashboard or via CLI:

```bash
# Option 1: Specific origins (more secure)
CORS_ORIGINS=["https://content-engine-frontend-green.vercel.app"]

# Option 2: Multiple origins
CORS_ORIGINS=["https://content-engine-frontend-green.vercel.app","https://custom-domain.com"]

# Option 3: Allow all (NOT recommended for production)
CORS_ORIGINS=["*"]
```

**Current Production Setting:**
```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:3456","https://content-engine-frontend-green.vercel.app","https://content-engine-frontend-kcqm1quew-prompt-stacks-projects.vercel.app","https://content-engine-frontend-33yjj47nq-prompt-stacks-projects.vercel.app","https://*.vercel.app"]
```

#### Local Development

In `/backend/app/core/config.py`:

```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:3456",
    # Vercel deployments handled by regex in main.py
]
```

## Frontend Configuration

### API URL Configuration

The frontend needs to know the backend URL. This is set via environment variables:

#### Production (Vercel)

In Vercel dashboard, set:
```
NEXT_PUBLIC_API_URL=https://content-engine-production.up.railway.app
```

#### Local Development

In `/frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:9765
```

### Making Requests

When making API requests from the frontend, include credentials:

```typescript
const response = await fetch(`${API_URL}/api/newsletters/extractions`, {
  credentials: 'include'  // Required for cookies/auth
});
```

## How CORS Works

### 1. Simple Requests

For simple GET requests, the browser:
1. Sends request with `Origin` header
2. Backend responds with `Access-Control-Allow-Origin` header
3. Browser allows JavaScript to read the response

### 2. Preflight Requests

For complex requests (POST, PUT, DELETE, custom headers), the browser:
1. Sends OPTIONS request (preflight) to check permissions
2. Backend responds with allowed methods/headers
3. If allowed, browser sends actual request
4. Browser caches preflight response for `max_age` duration

Example preflight:
```
OPTIONS /api/newsletters/extractions
Origin: https://content-engine-frontend-green.vercel.app
Access-Control-Request-Method: GET
```

Backend response:
```
Access-Control-Allow-Origin: https://content-engine-frontend-green.vercel.app
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Max-Age: 3600
```

## Testing CORS

### From Command Line

Test preflight (OPTIONS):
```bash
curl -v -X OPTIONS https://content-engine-production.up.railway.app/api/newsletters/extractions \
  -H "Origin: https://content-engine-frontend-green.vercel.app" \
  -H "Access-Control-Request-Method: GET"
```

Test actual request:
```bash
curl -v -X GET https://content-engine-production.up.railway.app/api/newsletters/extractions \
  -H "Origin: https://content-engine-frontend-green.vercel.app"
```

Look for these headers in the response:
- `access-control-allow-origin`
- `access-control-allow-credentials`
- `access-control-allow-methods`

### From Browser

1. Open browser DevTools (F12)
2. Go to Network tab
3. Load your frontend app
4. Look for API requests
5. Check response headers for `access-control-*` headers

## Common Issues & Solutions

### Issue 1: "No 'Access-Control-Allow-Origin' header present"

**Symptom**: CORS error in browser console

**Causes**:
1. Backend is returning 500 error before CORS middleware runs
2. Origin not in allowed list
3. Backend not deployed with latest CORS config

**Solutions**:
1. Check backend logs for errors (might be database/model issues)
2. Add origin to `CORS_ORIGINS` or verify regex pattern matches
3. Redeploy backend with updated configuration

### Issue 2: Authentication Not Working

**Symptom**: Cookies not sent, authentication fails

**Causes**:
1. `allow_credentials` not set to `True`
2. Frontend not sending `credentials: 'include'`
3. Origin doesn't exactly match (including protocol and port)

**Solutions**:
1. Verify `allow_credentials=True` in backend
2. Add `credentials: 'include'` to all fetch requests
3. Ensure origin matches exactly (https vs http, www vs non-www)

### Issue 3: Preflight Fails

**Symptom**: OPTIONS request returns error

**Causes**:
1. Custom headers not allowed
2. HTTP method not allowed
3. Authentication middleware interfering with OPTIONS

**Solutions**:
1. Set `allow_headers=["*"]` or list specific headers
2. Set `allow_methods=["*"]` or list specific methods
3. Ensure authentication middleware skips OPTIONS requests

## Security Considerations

### Production Best Practices

1. **Use Specific Origins**: Instead of wildcard `*`, list exact domains
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

2. **Avoid Regex in Production**: The regex `https://.*\.vercel\.app` allows ANY Vercel deployment
   - Acceptable for development
   - Consider limiting to specific subdomains in production

3. **Use HTTPS Only**: Never allow `http://` origins in production

4. **Limit Methods**: Instead of `["*"]`, only allow needed methods
   ```python
   allow_methods=["GET", "POST", "PUT", "DELETE"]
   ```

5. **Limit Headers**: Explicitly list required headers instead of `["*"]`

### Development vs Production

**Development**:
- Loose CORS (allow all Vercel deployments)
- Allow localhost origins
- More permissive settings for testing

**Production**:
- Strict CORS (specific origins only)
- No localhost origins
- Minimal necessary permissions

## Updating CORS Configuration

### Adding a New Frontend Domain

1. **Backend**: Add domain to Railway environment variables
   ```bash
   railway variables set CORS_ORIGINS='["https://old-domain.com","https://new-domain.com"]'
   ```

2. **Redeploy**: Railway will auto-redeploy with new settings

3. **Verify**: Test from new domain

### Changing Vercel Deployment URL

1. **Update Vercel Environment Variable**:
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production
   # Enter: https://content-engine-production.up.railway.app
   ```

2. **Redeploy Frontend**: Trigger new Vercel deployment

3. **No Backend Changes Needed**: Regex already allows all Vercel domains

## Troubleshooting Checklist

When experiencing CORS issues:

- [ ] Check browser console for exact error message
- [ ] Verify backend is responding (not 500 error)
- [ ] Confirm origin is in `CORS_ORIGINS` or matches regex
- [ ] Test with curl to isolate browser vs backend issue
- [ ] Check Railway logs for backend errors
- [ ] Verify environment variables are set correctly
- [ ] Confirm latest code is deployed to Railway
- [ ] Test OPTIONS preflight request separately
- [ ] Check if authentication is required and credentials are included

## Related Files

- Backend CORS config: `/backend/app/main.py`
- Backend settings: `/backend/app/core/config.py`
- Frontend API client: `/frontend/app/newsletters/page.tsx`
- Environment configs:
  - Railway: Railway dashboard > Variables
  - Vercel: Vercel dashboard > Settings > Environment Variables
  - Local backend: `/backend/.env`
  - Local frontend: `/frontend/.env.local`

## References

- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
