from datetime import datetime
from typing import List, Dict
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import base_scraper
from scrapers.base_scraper import BaseSofascoreScraper

logger = logging.getLogger(__name__)

class FixturesScraper(BaseSofascoreScraper):
    """Scraper dedicated to fetching fixture data."""
    
    def get_fixtures_by_date(self, date: datetime) -> List[Dict]:
        """Get all football fixtures for a specific date."""
        date_str = date.strftime('%Y-%m-%d')
        endpoint = f"/sport/football/scheduled-events/{date_str}"
        
        logger.info(f"Fetching fixtures for {date_str}")
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            fixtures = []
            for event in data['events']:
                # Extract only essential fixture information
                fixture = {
                    'match_id': event.get('id'),
                    'home_team': event.get('homeTeam', {}).get('name'),
                    'away_team': event.get('awayTeam', {}).get('name'),
                    'home_team_id': event.get('homeTeam', {}).get('id'),
                    'away_team_id': event.get('awayTeam', {}).get('id'),
                    'tournament': event.get('tournament', {}).get('name'),
                    'tournament_id': event.get('tournament', {}).get('id'),
                    'country': event.get('tournament', {}).get('category', {}).get('name'),
                    'start_timestamp': event.get('startTimestamp'),
                    'status': event.get('status', {}).get('type'),
                    'home_score': event.get('homeScore', {}).get('current'),
                    'away_score': event.get('awayScore', {}).get('current'),
                }
                fixtures.append(fixture)
                
            logger.info(f"Successfully fetched {len(fixtures)} fixtures")
            return fixtures
        
        logger.warning(f"No fixtures found for {date_str}")
        return []
    
    def get_fixtures_by_tournament(self, tournament_id: int, season_id: int = None) -> List[Dict]:
        """Get fixtures for a specific tournament."""
        endpoint = f"/tournament/{tournament_id}/season/{season_id}/events" if season_id else f"/tournament/{tournament_id}/events/next/0"
        
        logger.info(f"Fetching fixtures for tournament {tournament_id}")
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            return self._parse_events(data['events'])
        
        return []
    
    def _parse_events(self, events: List) -> List[Dict]:
        """Helper method to parse event data consistently."""
        fixtures = []
        for event in events:
            fixture = {
                'match_id': event.get('id'),
                'home_team': event.get('homeTeam', {}).get('name'),
                'away_team': event.get('awayTeam', {}).get('name'),
                'home_team_id': event.get('homeTeam', {}).get('id'),
                'away_team_id': event.get('awayTeam', {}).get('id'),
                'start_timestamp': event.get('startTimestamp'),
                'status': event.get('status', {}).get('type'),
            }
            fixtures.append(fixture)
        return fixtures

# Test function
def test_fixtures_scraper():
    """Test the fixtures scraper independently."""
    from datetime import timedelta
    
    scraper = FixturesScraper()
    
    # Test today's fixtures
    today = datetime.now()
    print(f"\n{'='*50}")
    print(f"Testing Fixtures Scraper - {today.strftime('%Y-%m-%d')}")
    print(f"{'='*50}\n")
    
    fixtures = scraper.get_fixtures_by_date(today)
    
    if fixtures:
        print(f"✅ Successfully fetched {len(fixtures)} fixtures\n")
        
        # Show first 3 fixtures with details
        for i, fixture in enumerate(fixtures[:3], 1):
            print(f"Match {i}:")
            print(f"  {fixture['home_team']} vs {fixture['away_team']}")
            print(f"  Tournament: {fixture['tournament']} ({fixture['country']})")
            print(f"  Match ID: {fixture['match_id']}")
            print(f"  Status: {fixture['status']}")
            print()
    else:
        print("❌ No fixtures found")
    
    # Test tomorrow's fixtures
    tomorrow = today + timedelta(days=1)
    print(f"\nFetching tomorrow's fixtures ({tomorrow.strftime('%Y-%m-%d')})...")
    tomorrow_fixtures = scraper.get_fixtures_by_date(tomorrow)
    print(f"Found {len(tomorrow_fixtures)} fixtures for tomorrow")

if __name__ == "__main__":
    test_fixtures_scraper()
