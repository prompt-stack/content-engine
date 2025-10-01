# 👑 Owner Account Setup Guide

**You are the OWNER** - The highest privilege level in Content Engine

---

## 🎯 What is OWNER?

**OWNER** is above SUPERADMIN. You have:

### Roles Hierarchy
```
USER → ADMIN → SUPERADMIN → OWNER (you!)
```

### Your Privileges as OWNER

| Permission | Regular User | Admin | SuperAdmin | OWNER (You) |
|------------|-------------|-------|------------|-------------|
| **Use API** | ✅ (limited) | ✅ | ✅ | ✅ **UNLIMITED** |
| **Rate Limits** | 100-50K/mo | Same | Same | ♾️ **NONE** |
| **Manage Users** | ❌ | ✅ | ✅ | ✅ |
| **Manage System** | ❌ | ❌ | ✅ | ✅ |
| **Bypass Limits** | ❌ | ❌ | ❌ | ✅ |
| **Full Access** | ❌ | ❌ | ❌ | ✅ |

### What This Means
- ✅ **Unlimited API calls** - No rate limits ever
- ✅ **All features unlocked** - Extract, Research, LLM, Image, Social
- ✅ **Manage everything** - Users, settings, system config
- ✅ **Your social accounts** - Connect Twitter, LinkedIn, etc.
- ✅ **No billing** - You own the system

---

## 🚀 Setup Process

### Step 1: Create Your Owner Account

```bash
cd /Users/hoff/My\ Drive/tools/data-processing/content-engine/backend

# Create owner account
python scripts/create_owner.py
```

**You'll be prompted for**:
- Email: (your email)
- Password: (choose a strong password)

**This creates**:
```
User ID: 1
Email: your@email.com
Role: OWNER
Tier: OWNER
Rate Limit: UNLIMITED
is_superuser: True
is_owner: True
```

---

### Step 2: Connect Your Social Media Accounts

```bash
# Interactive social credential setup
python scripts/manage_social_credentials.py
```

**This will**:
1. Ask for your email (defaults to owner account)
2. Show connected platforms
3. Let you add credentials for:
   - Twitter (X)
   - LinkedIn
   - Reddit
   - YouTube
   - Facebook (optional)
   - Instagram (optional)

**Credentials are stored in**:
```
config/social_credentials/
├── user_1_twitter.json
├── user_1_linkedin.json
├── user_1_reddit.json
├── user_1_youtube.json
├── user_1_facebook.json  (optional)
└── user_1_instagram.json (optional)
```

---

## 🔐 Getting API Credentials

### Twitter (Required)

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create App: "Content Engine"
3. Enable OAuth 1.0a with **Read and Write**
4. Get API Key → `TWITTER_API_KEY`
5. Get API Secret → `TWITTER_API_SECRET`
6. Generate Access Token → `TWITTER_ACCESS_TOKEN`
7. Generate Access Secret → `TWITTER_ACCESS_SECRET`

**Cost**: $100/mo for Basic plan (10K tweets/month)

### LinkedIn (Required)

1. Go to https://www.linkedin.com/developers/apps
2. Create App: "Content Engine"
3. Request "Share on LinkedIn" product (wait 1-2 days)
4. Get Client ID → `LINKEDIN_CLIENT_ID`
5. Get Client Secret → `LINKEDIN_CLIENT_SECRET`
6. Run OAuth flow to get Access Token

**Cost**: FREE

### Reddit (Required)

1. Go to https://www.reddit.com/prefs/apps
2. Create App (Script type): "Content Engine"
3. Get Client ID (under app name) → `REDDIT_CLIENT_ID`
4. Get Secret → `REDDIT_CLIENT_SECRET`
5. Set User Agent: `ContentEngine/1.0 (by /u/your_username)`
6. Use your Reddit username/password

**Cost**: FREE

### YouTube (Required)

1. Go to https://console.cloud.google.com
2. Create project: "Content Engine"
3. Enable YouTube Data API v3
4. Create OAuth 2.0 Client ID (Desktop app)
5. Download `client_secrets.json` → place in `config/`

**Cost**: FREE (6 videos/day limit)

### Facebook (Optional)

1. Go to https://developers.facebook.com
2. Create Business App: "Content Engine"
3. Add "Pages" product
4. Get App ID and Secret
5. Use Graph API Explorer to get Page Access Token
6. Get your Page ID

**Cost**: FREE

### Instagram (Optional)

1. Convert Instagram to Business account
2. Connect to Facebook Page
3. Use Facebook App from above
4. Add Instagram Graph API product
5. Get Instagram Business Account ID

**Cost**: FREE

---

## 📁 File Structure After Setup

```
config/
├── social_credentials/
│   ├── user_1_twitter.json
│   ├── user_1_linkedin.json
│   ├── user_1_reddit.json
│   ├── user_1_youtube.json
│   ├── user_1_facebook.json
│   └── user_1_instagram.json
├── social_tokens/
│   ├── twitter_oauth.json      # Auto-generated
│   ├── linkedin_oauth.json     # Auto-generated
│   ├── reddit_oauth.json       # Auto-generated
│   └── youtube_oauth.json      # Auto-generated
└── client_secrets.json         # YouTube OAuth (from Google Cloud)
```

---

## 🎯 Your Complete Workflow

Once setup is complete, you can:

### 1. Extract Content
```bash
curl -X POST http://localhost:9765/api/extract/tiktok \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tiktok.com/..."}'
```

### 2. Research Context
```bash
curl -X POST http://localhost:9765/api/search/context \
  -H "Content-Type: application/json" \
  -d '{"content_summary": "..."}'
```

### 3. Process with AI
```bash
curl -X POST http://localhost:9765/api/llm/process-content \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "task": "summarize"}'
```

### 4. Generate Image
```bash
curl -X POST http://localhost:9765/api/media/generate-from-content \
  -H "Content-Type: application/json" \
  -d '{"content": "..."}'
```

### 5. Post to Social (NEW!)
```bash
# Twitter
curl -X POST http://localhost:9765/api/social/twitter/post \
  -H "Content-Type: application/json" \
  -d '{"text": "..."}'

# LinkedIn
curl -X POST http://localhost:9765/api/social/linkedin/post \
  -H "Content-Type: application/json" \
  -d '{"text": "..."}'

# Multi-platform
curl -X POST http://localhost:9765/api/social/publish \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "platforms": ["twitter", "linkedin"]}'
```

---

## 🔑 Authentication in API Calls

### As Owner (Development)
```bash
# No auth needed in development mode
curl http://localhost:9765/api/extract/tiktok ...
```

### In Production (Future)
```bash
# With JWT token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:9765/api/extract/tiktok ...
```

---

## 📊 Your Dashboard View (Future)

```
Content Engine - Owner Dashboard
════════════════════════════════════════════

👤 Account: you@email.com
🎭 Role: OWNER
🎫 Tier: OWNER (Unlimited)

📊 Usage This Month:
  Extractions: 1,245
  LLM Calls: 3,892
  Image Generations: 523
  Social Posts: 187
  Rate Limit: ♾️ UNLIMITED

🔗 Connected Platforms:
  ✅ Twitter (@yourusername)
  ✅ LinkedIn (Your Name)
  ✅ Reddit (u/yourusername)
  ✅ YouTube (Your Channel)
  🔘 Facebook (Not connected)
  🔘 Instagram (Not connected)

💰 API Costs This Month:
  OpenAI: $12.43
  Anthropic: $8.21
  Gemini: $2.10
  DeepSeek: $0.45
  Twitter API: $100.00
  ────────────────────
  Total: $123.19

👥 Users: 1 (just you for now)
📈 System Status: ✅ Healthy
```

---

## 🎯 Quick Start Commands

### Create Owner Account
```bash
cd backend
python scripts/create_owner.py
```

### Add Social Credentials
```bash
python scripts/manage_social_credentials.py
```

### Start Content Engine
```bash
docker-compose up -d
```

### Test Complete Pipeline
```bash
# Extract TikTok → Research → Summarize → Post
python examples/workflow_with_social.py
```

---

## 🏆 What Makes You Special

### As OWNER, You Can:

1. **Use Everything Unlimited**
   - No rate limits
   - All AI providers
   - All platforms
   - Unlimited social posts

2. **Test and Develop**
   - Your own account for testing
   - No risk of hitting limits
   - Full system access

3. **Manage System**
   - Add/remove users
   - Change settings
   - View all usage
   - System configuration

4. **Add More Users Later**
   - FREE tier (100 requests/month)
   - STARTER tier (1K requests/month) - $29/mo
   - PRO tier (10K requests/month) - $99/mo
   - BUSINESS tier (50K requests/month) - $299/mo

---

## 🚀 Next Steps

1. ✅ Run `python scripts/create_owner.py`
2. ✅ Get Twitter API credentials ($100/mo)
3. ✅ Get LinkedIn credentials (free)
4. ✅ Get Reddit credentials (free)
5. ✅ Run `python scripts/manage_social_credentials.py`
6. ✅ Test posting to each platform
7. ✅ Run complete workflow
8. 🎉 You now own a complete content automation platform!

---

## 💡 Pro Tips

### For Testing
- Use your personal social accounts
- Start with Twitter + LinkedIn (easiest)
- Test each platform individually first
- Then test multi-platform posting

### For Production
- Create dedicated brand accounts
- Set up proper OAuth flows for users
- Monitor API costs
- Consider Buffer integration for complex platforms

### Security
- Keep credentials in `config/` (gitignored)
- Never commit tokens to git
- Rotate tokens periodically
- Use environment variables in production

---

## 🎯 Summary

**You are the OWNER**:
- ♾️ Unlimited everything
- 👑 Highest privileges
- 🔧 Full system control
- 💰 No billing (you own it)

**Your Content Engine can**:
- Extract from 6 platforms
- Research with AI (Tavily)
- Process with 4 LLMs (50+ models)
- Generate images (6+ models)
- **Post to 6 social platforms** (NEW!)

**Complete automation**:
```
URL → Extract → Research → AI Process → Image → Social Post
```

**You're the only person who can do all of this in one system!** 🚀