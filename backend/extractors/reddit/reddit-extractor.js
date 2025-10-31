// Reddit Post Extractor for Content Stack
// Uses Reddit's JSON API to extract posts and comments

import fetch from 'node-fetch';
import fs from 'fs/promises';

const USER_AGENT = 'ContentStack/1.0 (https://github.com/contentstack)';

/**
 * Resolve Reddit short link to full URL by following redirects
 */
async function resolveShortLink(url) {
    // Check if this is a short link
    if (!/\/r\/[^\/]+\/s\//.test(url)) {
        return url; // Not a short link, return as-is
    }

    console.log('🔗 Detected short link, resolving...');

    const response = await fetch(url, {
        headers: {
            'User-Agent': USER_AGENT
        },
        redirect: 'manual' // Don't follow redirects automatically
    });

    if (response.status === 301 || response.status === 302) {
        const location = response.headers.get('location');
        if (location) {
            // Clean up the URL (remove query params for cleaner URL)
            const resolvedUrl = location.split('?')[0];
            console.log(`✅ Resolved to: ${resolvedUrl}`);
            return resolvedUrl;
        }
    }

    throw new Error('Failed to resolve short link - no redirect found');
}

/**
 * Fetch Reddit post data using JSON API
 */
async function fetchRedditData(url) {
    // Add .json to the URL
    const jsonUrl = url.replace(/\/$/, '') + '.json';

    const response = await fetch(jsonUrl, {
        headers: {
            'User-Agent': USER_AGENT,
            'Accept': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

/**
 * Format comment with proper indentation
 */
function formatComment(comment, depth = 0) {
    if (!comment.data || comment.kind !== 't1') return '';
    
    const indent = '  '.repeat(depth);
    const author = comment.data.author;
    const score = comment.data.score;
    const body = comment.data.body;
    const awards = comment.data.total_awards_received || 0;
    
    let formatted = `${indent}u/${author} • ${score} points`;
    if (awards > 0) formatted += ` • ${awards} award${awards > 1 ? 's' : ''}`;
    formatted += `\n${indent}${body.replace(/\n/g, '\n' + indent)}\n`;
    
    // Process replies
    if (comment.data.replies && comment.data.replies.data && comment.data.replies.data.children) {
        for (const reply of comment.data.replies.data.children) {
            if (reply.kind === 't1') {
                formatted += '\n' + formatComment(reply, depth + 1);
            }
        }
    }
    
    return formatted;
}

/**
 * Extract Reddit post and comments
 */
export async function extractReddit(url) {
    try {
        // Resolve short links first
        const resolvedUrl = await resolveShortLink(url);
        const data = await fetchRedditData(resolvedUrl);
        
        // Extract post data
        const postData = data[0].data.children[0].data;
        const commentsData = data[1].data.children;
        
        // Build content
        let content = `# ${postData.title}\n\n`;
        content += `**Posted by** u/${postData.author} in r/${postData.subreddit}\n`;
        content += `**Score:** ${postData.score} points (${Math.round(postData.upvote_ratio * 100)}% upvoted)\n`;
        content += `**Comments:** ${postData.num_comments}\n`;
        content += `**Posted:** ${new Date(postData.created_utc * 1000).toLocaleString()}\n`;
        
        if (postData.total_awards_received > 0) {
            content += `**Awards:** ${postData.total_awards_received}\n`;
        }
        
        content += `\n---\n\n`;
        
        // Add post content
        if (postData.selftext) {
            content += `${postData.selftext}\n\n`;
        } else if (postData.url && postData.url !== url) {
            content += `**Link post:** ${postData.url}\n\n`;
        }
        
        // Add post flair if exists
        if (postData.link_flair_text) {
            content += `**Flair:** ${postData.link_flair_text}\n\n`;
        }
        
        content += `---\n\n## Comments\n\n`;
        
        // Extract top-level comments (limit to top 20 for readability)
        const topComments = commentsData
            .filter(c => c.kind === 't1')
            .slice(0, 20);
        
        if (topComments.length === 0) {
            content += '*No comments yet*\n';
        } else {
            for (const comment of topComments) {
                content += formatComment(comment) + '\n---\n\n';
            }
        }
        
        return {
            platform: 'reddit',
            title: postData.title,
            author: `u/${postData.author}`,
            url: url,
            content: content,
            metadata: {
                subreddit: postData.subreddit,
                score: postData.score,
                upvoteRatio: postData.upvote_ratio,
                numComments: postData.num_comments,
                created: new Date(postData.created_utc * 1000).toISOString(),
                permalink: `https://reddit.com${postData.permalink}`,
                isVideo: postData.is_video || false,
                isNsfw: postData.over_18 || false,
                awards: postData.total_awards_received || 0
            },
            success: true
        };
        
    } catch (error) {
        console.error('Reddit extraction error:', error);
        return {
            platform: 'reddit',
            title: 'Reddit Post',
            url: url,
            content: `Failed to extract Reddit post: ${error.message}\n\nURL: ${url}`,
            error: error.message,
            success: false
        };
    }
}

/**
 * Format for Content Stack integration
 */
export async function extractRedditForContentStack(url) {
    return await extractReddit(url);
}

// CLI usage
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
    const url = process.argv[2];
    const outputFile = process.argv[3] || 'reddit-post.md';
    
    if (!url) {
        console.log('Usage: node reddit-extractor.js <reddit-url> [output.md]');
        console.log('\nExample:');
        console.log('  node reddit-extractor.js https://www.reddit.com/r/AskReddit/comments/...');
        process.exit(0);
    }
    
    try {
        const result = await extractReddit(url);
        
        if (result.success) {
            await fs.writeFile(outputFile, result.content, 'utf8');
            console.log(`\n✅ Reddit post saved to: ${outputFile}`);
            console.log(`Title: ${result.title}`);
            console.log(`Subreddit: r/${result.metadata.subreddit}`);
            console.log(`Comments: ${result.metadata.numComments}`);
        } else {
            console.error(`\n❌ Failed: ${result.error}`);
            process.exit(1);
        }
    } catch (error) {
        console.error('\n❌ Error:', error.message);
        process.exit(1);
    }
}