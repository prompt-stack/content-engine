// Simple Article Scraper using Cheerio only
// Lightweight scraper for static HTML content

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import fs from 'fs/promises';
import { URL } from 'url';

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

/**
 * Fetch HTML from URL
 */
async function fetchHTML(url) {
  const response = await fetch(url, {
    headers: {
      'User-Agent': USER_AGENT,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'gzip, deflate, br',
      'DNT': '1',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1',
      'Cache-Control': 'max-age=0'
    },
    redirect: 'follow',
    timeout: 20000
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.text();
}

/**
 * Extract article using Cheerio selectors
 */
function extractArticle(html, url) {
  const $ = cheerio.load(html);
  
  // Remove unwanted elements
  $('script, style, noscript, iframe, svg').remove();
  
  // Extract metadata
  const title = $('meta[property="og:title"]').attr('content') ||
                $('meta[name="twitter:title"]').attr('content') ||
                $('title').text() ||
                $('h1').first().text().trim();
  
  const author = $('meta[name="author"]').attr('content') ||
                 $('meta[property="article:author"]').attr('content') ||
                 $('[rel="author"]').text().trim() ||
                 $('.author').text().trim() ||
                 $('[itemprop="author"]').text().trim();
  
  const description = $('meta[property="og:description"]').attr('content') ||
                      $('meta[name="description"]').attr('content') ||
                      $('meta[name="twitter:description"]').attr('content');
  
  const publishDate = $('meta[property="article:published_time"]').attr('content') ||
                      $('time[pubdate]').attr('datetime') ||
                      $('time').first().attr('datetime');
  
  // Find main content
  const contentSelectors = [
    'article',
    '[role="article"]',
    'main article',
    '.post-content',
    '.entry-content',
    '.article-content',
    '.article-body',
    '.story-body',
    '[itemprop="articleBody"]',
    '.content',
    '#content'
  ];
  
  let content = '';
  let $content = null;
  
  for (const selector of contentSelectors) {
    const element = $(selector).first();
    if (element.length && element.text().trim().length > 100) {
      $content = element;
      break;
    }
  }
  
  // If no main content found, try to extract paragraphs
  if (!$content) {
    // Find the container with the most paragraphs
    let maxParagraphs = 0;
    let bestContainer = null;
    
    $('div, section, article').each((i, elem) => {
      const paragraphs = $(elem).find('p').length;
      if (paragraphs > maxParagraphs) {
        maxParagraphs = paragraphs;
        bestContainer = elem;
      }
    });
    
    if (bestContainer && maxParagraphs > 3) {
      $content = $(bestContainer);
    }
  }
  
  // Extract text content
  if ($content) {
    // Clean up the content
    $content.find('aside, .sidebar, .advertisement, .social-share, .related-posts').remove();
    
    // Extract paragraphs and headings
    const elements = [];
    $content.find('p, h1, h2, h3, h4, h5, h6, ul, ol, blockquote').each((i, elem) => {
      const $elem = $(elem);
      const text = $elem.text().trim();
      
      if (text.length > 20) {
        if (elem.name.match(/^h[1-6]$/)) {
          elements.push(`\n## ${text}\n`);
        } else if (elem.name === 'blockquote') {
          elements.push(`\n> ${text}\n`);
        } else if (elem.name === 'ul' || elem.name === 'ol') {
          const items = [];
          $elem.find('li').each((j, li) => {
            items.push(`- ${$(li).text().trim()}`);
          });
          if (items.length > 0) {
            elements.push('\n' + items.join('\n') + '\n');
          }
        } else {
          elements.push(text);
        }
      }
    });
    
    content = elements.join('\n\n');
  }
  
  // Fallback: get all paragraphs
  if (!content || content.length < 200) {
    const paragraphs = [];
    $('p').each((i, elem) => {
      const text = $(elem).text().trim();
      if (text.length > 50) {
        paragraphs.push(text);
      }
    });
    content = paragraphs.join('\n\n');
  }
  
  return {
    title: title || 'Untitled Article',
    author: author || 'Unknown',
    description: description || '',
    publishDate: publishDate || '',
    content: content,
    url: url,
    domain: new URL(url).hostname
  };
}

/**
 * Main scraping function
 */
export async function scrapeArticle(url) {
  try {
    console.log(`Fetching: ${url}`);
    const html = await fetchHTML(url);
    const article = extractArticle(html, url);
    
    return {
      success: true,
      ...article,
      wordCount: article.content.split(/\s+/).filter(word => word.length > 0).length
    };
  } catch (error) {
    console.error('Scraping error:', error);
    return {
      success: false,
      url: url,
      error: error.message
    };
  }
}

/**
 * Format for Content Stack
 */
export async function extractArticleForContentStack(url) {
  const result = await scrapeArticle(url);
  
  if (!result.success) {
    let content = `Failed to extract article: ${result.error}\n\n`;
    
    // Add helpful messages for common errors
    if (result.error.includes('403') || result.error.includes('401')) {
      content += `This site appears to have a paywall or is blocking automated access.\n\n`;
      content += `Try:\n`;
      content += `1. Copy the article text manually from your browser\n`;
      content += `2. Use a "reader mode" browser extension\n`;
      content += `3. Check if the article is available through archive.org\n`;
    } else if (result.error.includes('404')) {
      content += `The article was not found. Please check the URL.`;
    } else if (result.error.includes('timeout')) {
      content += `The request timed out. The site may be slow or blocking requests.`;
    }
    
    return {
      platform: 'article',
      title: 'Article',
      url: url,
      content: content,
      error: result.error,
      success: false
    };
  }
  
  let content = `# ${result.title}\n\n`;
  
  if (result.author !== 'Unknown') {
    content += `**Author:** ${result.author}  \n`;
  }
  
  if (result.publishDate) {
    content += `**Published:** ${result.publishDate}  \n`;
  }
  
  content += `**Source:** ${result.domain}  \n`;
  content += `**URL:** ${result.url}  \n`;
  content += `**Words:** ${result.wordCount}  \n\n`;
  
  if (result.description) {
    content += `> ${result.description}\n\n`;
  }
  
  content += `---\n\n${result.content}`;
  
  return {
    platform: 'article',
    title: result.title,
    author: result.author,
    url: result.url,
    content: content,
    metadata: {
      domain: result.domain,
      wordCount: result.wordCount,
      publishDate: result.publishDate,
      description: result.description
    },
    success: true
  };
}

// CLI usage
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const url = process.argv[2];
  const outputFile = process.argv[3] || 'article.md';
  
  if (!url) {
    console.log('Usage: node simple-scraper.js <url> [output.md]');
    console.log('\nA lightweight article scraper using Cheerio');
    console.log('\nExamples:');
    console.log('  node simple-scraper.js https://example.com/article');
    console.log('  node simple-scraper.js https://blog.com/post output.md');
    process.exit(0);
  }
  
  try {
    const result = await extractArticleForContentStack(url);
    
    if (result.success) {
      await fs.writeFile(outputFile, result.content, 'utf8');
      console.log(`\n✅ Article saved to: ${outputFile}`);
      console.log(`Title: ${result.title}`);
      console.log(`Words: ${result.metadata.wordCount}`);
    } else {
      console.error(`\n❌ Failed: ${result.error}`);
      process.exit(1);
    }
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}