from typing import List, Dict
from datetime import datetime
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamStatsScraper(BaseSofascoreScraper):
    """Scraper for fetching team historical match data."""
    
    def get_team_last_matches(self, team_id: int, limit: int = 10) -> Dict:
        """
        Get team's last N finished matches using events/last endpoint.
        """
        endpoint = f"/team/{team_id}/events/last/0"  # 0 gets recent matches
        
        logger.info(f"Fetching recent matches for team {team_id}")
        data = self._make_request(endpoint)
        
        if not data or 'events' not in data:
            logger.error(f"Failed to fetch data for team {team_id}")
            return None
        
        events = data['events']
        
        if not events:
            return None
        
        # Get team name
        first_event = events[0]
        home_team = first_event.get('homeTeam', {})
        away_team = first_event.get('awayTeam', {})
        team_name = home_team.get('name') if home_team.get('id') == team_id else away_team.get('name')
        
        # Parse and filter only FINISHED matches
        matches = []
        for event in events:
            status = event.get('status', {}).get('type')
            if status == 'finished':
                match_data = self._parse_match(event, team_id)
                if match_data:
                    matches.append(match_data)
        
        # Sort by date (most recent first)
        matches.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'team_id': team_id,
            'team_name': team_name,
            'matches': matches[:limit]
        }
    
    def _parse_match(self, event: Dict, team_id: int) -> Dict:
        """Parse a single match into clean format."""
        home_team = event.get('homeTeam', {})
        away_team = event.get('awayTeam', {})
        home_score = event.get('homeScore', {}).get('current')
        away_score = event.get('awayScore', {}).get('current')
        
        # Skip if no scores available
        if home_score is None or away_score is None:
            return None
        
        # Determine if our team was home or away
        is_home = home_team.get('id') == team_id
        
        if is_home:
            opponent = away_team.get('name')
            opponent_id = away_team.get('id')
            team_score = home_score
            opponent_score = away_score
            venue = 'Home'
        else:
            opponent = home_team.get('name')
            opponent_id = home_team.get('id')
            team_score = away_score
            opponent_score = home_score
            venue = 'Away'
        
        # Determine result
        if team_score > opponent_score:
            result = 'W'
        elif team_score < opponent_score:
            result = 'L'
        else:
            result = 'D'
        
        # Get match date - properly handle timestamp
        timestamp = event.get('startTimestamp')
        if timestamp:
            # Convert Unix timestamp to datetime
            dt = datetime.fromtimestamp(timestamp)
            match_date = dt.strftime('%d.%m.%Y')
            match_year = dt.year
        else:
            match_date = 'Unknown'
            match_year = 0
        
        return {
            'match_id': event.get('id'),
            'date': match_date,
            'timestamp': timestamp,  # Keep for sorting
            'year': match_year,
            'opponent': opponent,
            'opponent_id': opponent_id,
            'venue': venue,
            'team_score': team_score,
            'opponent_score': opponent_score,
            'result': result,
            'tournament': event.get('tournament', {}).get('name', 'Unknown'),
            'tournament_id': event.get('tournament', {}).get('id')
        }
    
    def display_team_data(self, team_data: Dict):
        """Display team historical data in clean format."""
        if not team_data:
            print("❌ No data available")
            return
        
        team_name = team_data['team_name']
        matches = team_data['matches']
        
        print("\n" + "="*80)
        print(f"🏆 TEAM: {team_name.upper()}")
        print(f"📊 Team ID: {team_data['team_id']}")
        print("="*80)
        
        if not matches:
            print("❌ No finished matches found")
            return
        
        print(f"\n📅 LAST {len(matches)} FINISHED MATCHES (Most Recent First):\n")
        
        for i, match in enumerate(matches, 1):
            result_emoji = "✅" if match['result'] == 'W' else "❌" if match['result'] == 'L' else "➖"
            
            print(f"Match {i}: {match['date']} (Year: {match['year']})")
            print(f"  {result_emoji} {match['result']} | {match['team_score']}-{match['opponent_score']} vs {match['opponent']} ({match['venue']})")
            print(f"  Tournament: {match['tournament']}")
            print(f"  Match ID: {match['match_id']}")
            print()


def test_newcastle():
    """Test with Newcastle United (Team ID: 39)."""
    scraper = TeamStatsScraper()
    
    print("\n" + "🔍 TEAM HISTORICAL DATA SCRAPER TEST".center(80))
    print("="*80)
    print("Testing with: Newcastle United (ID: 39)")
    print("Expected: Most recent match should be 06.12.2024 vs Brentford 2-1")
    print("="*80)
    
    team_data = scraper.get_team_last_matches(team_id=39, limit=10)
    scraper.display_team_data(team_data)
    
    print("\n" + "="*80)
    print("✅ Scraper test complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_newcastle()
