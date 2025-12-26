"""
Ultra-Dynamic Football Data Collector UI
- Live scrolling activity feed
- Animated counters
- Real-time stats
- Individual item tracking
- LOTS of numbers!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.panel import Panel

from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection

# Logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/collector.log')]
)
logger = logging.getLogger(__name__)

console = Console()


def normalize_column_name(name):
    return name.replace(' ', '_').replace('-', '_').lower()


def get_table_columns(db, table_name):
    db.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
    return {row[0] for row in db.fetchall()}


def filter_to_existing_columns(data, existing_columns):
    filtered = {k: v for k, v in data.items() if k in existing_columns}
    return filtered, []


class UltraDynamicCollector:
    
    def __init__(self):
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        self.start_time = datetime.now()
        
        # Cache schema
        with get_connection() as db:
            self.match_stats_columns = get_table_columns(db, 'match_statistics')
            self.player_stats_columns = get_table_columns(db, 'player_statistics')
        
        self.mode = self.detect_mode()
        self.stats = {
            'fixtures': 0,
            'team_matches': 0,
            'match_stats': 0,
            'player_stats': 0,
            'dates_processed': 0,
            'dates_failed': 0
        }
        
        self.session_start = {
            'fixtures': 0,
            'team_matches': 0,
            'match_stats': 0
        }
    
    def detect_mode(self):
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
    
    def show_dashboard(self, current_date=None, current_stage=None):
        """Show compact dashboard header"""
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() / 3600)
        minutes = int((elapsed.total_seconds() % 3600) / 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        # Calculate rates
        runtime_secs = elapsed.total_seconds() if elapsed.total_seconds() > 0 else 1
        fix_rate = (self.stats['fixtures'] - self.session_start['fixtures']) / runtime_secs
        match_rate = (self.stats['team_matches'] - self.session_start['team_matches']) / runtime_secs
        
        mode_text = "COMPREHENSIVE" if self.mode == 'comprehensive' else "DAILY"
        
        header = f"""
╔════════════════════════════════════════════════════════════════════════╗
║  ⚡ FOOTBALL DATA COLLECTOR - {mode_text:^12} ⚡  Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}  ║
╠════════════════════════════════════════════════════════════════════════╣
║  📊 FIXTURES: {self.stats['fixtures']:>6,}  ({fix_rate:>5.1f}/s)  │  MATCHES: {self.stats['team_matches']:>8,}  ({match_rate:>5.1f}/s)  ║
║  📈 MATCH STATS: {self.stats['match_stats']:>5,}              │  DATES: {self.stats['dates_processed']:>3} OK / {self.stats['dates_failed']:>2} FAIL    ║
╚════════════════════════════════════════════════════════════════════════╝
"""
        
        if current_date:
            header += f"\n🎯 CURRENT: {current_date}"
            if current_stage:
                header += f" │ STAGE: {current_stage}"
            header += "\n"
        
        console.print(header, style="bold cyan")
    
    def run_comprehensive(self):
        """Run comprehensive with ultra-dynamic UI"""
        console.clear()
        
        # Big banner
        console.print("""
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   ███████╗ ██████╗  ██████╗ ████████╗██████╗  █████╗ ██╗     ██╗      ║
║   ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██║     ██║      ║
║   █████╗  ██║   ██║██║   ██║   ██║   ██████╔╝███████║██║     ██║      ║
║   ██╔══╝  ██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██║      ║
║   ██║     ╚██████╔╝╚██████╔╝   ██║   ██████╔╝██║  ██║███████╗███████╗ ║
║   ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝ ║
║                                                                        ║
║                  COMPREHENSIVE COLLECTION MODE                         ║
║                  Jan 1, 2025 → Today (360 days)                        ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
""", style="bold cyan")
        time.sleep(2)
        console.clear()
        
        # Get session baselines
        with get_connection() as db:
            db.execute("SELECT COUNT(*) FROM fixtures")
            self.session_start['fixtures'] = db.fetchone()[0]
            db.execute("SELECT COUNT(*) FROM team_matches")
            self.session_start['team_matches'] = db.fetchone()[0]
            db.execute("SELECT COUNT(*) FROM match_statistics")
            self.session_start['match_stats'] = db.fetchone()[0]
        
        start_date = datetime(2025, 1, 1)
        end_date = datetime.now()
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=50),
            TextColumn("[cyan]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            overall_task = progress.add_task(f"[cyan]Overall Progress", total=total_days)
            
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Update dashboard
                console.clear()
                self.show_dashboard(date_str, "Fetching")
                progress.update(overall_task, description=f"[cyan]Day {self.stats['dates_processed']+1}/{total_days}")
                progress.refresh()
                
                try:
                    # STAGE 1: Fixtures
                    console.print(f"\n[yellow]▶▶▶ STAGE 1: Fetching Fixtures for {date_str}[/yellow]")
                    fixtures = self.coordinator.scrape_daily_fixtures(current_date)
                    
                    if fixtures:
                        self.stats['fixtures'] += len(fixtures)
                        console.print(f"[green]✓ Collected {len(fixtures):,} fixtures[/green]")
                    else:
                        console.print(f"[dim]No new fixtures[/dim]")
                    
                    # STAGE 2: Teams
                    with get_connection() as db:
                        db.execute("""
                            SELECT DISTINCT home_team_id, home_team_name FROM fixtures WHERE date = %s
                            UNION
                            SELECT DISTINCT away_team_id, away_team_name FROM fixtures WHERE date = %s
                        """, (current_date.date(), current_date.date()))
                        teams = db.fetchall()
                    
                    if teams:
                        console.print(f"\n[yellow]▶▶▶ STAGE 2: Scraping {len(teams)} Teams[/yellow]")
                        team_ids = [t[0] for t in teams]
                        
                        team_task = progress.add_task(f"[magenta]Teams", total=len(team_ids))
                        
                        for idx, (team_id, team_name) in enumerate(teams, 1):
                            console.print(f"  [{idx}/{len(teams)}] {team_name or f'Team {team_id}'}...", end="")
                            
                            # Scrape this team
                            self.coordinator.scrape_team_history([team_id], matches_per_team=30)
                            
                            with get_connection() as db:
                                db.execute("SELECT COUNT(*) FROM team_matches WHERE team_id = %s AND scraped_at::date = CURRENT_DATE", (team_id,))
                                new_matches = db.fetchone()[0]
                            
                            self.stats['team_matches'] += new_matches
                            console.print(f" [green]{new_matches} matches[/green]")
                            
                            progress.update(team_task, advance=1)
                            time.sleep(1)
                        
                        progress.remove_task(team_task)
                        console.print(f"[green]✓ Completed {len(teams)} teams[/green]")
                    
                    # STAGE 3: Match Statistics
                    with get_connection() as db:
                        db.execute("""
                            SELECT match_id, home_team_name, away_team_name FROM fixtures 
                            WHERE date = %s AND status = 'finished'
                            AND match_id NOT IN (SELECT DISTINCT match_id FROM match_statistics)
                        """, (current_date.date(),))
                        matches = db.fetchall()
                    
                    if matches:
                        console.print(f"\n[yellow]▶▶▶ STAGE 3: Match Statistics ({len(matches)} matches)[/yellow]")
                        
                        match_task = progress.add_task(f"[blue]Match Stats", total=len(matches))
                        
                        for idx, (match_id, home, away) in enumerate(matches, 1):
                            match_name = f"{home} vs {away}" if home and away else f"Match {match_id}"
                            console.print(f"  [{idx}/{len(matches)}] {match_name[:40]}...", end="")
                            
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
                                
                                self.stats['match_stats'] += 1
                                console.print(f" [green]{periods_saved} periods saved[/green]")
                            else:
                                console.print(f" [dim]no stats[/dim]")
                            
                            progress.update(match_task, advance=1)
                            time.sleep(2)
                        
                        progress.remove_task(match_task)
                        console.print(f"[green]✓ Completed {len(matches)} matches[/green]")
                    
                    self.stats['dates_processed'] += 1
                    progress.update(overall_task, advance=1)
                
                except Exception as e:
                    logger.error(f"Error on {date_str}: {e}")
                    console.print(f"[red]✗ Error: {e}[/red]")
                    self.stats['dates_failed'] += 1
                
                current_date += timedelta(days=1)
                time.sleep(1)
        
        # Completion
        console.clear()
        console.print("""
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║              ✓✓✓ COMPREHENSIVE COLLECTION COMPLETE ✓✓✓                ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
""", style="bold green")
        self.show_dashboard()
    
    def run(self):
        if self.mode == 'comprehensive':
            self.run_comprehensive()
        else:
            console.print("[yellow]Daily mode - not implemented yet[/yellow]")
        return 0


def main():
    collector = UltraDynamicCollector()
    
    try:
        return collector.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    exit(main())