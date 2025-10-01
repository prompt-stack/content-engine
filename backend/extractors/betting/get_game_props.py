#!/usr/bin/env python3
"""
Get all prop bets for Bengals vs Jaguars game
Using The Odds API with your API key
"""

import requests
import json
from datetime import datetime

API_KEY = "2af80eec74761181165b4eb50efcc0c8"
BASE_URL = "https://api.the-odds-api.com/v4"

def get_nfl_games():
    """Get today's NFL games"""
    url = f"{BASE_URL}/sports/americanfootball_nfl/events"
    params = {
        'apiKey': API_KEY,
        'dateFormat': 'iso'
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        games = response.json()
        # Find Bengals vs Jaguars game
        for game in games:
            home = game.get('home_team', '').lower()
            away = game.get('away_team', '').lower()
            if ('bengals' in home or 'cincinnati' in home) and ('jaguars' in away or 'jacksonville' in away):
                return game
            elif ('jaguars' in home or 'jacksonville' in home) and ('bengals' in away or 'cincinnati' in away):
                return game
    return None

def get_game_props(event_id):
    """Get all available prop bets for a specific game"""
    
    # All available prop markets
    prop_markets = [
        # Player props
        'player_pass_tds',
        'player_pass_yds',
        'player_pass_completions',
        'player_pass_attempts',
        'player_pass_interceptions',
        'player_pass_longest_completion',
        'player_rush_yds',
        'player_rush_attempts',
        'player_rush_longest',
        'player_receptions',
        'player_reception_yds',
        'player_reception_longest',
        'player_kicking_points',
        'player_field_goals',
        'player_tackles_assists',
        'player_1st_td',
        'player_last_td',
        'player_anytime_td',
        
        # Game props  
        'totals',
        'spreads',
        'h2h',
        'btts',  # Both teams to score
        'draw_no_bet'
    ]
    
    all_props = {}
    print(f"\nFetching props for Event ID: {event_id}")
    print("=" * 50)
    
    for market in prop_markets:
        url = f"{BASE_URL}/sports/americanfootball_nfl/events/{event_id}/odds"
        params = {
            'apiKey': API_KEY,
            'regions': 'us',
            'markets': market,
            'bookmakers': 'fanduel,draftkings,betmgm,caesars,pointsbetus'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('bookmakers'):
                    # Extract props from each bookmaker
                    for bookmaker in data['bookmakers']:
                        book_name = bookmaker['title']
                        if book_name not in all_props:
                            all_props[book_name] = {}
                        
                        for market_data in bookmaker.get('markets', []):
                            market_key = market_data.get('key', market)
                            outcomes = market_data.get('outcomes', [])
                            
                            if outcomes:
                                all_props[book_name][market_key] = outcomes
                                print(f"✓ Found {len(outcomes)} {market} props from {book_name}")
        except Exception as e:
            print(f"Error fetching {market}: {e}")
    
    return all_props

def format_props(props_data):
    """Format props for easy reading"""
    print("\n" + "=" * 60)
    print("PROP BETS FOR BENGALS VS JAGUARS")
    print("=" * 60)
    
    for bookmaker, markets in props_data.items():
        print(f"\n📚 {bookmaker}")
        print("-" * 40)
        
        for market, outcomes in markets.items():
            # Group by player for player props
            if 'player' in market:
                players = {}
                for outcome in outcomes:
                    player = outcome.get('description', outcome.get('name', 'Unknown'))
                    if player not in players:
                        players[player] = []
                    players[player].append({
                        'type': outcome.get('name', ''),
                        'point': outcome.get('point', ''),
                        'price': outcome.get('price', '')
                    })
                
                print(f"\n  {market.replace('_', ' ').title()}:")
                for player, props in players.items():
                    print(f"    • {player}")
                    for prop in props:
                        if prop['point']:
                            print(f"      {prop['type']}: {prop['point']} ({prop['price']:+.0f})")
                        else:
                            print(f"      {prop['price']:+.0f}")
            else:
                # Regular game props
                print(f"\n  {market.replace('_', ' ').title()}:")
                for outcome in outcomes[:5]:  # Limit display
                    name = outcome.get('name', '')
                    price = outcome.get('price', '')
                    point = outcome.get('point', '')
                    if point:
                        print(f"    • {name}: {point} ({price:+.0f})")
                    else:
                        print(f"    • {name}: {price:+.0f}")

def main():
    print("🏈 Getting Bengals vs Jaguars prop bets...")
    
    # Find the game
    game = get_nfl_games()
    if not game:
        print("❌ Could not find Bengals vs Jaguars game today")
        return
    
    print(f"\n✓ Found game: {game['away_team']} @ {game['home_team']}")
    print(f"  Start time: {game['commence_time']}")
    
    # Get all props
    props = get_game_props(game['id'])
    
    # Format and display
    if props:
        format_props(props)
        
        # Save to file
        with open('bengals_jags_props.json', 'w') as f:
            json.dump(props, f, indent=2)
        print(f"\n✓ Full props data saved to bengals_jags_props.json")
    else:
        print("❌ No props found")
    
    # Show API usage
    print(f"\n📊 API Usage: Check your remaining quota at https://the-odds-api.com/account/")

if __name__ == "__main__":
    main()