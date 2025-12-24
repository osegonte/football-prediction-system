from typing import Dict, List, Optional
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSofascoreScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerStatsScraper(BaseSofascoreScraper):
    """Scraper for fetching player lineups and individual statistics."""
    
    def get_match_lineups(self, match_id: int) -> Dict:
        """
        Get lineups and player statistics for a match.
        Returns starting XI, bench, and missing players for both teams.
        """
        endpoint = f"/event/{match_id}/lineups"
        
        logger.info(f"Fetching lineups for match {match_id}")
        data = self._make_request(endpoint)
        
        if not data:
            logger.error(f"No lineup data found for match {match_id}")
            return None
        
        home_team = data.get('home', {})
        away_team = data.get('away', {})
        
        lineups = {
            'match_id': match_id,
            'home': self._parse_team_lineup(home_team),
            'away': self._parse_team_lineup(away_team)
        }
        
        return lineups
    
    def _parse_team_lineup(self, team_data: Dict) -> Dict:
        """Parse lineup data for one team."""
        team_info = {
            'team_name': team_data.get('teamName', 'Unknown'),
            'team_id': team_data.get('teamId'),
            'formation': team_data.get('formation'),
            'starting_xi': [],
            'substitutes': [],
            'missing_players': []
        }
        
        # Parse starting XI
        for player in team_data.get('players', []):
            player_info = self._parse_player(player)
            if player_info:
                team_info['starting_xi'].append(player_info)
        
        # Parse substitutes
        for player in team_data.get('substitutes', []):
            player_info = self._parse_player(player)
            if player_info:
                team_info['substitutes'].append(player_info)
        
        # Parse missing players (injured/suspended)
        for player in team_data.get('missingPlayers', []):
            missing_info = {
                'name': player.get('player', {}).get('name'),
                'player_id': player.get('player', {}).get('id'),
                'reason': str(player.get('reason', 'Unknown')),
                'position': player.get('player', {}).get('position')
            }
            team_info['missing_players'].append(missing_info)
        
        return team_info
    
    def _parse_player(self, player_data: Dict) -> Dict:
        """Parse individual player data."""
        player = player_data.get('player', {})
        
        player_info = {
            'name': player.get('name'),
            'player_id': player.get('id'),
            'position': player.get('position'),
            'jersey_number': player.get('jerseyNumber'),
            'shirt_number': player_data.get('shirtNumber'),
            'substitute': player_data.get('substitute', False),
            'rating': player_data.get('statistics', {}).get('rating'),
            'minutes_played': player_data.get('statistics', {}).get('minutesPlayed'),
            'goals': player_data.get('statistics', {}).get('goals'),
            'assists': player_data.get('statistics', {}).get('goalAssist'),
            'total_shots': player_data.get('statistics', {}).get('totalShots'),
            'accurate_passes': player_data.get('statistics', {}).get('accuratePasses'),
            'total_passes': player_data.get('statistics', {}).get('totalPasses'),
            'tackles': player_data.get('statistics', {}).get('tackles'),
            'interceptions': player_data.get('statistics', {}).get('interceptions'),
            'duels_won': player_data.get('statistics', {}).get('duelsWon'),
            'duels_total': player_data.get('statistics', {}).get('duelLost'),
            'fouls_committed': player_data.get('statistics', {}).get('foulsCommitted'),
            'was_fouled': player_data.get('statistics', {}).get('wasFouled'),
            'yellow_cards': player_data.get('statistics', {}).get('yellowCards', 0),
            'red_cards': player_data.get('statistics', {}).get('redCards', 0)
        }
        
        return player_info
    
    def display_lineups(self, lineup_data: Dict):
        """Display lineups in clean format."""
        if not lineup_data:
            print("❌ No lineup data available")
            return
        
        match_id = lineup_data['match_id']
        home = lineup_data.get('home', {})
        away = lineup_data.get('away', {})
        
        print("\n" + "="*80)
        print(f"👥 MATCH LINEUPS")
        print(f"Match ID: {match_id}")
        print("="*80)
        
        # Display Home Team
        self._display_team_lineup(home, "HOME")
        
        print("\n" + "-"*80 + "\n")
        
        # Display Away Team
        self._display_team_lineup(away, "AWAY")
    
    def _display_team_lineup(self, team: Dict, team_type: str):
        """Display lineup for one team."""
        if not team:
            print(f"❌ No {team_type} team data")
            return
        
        print(f"\n🏠 {team_type} TEAM: {team['team_name'].upper()}")
        print(f"Formation: {team.get('formation', 'Unknown')}")
        
        # Starting XI
        print(f"\n⚽ STARTING XI ({len(team['starting_xi'])} players):")
        print("-" * 80)
        for i, player in enumerate(team['starting_xi'], 1):
            rating = f"{player['rating']:.1f}" if player['rating'] else "N/A"
            minutes = player['minutes_played'] if player['minutes_played'] else "N/A"
            goals = player['goals'] if player['goals'] else 0
            assists = player['assists'] if player['assists'] else 0
            
            print(f"{i:2d}. {player['name']:25s} | Pos: {player['position']:3s} | "
                  f"#: {player['jersey_number'] or 'N/A':>3} | Rating: {rating:>4} | "
                  f"Min: {minutes:>3} | G:{goals} A:{assists}")
        
        # Substitutes
        if team['substitutes']:
            print(f"\n🪑 SUBSTITUTES ({len(team['substitutes'])} players):")
            print("-" * 80)
            for i, player in enumerate(team['substitutes'], 1):
                rating = f"{player['rating']:.1f}" if player['rating'] else "N/A"
                minutes = player['minutes_played'] if player['minutes_played'] else 0
                
                print(f"{i:2d}. {player['name']:25s} | Pos: {player['position']:3s} | "
                      f"#: {player['jersey_number'] or 'N/A':>3} | Rating: {rating:>4} | "
                      f"Min: {minutes:>3}")
        
        # Missing Players
        if team['missing_players']:
            print(f"\n🚑 MISSING PLAYERS ({len(team['missing_players'])} players):")
            print("-" * 80)
            for i, player in enumerate(team['missing_players'], 1):
                print(f"{i:2d}. {player['name']:25s} | Reason: {player['reason']} | Pos: {player['position']}")


def test_player_stats():
    """Test player stats scraper with a finished match."""
    import sys
    sys.path.append('.')
    
    from scrapers.team_stats_scraper import TeamStatsScraper
    
    # Get Newcastle's recent match
    team_scraper = TeamStatsScraper()
    team_data = team_scraper.get_team_last_matches(team_id=39, limit=1)
    
    if not team_data or not team_data['matches']:
        print("❌ Could not fetch team data")
        return
    
    recent_match = team_data['matches'][0]
    match_id = recent_match['match_id']
    
    print("\n" + "🔍 PLAYER STATS SCRAPER TEST".center(80))
    print("="*80)
    print(f"Testing with Newcastle's most recent match:")
    print(f"Date: {recent_match['date']}")
    print(f"Opponent: {recent_match['opponent']}")
    print(f"Score: {recent_match['team_score']}-{recent_match['opponent_score']}")
    print(f"Match ID: {match_id}")
    print("="*80)
    
    # Get lineups and player stats
    player_scraper = PlayerStatsScraper()
    lineups = player_scraper.get_match_lineups(match_id)
    player_scraper.display_lineups(lineups)
    
    print("\n" + "="*80)
    print("✅ Player stats scraper test complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_player_stats()
