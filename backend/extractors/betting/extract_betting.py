#!/usr/bin/env python3
"""
Betting Lines Extractor for FanDuel and other sportsbooks
Extracts prop bets, odds, and betting lines from sports betting sites
"""

import asyncio
import json
import sys
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright

class BettingExtractor:
    def __init__(self):
        self.supported_sites = [
            'sportsbook.fanduel.com',
            'sportsbook.draftkings.com',
            'caesars.com/sportsbook'
        ]
    
    async def extract(self, url):
        """Extract betting data from URL"""
        domain = urlparse(url).netloc
        
        async with async_playwright() as p:
            # Launch browser with more realistic settings to avoid detection
            browser = await p.chromium.launch(
                headless=False,  # Run with GUI for better compatibility
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to page with more lenient wait condition
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for betting content to load
                await page.wait_for_timeout(3000)
                
                # Extract based on site
                if 'fanduel.com' in domain:
                    data = await self._extract_fanduel(page, url)
                elif 'draftkings.com' in domain:
                    data = await self._extract_draftkings(page, url)
                else:
                    data = await self._extract_generic(page, url)
                
                await browser.close()
                return data
                
            except Exception as e:
                await browser.close()
                return {
                    'success': False,
                    'error': str(e),
                    'url': url
                }
    
    async def _extract_fanduel(self, page, url):
        """Extract FanDuel specific betting data"""
        try:
            # Get game title
            title = await page.title()
            
            # Extract all prop bets
            prop_bets = []
            
            # Look for prop bet sections
            prop_sections = await page.query_selector_all('[data-test-id*="prop"], [class*="prop"]')
            
            for section in prop_sections:
                try:
                    bet_text = await section.inner_text()
                    prop_bets.append(bet_text.strip())
                except:
                    pass
            
            # Extract main betting lines (spread, moneyline, total)
            main_lines = {}
            
            # Spread
            spread_elements = await page.query_selector_all('[aria-label*="spread"], [class*="spread"]')
            if spread_elements:
                spreads = []
                for elem in spread_elements[:2]:  # Get first 2 (home/away)
                    text = await elem.inner_text()
                    spreads.append(text.strip())
                main_lines['spread'] = spreads
            
            # Moneyline
            moneyline_elements = await page.query_selector_all('[aria-label*="moneyline"], [class*="moneyline"]')
            if moneyline_elements:
                moneylines = []
                for elem in moneyline_elements[:2]:
                    text = await elem.inner_text()
                    moneylines.append(text.strip())
                main_lines['moneyline'] = moneylines
            
            # Over/Under
            total_elements = await page.query_selector_all('[aria-label*="total"], [class*="total"], [aria-label*="over"], [aria-label*="under"]')
            if total_elements:
                totals = []
                for elem in total_elements[:2]:
                    text = await elem.inner_text()
                    totals.append(text.strip())
                main_lines['total'] = totals
            
            # Get all betting options as fallback
            all_bets = []
            bet_containers = await page.query_selector_all('[role="button"][aria-label*="-"], [class*="bet-button"], [class*="outcome"]')
            
            for container in bet_containers[:50]:  # Limit to first 50 to avoid too much data
                try:
                    text = await container.inner_text()
                    aria_label = await container.get_attribute('aria-label')
                    
                    bet_info = {
                        'text': text.strip(),
                        'label': aria_label
                    }
                    
                    if bet_info['text']:
                        all_bets.append(bet_info)
                except:
                    pass
            
            return {
                'success': True,
                'platform': 'fanduel',
                'url': url,
                'title': title,
                'main_lines': main_lines,
                'prop_bets': prop_bets,
                'all_bets': all_bets,
                'extracted_at': datetime.now().isoformat(),
                'bet_count': len(all_bets)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'FanDuel extraction error: {str(e)}',
                'url': url
            }
    
    async def _extract_draftkings(self, page, url):
        """Extract DraftKings specific betting data"""
        # Similar structure to FanDuel but with DraftKings-specific selectors
        return await self._extract_generic(page, url)
    
    async def _extract_generic(self, page, url):
        """Generic extraction for any betting site"""
        try:
            title = await page.title()
            
            # Get all text content
            content = await page.inner_text('body')
            
            # Look for odds patterns (e.g., +150, -110, O/U 45.5)
            import re
            odds_pattern = r'[+-]\d{3,4}|O\/U \d+\.?\d*|\d+\.5 [+-]\d{3,4}'
            odds_found = re.findall(odds_pattern, content)
            
            return {
                'success': True,
                'platform': 'generic',
                'url': url,
                'title': title,
                'odds_found': odds_found[:100],  # Limit to first 100 odds
                'content_preview': content[:2000],
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Generic extraction error: {str(e)}',
                'url': url
            }

async def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python extract_betting.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    extractor = BettingExtractor()
    
    print(f"Extracting betting data from: {url}")
    result = await extractor.extract(url)
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    asyncio.run(main())