"""
Terminal UI Module - Professional Full-Screen Dashboard
Inspired by btop/htop - one screen, no scrolling, maximum density
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
import psutil

console = Console()


class FootballUI:
    """Full-screen professional dashboard"""
    
    def __init__(self):
        self.activity_log = []
        self.errors = 0
        self.duplicates = 0
        self.retries = 0
        self.last_latency = 0
    
    def add_activity(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.activity_log.append(f"[{timestamp}] {message}")
        if len(self.activity_log) > 6:
            self.activity_log.pop(0)
    
    def track_error(self):
        self.errors += 1
    
    def track_duplicate(self):
        self.duplicates += 1
    
    def track_retry(self):
        self.retries += 1
    
    def update_latency(self, latency_ms):
        self.last_latency = latency_ms
    
    def create_progress_bar(self, current, total, width=15):
        """Create visual progress bar - ASCII only for compatibility"""
        if total == 0:
            return "-" * width
        
        filled = int(width * current / total)
        empty = width - filled
        
        # Use ASCII: # for filled, - for empty
        return "#" * filled + "-" * empty
    
    def show_startup_banner(self, mode):
        """Show startup banner"""
        console.clear()
        
        banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ███████╗ ██████╗  ██████╗ ████████╗██████╗  █████╗ ██╗     ██╗       ║
║   ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██║     ██║       ║
║   █████╗  ██║   ██║██║   ██║   ██║   ██████╔╝███████║██║     ██║       ║
║   ██╔══╝  ██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║     ██║       ║
║   ██║     ╚██████╔╝╚██████╔╝   ██║   ██████╔╝██║  ██║███████╗███████╗  ║
║   ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝  ║
║                                                                          ║
║              COMPREHENSIVE COLLECTION - SOFASCORE DATA                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
        
        console.print(banner, style="bold cyan")
    
    def create_dashboard(self, cumulative_stats, daily_stats, runtime, 
                        current_activity, total_days):
        """
        Create full-screen dashboard with current activity boxes
        current_activity format:
        {
            'phase': 1-4,
            'fixtures': {'current': 'date', 'total': X, 'done': Y},
            'teams': {'current': 'team_name', 'total': X, 'done': Y},
            'match_stats': {'current': 'match_name', 'total': X, 'done': Y},
            'player_stats': {'current': 'match_name', 'total': X, 'done': Y}
        }
        """
        
        # Calculate runtime
        hours = int(runtime.total_seconds() / 3600)
        minutes = int((runtime.total_seconds() % 3600) / 60)
        seconds = int(runtime.total_seconds() % 60)
        
        # Calculate rates (per minute)
        runtime_secs = runtime.total_seconds() if runtime.total_seconds() > 0 else 1
        fix_rate = (daily_stats['fixtures'] / runtime_secs) * 60
        match_rate = (daily_stats['team_matches'] / runtime_secs) * 60
        stats_rate = (daily_stats['match_stats'] / runtime_secs * 60) if daily_stats['match_stats'] > 0 else 0
        players_rate = (daily_stats['player_stats'] / runtime_secs * 60) if daily_stats['player_stats'] > 0 else 0
        
        # Calculate ETA
        phase = current_activity.get('phase', 1)
        phase_names = {1: 'Fixtures', 2: 'Teams', 3: 'Match Stats', 4: 'Player Stats'}
        current_phase = phase_names.get(phase, 'Unknown')
        
        # Get system health
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        disk = psutil.disk_usage('/')
        disk_gb = disk.used / (1024**3)
        
        # Create main layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="upper", size=6),
            Layout(name="middle", size=11),
            Layout(name="detail", size=8),
            Layout(name="bottom", size=10)
        )
        
        # HEADER
        header_text = f"FOOTBALL DATA COLLECTOR - SOFASCORE | ⏱ {hours:02d}:{minutes:02d}:{seconds:02d} | Phase {phase}: {current_phase}"
        layout["header"].update(Panel(header_text, style="bold cyan"))
        
        # UPPER: System Health + Progress
        layout["upper"].split_row(
            Layout(name="health", ratio=1),
            Layout(name="progress", ratio=2)
        )
        
        health_content = f"""CPU {self.create_progress_bar(int(cpu_percent), 100, 10)} {cpu_percent:5.1f}%
RAM {self.create_progress_bar(int(ram_percent), 100, 10)} {ram_percent:5.1f}%
DIS {self.create_progress_bar(int(disk_gb), 100, 10)} {disk_gb:5.1f}GB
LAT {self.create_progress_bar(min(int(self.last_latency), 1000), 1000, 10)} {self.last_latency:5.0f}ms"""
        
        layout["health"].update(Panel(health_content, title="SYSTEM HEALTH", border_style="green"))
        
        # Progress - Overall stats
        progress_content = f"""FIXTURES:  {cumulative_stats['fixtures']:>8,}  (+{daily_stats['fixtures']:<6,})  {fix_rate:>5.1f}/m
TEAMS:     {cumulative_stats['team_matches']:>8,}  (+{daily_stats['team_matches']:<6,})  {match_rate:>5.1f}/m
STATS:     {cumulative_stats['match_stats']:>8,}  (+{daily_stats['match_stats']:<6,})  {stats_rate:>5.1f}/m
PLAYERS:   {cumulative_stats['player_stats']:>8,}  (+{daily_stats['player_stats']:<6,})  {players_rate:>5.1f}/m"""
        
        layout["progress"].update(Panel(progress_content, title="COLLECTION SUMMARY", border_style="yellow"))
        
        # MIDDLE: Entities
        entities_table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        entities_table.add_column("Entity", style="cyan", width=15)
        entities_table.add_column("Bar", width=20)
        entities_table.add_column("Total", justify="right", style="green", width=10)
        entities_table.add_column("Today", justify="right", style="yellow", width=8)
        entities_table.add_column("Rate", justify="right", style="magenta", width=8)
        
        expected_fixtures = total_days * 70 if total_days > 0 else 1
        expected_teams = 3000
        expected_match_stats = 1000
        expected_players = 10000
        
        entities_table.add_row(
            "Fixtures",
            self.create_progress_bar(cumulative_stats['fixtures'], expected_fixtures, 15),
            f"{cumulative_stats['fixtures']:,}",
            f"+{daily_stats['fixtures']}",
            f"{fix_rate:.1f}/m"
        )
        entities_table.add_row(
            "Team Matches",
            self.create_progress_bar(cumulative_stats['team_matches'], expected_teams, 15),
            f"{cumulative_stats['team_matches']:,}",
            f"+{daily_stats['team_matches']}",
            f"{match_rate:.1f}/m"
        )
        entities_table.add_row(
            "Match Stats",
            self.create_progress_bar(cumulative_stats['match_stats'], expected_match_stats, 15),
            f"{cumulative_stats['match_stats']:,}",
            f"+{daily_stats['match_stats']}",
            f"{stats_rate:.1f}/m"
        )
        entities_table.add_row(
            "Player Stats",
            self.create_progress_bar(cumulative_stats['player_stats'], expected_players, 15),
            f"{cumulative_stats['player_stats']:,}",
            f"+{daily_stats['player_stats']}",
            f"{players_rate:.1f}/m"
        )
        
        layout["middle"].update(Panel(entities_table, title="ENTITY COLLECTION STATUS", border_style="cyan"))
        
        # DETAIL: 4 boxes showing current activity for each entity type
        layout["detail"].split_row(
            Layout(name="fix_box"),
            Layout(name="team_box"),
            Layout(name="match_box"),
            Layout(name="player_box")
        )
        
        # Fixtures box
        fix_activity = current_activity.get('fixtures', {})
        fix_current = fix_activity.get('current', '')
        fix_done = fix_activity.get('done', 0)
        fix_total = fix_activity.get('total', 0)
        fix_pct = (fix_done / fix_total * 100) if fix_total > 0 else 0
        fix_bar = self.create_progress_bar(fix_done, fix_total, 10)
        fix_content = f"{fix_bar}\n{fix_done}/{fix_total}\n{fix_current[:15]}" if fix_current else f"{fix_bar}\n{fix_done}/{fix_total}\nWaiting..."
        layout["fix_box"].update(Panel(fix_content, title="FIXTURES", border_style="cyan" if phase == 1 else "dim"))
        
        # Teams box
        team_activity = current_activity.get('teams', {})
        team_current = team_activity.get('current', '')
        team_done = team_activity.get('done', 0)
        team_total = team_activity.get('total', 0)
        team_bar = self.create_progress_bar(team_done, team_total, 10)
        team_content = f"{team_bar}\n{team_done}/{team_total}\n{team_current[:15]}" if team_current else f"{team_bar}\n{team_done}/{team_total}\nWaiting..."
        layout["team_box"].update(Panel(team_content, title="TEAMS", border_style="yellow" if phase == 2 else "dim"))
        
        # Match Stats box
        match_activity = current_activity.get('match_stats', {})
        match_current = match_activity.get('current', '')
        match_done = match_activity.get('done', 0)
        match_total = match_activity.get('total', 0)
        match_bar = self.create_progress_bar(match_done, match_total, 10)
        match_content = f"{match_bar}\n{match_done}/{match_total}\n{match_current[:15]}" if match_current else f"{match_bar}\n{match_done}/{match_total}\nWaiting..."
        layout["match_box"].update(Panel(match_content, title="MATCH STATS", border_style="green" if phase == 3 else "dim"))
        
        # Player Stats box
        player_activity = current_activity.get('player_stats', {})
        player_current = player_activity.get('current', '')
        player_done = player_activity.get('done', 0)
        player_total = player_activity.get('total', 0)
        player_bar = self.create_progress_bar(player_done, player_total, 10)
        player_content = f"{player_bar}\n{player_done}/{player_total}\n{player_current[:15]}" if player_current else f"{player_bar}\n{player_done}/{player_total}\nWaiting..."
        layout["player_box"].update(Panel(player_content, title="PLAYERS", border_style="magenta" if phase == 4 else "dim"))
        
        # Quality
        db_status = "✓" if cumulative_stats.get('fixtures', 0) > 0 else "!"
        quality_content = f"Dupes {self.create_progress_bar(self.duplicates, 100, 8)} {self.duplicates:3} | Fails {self.create_progress_bar(self.errors, 50, 8)} {self.errors:3} | Retries {self.create_progress_bar(self.retries, 20, 8)} {self.retries:3} | DB {db_status}"
        
        # BOTTOM: Live Feed
        feed_text = "\n".join(self.activity_log[-6:]) if self.activity_log else "Waiting for activity..."
        layout["bottom"].update(Panel(feed_text, title="LIVE FEED", border_style="cyan"))
        
        return layout
    
    def show_completion_banner(self, cumulative_stats, runtime):
        """Show completion"""
        console.clear()
        
        hours = int(runtime.total_seconds() / 3600)
        minutes = int((runtime.total_seconds() % 3600) / 60)
        total_records = cumulative_stats['fixtures'] + cumulative_stats['team_matches'] + cumulative_stats['match_stats'] + cumulative_stats['player_stats']
        
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                     *** COLLECTION COMPLETE ***                          ║
║                                                                          ║
║                     Runtime: {hours:02d}h {minutes:02d}m                                    ║
║                     Total Records: {total_records:,}                                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
        
        console.print(banner, style="bold green")
    
    def show_error(self, message):
        """Show error message"""
        console.print(f"\n[bold red]ERROR: {message}[/bold red]\n")
    
    def show_warning(self, message):
        """Show warning message"""
        console.print(f"\n[yellow]WARNING: {message}[/yellow]\n")


# Global instance
ui = FootballUI()


# Functions
def show_startup_banner(mode):
    ui.show_startup_banner(mode)


def create_dashboard(cumulative_stats, daily_stats, runtime, 
                     current_activity, total_days):
    return ui.create_dashboard(
        cumulative_stats, daily_stats, runtime,
        current_activity, total_days
    )


def add_activity(message):
    ui.add_activity(message)


def track_error():
    ui.track_error()


def track_duplicate():
    ui.track_duplicate()


def track_retry():
    ui.track_retry()


def update_latency(latency_ms):
    ui.update_latency(latency_ms)


def show_completion_banner(cumulative_stats, runtime):
    ui.show_completion_banner(cumulative_stats, runtime)


def show_error(message):
    ui.show_error(message)


def show_warning(message):
    ui.show_warning(message)