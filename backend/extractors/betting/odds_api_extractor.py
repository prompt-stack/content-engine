#!/usr/bin/env python3
"""
Prop Bets Extractor using The Odds API
Fetches comprehensive betting data including prop bets from multiple sportsbooks
"""

import requests
import json
from datetime import datetime

class OddsAPIExtractor:
    def __init__(self, api_key=None):
        """
        Initialize with API key from https://the-odds-api.com/
        Free tier: 500 requests/month
        """
        self.api_key = api_key or "2af80eec74761181165b4eb50efcc0c8"
        self.base_url = "https://api.the-odds-api.com/v4"
        
    def get_prop_bets(self, sport='americanfootball_nfl', game_id=None):
        """
        Get prop bets for specific sport or game
        
        Sports keys: americanfootball_nfl, basketball_nba, baseball_mlb, etc.
        """
        
        # Get list of games first
        if not game_id:
            games = self.get_upcoming_games(sport)
            if games:
                game_id = games[0]['id']  # Get first game
        
        # Fetch prop markets
        prop_markets = [
            'player_pass_tds',
            'player_pass_yds', 
            'player_rush_yds',
            'player_receptions',
            'player_reception_yds',
            'player_anytime_td',
            'player_1st_td',
            'player_last_td',
            'player_rush_attempts',
            'player_assists',
            'player_points',
            'player_rebounds',
            'player_threes',
            'player_shots',
            'player_hits',
            'player_home_runs',
            'player_strikeouts'
        ]
        
        all_props = {}
        
        for market in prop_markets:
            url = f"{self.base_url}/sports/{sport}/events/{game_id}/odds"
            
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': market,
                'oddsFormat': 'american',
                'bookmakers': 'fanduel,draftkings,betmgm,caesars'
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('bookmakers'):
                        all_props[market] = data
                        print(f"✓ Found {market} props")
            except Exception as e:
                print(f"✗ Error fetching {market}: {e}")
        
        return all_props
    
    def get_upcoming_games(self, sport='americanfootball_nfl'):
        """Get list of upcoming games"""
        url = f"{self.base_url}/sports/{sport}/odds"
        
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'bookmakers': 'fanduel'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    
    def extract_fanduel_props(self, props_data):
        """Extract and format FanDuel prop bets"""
        formatted_props = []
        
        for market_type, market_data in props_data.items():
            for bookmaker in market_data.get('bookmakers', []):
                if bookmaker['key'] == 'fanduel':
                    for market in bookmaker.get('markets', []):
                        for outcome in market.get('outcomes', []):
                            prop = {
                                'type': market_type,
                                'player': outcome.get('description', outcome.get('name')),
                                'line': outcome.get('point'),
                                'over_odds': None,
                                'under_odds': None,
                                'price': outcome.get('price')
                            }
                            
                            # Handle over/under props
                            if 'name' in outcome:
                                if outcome['name'].lower() == 'over':
                                    prop['over_odds'] = outcome['price']
                                elif outcome['name'].lower() == 'under':
                                    prop['under_odds'] = outcome['price']
                            
                            formatted_props.append(prop)
        
        return formatted_props

# Example usage
if __name__ == "__main__":
    # Using your API key
    extractor = OddsAPIExtractor()
    
    # Get NFL prop bets
    props = extractor.get_prop_bets('americanfootball_nfl')
    
    # Extract FanDuel specific props
    fanduel_props = extractor.extract_fanduel_props(props)
    
    print(json.dumps(fanduel_props, indent=2))