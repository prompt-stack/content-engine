# Article Scraper

Advanced web article extraction tool for Content Stack that intelligently handles both static and JavaScript-rendered content.

## Features

- **Smart Content Extraction**: Uses Mozilla's Readability library for clean article extraction
- **JavaScript Support**: Automatically falls back to Playwright for dynamic content
- **Metadata Extraction**: Captures title, author, publish date, and description
- **Clean Markdown Output**: Converts HTML to clean, readable Markdown
- **Paywall Detection**: Provides helpful messages for sites that block access
- **Robust Error Handling**: Multiple extraction strategies ensure content is captured

## Setup

```bash
npm install
npx playwright install chromium  # One-time browser download for JavaScript sites
```

## Files

- `article-scraper.js` - Advanced extractor with Playwright support for JavaScript sites
- `simple-scraper.js` - Lightweight alternative using only Cheerio (faster for static sites)
- `package.json` - Dependencies and metadata

## Usage

### Command Line

Extract an article and save to file:

```bash
# For static sites (faster):
node simple-scraper.js <url> [output.md]

# For JavaScript-heavy sites:
node article-scraper.js <url> [output.md]

# Examples:
node article-scraper.js https://windsurf.com/blog/windsurfs-next-stage
node simple-scraper.js https://en.wikipedia.org/wiki/Artificial_intelligence
```

### Programmatic Usage

```javascript
import { scrapeArticle, extractArticleForContentStack } from './simple-scraper.js';

// Basic extraction
const result = await scrapeArticle('https://example.com/article');
if (result.success) {
  console.log(result.title);
  console.log(result.content);
}

// Content Stack format
const content = await extractArticleForContentStack('https://example.com/article');
console.log(content);
```

## API

### `scrapeArticle(url)`

Scrapes an article from the given URL.

**Returns:**
```javascript
{
  success: boolean,
  title: string,
  author: string,
  description: string,
  publishDate: string,
  content: string,        // Markdown content
  url: string,           // Final URL after redirects
  domain: string,        // Source domain
  wordCount: number,
  error?: string         // Error message if failed
}
```

### `extractArticleForContentStack(url)`

Formats article content for Content Stack integration.

**Returns:**
```javascript
{
  platform: 'article',
  title: string,
  author: string,
  url: string,
  content: string,       // Formatted Markdown with metadata
  metadata: {
    domain: string,
    wordCount: number,
    publishDate: string,
    description: string
  },
  success: boolean,
  error?: string
}
```

## How It Works

### Advanced Scraper (article-scraper.js)
1. **Initial Fetch**: Attempts to fetch the page using standard HTTP request
2. **Readability Extraction**: Uses Mozilla's Readability algorithm first
3. **Content Check**: If content < 100 words, assumes JavaScript rendering needed
4. **Playwright Fallback**: Launches headless browser to render JavaScript
5. **Re-extraction**: Runs extraction algorithms on fully rendered content
6. **Format Output**: Converts to Markdown and structures for Content Stack

### Simple Scraper (simple-scraper.js)
1. **Fetch Page**: Downloads HTML with browser-like headers
2. **Extract Metadata**: Looks for OpenGraph, Twitter Card, and standard meta tags
3. **Find Content**: Uses common article selectors and patterns
4. **Clean & Convert**: Removes ads/navigation and converts to Markdown
5. **Format Output**: Structures content for Content Stack

## Extraction Strategy

The scraper tries multiple approaches to find article content:

1. **Semantic HTML**: Looks for `<article>`, `[role="article"]`, etc.
2. **Common Classes**: Searches for `.post-content`, `.article-body`, etc.
3. **Paragraph Analysis**: Finds containers with the most paragraphs
4. **Fallback**: Extracts all substantial paragraphs as last resort

## Supported Sites

Successfully tested with:
- Personal blogs (e.g., blog.samaltman.com)
- News sites (e.g., NYTimes, with proper headers)
- Medium articles
- Substack newsletters
- Most standard blog platforms

## Limitations

- **Paywalls**: Some sites (WSJ, Financial Times) have hard paywalls
- **Anti-Scraping**: Some sites actively block automated access
- **Complex Layouts**: May struggle with unusual or heavily customized layouts
- **Large Pages**: Playwright may timeout on very large pages
- **Authentication**: Sites requiring login won't work without credentials

## Error Handling

The scraper provides helpful error messages:

- **403/401 Errors**: Suggests manual extraction methods
- **404 Errors**: Indicates broken or invalid URL
- **Timeout**: Site may be slow or blocking requests
- **No Content**: Article structure not recognized

## Integration with Content Stack

This scraper is designed to work with Content Stack's URL extraction pipeline:

1. User submits article URL
2. System calls `extractArticleForContentStack(url)`
3. Content is formatted with metadata
4. Ready for categorization and processing

## Future Enhancements

- Support for more complex layouts
- Archive.org fallback for paywalled content
- PDF article extraction
- Multi-page article support
- Language detection and translation

## Dependencies

### Core Dependencies
- `node-fetch`: HTTP requests with full header control
- `cheerio`: Fast, jQuery-like HTML parsing

### Advanced Scraper Additional Dependencies
- `@mozilla/readability`: Mozilla's article extraction algorithm
- `jsdom`: DOM implementation for Readability
- `turndown`: HTML to Markdown conversion
- `playwright`: Browser automation for JavaScript sites

## Notes

- Uses realistic browser headers to avoid basic bot detection
- Handles redirects automatically
- Preserves formatting like lists and blockquotes
- Strips unnecessary elements (ads, navigation, etc.)