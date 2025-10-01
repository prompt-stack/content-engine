# Reddit Extractor

Comprehensive Reddit thread extraction for Content Stack, including posts, comments, and metadata.

## Features

- **Full Thread Extraction**: Post content, all comments, and replies
- **Rich Metadata**: Upvotes, awards, post flair, subreddit info
- **Comment Hierarchy**: Preserves thread structure and conversation flow
- **Multiple Formats**: Supports various Reddit URL formats
- **Author Attribution**: Tracks usernames and scores for each contribution
- **Clean Formatting**: Converts Reddit markdown to readable text

## Setup

```bash
npm install
```

## Usage

### Command Line

Extract a Reddit post with comments:

```bash
node reddit-extractor.js <reddit-url> [output.md]

# Examples:
node reddit-extractor.js https://www.reddit.com/r/AskReddit/comments/xyz123/
node reddit-extractor.js https://old.reddit.com/r/technology/comments/abc456/ output.md
```

### Programmatic Usage

```javascript
import { extractRedditThread, extractRedditForContentStack } from './reddit-extractor.js';

// Basic extraction
const result = await extractRedditThread('https://reddit.com/r/tech/comments/123/');
if (result.success) {
  console.log(result.title);
  console.log(result.post);
  console.log(result.comments);
}

// Content Stack format
const content = await extractRedditForContentStack('https://redd.it/abc123');
console.log(content);
```

## API

### `extractRedditThread(url)`

Extracts complete thread data from a Reddit URL.

**Returns:**
```javascript
{
  success: boolean,
  title: string,              // Post title
  author: string,             // Post author (u/username)
  subreddit: string,          // r/subreddit
  post: {
    content: string,          // Post text/content
    score: number,            // Upvotes
    awards: number,           // Award count
    created: string,          // ISO date
    edited: boolean,          // If post was edited
    flair: string,            // Post flair text
    url: string               // External URL if link post
  },
  comments: [{
    author: string,           // Comment author
    content: string,          // Comment text
    score: number,            // Comment score
    awards: number,           // Award count
    created: string,          // ISO date
    depth: number,            // Reply depth (0 = top level)
    replies: []               // Nested replies
  }],
  metadata: {
    totalComments: number,
    postId: string,
    permalink: string,
    isLocked: boolean,
    isNSFW: boolean,
    isStickied: boolean,
    upvoteRatio: number       // Upvote percentage (0-1)
  },
  error?: string              // Error message if failed
}
```

### `extractRedditForContentStack(url)`

Formats Reddit content for Content Stack integration.

**Returns:**
```javascript
{
  platform: 'reddit',
  title: string,              // Post title
  author: string,             // Post author
  url: string,                // Full Reddit URL
  content: string,            // Formatted thread with comments
  metadata: {
    subreddit: string,
    score: number,
    commentCount: number,
    created: string,
    flair: string,
    awards: number,
    isNSFW: boolean,
    upvoteRatio: number
  },
  success: boolean,
  error?: string
}
```

## How It Works

1. **URL Parsing**: Handles reddit.com, old.reddit.com, redd.it short links
2. **JSON API Access**: Uses Reddit's JSON endpoint (.json suffix)
3. **Data Extraction**: Parses post data and comment tree
4. **Comment Threading**: Maintains reply hierarchy and relationships
5. **Content Formatting**: Structures for easy reading and processing

## Output Format

The extractor generates a hierarchical thread view:

```
Title: What's your favorite programming language and why?
Author: u/developer123
Subreddit: r/programming
Score: 1,234 | Comments: 567 | Awards: 3
Date: 2024-01-15
Flair: Discussion

Post:
I've been programming for 10 years and I'm curious what languages
everyone prefers these days. Personally, I've been enjoying Rust...

Comments:

u/coder456 (Score: 234):
Python for me! The syntax is clean and the ecosystem is amazing.

  u/developer123 (OP) (Score: 45):
  I love Python too! What frameworks do you use?
  
    u/coder456 (Score: 23):
    Django for web apps, FastAPI for APIs. Both are excellent.

u/rustacean (Score: 189):
Rust gang! The memory safety guarantees are a game changer...
```

## Supported Content

- Text posts (self posts)
- Link posts with descriptions
- Image/video posts with captions
- Crossposted content
- All comment types and depths
- Deleted/removed content indicators

## URL Formats

The extractor supports all common Reddit URL formats:

- `https://www.reddit.com/r/subreddit/comments/id/title/`
- `https://old.reddit.com/r/subreddit/comments/id/`
- `https://reddit.com/comments/id/`
- `https://redd.it/id`
- `https://www.reddit.com/r/subreddit/s/shareId`

## Limitations

- **Private Subreddits**: Cannot access private or quarantined content
- **Deleted Content**: Shows [deleted] or [removed] placeholders
- **Rate Limiting**: Reddit may limit requests from same IP
- **Large Threads**: Very large threads (10k+ comments) may be truncated
- **Live Threads**: May not capture real-time updates

## Error Handling

The extractor provides specific error messages:

- **404 Not Found**: Post deleted or doesn't exist
- **403 Forbidden**: Private subreddit or banned content
- **429 Too Many Requests**: Rate limited, retry later
- **Invalid URL**: Not a valid Reddit thread URL

## Integration with Content Stack

This extractor integrates with Content Stack's URL extraction pipeline:

1. User submits Reddit URL
2. System detects Reddit platform
3. Calls `extractRedditForContentStack(url)`
4. Full thread formatted with metadata
5. Ready for categorization and processing

## Advanced Features

### Comment Filtering
- Extracts all comments by default
- Preserves "Load more comments" indicators
- Handles "Continue this thread" deep replies

### Metadata Extraction
- Post and comment scores
- Award counts and types
- User flair and post flair
- Timestamps and edit indicators
- Stickied and distinguished comments

## Dependencies

- `node-fetch`: HTTP requests
- No HTML parsing needed (uses JSON API)

## Notes

- Uses Reddit's official JSON API
- No authentication required for public content
- Respects Reddit's robots.txt and rate limits
- Preserves markdown formatting
- Handles special characters and emoji

## Best Practices

1. **Rate Limiting**: Wait 1-2 seconds between requests
2. **User Agent**: Uses descriptive user agent for transparency
3. **Caching**: Consider caching results to reduce API calls
4. **Error Handling**: Gracefully handle deleted/removed content

## Status

✅ **Working** - This implementation uses Reddit's JSON API for reliable, efficient thread extraction without authentication requirements.