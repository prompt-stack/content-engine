# Content Engine - Comprehensive Testing Plan

## Test Execution Date
Date: 2025-10-16

## API Endpoints Inventory

### 1. Health & System
- [ ] `GET /` - Root health check
- [ ] `GET /health` - Detailed health check

### 2. Extractors (Content Extraction)
- [ ] `POST /api/extract/reddit` - Extract Reddit post + comments
- [ ] `POST /api/extract/tiktok` - Extract TikTok video transcript
- [ ] `POST /api/extract/youtube` - Extract YouTube transcript
- [ ] `POST /api/extract/article` - Extract article content
- [ ] `POST /api/extract/auto` - Auto-detect platform and extract

### 3. Captures (Content Vault)
- [ ] `POST /api/capture/text` - Capture text content
- [ ] `GET /api/capture/list` - List all captures
- [ ] `GET /api/capture/search?q={query}` - Search captures
- [ ] `GET /api/capture/{id}` - Get specific capture
- [ ] `DELETE /api/capture/{id}` - Delete capture
- [ ] `GET /api/capture/stats/count` - Get capture count

### 4. LLM Processing
- [ ] `GET /api/llm/providers` - List available LLM providers
- [ ] `POST /api/llm/generate` - Generate text with LLM
- [ ] `POST /api/llm/process-content` - Process content with LLM

### 5. Media Generation
- [ ] `GET /api/media/providers` - List media providers
- [ ] `POST /api/media/generate-image` - Generate image from prompt
- [ ] `POST /api/media/generate-from-content` - Generate image from content

### 6. Search
- [ ] `GET /api/search/capabilities` - Get search capabilities
- [ ] `POST /api/search/search` - General search
- [ ] `POST /api/search/context` - Context-based search
- [ ] `POST /api/search/trending` - Trending topics search
- [ ] `POST /api/search/fact-check` - Fact check search
- [ ] `POST /api/search/news` - News search
- [ ] `POST /api/search/research` - Research search

### 7. Prompts
- [ ] `GET /api/prompts/list` - List all prompts
- [ ] `GET /api/prompts/categories` - List prompt categories
- [ ] `GET /api/prompts/{id}` - Get specific prompt
- [ ] `POST /api/prompts/render` - Render prompt with variables

### 8. Newsletters
- [ ] `GET /api/newsletters/digests` - List newsletter digests
- [ ] `GET /api/newsletters/resolved` - List resolved links
- [ ] `GET /api/newsletters/config` - Get newsletter config
- [ ] `PUT /api/newsletters/config` - Update newsletter config
- [ ] `POST /api/newsletters/config/test-url` - Test URL pattern
- [ ] `POST /api/newsletters/resolve` - Resolve newsletter links

## Database Connection Tests

### Tables to Verify
- [ ] `users` - User authentication table
- [ ] `captures` - Content vault table
- [ ] `newsletter_digests` - Newsletter digest table
- [ ] `newsletter_resolved_links` - Resolved links table
- [ ] `newsletter_config` - Newsletter configuration table

### Database Operations
- [ ] INSERT - Create new records
- [ ] SELECT - Read records
- [ ] UPDATE - Modify records
- [ ] DELETE - Remove records
- [ ] SEARCH - Full-text search

## Critical User Flows

### Flow 1: Content Extraction → Vault
1. User pastes URL on /extract page
2. Backend extracts content
3. Content auto-saves to vault
4. User sees "✓ Saved to Vault" message
5. User clicks "View in Vault"
6. Content appears in vault

### Flow 2: iOS Capture → Vault
1. User copies text on iPhone
2. Runs iOS Shortcut
3. Text sent to API via ngrok
4. Saved to captures table
5. Visible in /vault page

### Flow 3: Newsletter Processing
1. User configures newsletter settings
2. Backend extracts links from Gmail
3. Links resolved (redirects followed)
4. Content filtered by whitelist
5. Results visible in /newsletters

## Test Results

### ✅ Known Working
- iOS Shortcut → Capture API → Database
- Vault page displays captures
- Search functionality in vault

### ⚠️ Needs Testing
- All extractor endpoints with real URLs
- LLM integration endpoints
- Newsletter resolution flow
- Media generation
- Search endpoints

### ❌ Known Issues
- None documented yet

## Test Scripts Location
- Playwright tests: `/frontend/e2e/`
- Backend tests: `/backend/tests/`
- Manual test scripts: `/backend/test_*.py`

## Environment Requirements
- PostgreSQL database running
- API keys configured (.env)
- Frontend dev server running (port 3456)
- Backend API running (port 9765)
- ngrok tunnel (optional, for iOS)
