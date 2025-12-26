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
        """Create visual progress bar - block style"""
        if total == 0:
            return "░" * width
        
        filled = int(width * current / total)
        empty = width - filled
        
        # Use blocks: █ for filled, ░ for empty
        return "█" * filled + "░" * empty
    
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
                        current_date=None, current_stage=None,
                        stage_progress=None, total_days=0, days_completed=0):
        """Create full-screen dashboard"""
        
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
        if days_completed > 0 and runtime_secs > 0:
            days_remaining = total_days - days_completed
            avg_time_per_day = runtime_secs / days_completed
            eta_seconds = days_remaining * avg_time_per_day
            eta_hours = int(eta_seconds / 3600)
            eta_minutes = int((eta_seconds % 3600) / 60)
            eta_str = f"~{eta_hours}h {eta_minutes}m"
        else:
            eta_str = "Calculating..."
        
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
            Layout(name="bottom", size=10)
        )
        
        # HEADER
        header_text = f"FOOTBALL DATA COLLECTOR - SOFASCORE | ⏱ {hours:02d}:{minutes:02d}:{seconds:02d} | {current_stage or 'Init'} | ETA {eta_str}"
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
        
        # Progress
        overall_pct = (days_completed / total_days * 100) if total_days > 0 else 0
        today_count = sum(daily_stats.values()) - daily_stats.get('dates_processed', 0) - daily_stats.get('dates_failed', 0)
        
        stage_current = stage_progress.get('current', 0) if stage_progress else 0
        stage_total = stage_progress.get('total', 1) if stage_progress else 1
        
        progress_content = f"""OVERALL {self.create_progress_bar(days_completed, total_days, 15)} {days_completed:4} / {total_days}
TODAY   {self.create_progress_bar(today_count, 200, 15)} +{today_count:4}
STAGE   {self.create_progress_bar(stage_current, stage_total, 15)} {stage_current:4} / {stage_total}
ETA     {self.create_progress_bar(days_completed, total_days, 15)} {eta_str}"""
        
        layout["progress"].update(Panel(progress_content, title="PROGRESS", border_style="yellow"))
        
        # MIDDLE: Entities + Quality
        layout["middle"].split_column(
            Layout(name="entities", size=8),
            Layout(name="quality", size=3)
        )
        
        # Entities
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
        
        layout["entities"].update(Panel(entities_table, title="ENTITY COLLECTION STATUS", border_style="cyan"))
        
        # Quality
        db_status = "✓" if cumulative_stats.get('fixtures', 0) > 0 else "!"
        quality_content = f"Dupes {self.create_progress_bar(self.duplicates, 100, 8)} {self.duplicates:3} | Fails {self.create_progress_bar(self.errors, 50, 8)} {self.errors:3} | Retries {self.create_progress_bar(self.retries, 20, 8)} {self.retries:3} | DB {db_status}"
        
        layout["quality"].update(Panel(quality_content, title="QUALITY & FLOW", border_style="magenta"))
        
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


# Global instance
ui = FootballUI()


# Functions
def show_startup_banner(mode):
    ui.show_startup_banner(mode)


def create_dashboard(cumulative_stats, daily_stats, runtime, 
                     current_date=None, current_stage=None,
                     stage_progress=None, total_days=0, days_completed=0):
    return ui.create_dashboard(
        cumulative_stats, daily_stats, runtime,
        current_date, current_stage, stage_progress, total_days, days_completed
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