"""
Football Data Collector - Smart Mode with Clean Retro UI
Automatically switches between comprehensive and daily collection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
import time

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from display.terminal_ui import display, show_mode_banner, show_header, show_stats, show_completion, show_date_processing, show_daily_stat
from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection

# Logging to file only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/collector.log')]
)
logger = logging.getLogger(__name__)


def normalize_column_name(name):
    return name.replace(' ', '_').replace('-', '_').lower()


def get_table_columns(db, table_name):
    db.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
    return {row[0] for row in db.fetchall()}


def filter_to_existing_columns(data, existing_columns):
    filtered = {k: v for k, v in data.items() if k in existing_columns}
    skipped = [k for k in data.keys() if k not in existing_columns]
    return filtered, skipped


class SmartCollector:
    
    def __init__(self):
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        self.start_time = datetime.now()
        
        # Cache schema
        with get_connection() as db:
            self.match_stats_columns = get_table_columns(db, 'match_statistics')
            self.player_stats_columns = get_table_columns(db, 'player_statistics')
        
        # Determine mode
        self.mode = self.detect_mode()
        self.stats = {
            'fixtures': 0,
            'teams': 0,
            'team_matches': 0,
            'match_stats': 0,
            'player_stats': 0,
            'dates_processed': 0,
            'dates_failed': 0
        }
    
    def detect_mode(self):
        """Detect if we need comprehensive or daily collection"""
        try:
            with get_connection() as db:
                # Check latest date in database
                db.execute("SELECT MAX(date) FROM fixtures")
                result = db.fetchone()
                latest_date = result[0] if result[0] else None
                
                # Check how many days we have
                db.execute("SELECT COUNT(DISTINCT date) FROM fixtures")
                days_collected = db.fetchone()[0]
                
                target_start = datetime(2025, 1, 1).date()
                today = datetime.now().date()
                total_days_needed = (today - target_start).days + 1
                
                # If we have less than 80% of data, run comprehensive
                if not latest_date or days_collected < (total_days_needed * 0.8):
                    return 'comprehensive'
                
                # If latest date is older than 2 days, run comprehensive
                if (today - latest_date).days > 2:
                    return 'comprehensive'
                
                # Otherwise, daily mode
                return 'daily'
        
        except Exception as e:
            logger.error(f"Error detecting mode: {e}")
            # Default to comprehensive if unsure
            return 'comprehensive'
    
    def get_today_stats(self):
        """Get today's statistics from database"""
        try:
            with get_connection() as db:
                db.execute("SELECT COUNT(*) FROM fixtures WHERE scraped_at::date = CURRENT_DATE")
                fixtures_today = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM team_matches WHERE scraped_at::date = CURRENT_DATE")
                matches_today = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM match_statistics WHERE scraped_at::date = CURRENT_DATE")
                stats_today = db.fetchone()[0]
            
            return {
                'fixtures_today': fixtures_today,
                'team_matches_today': matches_today,
                'match_stats_today': stats_today
            }
        except Exception as e:
            logger.error(f"Error getting today stats: {e}")
            return {
                'fixtures_today': 0,
                'team_matches_today': 0,
                'match_stats_today': 0
            }
    
    def show_current_status(self):
        """Display current status"""
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() / 3600)
        minutes = int((elapsed.total_seconds() % 3600) / 60)
        
        today_stats = self.get_today_stats()
        
        show_header(
            self.mode,
            hours,
            minutes,
            self.stats['dates_processed'],
            self.stats['dates_failed']
        )
        show_stats(self.stats, today_stats)
    
    def run_comprehensive(self):
        """Run comprehensive historical collection"""
        display.clear()
        show_mode_banner('comprehensive')
        
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        with Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[green]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=display.console
        ) as progress:
            
            overall = progress.add_task("[cyan]Overall", total=total_days)
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                try:
                    # Stage 1: Fixtures
                    fixtures = self.coordinator.scrape_daily_fixtures(current_date)
                    if fixtures:
                        self.stats['fixtures'] += len(fixtures)
                    
                    # Stage 2: Teams
                    with get_connection() as db:
                        db.execute("""
                            SELECT DISTINCT home_team_id FROM fixtures WHERE date = %s
                            UNION
                            SELECT DISTINCT away_team_id FROM fixtures WHERE date = %s
                        """, (current_date.date(), current_date.date()))
                        team_ids = [row[0] for row in db.fetchall()]
                    
                    if team_ids:
                        self.coordinator.scrape_team_history(team_ids, matches_per_team=30)
                        with get_connection() as db:
                            db.execute("SELECT COUNT(*) FROM team_matches WHERE scraped_at::date = CURRENT_DATE")
                            self.stats['team_matches'] += db.fetchone()[0]
                    
                    # Stage 3: Match Statistics
                    with get_connection() as db:
                        db.execute("""
                            SELECT match_id FROM fixtures 
                            WHERE date = %s AND status = 'finished'
                            AND match_id NOT IN (SELECT DISTINCT match_id FROM match_statistics)
                        """, (current_date.date(),))
                        match_ids = [row[0] for row in db.fetchall()]
                    
                    for match_id in match_ids:
                        match_stats = self.match_stats_scraper.get_match_statistics(match_id)
                        if match_stats:
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
                            
                            self.stats['match_stats'] += 1
                        time.sleep(2)
                    
                    self.stats['dates_processed'] += 1
                    progress.update(overall, advance=1, description=f"[cyan]{date_str}")
                
                except Exception as e:
                    logger.error(f"Error on {date_str}: {e}")
                    self.stats['dates_failed'] += 1
                
                current_date += timedelta(days=1)
                time.sleep(2)
        
        # Show completion
        show_completion('comprehensive', datetime.now() - self.start_time)
        self.show_current_status()
    
    def run_daily(self):
        """Run daily incremental collection"""
        display.clear()
        show_mode_banner('daily')
        
        # Collect yesterday and today
        dates_to_collect = [
            datetime.now().date() - timedelta(days=1),
            datetime.now().date()
        ]
        
        for date in dates_to_collect:
            date_str = date.strftime('%Y-%m-%d')
            show_date_processing(date_str)
            
            try:
                # Stage 1: Fixtures
                fixtures = self.coordinator.scrape_daily_fixtures(datetime.combine(date, datetime.min.time()))
                if fixtures:
                    self.stats['fixtures'] += len(fixtures)
                    show_daily_stat("Fixtures", len(fixtures))
                
                # Stage 2: Teams (only new teams)
                with get_connection() as db:
                    db.execute("""
                        SELECT DISTINCT home_team_id FROM fixtures WHERE date = %s
                        AND home_team_id NOT IN (SELECT DISTINCT team_id FROM team_matches WHERE scraped_at::date >= CURRENT_DATE - INTERVAL '7 days')
                        UNION
                        SELECT DISTINCT away_team_id FROM fixtures WHERE date = %s
                        AND away_team_id NOT IN (SELECT DISTINCT team_id FROM team_matches WHERE scraped_at::date >= CURRENT_DATE - INTERVAL '7 days')
                    """, (date, date))
                    team_ids = [row[0] for row in db.fetchall()]
                
                if team_ids:
                    self.coordinator.scrape_team_history(team_ids, matches_per_team=5)
                    show_daily_stat("Teams updated", len(team_ids))
                
                # Stage 3: Match Statistics
                with get_connection() as db:
                    db.execute("""
                        SELECT match_id FROM fixtures 
                        WHERE date = %s AND status = 'finished'
                        AND match_id NOT IN (SELECT DISTINCT match_id FROM match_statistics)
                    """, (date,))
                    match_ids = [row[0] for row in db.fetchall()]
                
                for match_id in match_ids:
                    match_stats = self.match_stats_scraper.get_match_statistics(match_id)
                    if match_stats:
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
                        
                        self.stats['match_stats'] += 1
                    time.sleep(2)
                
                if match_ids:
                    show_daily_stat("Match stats", len(match_ids))
                
                self.stats['dates_processed'] += 1
                display.console.print()
            
            except Exception as e:
                logger.error(f"Error on {date_str}: {e}")
                self.stats['dates_failed'] += 1
        
        # Show completion
        show_completion('daily', datetime.now() - self.start_time)
        self.show_current_status()
    
    def run(self):
        """Run appropriate collection mode"""
        if self.mode == 'comprehensive':
            self.run_comprehensive()
        else:
            self.run_daily()
        
        return 0


def main():
    collector = SmartCollector()
    
    try:
        return collector.run()
    except KeyboardInterrupt:
        display.console.print("\n[yellow]Collection stopped by user[/yellow]")
        return 1
    except Exception as e:
        display.console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    exit(main())