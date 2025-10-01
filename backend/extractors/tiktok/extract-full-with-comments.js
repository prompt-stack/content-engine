#!/usr/bin/env node
import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { decode } from 'html-entities';
import { getTranscript } from './tiktok-extractor.js';

const UA_HEADERS = {
  'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  referer: 'https://www.tiktok.com/',
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  'accept-language': 'en-US,en;q=0.5',
  'cache-control': 'no-cache'
};

/**
 * Parse engagement metrics (11.4K -> 11400)
 */
function parseMetric(text) {
  if (!text) return 0;
  text = text.trim();
  if (text.endsWith('K')) {
    return Math.round(parseFloat(text.slice(0, -1)) * 1000);
  }
  if (text.endsWith('M')) {
    return Math.round(parseFloat(text.slice(0, -1)) * 1000000);
  }
  return parseInt(text.replace(/,/g, ''), 10) || 0;
}

/**
 * Extract comments from HTML
 */
function extractCommentsFromHtml($) {
  const comments = [];
  
  // Find all comment containers
  $('.css-1mf23fd-DivContentContainer').each((i, elem) => {
    const $comment = $(elem);
    
    // Extract username
    const username = $comment.find('[data-e2e^="comment-username-"]').text().trim();
    
    // Extract comment text
    const commentText = $comment.find('[data-e2e^="comment-level-"]').text().trim();
    
    // Extract time
    const timeText = $comment.find('[data-e2e^="comment-time-"]').text().trim();
    
    // Extract likes count (if available)
    const likesText = $comment.find('[data-e2e^="comment-like-count"]').text().trim();
    const likes = parseMetric(likesText);
    
    // Check if comment has creator's heart
    const hasCreatorHeart = $comment.find('svg').filter((i, svg) => {
      return $(svg).html().includes('#FE2C55');
    }).length > 0;
    
    if (username && commentText) {
      comments.push({
        author: username,
        text: commentText,
        time: timeText,
        likes: likes || 0,
        hasCreatorHeart
      });
    }
  });
  
  return comments;
}

/**
 * Extract full TikTok content with all comments
 */
async function extractFullContentWithComments(url) {
  try {
    // Get transcript first
    const transcript = await getTranscript(url);
    
    // Fetch page HTML with proper headers
    const response = await fetch(url, { 
      headers: UA_HEADERS, 
      redirect: 'follow',
      method: 'GET'
    });
    
    const html = await response.text();
    const $ = cheerio.load(html);
    
    // Parse script data for video info
    const script = $('#__UNIVERSAL_DATA_FOR_REHYDRATION__');
    if (!script.length) throw new Error('data script not found');
    
    const data = JSON.parse(decode(script.html()));
    const item = data.__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct;
    
    // Extract stats
    const stats = item.stats || {};
    
    // Extract metrics from HTML as fallback
    const likes = $('[data-e2e="browse-like-count"]').text() || stats.diggCount;
    const comments = $('[data-e2e="browse-comment-count"]').text() || stats.commentCount;
    const saves = $('[data-e2e="undefined-count"]').text() || stats.collectCount;
    const shares = stats.shareCount || 0;
    const views = stats.playCount || 0;
    
    // User info
    const user = item.author;
    
    // Extract comments from HTML
    const extractedComments = extractCommentsFromHtml($);
    
    // Also try to get comments from script data
    const scriptComments = [];
    if (data.__DEFAULT_SCOPE__['webapp.video-detail'].commentInfo) {
      const commentList = data.__DEFAULT_SCOPE__['webapp.video-detail'].commentInfo.commentList || [];
      commentList.forEach(comment => {
        scriptComments.push({
          text: comment.text,
          author: comment.user.uniqueId,
          likes: comment.diggCount,
          time: new Date(comment.createTime * 1000).toLocaleDateString(),
          hasCreatorHeart: comment.isAuthorDiked || false,
          replies: comment.replyCommentTotal || 0
        });
      });
    }
    
    // Merge comments (prefer script comments as they have more data)
    const allComments = scriptComments.length > 0 ? scriptComments : extractedComments;
    
    return {
      success: true,
      title: item.desc || `TikTok by @${user.uniqueId}`,
      creator: `@${user.uniqueId}`,
      transcript: transcript.text,
      description: item.desc,
      hashtags: (item.textExtra || []).filter(e => e.hashtagName).map(e => e.hashtagName),
      metadata: {
        views: parseMetric(views.toString()),
        likes: parseMetric(likes.toString()),
        comments: parseMetric(comments.toString()),
        shares: parseMetric(shares.toString()),
        saves: parseMetric(saves.toString()),
        duration: item.video.duration,
        createdAt: new Date(item.createTime * 1000).toISOString(),
        videoId: item.id,
        user: user.uniqueId,
        language: transcript.metadata?.language || 'en',
        userStats: {
          followers: user.stats?.followerCount || 0,
          following: user.stats?.followingCount || 0,
          verified: user.verified || false
        }
      },
      comments: allComments,
      url: response.url
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// CLI usage
if (process.argv[2]) {
  const url = process.argv[2];
  const result = await extractFullContentWithComments(url);
  
  if (result.success) {
    console.log('\n✅ TikTok Content Extracted with Comments\n');
    console.log(`Title: ${result.title}`);
    console.log(`Creator: ${result.creator}`);
    console.log(`URL: ${result.url}\n`);
    
    console.log('📊 Engagement Metrics:');
    console.log(`Views: ${result.metadata.views.toLocaleString()}`);
    console.log(`Likes: ${result.metadata.likes.toLocaleString()}`);
    console.log(`Comments: ${result.metadata.comments.toLocaleString()}`);
    console.log(`Shares: ${result.metadata.shares.toLocaleString()}`);
    console.log(`Saves: ${result.metadata.saves.toLocaleString()}`);
    console.log(`Duration: ${result.metadata.duration}s\n`);
    
    console.log('📝 Description:');
    console.log(result.description || 'No description');
    
    if (result.hashtags.length > 0) {
      console.log('\n#️⃣ Hashtags:');
      console.log(result.hashtags.map(h => `#${h}`).join(' '));
    }
    
    console.log('\n💬 Transcript:');
    console.log(result.transcript || 'No transcript available');
    
    if (result.comments.length > 0) {
      console.log(`\n💭 All Comments (${result.comments.length} total):`);
      console.log('─'.repeat(60));
      result.comments.forEach((comment, index) => {
        console.log(`\n${index + 1}. @${comment.author}${comment.hasCreatorHeart ? ' ❤️' : ''}`);
        console.log(`   "${comment.text}"`);
        console.log(`   ${comment.likes > 0 ? `${comment.likes} likes` : 'No likes'} • ${comment.time || 'Unknown time'}`);
        if (comment.replies > 0) {
          console.log(`   ${comment.replies} replies`);
        }
      });
      console.log('─'.repeat(60));
    }
    
    console.log('\n👤 Creator Stats:');
    console.log(`Followers: ${result.metadata.userStats.followers.toLocaleString()}`);
    console.log(`Following: ${result.metadata.userStats.following.toLocaleString()}`);
    console.log(`Verified: ${result.metadata.userStats.verified ? '✓' : '✗'}`);
    
    // Save to JSON file
    const outputFile = `tiktok-${result.metadata.videoId}-full.json`;
    const fs = await import('fs/promises');
    await fs.writeFile(outputFile, JSON.stringify(result, null, 2));
    console.log(`\n💾 Full data saved to: ${outputFile}`);
  } else {
    console.error('❌ Error:', result.error);
  }
}

export { extractFullContentWithComments };