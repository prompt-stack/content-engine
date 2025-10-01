#!/usr/bin/env node

// JSON Article Scraper - outputs structured JSON data
// Based on simple-scraper.js but with JSON output

import fetch from 'node-fetch';
import * as cheerio from 'cheerio';
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
      'Upgrade-Insecure-Requests': '1'
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
  $('script, style, noscript, iframe, svg, nav, header, footer, aside').remove();
  
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
    '#content',
    'main'
  ];
  
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
    let maxParagraphs = 0;
    let bestContainer = null;
    
    $('div, section, main').each((i, elem) => {
      const paragraphs = $(elem).find('p').length;
      if (paragraphs > maxParagraphs) {
        maxParagraphs = paragraphs;
        bestContainer = $(elem);
      }
    });
    
    $content = bestContainer || $('body');
  }
  
  // Extract text content
  let textContent = '';
  let htmlContent = '';
  
  if ($content) {
    // Get all paragraphs
    const paragraphs = [];
    $content.find('p, h1, h2, h3, h4, h5, h6, li').each((i, elem) => {
      const text = $(elem).text().trim();
      if (text.length > 0) {
        paragraphs.push(text);
      }
    });
    
    textContent = paragraphs.join('\n\n');
    htmlContent = $content.html() || '';
  }
  
  // Calculate word count
  const wordCount = textContent.split(/\s+/).filter(word => word.length > 0).length;
  
  // Extract images
  const images = [];
  $('img').each((i, elem) => {
    const src = $(elem).attr('src');
    const alt = $(elem).attr('alt') || '';
    if (src) {
      // Convert relative URLs to absolute
      try {
        const absoluteUrl = new URL(src, url).href;
        images.push({ src: absoluteUrl, alt });
      } catch (e) {
        // Skip invalid URLs
      }
    }
  });
  
  return {
    url,
    title: title || '',
    author: author || '',
    date: publishDate || '',
    description: description || '',
    content: textContent,
    htmlContent,
    wordCount,
    images,
    extractedAt: new Date().toISOString()
  };
}

/**
 * Main scraping function
 */
async function scrapeArticle(url) {
  try {
    const html = await fetchHTML(url);
    const article = extractArticle(html, url);
    
    // Output JSON to stdout
    console.log(JSON.stringify(article, null, 2));
    
    return article;
  } catch (error) {
    // Output error as JSON
    const errorResult = {
      url,
      error: error.message,
      extractedAt: new Date().toISOString()
    };
    console.log(JSON.stringify(errorResult, null, 2));
    process.exit(1);
  }
}

// CLI usage
if (process.argv.length < 3) {
  console.error('Usage: node json-scraper.js <url>');
  process.exit(1);
}

const url = process.argv[2];
scrapeArticle(url);