"""
Football Data Collector - PROPER 4-PHASE COLLECTION
Phase 1: ALL Fixtures
Phase 2: ALL Team History
Phase 3: ALL Match Stats (finished only)
Phase 4: ALL Player Stats (finished only)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging FIRST
import logging
os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler('logs/collector.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.root.handlers = []
logging.root.addHandler(file_handler)
logging.root.setLevel(logging.DEBUG)

from datetime import datetime, timedelta
import time
from rich.live import Live
from rich.console import Console

from display import terminal_ui
from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection

console = Console()
logger = logging.getLogger(__name__)


# Helper functions for data processing
def normalize_column_name(name):
    """Normalize column names to snake_case"""
    import re
    # Convert camelCase to snake_case
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()


def filter_to_existing_columns(data, existing_columns):
    """Filter data dict to only include columns that exist in the table"""
    filtered_data = {k: v for k, v in data.items() if k in existing_columns}
    missing_columns = set(data.keys()) - set(existing_columns)
    return filtered_data, missing_columns


class DataCollector:
    """4-Phase Data Collector"""
    
    def __init__(self):
        self.mode = 'comprehensive'
        self.start_time = datetime.now()
        
        # Stats tracking
        self.cumulative = {
            'fixtures': 0,
            'team_matches': 0,
            'match_stats': 0,
            'player_stats': 0,
            'dates_processed': 0,
            'dates_failed': 0
        }
        
        self.daily = {
            'fixtures': 0,
            'team_matches': 0,
            'match_stats': 0,
            'player_stats': 0
        }
        
        # Current activity tracking for UI
        self.current_activity = {
            'phase': 1,
            'fixtures': {'current': '', 'total': 0, 'done': 0},
            'teams': {'current': '', 'total': 0, 'done': 0},
            'match_stats': {'current': '', 'total': 0, 'done': 0},
            'player_stats': {'current': '', 'total': 0, 'done': 0}
        }
        
        # Initialize scrapers
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        
        # Get match_statistics columns
        with get_connection() as db:
            db.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'match_statistics'
            """)
            self.match_stats_columns = [row[0] for row in db.fetchall()]
    
    def get_runtime(self):
        """Get runtime as timedelta"""
        return datetime.now() - self.start_time
    
    def run_comprehensive(self):
        """Run 4-phase comprehensive collection"""
        terminal_ui.show_startup_banner(self.mode)
        time.sleep(2)
        
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        total_days = (end_date - start_date).days + 1
        
        console = Console()
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            
            # ========== PHASE 1: COLLECT ALL FIXTURES ==========
            terminal_ui.add_activity("=== PHASE 1: Collecting ALL Fixtures ===")
            self.current_activity['phase'] = 1
            self.current_activity['fixtures']['total'] = total_days
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                self.current_activity['fixtures']['current'] = date_str
                
                dashboard = terminal_ui.create_dashboard(
                    self.cumulative, self.daily, self.get_runtime(),
                    self.current_activity, total_days
                )
                live.update(dashboard)
                
                try:
                    terminal_ui.add_activity(f"Fetching fixtures: {date_str}")
                    fixtures = self.coordinator.scrape_daily_fixtures(current_date)
                    
                    if fixtures:
                        self.cumulative['fixtures'] += len(fixtures)
                        self.daily['fixtures'] += len(fixtures)
                        terminal_ui.add_activity(f"  ✓ {len(fixtures)} fixtures")
                    else:
                        terminal_ui.add_activity(f"  - No fixtures for {date_str}")
                    
                    self.current_activity['fixtures']['done'] += 1
                    
                except Exception as e:
                    logger.error(f"Error fetching fixtures for {date_str}: {e}")
                    terminal_ui.add_activity(f"  ✗ ERROR: {str(e)[:40]}")
                
                current_date += timedelta(days=1)
                time.sleep(0.5)
            
            terminal_ui.add_activity(f"✓ PHASE 1 COMPLETE: {self.cumulative['fixtures']} fixtures")
            
            # ========== PHASE 2: COLLECT ALL TEAM HISTORY ==========
            terminal_ui.add_activity("=== PHASE 2: Collecting Team History ===")
            self.current_activity['phase'] = 2
            
            # Get all unique teams
            with get_connection() as db:
                db.execute("""
                    SELECT DISTINCT team_id, team_name FROM (
                        SELECT home_team_id as team_id, home_team_name as team_name FROM fixtures
                        UNION
                        SELECT away_team_id as team_id, away_team_name as team_name FROM fixtures
                    ) teams ORDER BY team_id
                """)
                all_teams = db.fetchall()
            
            self.current_activity['teams']['total'] = len(all_teams)
            terminal_ui.add_activity(f"Found {len(all_teams)} unique teams")
            
            for idx, (team_id, team_name) in enumerate(all_teams, 1):
                self.current_activity['teams']['current'] = team_name or f"Team {team_id}"
                self.current_activity['teams']['done'] = idx
                
                dashboard = terminal_ui.create_dashboard(
                    self.cumulative, self.daily, self.get_runtime(),
                    self.current_activity, total_days
                )
                live.update(dashboard)
                
                try:
                    terminal_ui.add_activity(f"[{idx}/{len(all_teams)}] {team_name or f'Team {team_id}'}")
                    
                    # Check if already scraped
                    with get_connection() as db:
                        db.execute("""
                            SELECT COUNT(*) FROM team_matches 
                            WHERE team_id = %s
                        """, (team_id,))
                        existing = db.fetchone()[0]
                    
                    if existing >= 30:
                        terminal_ui.add_activity(f"  - Already have {existing} matches, skipping")
                        continue
                    
                    # Scrape team history
                    self.coordinator.scrape_team_history([team_id], matches_per_team=30)
                    
                    # Count new matches
                    with get_connection() as db:
                        db.execute("""
                            SELECT COUNT(*) FROM team_matches 
                            WHERE team_id = %s AND scraped_at::date = CURRENT_DATE
                        """, (team_id,))
                        new_matches = db.fetchone()[0]
                    
                    self.cumulative['team_matches'] += new_matches
                    self.daily['team_matches'] += new_matches
                    terminal_ui.add_activity(f"  ✓ {new_matches} matches")
                    
                except Exception as e:
                    logger.error(f"Error scraping team {team_id}: {e}")
                    terminal_ui.add_activity(f"  ✗ ERROR: {str(e)[:40]}")
                
                time.sleep(0.5)
            
            terminal_ui.add_activity(f"✓ PHASE 2 COMPLETE: {self.cumulative['team_matches']} team matches")
            
            # ========== PHASE 3: COLLECT MATCH STATISTICS ==========
            terminal_ui.add_activity("=== PHASE 3: Collecting Match Statistics ===")
            self.current_activity['phase'] = 3
            
            # Get all finished matches without stats
            with get_connection() as db:
                db.execute("""
                    SELECT match_id, home_team_name, away_team_name 
                    FROM fixtures 
                    WHERE status = 'finished'
                    AND match_id NOT IN (SELECT DISTINCT match_id FROM match_statistics)
                    ORDER BY date
                """)
                matches_to_scrape = db.fetchall()
            
            self.current_activity['match_stats']['total'] = len(matches_to_scrape)
            terminal_ui.add_activity(f"Found {len(matches_to_scrape)} finished matches needing stats")
            
            for idx, (match_id, home, away) in enumerate(matches_to_scrape, 1):
                match_name = f"{home} vs {away}" if home and away else f"Match {match_id}"
                self.current_activity['match_stats']['current'] = match_name
                self.current_activity['match_stats']['done'] = idx
                
                dashboard = terminal_ui.create_dashboard(
                    self.cumulative, self.daily, self.get_runtime(),
                    self.current_activity, total_days
                )
                live.update(dashboard)
                
                try:
                    terminal_ui.add_activity(f"[{idx}/{len(matches_to_scrape)}] {match_name[:50]}")
                    
                    match_stats = self.match_stats_scraper.get_match_statistics(match_id)
                    if match_stats:
                        periods_saved = 0
                        for period_key, period_name in [('first_half', '1ST'), ('second_half', '2ND')]:
                            if match_stats.get(period_key):
                                data = match_stats[period_key].copy()
                                data['match_id'] = match_id
                                data['period'] = period_name
                                
                                normalized = {normalize_column_name(k): v for k, v in data.items()}
                                filtered, _ = filter_to_existing_columns(normalized, self.match_stats_columns)
                                
                                with get_connection() as db:
                                    cols = list(filtered.keys())
                                    placeholders = ", ".join([f"%({col})s" for col in cols])
                                    col_names = ", ".join(cols)
                                    db.execute(f"""
                                        INSERT INTO match_statistics ({col_names})
                                        VALUES ({placeholders})
                                        ON CONFLICT (match_id, period) DO NOTHING
                                    """, filtered)
                                periods_saved += 1
                        
                        self.cumulative['match_stats'] += 1
                        self.daily['match_stats'] += 1
                        terminal_ui.add_activity(f"  ✓ {periods_saved} periods saved")
                    else:
                        terminal_ui.add_activity(f"  - No stats available yet")
                    
                except Exception as e:
                    logger.error(f"Error scraping match stats {match_id}: {e}")
                    terminal_ui.add_activity(f"  ✗ ERROR: {str(e)[:40]}")
                
                time.sleep(1)
            
            terminal_ui.add_activity(f"✓ PHASE 3 COMPLETE: {self.cumulative['match_stats']} match stats")
            
            # ========== PHASE 4: COLLECT PLAYER STATISTICS ==========
            terminal_ui.add_activity("=== PHASE 4: Collecting Player Statistics ===")
            self.current_activity['phase'] = 4
            
            # Get finished matches without player stats
            with get_connection() as db:
                db.execute("""
                    SELECT match_id, home_team_name, away_team_name 
                    FROM fixtures 
                    WHERE status = 'finished'
                    AND match_id NOT IN (SELECT DISTINCT match_id FROM player_statistics)
                    ORDER BY date
                """)
                player_matches = db.fetchall()
            
            self.current_activity['player_stats']['total'] = len(player_matches)
            terminal_ui.add_activity(f"Found {len(player_matches)} matches needing player stats")
            
            for idx, (match_id, home, away) in enumerate(player_matches, 1):
                match_name = f"{home} vs {away}" if home and away else f"Match {match_id}"
                self.current_activity['player_stats']['current'] = match_name
                self.current_activity['player_stats']['done'] = idx
                
                dashboard = terminal_ui.create_dashboard(
                    self.cumulative, self.daily, self.get_runtime(),
                    self.current_activity, total_days
                )
                live.update(dashboard)
                
                try:
                    terminal_ui.add_activity(f"[{idx}/{len(player_matches)}] {match_name[:50]}")
                    
                    lineups = self.player_stats_scraper.get_match_lineups(match_id)
                    if lineups:
                        players_saved = 0
                        
                        # Process both teams
                        for team_key in ['home', 'away']:
                            if lineups.get(team_key):
                                team = lineups[team_key]
                                for player in team.get('starting_xi', []) + team.get('substitutes', []):
                                    try:
                                        with get_connection() as db:
                                            db.execute("""
                                                INSERT INTO player_statistics (
                                                    match_id, player_id, player_name, team_id, team_name,
                                                    position, shirt_number, substitute, minutes_played, rating,
                                                    goals, assists, total_shots, accurate_passes, total_passes,
                                                    tackles, interceptions, duels_won, fouls_committed, was_fouled,
                                                    yellow_cards, red_cards
                                                ) VALUES (
                                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                                )
                                                ON CONFLICT (match_id, player_id) DO NOTHING
                                            """, (
                                                match_id, player['player_id'], player['name'],
                                                team['team_id'], team['team_name'],
                                                player.get('position'), player.get('shirt_number'),
                                                player.get('substitute', False), player.get('minutes_played'),
                                                player.get('rating'), player.get('goals'), player.get('assists'),
                                                player.get('total_shots'), player.get('accurate_passes'),
                                                player.get('total_passes'), player.get('tackles'),
                                                player.get('interceptions'), player.get('duels_won'),
                                                player.get('fouls_committed'), player.get('was_fouled'),
                                                player.get('yellow_cards'), player.get('red_cards')
                                            ))
                                            players_saved += 1
                                    except Exception as e:
                                        logger.error(f"Error saving player {player.get('name')}: {e}")
                        
                        self.cumulative['player_stats'] += players_saved
                        self.daily['player_stats'] += players_saved
                        terminal_ui.add_activity(f"  ✓ {players_saved} players saved")
                    else:
                        terminal_ui.add_activity(f"  - No player data available")
                    
                except Exception as e:
                    logger.error(f"Error scraping player stats {match_id}: {e}")
                    terminal_ui.add_activity(f"  ✗ ERROR: {str(e)[:40]}")
                
                time.sleep(1)
            
            terminal_ui.add_activity(f"✓ PHASE 4 COMPLETE: {self.cumulative['player_stats']} player records")
        
        # Show completion
        terminal_ui.show_completion_banner(self.cumulative, self.get_runtime())
    
    def run(self):
        """Main run method"""
        if self.mode == 'comprehensive':
            self.run_comprehensive()
        else:
            terminal_ui.show_warning("Daily mode not implemented")
        return 0


def main():
    collector = DataCollector()
    
    try:
        return collector.run()
    except KeyboardInterrupt:
        terminal_ui.show_warning("Stopped by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        terminal_ui.show_error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())