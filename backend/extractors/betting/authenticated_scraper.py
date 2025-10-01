#!/usr/bin/env python3
"""
Authenticated FanDuel Scraper
Logs in and extracts prop bets after authentication
"""

import asyncio
import json
from playwright.async_api import async_playwright
import time

class AuthenticatedFanDuelScraper:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.props_data = []
    
    async def login_and_extract(self, game_url):
        """Login to FanDuel and extract prop bets"""
        
        async with async_playwright() as p:
            # Launch browser in non-headless mode for initial setup
            browser = await p.chromium.launch(
                headless=False,  # Set to True after testing
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to FanDuel
                await page.goto('https://sportsbook.fanduel.com', wait_until='domcontentloaded')
                await page.wait_for_timeout(3000)
                
                # Look for login button
                login_btn = await page.query_selector('[aria-label*="Log In"], button:has-text("Log In")')
                if login_btn:
                    await login_btn.click()
                    await page.wait_for_timeout(2000)
                    
                    # Enter credentials if provided
                    if self.username and self.password:
                        await page.fill('input[name="email"], input[type="email"]', self.username)
                        await page.fill('input[name="password"], input[type="password"]', self.password)
                        await page.click('button[type="submit"]')
                        await page.wait_for_timeout(5000)
                
                # Navigate to specific game
                await page.goto(game_url, wait_until='networkidle')
                await page.wait_for_timeout(5000)
                
                # Extract prop bets
                props = await self.extract_props(page)
                
                await browser.close()
                return props
                
            except Exception as e:
                await browser.close()
                return {'error': str(e)}
    
    async def extract_props(self, page):
        """Extract all prop bets from the page"""
        props = {
            'player_props': [],
            'game_props': [],
            'team_props': []
        }
        
        # Click on Props tab if available
        props_tab = await page.query_selector('[aria-label*="Props"], button:has-text("Props"), [data-test*="props"]')
        if props_tab:
            await props_tab.click()
            await page.wait_for_timeout(2000)
        
        # Extract all prop categories
        prop_categories = await page.query_selector_all('[role="tabpanel"] [role="button"], [class*="MarketCard"]')
        
        for category in prop_categories:
            try:
                category_text = await category.inner_text()
                
                # Look for player props
                if any(keyword in category_text.lower() for keyword in ['passing', 'rushing', 'receiving', 'touchdown', 'anytime']):
                    # Click to expand
                    await category.click()
                    await page.wait_for_timeout(1000)
                    
                    # Extract betting options
                    options = await page.query_selector_all('[aria-label*="odds"], [class*="OutcomeButton"]')
                    
                    for option in options:
                        try:
                            label = await option.get_attribute('aria-label')
                            text = await option.inner_text()
                            
                            if label or text:
                                props['player_props'].append({
                                    'category': category_text,
                                    'label': label,
                                    'text': text,
                                    'timestamp': time.time()
                                })
                        except:
                            pass
                            
            except Exception as e:
                print(f"Error extracting category: {e}")
        
        return props
    
    async def extract_all_props_sections(self, page):
        """Extract props from all available sections"""
        
        # Common prop sections to look for
        sections = [
            'Popular',
            'Touchdown Scorer',
            'Passing Props',
            'Rushing Props', 
            'Receiving Props',
            'Defense/Special Teams',
            'Game Props',
            'Team Props',
            'Quarter Props',
            'Half Props',
            'Drive Props'
        ]
        
        all_props = {}
        
        for section in sections:
            # Try to find and click section
            section_elem = await page.query_selector(f'button:has-text("{section}"), [aria-label*="{section}"]')
            if section_elem:
                await section_elem.click()
                await page.wait_for_timeout(1500)
                
                # Extract props from this section
                props = await page.query_selector_all('[class*="OutcomeButton"], [role="button"][aria-label*="-"]')
                
                section_props = []
                for prop in props[:20]:  # Limit to avoid too much data
                    try:
                        text = await prop.inner_text()
                        aria = await prop.get_attribute('aria-label')
                        section_props.append({
                            'text': text,
                            'aria_label': aria
                        })
                    except:
                        pass
                
                if section_props:
                    all_props[section] = section_props
        
        return all_props

# Example usage
if __name__ == "__main__":
    scraper = AuthenticatedFanDuelScraper()
    
    # You can either:
    # 1. Run without credentials and manually log in when browser opens
    # 2. Provide credentials (be careful with security)
    
    game_url = "https://sportsbook.fanduel.com/football/nfl/jacksonville-jaguars-@-cincinnati-bengals-34662303"
    
    asyncio.run(scraper.login_and_extract(game_url))