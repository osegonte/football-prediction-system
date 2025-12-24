from typing import List, Dict
from datetime import datetime
import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataVerificationScraper(BaseSofascoreScraper):
    """Scraper for collecting and displaying raw match data for manual verification."""
    
    def get_team_last_7_matches(self, team_id: int) -> Dict:
        """
        Get the last 7 matches for a team with raw data.
        Returns team info + list of matches.
        """
        endpoint = f"/team/{team_id}/events/last/7"
        
        logger.info(f"Fetching last 7 matches for team {team_id}")
        data = self._make_request(endpoint)
        
        if not data or 'events' not in data:
            logger.error(f"Failed to fetch data for team {team_id}")
            return None
        
        events = data['events']
        
        # Get team name from first match
        if not events:
            return None
            
        first_event = events[0]
        home_team = first_event.get('homeTeam', {})
        away_team = first_event.get('awayTeam', {})
        
        # Determine which team is ours
        team_name = home_team.get('name') if home_team.get('id') == team_id else away_team.get('name')
        
        # Parse matches
        matches = []
        for event in events[:7]:  # Ensure only 7 matches
            match_data = self._parse_match(event, team_id)
            if match_data:
                matches.append(match_data)
        
        return {
            'team_id': team_id,
            'team_name': team_name,
            'matches': matches
        }
    
    def _parse_match(self, event: Dict, team_id: int) -> Dict:
        """Parse a single match into clean format."""
        home_team = event.get('homeTeam', {})
        away_team = event.get('awayTeam', {})
        home_score = event.get('homeScore', {}).get('current', 0)
        away_score = event.get('awayScore', {}).get('current', 0)
        
        # Determine if our team was home or away
        is_home = home_team.get('id') == team_id
        
        if is_home:
            opponent = away_team.get('name')
            team_score = home_score
            opponent_score = away_score
            venue = 'H'
        else:
            opponent = home_team.get('name')
            team_score = away_score
            opponent_score = home_score
            venue = 'A'
        
        # Determine result
        if team_score > opponent_score:
            result = 'W'
        elif team_score < opponent_score:
            result = 'L'
        else:
            result = 'D'
        
        # Get match date
        timestamp = event.get('startTimestamp')
        match_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else 'Unknown'
        
        return {
            'match_id': event.get('id'),
            'date': match_date,
            'opponent': opponent,
            'venue': venue,
            'team_score': team_score,
            'opponent_score': opponent_score,
            'result': result,
            'tournament': event.get('tournament', {}).get('name', 'Unknown')
        }
    
    def display_team_data(self, team_data: Dict):
        """Display team data in clean, readable format for manual verification."""
        if not team_data:
            print("❌ No data available")
            return
        
        team_name = team_data['team_name']
        matches = team_data['matches']
        
        print("\n" + "="*70)
        print(f"🏆 TEAM: {team_name.upper()}")
        print(f"📊 Team ID: {team_data['team_id']}")
        print("="*70)
        
        if not matches:
            print("❌ No matches found")
            return
        
        print(f"\n📅 LAST {len(matches)} MATCHES:\n")
        
        for i, match in enumerate(matches, 1):
            result_emoji = "✅" if match['result'] == 'W' else "❌" if match['result'] == 'L' else "➖"
            venue_text = "Home" if match['venue'] == 'H' else "Away"
            
            print(f"Match {i}: {match['date']}")
            print(f"  {result_emoji} {match['result']} | vs {match['opponent']} ({venue_text})")
            print(f"  Score: {match['team_score']}-{match['opponent_score']}")
            print(f"  Tournament: {match['tournament']}")
            print()


def test_three_random_teams():
    """Test scraper with 3 random teams for verification."""
    scraper = DataVerificationScraper()
    
    # Test with 3 well-known team IDs
    # Arsenal: 42, Liverpool: 44, Man City: 17
    test_teams = [
        42,   # Arsenal
        44,   # Liverpool  
        17    # Man City
    ]
    
    print("\n" + "🔍 FOOTBALL DATA VERIFICATION SYSTEM".center(70))
    print("=" * 70)
    print("Fetching last 7 matches for 3 teams...")
    print("=" * 70)
    
    for team_id in test_teams:
        team_data = scraper.get_team_last_7_matches(team_id)
        scraper.display_team_data(team_data)
        print("\n" + "-"*70 + "\n")


if __name__ == "__main__":
    test_three_random_teams()
