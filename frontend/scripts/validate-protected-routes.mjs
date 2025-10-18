#!/usr/bin/env node
/**
 * Validate Protected Routes
 *
 * Checks that all folders in app/(protected)/ are listed in src/config/routes.ts
 * Run this in CI or pre-commit to catch drift.
 *
 * Usage: node scripts/validate-protected-routes.mjs
 */

import { readdir, readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

// These are excluded from validation (not routes)
const EXCLUDED_FOLDERS = ['_components'];

async function getProtectedFolders() {
  const protectedDir = join(projectRoot, 'app', '(protected)');
  const entries = await readdir(protectedDir, { withFileTypes: true });

  return entries
    .filter(entry => entry.isDirectory())
    .map(entry => entry.name)
    .filter(name => !EXCLUDED_FOLDERS.includes(name));
}

async function getConfiguredRoutes() {
  // Read and parse the TypeScript config file
  const configPath = join(projectRoot, 'src', 'config', 'routes.ts');
  const content = await readFile(configPath, 'utf-8');

  // Extract PROTECTED_ROUTE_PREFIXES array using regex
  const match = content.match(/PROTECTED_ROUTE_PREFIXES\s*=\s*\[([\s\S]*?)\]\s*as const/);

  if (!match) {
    throw new Error('Could not find PROTECTED_ROUTE_PREFIXES in routes.ts');
  }

  // Extract all quoted strings from the array content
  const arrayContent = match[1];
  const routeMatches = arrayContent.matchAll(/['"]([^'"]+)['"]/g);

  const routes = Array.from(routeMatches)
    .map(m => m[1])
    .map(route => route.replace('/', ''));

  return routes;
}

async function validate() {
  console.log('🔍 Validating protected routes...\n');

  const folders = await getProtectedFolders();
  const configured = await getConfiguredRoutes();

  console.log('📁 Folders in app/(protected)/:');
  folders.forEach(f => console.log(`   - ${f}`));

  console.log('\n⚙️  Configured in src/config/routes.ts:');
  configured.forEach(r => console.log(`   - ${r}`));

  // Find missing routes
  const missing = folders.filter(f => !configured.includes(f));

  if (missing.length > 0) {
    console.log('\n❌ ERROR: Routes missing from src/config/routes.ts:');
    missing.forEach(m => console.log(`   - /${m}`));
    console.log('\n💡 Add these to PROTECTED_ROUTE_PREFIXES in src/config/routes.ts');
    process.exit(1);
  }

  // Find extra routes
  const extra = configured.filter(r => !folders.includes(r));

  if (extra.length > 0) {
    console.log('\n⚠️  WARNING: Configured routes not found in app/(protected)/:');
    extra.forEach(e => console.log(`   - /${e}`));
    console.log('\n💡 Remove these from PROTECTED_ROUTE_PREFIXES or create the folders');
  }

  if (missing.length === 0 && extra.length === 0) {
    console.log('\n✅ All protected routes are properly configured!');
  }
}

validate().catch(err => {
  console.error('❌ Validation failed:', err);
  process.exit(1);
});
