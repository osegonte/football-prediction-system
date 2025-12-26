"""
Football Data Collector - DATA COLLECTION ONLY
NO UI code here - all UI handled by display/terminal_ui.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging FIRST - suppress console output
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

# Import UI module (returns renderables)
from display import terminal_ui

# Import data collection modules
from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection

console = Console()
logger = logging.getLogger(__name__)


def normalize_column_name(name):
    """Normalize column names for database"""
    return name.replace(' ', '_').replace('-', '_').lower()


def get_table_columns(db, table_name):
    """Get columns for a table"""
    db.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
    return {row[0] for row in db.fetchall()}


def filter_to_existing_columns(data, existing_columns):
    """Filter data to only include existing columns"""
    filtered = {k: v for k, v in data.items() if k in existing_columns}
    return filtered, []


class DataCollector:
    """Data collection logic ONLY - no UI"""
    
    def __init__(self):
        # Initialize scrapers
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        
        # Timing
        self.start_time = datetime.now()
        
        # Cache database schema
        with get_connection() as db:
            self.match_stats_columns = get_table_columns(db, 'match_statistics')
            self.player_stats_columns = get_table_columns(db, 'player_statistics')
        
        # Detect mode
        self.mode = self.detect_mode()
        
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
        
        # Load initial stats
        self.load_cumulative_stats()
    
    def load_cumulative_stats(self):
        """Load cumulative stats from database"""
        try:
            with get_connection() as db:
                db.execute("SELECT COUNT(*) FROM fixtures")
                self.cumulative['fixtures'] = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM team_matches")
                self.cumulative['team_matches'] = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM match_statistics")
                self.cumulative['match_stats'] = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM player_statistics")
                self.cumulative['player_stats'] = db.fetchone()[0]
        except Exception as e:
            logger.error(f"Error loading cumulative stats: {e}")
    
    def detect_mode(self):
        """Detect if we should run comprehensive or daily mode"""
        try:
            with get_connection() as db:
                db.execute("SELECT MAX(date) FROM fixtures")
                result = db.fetchone()
                latest_date = result[0] if result[0] else None
                
                db.execute("SELECT COUNT(DISTINCT date) FROM fixtures")
                days_collected = db.fetchone()[0]
                
                target_start = datetime(2025, 1, 1).date()
                today = datetime.now().date()
                total_days_needed = (today - target_start).days + 1
                
                if not latest_date or days_collected < (total_days_needed * 0.8):
                    return 'comprehensive'
                
                if (today - latest_date).days > 2:
                    return 'comprehensive'
                
                return 'daily'
        except Exception as e:
            logger.error(f"Error detecting mode: {e}")
            return 'comprehensive'
    
    def get_runtime(self):
        """Get runtime as timedelta"""
        return datetime.now() - self.start_time
    
    def run_comprehensive(self):
        """Run comprehensive collection with Rich Live"""
        # Show startup banner
        terminal_ui.show_startup_banner(self.mode)
        time.sleep(2)
        
        # Setup date range
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        days_completed = 0
        
        terminal_ui.add_activity(f"Starting comprehensive collection: {total_days} days")
        
        # Use Rich Live for smooth updates
        console = Console()
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            # Loop through dates
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                try:
                    # STAGE 1: Fixtures
                    dashboard = terminal_ui.create_dashboard(
                        self.cumulative, self.daily, self.get_runtime(),
                        date_str, "Stage 1: Fetching Fixtures",
                        stage_progress={'current': 0, 'total': 1},
                        total_days=total_days, days_completed=days_completed
                    )
                    live.update(dashboard)
                    
                    terminal_ui.add_activity(f"STAGE 1: Fetching fixtures for {date_str}")
                    fixtures = self.coordinator.scrape_daily_fixtures(current_date)
                    
                    if fixtures:
                        self.cumulative['fixtures'] += len(fixtures)
                        self.daily['fixtures'] += len(fixtures)
                        terminal_ui.add_activity(f"  -> Collected {len(fixtures)} fixtures")
                    else:
                        terminal_ui.add_activity(f"  -> No new fixtures")
                    
                    # STAGE 2: Teams
                    with get_connection() as db:
                        db.execute("""
                            SELECT DISTINCT home_team_id, home_team_name FROM fixtures WHERE date = %s
                            UNION
                            SELECT DISTINCT away_team_id, away_team_name FROM fixtures WHERE date = %s
                        """, (current_date.date(), current_date.date()))
                        teams = db.fetchall()
                    
                    if teams:
                        terminal_ui.add_activity(f"STAGE 2: Scraping {len(teams)} teams")
                        
                        for idx, (team_id, team_name) in enumerate(teams, 1):
                            # Update display
                            dashboard = terminal_ui.create_dashboard(
                                self.cumulative, self.daily, self.get_runtime(),
                                date_str, f"Stage 2: Team History",
                                stage_progress={'current': idx, 'total': len(teams)},
                                total_days=total_days, days_completed=days_completed
                            )
                            live.update(dashboard)
                            
                            terminal_ui.add_activity(f"  [{idx}/{len(teams)}] {team_name or f'Team {team_id}'}...")
                            
                            # Scrape this team
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
                            terminal_ui.add_activity(f"    -> {new_matches} matches collected")
                            
                            time.sleep(0.5)
                    
                    # STAGE 3: Match Statistics
                    with get_connection() as db:
                        db.execute("""
                            SELECT match_id, home_team_name, away_team_name FROM fixtures 
                            WHERE date = %s AND status = 'finished'
                            AND match_id NOT IN (SELECT DISTINCT match_id FROM match_statistics)
                        """, (current_date.date(),))
                        matches = db.fetchall()
                    
                    if matches:
                        terminal_ui.add_activity(f"STAGE 3: Match Statistics ({len(matches)} matches)")
                        
                        for idx, (match_id, home, away) in enumerate(matches, 1):
                            dashboard = terminal_ui.create_dashboard(
                                self.cumulative, self.daily, self.get_runtime(),
                                date_str, f"Stage 3: Match Stats",
                                stage_progress={'current': idx, 'total': len(matches)},
                                total_days=total_days, days_completed=days_completed
                            )
                            live.update(dashboard)
                            
                            match_name = f"{home} vs {away}" if home and away else f"Match {match_id}"
                            terminal_ui.add_activity(f"  [{idx}/{len(matches)}] {match_name[:50]}...")
                            
                            # Scrape match stats
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
                                terminal_ui.add_activity(f"    -> {periods_saved} periods saved")
                            else:
                                terminal_ui.add_activity(f"    -> No stats available")
                            
                            time.sleep(1)
                    
                    # STAGE 4: Player Statistics
                    with get_connection() as db:
                        db.execute("""
                            SELECT match_id, home_team_name, away_team_name FROM fixtures 
                            WHERE date = %s AND status = 'finished'
                            AND match_id NOT IN (SELECT DISTINCT match_id FROM player_statistics)
                        """, (current_date.date(),))
                        player_matches = db.fetchall()
                    
                    if player_matches:
                        terminal_ui.add_activity(f"STAGE 4: Player Statistics ({len(player_matches)} matches)")
                    
                        for idx, (match_id, home, away) in enumerate(player_matches, 1):
                            dashboard = terminal_ui.create_dashboard(
                                self.cumulative, self.daily, self.get_runtime(),
                                date_str, f"Stage 4: Player Stats",
                                stage_progress={'current': idx, 'total': len(player_matches)},
                                total_days=total_days, days_completed=days_completed
                            )
                            live.update(dashboard)
                            
                            match_name = f"{home} vs {away}" if home and away else f"Match {match_id}"
                            terminal_ui.add_activity(f"  [{idx}/{len(player_matches)}] {match_name[:50]}...")
                            
                            # Scrape player stats
                            lineups = self.player_stats_scraper.get_match_lineups(match_id)
                            if lineups:
                                players_saved = 0
                                
                                # Process home team players
                                if lineups.get('home'):
                                    home_team = lineups['home']
                                    for player in home_team.get('starting_xi', []) + home_team.get('substitutes', []):
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
                                                    home_team['team_id'], home_team['team_name'],
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
                                
                                # Process away team players
                                if lineups.get('away'):
                                    away_team = lineups['away']
                                    for player in away_team.get('starting_xi', []) + away_team.get('substitutes', []):
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
                                                    away_team['team_id'], away_team['team_name'],
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
                                terminal_ui.add_activity(f"    -> {players_saved} players saved")
                            else:
                                terminal_ui.add_activity(f"    -> No player data available")
                            
                            time.sleep(1)
                    
                    self.cumulative['dates_processed'] += 1
                    days_completed += 1
                    terminal_ui.add_activity(f"Completed {date_str}")
                
                except Exception as e:
                    logger.error(f"Error on {date_str}: {e}")
                    terminal_ui.add_activity(f"ERROR on {date_str}: {str(e)[:50]}")
                    self.cumulative['dates_failed'] += 1
                
                current_date += timedelta(days=1)
                time.sleep(0.5)
        
        # Show completion
        terminal_ui.show_completion_banner(self.cumulative, self.get_runtime())
    
    def run(self):
        """Main run method"""
        if self.mode == 'comprehensive':
            self.run_comprehensive()
        else:
            terminal_ui.show_warning("Daily mode - not implemented yet")
        return 0


def main():
    collector = DataCollector()
    
    try:
        return collector.run()
    except KeyboardInterrupt:
        terminal_ui.show_warning("Stopped by user")
        return 1
    except Exception as e:
        terminal_ui.show_error(str(e))
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    exit(main())