#!/usr/bin/env node
import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { decode } from 'html-entities';
import { getTranscript } from './tiktok-extractor.js';

const UA_HEADERS = {
  'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  referer: 'https://www.tiktok.com/'
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
 * Extract full TikTok content with metrics
 */
async function extractFullContent(url) {
  try {
    // Get transcript first
    const transcript = await getTranscript(url);
    
    // Fetch page HTML
    const response = await fetch(url, { headers: UA_HEADERS, redirect: 'follow' });
    const html = await response.text();
    const $ = cheerio.load(html);
    
    // Parse script data
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
    
    // Extract top comments if available
    const topComments = [];
    if (data.__DEFAULT_SCOPE__['webapp.video-detail'].commentInfo) {
      const commentList = data.__DEFAULT_SCOPE__['webapp.video-detail'].commentInfo.commentList || [];
      commentList.slice(0, 5).forEach(comment => {
        topComments.push({
          text: comment.text,
          author: comment.user.uniqueId,
          likes: comment.diggCount
        });
      });
    }
    
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
      topComments,
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
  const result = await extractFullContent(url);
  
  if (result.success) {
    console.log('\n✅ TikTok Content Extracted\n');
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
    
    if (result.topComments.length > 0) {
      console.log('\n💭 Top Comments:');
      result.topComments.forEach(comment => {
        console.log(`- @${comment.author}: "${comment.text}" (${comment.likes} likes)`);
      });
    }
    
    console.log('\n👤 Creator Stats:');
    console.log(`Followers: ${result.metadata.userStats.followers.toLocaleString()}`);
    console.log(`Following: ${result.metadata.userStats.following.toLocaleString()}`);
    console.log(`Verified: ${result.metadata.userStats.verified ? '✓' : '✗'}`);
  } else {
    console.error('❌ Error:', result.error);
  }
}

export { extractFullContent };