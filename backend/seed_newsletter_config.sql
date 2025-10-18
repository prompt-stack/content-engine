-- Sample Newsletter Config Data
-- This shows what the newsletter_config table looks like with data

-- Example 1: Default config for user_id=NULL (system default, single-user mode)
INSERT INTO newsletter_config (id, user_id, config_data, created_at, updated_at) VALUES (
  1,
  NULL,  -- NULL user_id = system default config
  '{
    "newsletters": {
      "enabled": true,
      "sources": [
        {
          "name": "AlphaSignal",
          "email": "news@alphasignal.ai",
          "enabled": true,
          "category": "tech",
          "priority": "high"
        },
        {
          "name": "The Rundown Tech",
          "email": "crew@technews.therundown.ai",
          "enabled": true,
          "category": "tech",
          "priority": "high"
        },
        {
          "name": "The Rundown AI",
          "email": "news@daily.therundown.ai",
          "enabled": true,
          "category": "ai",
          "priority": "high"
        }
      ]
    },
    "settings": {
      "default_days_back": 7,
      "max_results": 100,
      "auto_digest": true,
      "auto_excel": false,
      "output_format": ["json", "markdown"],
      "filter_promotional": true,
      "extract_links": true,
      "categories_enabled": ["tech", "ai", "business", "product"]
    },
    "content_filtering": {
      "description": "Control which domains/URLs to always accept or reject",
      "whitelist_domains": [
        "techcrunch.com",
        "theverge.com",
        "wired.com",
        "github.com",
        "arxiv.org",
        "huggingface.co",
        "openai.com"
      ],
      "blacklist_domains": [
        "typeform.com",
        "mailchi.mp",
        "surveymonkey.com"
      ],
      "curator_domains": [
        "alphasignal.ai",
        "therundown.ai",
        "rundown.ai"
      ],
      "content_indicators": [
        "/blog/",
        "/article/",
        "/news/",
        "/post/",
        "/2025/",
        "/p/",
        "/status/",
        "/guides/"
      ]
    }
  }'::jsonb,
  NOW(),
  NOW()
);

-- Example 2: User-specific config (when multi-user is enabled)
-- INSERT INTO newsletter_config (id, user_id, config_data, created_at, updated_at) VALUES (
--   2,
--   1,  -- user_id=1 (your user account)
--   '{
--     "newsletters": {
--       "enabled": true,
--       "sources": [...]
--     },
--     ...
--   }'::jsonb,
--   NOW(),
--   NOW()
-- );

-- How to query this data:
-- SELECT id, user_id, config_data->>'newsletters' as newsletters FROM newsletter_config;
-- SELECT config_data->'content_filtering'->'whitelist_domains' as whitelist FROM newsletter_config WHERE user_id IS NULL;
