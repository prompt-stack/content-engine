# Supported URL Formats (October 2025)

The extractors now normalise most desktop and mobile URLs. Short links are automatically expanded before processing (see `backend/app/services/extractors/url_utils.py`).

## TikTok

- ✅ `https://www.tiktok.com/@user/video/1234567890`
- ✅ `https://www.tiktok.com/t/ZP8SEBDrP/` (expanded automatically)
- ✅ `https://vm.tiktok.com/XXXX/`

> **If extraction fails**: TikTok occasionally blocks automated requests. Re-run or try a desktop URL; the extractor handles captions when available.

## Reddit

- ✅ `https://www.reddit.com/r/pics/comments/abc123/example_title/`
- ✅ `https://www.reddit.com/r/pics/s/d0oTzG60MY` (short share links)
- ✅ `https://redd.it/abc123`

Shortened and mobile links are expanded and cleaned before passing to the Python wrapper (`reddit_extractor.py`).

## YouTube

- ✅ `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- ✅ `https://youtu.be/dQw4w9WgXcQ`
- ✅ `https://www.youtube.com/shorts/dQw4w9WgXcQ`
- ✅ `https://www.youtube.com/live/dQw4w9WgXcQ`

The extractor uses yt-dlp with multiple client fallbacks, so all standard formats work.

## Articles & Web Pages

- ✅ Any `http(s)://` URL pointing to HTML content. Readability.js cleans the output and removes boilerplate.

## Gmail Newsletters

- URLs are resolved from newsletter HTML, and tracking links are unwrapped (see `backend/extractors/email` pipeline).

---

### Best Practices

- Provide canonical desktop URLs when possible for the most stable output.
- Remove query parameters if you encounter site-specific issues (rare with the current implementation).
- Monitor extractor logs (`backend/app/services/extractors/*`) for provider-specific rate limits.

With these improvements, you can safely accept links from mobile devices, copied share URLs, or shortened routes without additional preprocessing.
