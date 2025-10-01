// Web Article Scraper for Content Stack
// Fetches and extracts clean article content from URLs

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
import TurndownService from 'turndown';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { URL } from 'url';
import fs from 'fs/promises';
import { chromium } from 'playwright';

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

/**
 * Fetch HTML content from URL
 */
async function fetchPage(url) {
  const response = await fetch(url, {
    headers: {
      'User-Agent': USER_AGENT,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.5',
      'Accept-Encoding': 'gzip, deflate',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1'
    },
    redirect: 'follow',
    timeout: 30000
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('text/html')) {
    throw new Error(`Invalid content type: ${contentType}`);
  }

  return {
    html: await response.text(),
    url: response.url // Final URL after redirects
  };
}

/**
 * Extract article content using Readability
 */
function extractWithReadability(html, url) {
  const dom = new JSDOM(html, { url });
  const reader = new Readability(dom.window.document);
  const article = reader.parse();
  
  if (!article) {
    throw new Error('Readability could not parse article');
  }
  
  return {
    title: article.title,
    author: article.byline,
    content: article.content,
    textContent: article.textContent,
    length: article.length,
    excerpt: article.excerpt,
    siteName: article.siteName
  };
}

/**
 * Fallback extraction using Cheerio
 */
function extractWithCheerio(html, url) {
  const $ = cheerio.load(html);
  
  // Remove scripts and styles
  $('script, style, noscript').remove();
  
  // Try to find title
  let title = $('meta[property="og:title"]').attr('content') ||
              $('meta[name="twitter:title"]').attr('content') ||
              $('title').text() ||
              $('h1').first().text();
  
  // Try to find author
  let author = $('meta[name="author"]').attr('content') ||
               $('meta[property="article:author"]').attr('content') ||
               $('.author').first().text() ||
               $('[rel="author"]').first().text();
  
  // Try to find description
  let description = $('meta[property="og:description"]').attr('content') ||
                    $('meta[name="description"]').attr('content') ||
                    $('meta[name="twitter:description"]').attr('content');
  
  // Try to find main content
  const contentSelectors = [
    'article', 
    'main',
    '[role="main"]',
    '.post-content',
    '.entry-content',
    '.content',
    '#content',
    '.article-body',
    '.story-body'
  ];
  
  let content = '';
  for (const selector of contentSelectors) {
    const element = $(selector).first();
    if (element.length && element.text().trim().length > 200) {
      content = element.html();
      break;
    }
  }
  
  // If no content found, try to get body paragraphs
  if (!content) {
    const paragraphs = $('p').map((i, el) => $(el).text().trim()).get()
      .filter(p => p.length > 50);
    
    if (paragraphs.length > 3) {
      content = paragraphs.join('\n\n');
    }
  }
  
  return {
    title: title?.trim(),
    author: author?.trim(),
    description: description?.trim(),
    content: content,
    siteName: new URL(url).hostname
  };
}

/**
 * Convert HTML to Markdown
 */
function htmlToMarkdown(html) {
  const turndownService = new TurndownService({
    headingStyle: 'atx',
    codeBlockStyle: 'fenced',
    bulletListMarker: '-'
  });
  
  // Add custom rules
  turndownService.addRule('removeImages', {
    filter: 'img',
    replacement: () => ''
  });
  
  turndownService.addRule('removeVideos', {
    filter: ['video', 'iframe'],
    replacement: () => ''
  });
  
  return turndownService.turndown(html);
}

/**
 * Fetch page content using Playwright for JavaScript-heavy sites
 */
async function fetchPageWithPlaywright(url) {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const context = await browser.newContext({
      userAgent: USER_AGENT
    });
    
    const page = await context.newPage();
    
    // Navigate and wait for content
    await page.goto(url, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait a bit more for dynamic content
    await page.waitForTimeout(2000);
    
    // Try to wait for article content selectors
    try {
      await page.waitForSelector('article, [role="article"], main, .content, .post-content', { 
        timeout: 5000 
      });
    } catch {
      // Continue even if selectors not found
    }
    
    // Get the rendered HTML
    const html = await page.content();
    const finalUrl = page.url();
    
    await browser.close();
    
    return { html, url: finalUrl };
  } catch (error) {
    await browser.close();
    throw error;
  }
}

/**
 * Main article extraction function
 */
export async function scrapeArticle(url) {
  try {
    let { html, url: finalUrl } = await fetchPage(url);
    
    let article;
    try {
      // Try Readability first
      article = extractWithReadability(html, finalUrl);
    } catch (e) {
      // Fallback to Cheerio
      article = extractWithCheerio(html, finalUrl);
    }
    
    // Convert content to markdown
    let markdown = article.content ? htmlToMarkdown(article.content) : article.textContent || '';
    
    // Clean up text
    let cleanText = markdown
      .replace(/\n{3,}/g, '\n\n')  // Remove excessive newlines
      .replace(/^\s+|\s+$/g, '')    // Trim
      .replace(/\t/g, '  ');        // Replace tabs with spaces
    
    // If content is too short, try Playwright
    const wordCount = cleanText.split(/\s+/).filter(word => word.length > 0).length;
    if (wordCount < 100) {
      
      try {
        const playwrightResult = await fetchPageWithPlaywright(url);
        
        // Try extraction again with Playwright-rendered content
        try {
          article = extractWithReadability(playwrightResult.html, playwrightResult.url);
        } catch (e) {
          article = extractWithCheerio(playwrightResult.html, playwrightResult.url);
        }
        
        // Re-convert and clean
        markdown = article.content ? htmlToMarkdown(article.content) : article.textContent || '';
        cleanText = markdown
          .replace(/\n{3,}/g, '\n\n')
          .replace(/^\s+|\s+$/g, '')
          .replace(/\t/g, '  ');
          
        finalUrl = playwrightResult.url;
      } catch (playwrightError) {
        console.error('Playwright extraction failed:', playwrightError.message);
        // Continue with original extraction
      }
    }
    
    return {
      success: true,
      url: finalUrl,
      title: article.title || 'Untitled',
      author: article.author || 'Unknown',
      siteName: article.siteName || new URL(finalUrl).hostname,
      excerpt: article.excerpt || cleanText.substring(0, 200) + '...',
      content: cleanText,
      wordCount: cleanText.split(/\s+/).filter(word => word.length > 0).length,
      metadata: {
        length: article.length,
        scraped: new Date().toISOString()
      }
    };
    
  } catch (error) {
    console.error('Scraping error:', error);
    return {
      success: false,
      url: url,
      error: error.message,
      metadata: {
        scraped: new Date().toISOString()
      }
    };
  }
}

/**
 * Format article for Content Stack
 */
export async function extractArticleForContentStack(url) {
  const result = await scrapeArticle(url);
  
  if (!result.success) {
    return {
      platform: 'article',
      title: 'Article',
      url: url,
      content: `Failed to extract article: ${result.error}`,
      error: result.error,
      success: false
    };
  }
  
  // Extract domain from URL
  const urlObj = new URL(result.url || url);
  const domain = urlObj.hostname.replace('www.', '');
  
  const content = `# ${result.title}

**Author:** ${result.author}  
**Source:** ${result.siteName}  
**URL:** ${result.url}  
**Word Count:** ${result.wordCount}  

---

${result.content}`;
  
  return {
    platform: 'article',
    title: result.title || 'Article',
    author: result.author || '',
    domain: domain,
    url: result.url,
    content: result.content,
    description: result.excerpt || '',
    metadata: {
      siteName: result.siteName,
      wordCount: result.wordCount,
      excerpt: result.excerpt,
      publishedDate: result.metadata?.publishedDate || result.metadata?.datePublished,
      ...result.metadata
    },
    success: true
  };
}

// CLI usage
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const url = process.argv[2];
  const outputFile = process.argv[3] || 'article.md';
  
  if (!url) {
    console.log('Usage: node article-scraper.js <url> [output.md]');
    console.log('\nExamples:');
    console.log('  node article-scraper.js https://example.com/article');
    console.log('  node article-scraper.js https://medium.com/@user/post-title output.md');
    process.exit(0);
  }
  
  try {
    const result = await extractArticleForContentStack(url);
    
    // Output JSON for API consumption
    console.log(JSON.stringify(result));
    
    // Exit with appropriate code
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}