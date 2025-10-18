# 🔐 Social Platform Authentication (Status – October 2025)

## Current Status

Content Engine focuses on extraction and research today. **Direct social posting is not yet exposed via public API endpoints.** The backend contains early helpers under `app/services/social/`, but they are not wired into FastAPI routes.

| Platform | In-Code Support | Ready for Production? | Notes |
|----------|-----------------|------------------------|-------|
| Twitter (X)   | Draft poster (`twitter_poster.py`) | ⚠️ No | Requires OAuth 1.0a credentials; no API endpoint yet |
| LinkedIn      | Draft poster (`linkedin_poster.py`) | ⚠️ No | Uses REST API via OAuth; not exposed through FastAPI |
| Reddit        | Poster helper available             | ⚠️ No | Useful for internal tools only |
| YouTube       | Upload handled in separate tooling  | ⚠️ No | Integration not ported into Content Engine API |
| Facebook/Instagram | Not implemented                 | ❌    | Requires Facebook Graph API setup |
| TikTok        | Not implemented                     | ❌    | Restricted API access |

> Use the existing extraction and research endpoints today. Treat the social posting modules as **prototypes** until dedicated API routes are added.

---

## Recommended Approach (Roadmap)

1. **Short term**: expose simple posting endpoints for Twitter and LinkedIn that accept already-extracted content.
2. **Integrations**: support Buffer/n8n/Make webhooks so customers can use their existing schedulers.
3. **Credential storage**: leverage the scripts in `backend/scripts/manage_social_credentials.py` once endpoints exist; currently those scripts are for manual experiments.

---

## Getting Credentials (For Future Use)

If you plan to finish the social posting work, here’s a quick reminder of the OAuth requirements:

### Twitter (OAuth 1.0a)
- Create a developer account at https://developer.twitter.com/
- Generate API key/secret and user access token/secret with read/write permissions.
- Store in a secure location (e.g., Railway variables) when endpoints are ready.

### LinkedIn (OAuth 2.0)
- Register an app at https://www.linkedin.com/developers/apps
- Request “Share on LinkedIn” permissions.
- Obtain `CLIENT_ID`, `CLIENT_SECRET`, and user access tokens via OAuth flow.

### Reddit
- Create a “script” app at https://www.reddit.com/prefs/apps
- Collect client id/secret and the user’s username/password for script auth.

Keep credentials out of the repository—use environment variables or encrypted secrets.

---

## Until Posting Ships

- Continue using the extraction endpoints to gather content (`/api/extract/*`).
- Leverage the Tavily search endpoints for research.
- Export or sync results into existing social scheduling tools.
- Track social-posting progress in the product roadmap; this document will be updated once endpoints are live.

If you need help prioritising or implementing the posting APIs, see `docs/reports/SOCIAL-MEDIA-POSTING-ANALYSIS.md` for strategic guidance.
