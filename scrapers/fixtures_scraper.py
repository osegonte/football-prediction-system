from datetime import datetime
from typing import List, Dict
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixturesScraper(BaseSofascoreScraper):
    """Scraper for fetching daily fixtures."""
    
    def get_fixtures_by_date(self, date: datetime) -> List[Dict]:
        """Get all football fixtures for a specific date."""
        date_str = date.strftime('%Y-%m-%d')
        endpoint = f"/sport/football/scheduled-events/{date_str}"
        
        logger.info(f"Fetching fixtures for {date_str}")
        data = self._make_request(endpoint)
        
        if not data or 'events' not in data:
            logger.error(f"No fixtures found for {date_str}")
            return []
        
        fixtures = []
        for event in data['events']:
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
        
        logger.info(f"Found {len(fixtures)} fixtures")
        return fixtures
    
    def display_fixtures(self, fixtures: List[Dict]):
        """Display fixtures in clean format."""
        if not fixtures:
            print("❌ No fixtures found")
            return
        
        print("\n" + "="*80)
        print(f"📅 FIXTURES - {len(fixtures)} matches found")
        print("="*80 + "\n")
        
        # Group by tournament
        tournaments = {}
        for fixture in fixtures:
            tournament = fixture['tournament']
            if tournament not in tournaments:
                tournaments[tournament] = []
            tournaments[tournament].append(fixture)
        
        for tournament, matches in tournaments.items():
            print(f"\n🏆 {tournament.upper()}")
            print("-" * 80)
            
            for match in matches:
                # Format time
                if match['start_timestamp']:
                    match_time = datetime.fromtimestamp(match['start_timestamp']).strftime('%H:%M')
                else:
                    match_time = "TBD"
                
                # Format score if live
                if match['status'] == 'inprogress':
                    score = f"{match['home_score']}-{match['away_score']} ⚽ LIVE"
                elif match['status'] == 'finished':
                    score = f"{match['home_score']}-{match['away_score']} ✅ FT"
                else:
                    score = "vs"
                
                print(f"  {match_time} | {match['home_team']} {score} {match['away_team']}")
                print(f"         Match ID: {match['match_id']} | Home ID: {match['home_team_id']} | Away ID: {match['away_team_id']}")
            print()


def test_today_fixtures():
    """Test fetching today's fixtures."""
    scraper = FixturesScraper()
    
    today = datetime.now()
    
    print("\n" + "🔍 FIXTURES SCRAPER TEST".center(80))
    print("="*80)
    print(f"Date: {today.strftime('%Y-%m-%d')}")
    print("="*80)
    
    fixtures = scraper.get_fixtures_by_date(today)
    scraper.display_fixtures(fixtures)
    
    # Show summary
    print("\n" + "="*80)
    print(f"✅ Total fixtures scraped: {len(fixtures)}")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_today_fixtures()
