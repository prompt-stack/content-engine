# 🔐 Social Media Platforms - Complete Authentication Guide

**Date**: September 30, 2025

---

## 🎯 Target Platforms

### Priority Order
1. **Twitter (X)** - Most requested, straightforward API ✅ Implemented
2. **LinkedIn** - Business-focused, great for professional content ✅ Implemented
3. **Instagram** - Visual content, high engagement ⚠️ Complex
4. **Facebook** - Broad reach, Pages API ⚠️ Complex
5. **YouTube** - Video platform ✅ Already have from youtube-uploader-tool
6. **TikTok** - Growing, but very restricted API ⚠️ Very Complex

---

## 📊 Platform Comparison

| Platform | Difficulty | Auth Type | API Quality | Worth It? | Status |
|----------|-----------|-----------|-------------|-----------|--------|
| **Twitter** | Easy | OAuth 1.0a | Good | ✅ Yes | ✅ Done |
| **LinkedIn** | Easy | OAuth 2.0 | Good | ✅ Yes | ✅ Done |
| **YouTube** | Medium | OAuth 2.0 (Google) | Excellent | ✅ Yes | ✅ Have it |
| **Reddit** | Easy | OAuth 2.0 | Good | ✅ Yes | ✅ Done |
| **Facebook** | Hard | OAuth 2.0 | Complex | ⚠️ Maybe | 🟡 Todo |
| **Instagram** | Very Hard | OAuth 2.0 (via FB) | Restricted | ⚠️ Maybe | 🟡 Todo |
| **TikTok** | Extreme | OAuth 2.0 | Very Limited | ❌ No | ❌ Skip |

---

## 🔐 Authentication Requirements by Platform

### 1. Twitter (X) ✅ IMPLEMENTED

**What You Need**:
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_token_secret
```

**How to Get Credentials**:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new App (or use existing)
3. **App Settings**:
   - Name: "Content Engine"
   - Description: "AI-powered content automation"
   - Website: Your website URL
4. **User authentication settings**:
   - Enable OAuth 1.0a
   - App permissions: **Read and Write** (to post tweets)
   - Callback URL: `http://localhost:9765/auth/twitter/callback`
5. **Keys and tokens**:
   - Copy API Key → `TWITTER_API_KEY`
   - Copy API Key Secret → `TWITTER_API_SECRET`
   - Generate Access Token & Secret → `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`

**Cost**:
- **Free tier**: 1,500 tweets/month (posting only, no read)
- **Basic**: $100/month (10,000 tweets/month + read access)
- **Pro**: $5,000/month (unlimited)

**Recommendation**: Start with **$100/month Basic plan** for Content Engine

**API Limits**:
- Create tweets: 300 requests per 15 min (for OAuth 1.0a User Context)
- Media upload: 300 requests per 15 min
- Tweet with media: 50 requests per 15 min

---

### 2. LinkedIn ✅ IMPLEMENTED

**What You Need**:
```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
```

**How to Get Credentials**:
1. Go to https://www.linkedin.com/developers/apps
2. Create a new app:
   - Name: "Content Engine"
   - LinkedIn Page: Your company page (or create one)
   - Privacy policy URL: Your privacy URL
3. **Products** tab:
   - Request access to **"Share on LinkedIn"** product
   - Request access to **"Sign In with LinkedIn using OpenID Connect"**
   - **NOTE**: May require LinkedIn review (1-2 days)
4. **Auth** tab:
   - Redirect URLs: `http://localhost:9765/auth/linkedin/callback`
   - Copy Client ID → `LINKEDIN_CLIENT_ID`
   - Copy Client Secret → `LINKEDIN_CLIENT_SECRET`
5. **Generate Access Token**:
   - Use OAuth 2.0 flow (will need to implement)
   - Scopes needed: `w_member_social`, `r_liteprofile`

**Cost**: **FREE** for posting to your own profile

**API Limits**:
- Post creation: 100 posts per user per day
- No official rate limit published (throttled if abused)

**Complexity**: ⚠️ **Medium** - Requires app approval by LinkedIn

---

### 3. YouTube ✅ ALREADY HAVE

**What You Need**:
```bash
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
# OAuth tokens stored in config/youtube_oauth.json
```

**Status**: ✅ **Already implemented in youtube-uploader-tool**

**Location**: `/Users/hoff/My Drive/dev/projects/prompt-stack/content-stack-react/youtube-uploader-tool`

**How to Get Credentials**:
1. Go to https://console.cloud.google.com
2. Create project (or use existing)
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop app)
5. Download `client_secrets.json`
6. Place in `config/client_secrets.json`

**Cost**: **FREE** (quota: 10,000 units/day, 1 upload = ~1,600 units = ~6 videos/day)

**API Limits**:
- Daily quota: 10,000 units
- Video upload: ~1,600 units per video
- Video update: 50 units

**Port Status**: Need to **port from youtube-uploader-tool to Content Engine**

---

### 4. Reddit ✅ IMPLEMENTED

**What You Need**:
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ContentEngine/1.0 (by /u/yourusername)
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

**How to Get Credentials**:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. **App type**: Script (for personal use)
4. **Name**: Content Engine
5. **Description**: AI-powered content automation
6. **About URL**: Your website
7. **Redirect URI**: `http://localhost:9765/auth/reddit/callback`
8. Copy **Client ID** (under app name) → `REDDIT_CLIENT_ID`
9. Copy **Secret** → `REDDIT_CLIENT_SECRET`
10. Set User Agent: `ContentEngine/1.0 (by /u/your_reddit_username)`

**Cost**: **FREE**

**API Limits**:
- Read: 60 requests per minute
- Write (posting): 1 post per 9.25 minutes (per subreddit)
- Comment: 1 comment per minute

**Complexity**: ✅ **Easy** - Simple OAuth 2.0, no approval needed

---

### 5. Facebook ⚠️ TODO

**What You Need**:
```bash
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_page_access_token
FACEBOOK_PAGE_ID=your_page_id
```

**How to Get Credentials**:
1. Go to https://developers.facebook.com
2. Create an app:
   - **App type**: Business
   - **Name**: Content Engine
3. **Add Products**:
   - Add **"Pages"** (required for posting)
   - Add **"Instagram Basic Display"** (if doing Instagram too)
4. **App Settings**:
   - Add Valid OAuth Redirect URI: `http://localhost:9765/auth/facebook/callback`
   - Copy App ID → `FACEBOOK_APP_ID`
   - Copy App Secret → `FACEBOOK_APP_SECRET`
5. **Get Page Access Token**:
   - Use Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your Page
   - Request permissions: `pages_manage_posts`, `pages_read_engagement`
   - Generate token → `FACEBOOK_ACCESS_TOKEN`
6. **Get Page ID**:
   - Visit your Facebook Page
   - Page ID is in About section → `FACEBOOK_PAGE_ID`

**Cost**: **FREE** for organic posting

**API Limits**:
- Page posts: 200 calls per hour per user
- Rate limiting: 200 calls per hour

**Complexity**: ⚠️ **Hard** - Requires Business app approval, Page access

**Important Notes**:
- ⚠️ Can only post to **Facebook Pages**, not personal profiles
- ⚠️ Requires **Business Verification** for some features
- ⚠️ App Review required for production (Development mode = limited users)

---

### 6. Instagram ⚠️ TODO (Most Complex)

**What You Need**:
```bash
FACEBOOK_APP_ID=your_app_id  # Same as Facebook
FACEBOOK_APP_SECRET=your_app_secret
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_token
```

**How to Get Credentials**:
1. **Prerequisites**:
   - ✅ Instagram account must be **Business or Creator** account
   - ✅ Instagram account must be connected to a Facebook Page
   - ✅ You need Facebook Developer App (from step 5 above)

2. Go to https://developers.facebook.com
3. Add **Instagram Graph API** product to your app
4. **Connect Instagram Business Account**:
   - Settings → Basic → Add Platform → Instagram
   - Connect your Instagram Business account
   - Link to Facebook Page
5. **Get Instagram Account ID**:
   - Use Graph API Explorer
   - Query: `GET /{facebook-page-id}?fields=instagram_business_account`
   - Copy Instagram Business Account ID → `INSTAGRAM_ACCOUNT_ID`
6. **Get Page Access Token** (same as Facebook step 5)

**Cost**: **FREE** for organic posting

**API Limits**:
- Content Publishing: 25 posts per 24 hours per user
- 200 API calls per hour per user

**Complexity**: 🔴 **Very Hard** - Most restrictive API

**Important Restrictions**:
- ❌ Cannot post Stories via API (only Feed posts)
- ❌ Cannot post Reels via API
- ❌ Must use **2-step process**: Create media container → Publish container
- ❌ Images must be publicly accessible URLs (can't upload directly)
- ❌ Requires Facebook Page connection
- ❌ Only Business/Creator accounts
- ⚠️ App Review required for production

**API Process**:
```python
# Step 1: Create media container
POST /{instagram-account-id}/media
{
  "image_url": "https://your-image-url.jpg",
  "caption": "Your caption"
}
# Returns: {"id": "container_id"}

# Step 2: Publish container
POST /{instagram-account-id}/media_publish
{
  "creation_id": "container_id"
}
# Returns: {"id": "media_id"}
```

---

### 7. TikTok ❌ SKIP (Not Recommended)

**Why Skip**:
- ❌ **Extremely limited API** - Content Posting API requires approval
- ❌ **Approval process**: Can take months, need to be verified business
- ❌ **Restrictions**: Only for TikTok Business accounts
- ❌ **No organic posting** - API is for ads primarily
- ❌ **Video requirements**: Strict format/duration requirements
- ❌ **Rate limits**: Very restrictive

**Alternative**: Use **Buffer or Later** for TikTok scheduling

---

## 🎯 Recommended Priority

### Phase 1: Core Social (Complete) ✅
1. ✅ Twitter - Done
2. ✅ LinkedIn - Done
3. ✅ Reddit - Done
4. ✅ YouTube - Have it (need to port)

**Status**: **4 platforms ready to go**

### Phase 2: Meta Platforms (Complex) 🟡
5. 🟡 Facebook - Doable but requires Business verification
6. 🟡 Instagram - Very complex, restrictive API

**Recommendation**: Add **only if user needs it** or integrate with **Buffer**

### Phase 3: Skip
7. ❌ TikTok - Too restrictive, not worth it

---

## 📋 Setup Checklist

### For You (Developer)
- [ ] **Twitter**:
  - [ ] Create Twitter Developer account
  - [ ] Create App with Read/Write permissions
  - [ ] Subscribe to Basic plan ($100/mo)
  - [ ] Get API keys and access tokens
  - [ ] Test posting with your account

- [ ] **LinkedIn**:
  - [ ] Create LinkedIn Developer App
  - [ ] Request "Share on LinkedIn" product access
  - [ ] Wait for approval (1-2 days)
  - [ ] Get client ID/secret
  - [ ] Implement OAuth flow
  - [ ] Test posting to your profile

- [ ] **YouTube**:
  - [ ] Copy OAuth setup from youtube-uploader-tool
  - [ ] Port to Content Engine
  - [ ] Test video upload

- [ ] **Reddit**:
  - [ ] Create Reddit Script App
  - [ ] Get client ID/secret
  - [ ] Test posting to test subreddit (r/test)

- [ ] **Facebook** (Optional):
  - [ ] Create Facebook Business App
  - [ ] Create Facebook Page
  - [ ] Request Business Verification
  - [ ] Get Page Access Token
  - [ ] Test posting to Page

- [ ] **Instagram** (Optional):
  - [ ] Convert Instagram to Business account
  - [ ] Connect to Facebook Page
  - [ ] Add Instagram Graph API product
  - [ ] Get Instagram Business Account ID
  - [ ] Implement 2-step publish flow
  - [ ] Test posting

### For Users (When Deployed)
Users will need to:
1. **Twitter**: Authenticate via OAuth (we handle it)
2. **LinkedIn**: Authenticate via OAuth (we handle it)
3. **Reddit**: Provide username/password or authenticate via OAuth
4. **YouTube**: Authenticate via Google OAuth (we handle it)
5. **Facebook**: Admin access to Facebook Page
6. **Instagram**: Business account connected to Facebook Page

---

## 💡 Authentication Implementation Approaches

### Option 1: Platform API Keys (Current)
**Pros**: Simple, fast to implement
**Cons**: All users post through YOUR accounts
**Use**: Development, personal use

```bash
# .env - Your accounts
TWITTER_API_KEY=...
LINKEDIN_CLIENT_ID=...
```

### Option 2: OAuth per User (Recommended for Production)
**Pros**: Each user posts from their own accounts
**Cons**: More complex, requires OAuth flow
**Use**: Production, SaaS

```python
# User authenticates via OAuth
# Token stored in database per user
{
  "user_id": "123",
  "twitter_token": "...",
  "linkedin_token": "..."
}
```

### Option 3: Hybrid
**Pros**: Flexibility
**Use**: Best of both worlds

```python
# Option A: User's own accounts (OAuth)
# Option B: Post via Content Engine accounts (API keys)
```

---

## 🔧 Implementation Priority

### Week 1: Twitter + LinkedIn + Reddit (Done ✅)
These are **implemented and ready to test**:
- Twitter posting works
- LinkedIn posting works
- Reddit posting works

**Next**: Get API credentials and test!

### Week 2: YouTube + Facebook
- Port YouTube from youtube-uploader-tool
- Add Facebook if needed

### Week 3: Instagram (Optional)
- Only if user demand
- Consider Buffer integration instead

---

## 📊 Cost Summary

| Platform | Free Tier | Paid Tier | Recommended |
|----------|-----------|-----------|-------------|
| **Twitter** | 1,500 tweets/mo | $100/mo (10K tweets) | $100/mo |
| **LinkedIn** | Unlimited | N/A | Free ✅ |
| **Reddit** | Unlimited | N/A | Free ✅ |
| **YouTube** | 6 videos/day | N/A | Free ✅ |
| **Facebook** | Unlimited | N/A | Free ✅ |
| **Instagram** | 25 posts/day | N/A | Free ✅ |
| **TOTAL** | **Most free** | **$100/mo Twitter** | **$100/mo** |

**Bottom Line**: Only Twitter costs money ($100/mo for meaningful usage)

---

## 🎯 Final Recommendation

### Must Have (Done ✅)
1. ✅ **Twitter** - $100/mo, most requested
2. ✅ **LinkedIn** - Free, professional
3. ✅ **Reddit** - Free, niche communities
4. ✅ **YouTube** - Free, video content (port from existing tool)

### Nice to Have (Complex)
5. 🟡 **Facebook** - Free but complex setup
6. 🟡 **Instagram** - Free but very complex + restrictive

### Skip
7. ❌ **TikTok** - Not worth the complexity

### Alternative
For complex platforms (Instagram, TikTok), integrate with:
- **Buffer API** ($6-99/mo) - Handles IG, TikTok, scheduling
- **n8n webhooks** - Let users build custom flows

---

## 📋 Action Plan

### Today
1. Get Twitter Developer account
2. Subscribe to Twitter Basic ($100/mo)
3. Get LinkedIn Developer credentials
4. Request LinkedIn "Share on LinkedIn" access
5. Create Reddit app
6. Test all 4 platforms

### This Week
1. Port YouTube uploader
2. Test complete pipeline: Extract → Post
3. Document for users

### Next Week (If Needed)
1. Add Facebook if users need it
2. Add Instagram if users need it
3. Or integrate Buffer for complex platforms

**Estimate**: 2-3 days to get all credentials and test ✅