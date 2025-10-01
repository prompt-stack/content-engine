#!/usr/bin/env node
import { extractTikTokContent } from './tiktok-extractor.js';

const url = process.argv[2];
if (!url) {
  console.error('Usage: node get-metadata.js <tiktok-url>');
  process.exit(1);
}

const result = await extractTikTokContent(url);
console.log(JSON.stringify(result, null, 2));