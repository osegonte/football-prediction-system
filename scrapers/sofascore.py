import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SofascoreScraper:
    """
    Production-ready Sofascore scraper using their JSON API endpoints.
    """
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper with configurable delay between requests.
        
        Args:
            delay: Seconds to wait between requests (default 1.0)
        """
        self.base_url = "https://api.sofascore.com/api/v1"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sofascore.com/',
            'Cache-Control': 'no-cache',
        })
        
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """
        Make a request with error handling and retry logic.
        """
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Rate limited, waiting {self.delay * 3} seconds...")
                    time.sleep(self.delay * 3)
                else:
                    logger.error(f"Request failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.delay * 2)
                    
        return None
    
    def get_fixtures_by_date(self, date: datetime) -> List[dict]:
        """
        Get all football fixtures for a specific date.
        """
        date_str = date.strftime('%Y-%m-%d')
        endpoint = f"/sport/football/scheduled-events/{date_str}"
        
        logger.info(f"Fetching fixtures for {date_str}")
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            fixtures = []
            for event in data['events']:
                fixture = {
                    'id': event.get('id'),
                    'home_team': event.get('homeTeam', {}).get('name'),
                    'away_team': event.get('awayTeam', {}).get('name'),
                    'home_team_id': event.get('homeTeam', {}).get('id'),
                    'away_team_id': event.get('awayTeam', {}).get('id'),
                    'tournament': event.get('tournament', {}).get('name'),
                    'tournament_id': event.get('tournament', {}).get('id'),
                    'start_time': event.get('startTimestamp'),
                    'status': event.get('status', {}).get('description'),
                }
                fixtures.append(fixture)
                
            logger.info(f"Found {len(fixtures)} fixtures")
            return fixtures
        
        return []
    
    def get_team_form(self, team_id: int, limit: int = 10) -> List[dict]:
        """
        Get team's recent form (last N matches).
        """
        endpoint = f"/team/{team_id}/events/last/{limit}"
        
        logger.info(f"Fetching last {limit} matches for team {team_id}")
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            form = []
            for event in data['events']:
                home_team = event.get('homeTeam', {})
                away_team = event.get('awayTeam', {})
                home_score = event.get('homeScore', {}).get('current', 0)
                away_score = event.get('awayScore', {}).get('current', 0)
                
                is_home = home_team.get('id') == team_id
                team_score = home_score if is_home else away_score
                opponent_score = away_score if is_home else home_score
                
                result = 'W' if team_score > opponent_score else 'L' if team_score < opponent_score else 'D'
                
                form.append({
                    'date': event.get('startTimestamp'),
                    'opponent': away_team.get('name') if is_home else home_team.get('name'),
                    'home_away': 'H' if is_home else 'A',
                    'score': f"{team_score}-{opponent_score}",
                    'result': result,
                    'goals_for': team_score,
                    'goals_against': opponent_score,
                    'total_goals': team_score + opponent_score
                })
                
            return form
            
        return []
    
    def get_match_statistics(self, match_id: int) -> dict:
        """
        Get detailed statistics for a specific match.
        """
        endpoint = f"/event/{match_id}/statistics"
        
        logger.info(f"Fetching statistics for match {match_id}")
        data = self._make_request(endpoint)
        
        if data and 'statistics' in data:
            stats = {}
            for period in data['statistics']:
                period_name = period.get('period')
                if period_name == 'ALL':
                    for group in period.get('groups', []):
                        group_name = group.get('groupName')
                        for stat_item in group.get('statisticsItems', []):
                            name = stat_item.get('name')
                            home_val = stat_item.get('home')
                            away_val = stat_item.get('away')
                            stats[f"{name}_home"] = home_val
                            stats[f"{name}_away"] = away_val
            return stats
        
        return {}

# Test function
def test_scraper():
    """Test the Sofascore scraper with today's fixtures."""
    scraper = SofascoreScraper()
    
    # Get today's fixtures
    today = datetime.now()
    fixtures = scraper.get_fixtures_by_date(today)
    
    print(f"\n=== Today's Fixtures ({today.strftime('%Y-%m-%d')}) ===")
    print(f"Found {len(fixtures)} matches\n")
    
    # Show first 5 fixtures
    for fixture in fixtures[:5]:
        print(f"{fixture['home_team']} vs {fixture['away_team']}")
        print(f"  Tournament: {fixture['tournament']}")
        print(f"  Match ID: {fixture['id']}")
        print()
    
    # If we have fixtures, test getting team form for the first match
    if fixtures:
        first_fixture = fixtures[0]
        home_team_id = first_fixture['home_team_id']
        
        print(f"\n=== Form for {first_fixture['home_team']} ===")
        form = scraper.get_team_form(home_team_id, limit=5)
        
        for match in form:
            print(f"  {match['result']} - {match['score']} vs {match['opponent']} ({match['home_away']})")

if __name__ == "__main__":
    test_scraper()
