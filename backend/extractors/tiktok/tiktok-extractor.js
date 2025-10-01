// Direct TikTok Transcript Extractor - No browser needed!
// Fetches TikTok URL directly and extracts transcript

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import { decode } from 'html-entities';
import fs from 'fs/promises';

const UA_HEADERS = {
  'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  referer: 'https://www.tiktok.com/'
};

/**
 * Strip WebVTT to plain text
 */
function stripVtt(vtt) {
  return vtt
    .split(/\r?\n/)
    .filter(l => l && l !== 'WEBVTT' && !/^\d\d:\d\d/.test(l) && !/-->/.test(l))
    .join('\n');
}

/**
 * Fetch page HTML, following short-link redirects
 */
async function fetchHtml(tiktokUrl) {
  // 1) resolve /t/Z… short-links
  const r0 = await fetch(tiktokUrl, { headers: UA_HEADERS, redirect: 'follow' });
  const fullUrl = r0.url; // after 302s
  // 2) download page HTML
  return { html: await r0.text(), fullUrl };
}

/**
 * Main extraction function
 */
export async function getTranscript(url, preferLang = 'eng') {
  const { html, fullUrl } = await fetchHtml(url);

  const $ = cheerio.load(html);
  const script = $('#__UNIVERSAL_DATA_FOR_REHYDRATION__');
  if (!script.length) throw new Error('data script not found');

  const data = JSON.parse(decode(script.html()));
  const item =
    data.__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct;

  const user = item.author.uniqueId;
  const videoId = item.id;
  const subtitles = item.video.subtitleInfos || [];

  if (!subtitles.length)
    return {
      link: fullUrl,
      hasTranscript: false,
      text: '',
      metadata: { user, videoId, description: item.desc }
    };

  // pick ENG if present
  const track =
    subtitles.find(s => s.LanguageCodeName.startsWith(preferLang)) ||
    subtitles[0];

  const vtt = await (await fetch(track.Url, { headers: UA_HEADERS })).text();
  const text = stripVtt(vtt);

  return {
    link: fullUrl,
    hasTranscript: true,
    text,
    metadata: {
      user,
      videoId,
      language: track.LanguageCodeName,
      description: item.desc
    }
  };
}

/**
 * Format for Content Stack
 */
export async function extractTikTokForContentStack(url) {
  try {
    console.log('Fetching TikTok page...');
    const result = await getTranscript(url);
    
    if (!result.hasTranscript) {
      return {
        platform: 'tiktok',
        title: `TikTok by @${result.metadata.user}`,
        url: result.link,
        content: `TikTok Video (No Transcript Available)

@${result.metadata.user}
${result.metadata.description || 'No description'}

This video doesn't have captions. You may need to:
1. Watch the video and transcribe manually
2. Use speech-to-text tools
3. Check if captions are available in TikTok app`,
        metadata: result.metadata
      };
    }
    
    return {
      platform: 'tiktok',
      title: `TikTok by @${result.metadata.user}`,
      url: result.link,
      content: `TikTok Video Transcript

@${result.metadata.user}
Language: ${result.metadata.language}

Description:
${result.metadata.description || 'No description'}

---

Transcript:
${result.text}`,
      metadata: result.metadata,
      success: true
    };
    
  } catch (error) {
    console.error('TikTok extraction error:', error);
    
    // Common errors
    if (error.message.includes('403')) {
      return {
        platform: 'tiktok',
        title: 'TikTok Video',
        url: url,
        content: `Unable to fetch TikTok content - Access blocked.

TikTok may be blocking automated requests. Try:
1. Copy the video URL
2. Open in browser and copy captions manually
3. Or save the page HTML and process locally`,
        error: 'Access blocked'
      };
    }
    
    return {
      platform: 'tiktok',
      title: 'TikTok Video',
      url: url,
      content: `Failed to extract TikTok content: ${error.message}`,
      error: error.message
    };
  }
}

// CLI usage
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const url = process.argv[2];
  const out = process.argv[3] || 'transcript.txt';
  
  if (!url) {
    console.log('Usage: node tiktok-direct.js <tiktok-url> [outfile]');
    console.log('\nExamples:');
    console.log('  node tiktok-direct.js https://www.tiktok.com/@user/video/123456');
    console.log('  node tiktok-direct.js https://vm.tiktok.com/ZMh3K9Lf/');
    process.exit(0);
  }
  
  try {
    console.log(`Fetching: ${url}`);
    const res = await getTranscript(url);
    
    if (!res.hasTranscript) {
      console.log('No captions on that video.');
      console.log(`User: @${res.metadata.user}`);
      console.log(`Description: ${res.metadata.description || 'None'}`);
      process.exit(0);
    }
    
    const output = `TikTok Transcript
URL: ${res.link}
User: @${res.metadata.user}
Language: ${res.metadata.language}

${res.metadata.description ? `Description:\n${res.metadata.description}\n\n` : ''}Transcript:
${res.text}`;
    
    await fs.writeFile(out, output, 'utf8');
    console.log(`\n✅ Transcript saved → ${out}`);
    console.log(`Language: ${res.metadata.language}`);
    console.log(`Length: ${res.text.length} characters`);
  } catch (e) {
    console.error('\n❌ Error:', e.message);
    if (e.message.includes('403')) {
      console.error('\nTikTok may be blocking requests. Try using a VPN or proxy.');
    }
    process.exit(1);
  }
}