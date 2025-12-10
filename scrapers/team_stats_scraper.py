from typing import List, Dict, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logger = logging.getLogger(__name__)

class TeamStatsScraper(BaseSofascoreScraper):
    """Scraper dedicated to fetching team statistics and historical data."""
    
    def get_team_form(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Get team's recent match results."""
        endpoint = f"/team/{team_id}/events/last/{limit}"
        
        logger.info(f"Fetching last {limit} matches for team {team_id}")
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            return self._parse_team_form(data['events'], team_id)
        
        return []
    
    def get_team_statistics(self, team_id: int, tournament_id: int, season_id: Optional[int] = None) -> Dict:
        """Get comprehensive team statistics for a tournament/season."""
        if season_id:
            endpoint = f"/team/{team_id}/tournament/{tournament_id}/season/{season_id}/statistics"
        else:
            endpoint = f"/team/{team_id}/unique-tournament/{tournament_id}/season/current/statistics/overall"
        
        logger.info(f"Fetching statistics for team {team_id} in tournament {tournament_id}")
        data = self._make_request(endpoint)
        
        if data and 'statistics' in data:
            return self._parse_team_statistics(data['statistics'])
        
        return {}
    
    def _parse_team_form(self, events: List, team_id: int) -> List[Dict]:
        """Parse team form from events."""
        form = []
        for event in events:
            home_team = event.get('homeTeam', {})
            away_team = event.get('awayTeam', {})
            home_score = event.get('homeScore', {}).get('current', 0)
            away_score = event.get('awayScore', {}).get('current', 0)
            
            is_home = home_team.get('id') == team_id
            team_score = home_score if is_home else away_score
            opponent_score = away_score if is_home else home_score
            
            if team_score > opponent_score:
                result = 'W'
            elif team_score < opponent_score:
                result = 'L'
            else:
                result = 'D'
            
            form_data = {
                'match_id': event.get('id'),
                'date': event.get('startTimestamp'),
                'opponent': away_team.get('name') if is_home else home_team.get('name'),
                'opponent_id': away_team.get('id') if is_home else home_team.get('id'),
                'venue': 'H' if is_home else 'A',
                'team_score': team_score,
                'opponent_score': opponent_score,
                'result': result,
                'total_goals': team_score + opponent_score,
                'tournament': event.get('tournament', {}).get('name'),
            }
            form.append(form_data)
            
        return form
    
    def _parse_team_statistics(self, stats: Dict) -> Dict:
        """Parse team statistics into a clean format."""
        return {
            'matches_played': stats.get('matches', 0),
            'wins': stats.get('wins', 0),
            'draws': stats.get('draws', 0),
            'losses': stats.get('losses', 0),
            'goals_scored': stats.get('goalsScored', 0),
            'goals_conceded': stats.get('goalsConceded', 0),
            'clean_sheets': stats.get('cleanSheets', 0),
            'btts_count': stats.get('bothTeamsScore', 0),
            'avg_goals_scored': stats.get('goalsScored', 0) / max(stats.get('matches', 1), 1),
            'avg_goals_conceded': stats.get('goalsConceded', 0) / max(stats.get('matches', 1), 1),
        }
    
    def calculate_team_metrics(self, form_data: List[Dict]) -> Dict:
        """Calculate betting-relevant metrics from form data."""
        if not form_data:
            return {}
        
        total_matches = len(form_data)
        wins = sum(1 for m in form_data if m['result'] == 'W')
        draws = sum(1 for m in form_data if m['result'] == 'D')
        losses = sum(1 for m in form_data if m['result'] == 'L')
        
        goals_scored = sum(m['team_score'] for m in form_data)
        goals_conceded = sum(m['opponent_score'] for m in form_data)
        
        over_15 = sum(1 for m in form_data if m['total_goals'] > 1.5)
        over_25 = sum(1 for m in form_data if m['total_goals'] > 2.5)
        over_35 = sum(1 for m in form_data if m['total_goals'] > 3.5)
        
        btts = sum(1 for m in form_data if m['team_score'] > 0 and m['opponent_score'] > 0)
        clean_sheets = sum(1 for m in form_data if m['opponent_score'] == 0)
        
        return {
            'total_matches': total_matches,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': (wins / total_matches) * 100,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'avg_goals_scored': goals_scored / total_matches,
            'avg_goals_conceded': goals_conceded / total_matches,
            'over_15_percentage': (over_15 / total_matches) * 100,
            'over_25_percentage': (over_25 / total_matches) * 100,
            'over_35_percentage': (over_35 / total_matches) * 100,
            'btts_percentage': (btts / total_matches) * 100,
            'clean_sheet_percentage': (clean_sheets / total_matches) * 100,
        }

# Test function
def test_team_stats_scraper():
    """Test the team stats scraper independently."""
    scraper = TeamStatsScraper()
    
    # Test with a known team ID (50 is Brentford from your previous test)
    team_id = 50
    
    print(f"\n{'='*50}")
    print(f"Testing Team Stats Scraper")
    print(f"{'='*50}\n")
    
    # Get team form
    form = scraper.get_team_form(team_id, limit=5)
    
    if form:
        print(f"✅ Successfully fetched last {len(form)} matches\n")
        
        # Show match results
        print("Recent Form:")
        for match in form:
            result_symbol = "✅" if match['result'] == 'W' else "❌" if match['result'] == 'L' else "➖"
            print(f"  {result_symbol} {match['result']} - {match['team_score']}-{match['opponent_score']} vs {match['opponent']} ({match['venue']})")
        
        # Calculate and show metrics
        print("\n📊 Calculated Metrics:")
        metrics = scraper.calculate_team_metrics(form)
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Avg Goals Scored: {metrics['avg_goals_scored']:.2f}")
        print(f"  Avg Goals Conceded: {metrics['avg_goals_conceded']:.2f}")
        print(f"  Over 2.5 Goals: {metrics['over_25_percentage']:.1f}%")
        print(f"  BTTS: {metrics['btts_percentage']:.1f}%")
    else:
        print("❌ No form data found")

if __name__ == "__main__":
    test_team_stats_scraper()
