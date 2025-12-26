"""
Clean Retro Terminal UI - Display Module
Place in: display/terminal_ui.py

Pure ASCII, no emojis, professional retro aesthetic
"""

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


class RetroDisplay:
    """Clean retro ASCII terminal display"""
    
    def __init__(self):
        self.console = console
    
    def clear(self):
        """Clear the console"""
        self.console.clear()
    
    def print_header(self, mode, runtime_hours, runtime_minutes, dates_processed, dates_failed):
        """
        Print clean ASCII header
        
        Args:
            mode: 'comprehensive' or 'daily'
            runtime_hours: Hours running
            runtime_minutes: Minutes running
            dates_processed: Number of dates processed
            dates_failed: Number of dates failed
        """
        mode_display = "COMPREHENSIVE" if mode == 'comprehensive' else "DAILY UPDATE"
        
        header = f"""
+================================================================+
|        FOOTBALL DATA COLLECTOR - {mode_display:^16}         |
+================================================================+
|  Runtime: {runtime_hours:02d}h {runtime_minutes:02d}m                                            |
|  Dates:   {dates_processed:3d} processed  {dates_failed:3d} failed                        |
+================================================================+
"""
        self.console.print(header, style="cyan")
    
    def print_stats_table(self, stats, today_stats):
        """
        Print statistics table
        
        Args:
            stats: Dict with keys: fixtures, team_matches, match_stats, player_stats
            today_stats: Dict with keys: fixtures_today, team_matches_today, match_stats_today
        """
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("METRIC", style="cyan", width=20)
        table.add_column("TOTAL", justify="right", style="green", width=15)
        table.add_column("TODAY", justify="right", style="yellow", width=15)
        
        table.add_row(
            "Fixtures",
            f"{stats['fixtures']:,}",
            f"{today_stats['fixtures_today']:,}"
        )
        table.add_row(
            "Team Matches",
            f"{stats['team_matches']:,}",
            f"{today_stats['team_matches_today']:,}"
        )
        table.add_row(
            "Match Statistics",
            f"{stats['match_stats']:,}",
            f"{today_stats['match_stats_today']:,}"
        )
        table.add_row(
            "Players",
            f"{stats['player_stats']:,}",
            "-"
        )
        
        self.console.print(table)
    
    def print_mode_banner(self, mode):
        """
        Print mode banner at startup
        
        Args:
            mode: 'comprehensive' or 'daily'
        """
        if mode == 'comprehensive':
            banner = """[bold cyan]
+========================================+
|   COMPREHENSIVE COLLECTION MODE        |
+========================================+[/bold cyan]
Collecting: 2025-01-01 --> Today
"""
        else:
            banner = """[bold cyan]
+========================================+
|      DAILY COLLECTION MODE             |
+========================================+[/bold cyan]
Collecting today's matches + recent updates
"""
        self.console.print(banner)
        self.console.print()
    
    def print_date_processing(self, date_str):
        """Print current date being processed"""
        self.console.print(f"[cyan]>> Processing: {date_str}[/cyan]")
    
    def print_daily_stats(self, label, count):
        """
        Print daily collection stats with clean alignment
        
        Args:
            label: Stat label (e.g., 'Fixtures', 'Teams updated')
            count: Number to display
        """
        self.console.print(f"   {label:.<15}: {count:>6,}")
    
    def print_completion_banner(self, mode, runtime):
        """
        Print completion banner
        
        Args:
            mode: 'comprehensive' or 'daily'
            runtime: timedelta object
        """
        if mode == 'comprehensive':
            banner = """
[bold green]+===============================================================+
|        COMPREHENSIVE COLLECTION COMPLETE                     |
+===============================================================+[/bold green]
"""
            self.console.print(banner)
            self.console.print(f"\nSwitching to DAILY mode for future runs...")
            self.console.print(f"Runtime: {runtime}\n")
        else:
            self.console.print("\n[bold green]*** DAILY COLLECTION COMPLETE ***[/bold green]")
            self.console.print(f"Runtime: {runtime}\n")
    
    def print_error(self, message):
        """Print error message"""
        self.console.print(f"[red]ERROR: {message}[/red]")
    
    def print_warning(self, message):
        """Print warning message"""
        self.console.print(f"[yellow]WARNING: {message}[/yellow]")
    
    def print_success(self, message):
        """Print success message"""
        self.console.print(f"[green]SUCCESS: {message}[/green]")
    
    def print_info(self, message):
        """Print info message"""
        self.console.print(f"[cyan]INFO: {message}[/cyan]")
    
    def print_separator(self):
        """Print separator line"""
        self.console.print("=" * 64, style="dim")
    
    def print_progress_summary(self, current, total, elapsed_time):
        """
        Print progress summary during comprehensive collection
        
        Args:
            current: Current item number
            total: Total items
            elapsed_time: Time elapsed so far
        """
        percentage = (current / total * 100) if total > 0 else 0
        
        # Simple progress bar
        bar_width = 40
        filled = int(bar_width * current / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_width - filled)
        
        self.console.print(f"\nProgress  [{bar}]  {percentage:.0f}%  {elapsed_time}", style="cyan")


# Create global instance
display = RetroDisplay()


# Convenience functions
def clear_screen():
    """Clear the console"""
    display.clear()


def show_header(mode, runtime_hours, runtime_minutes, dates_processed, dates_failed):
    """Show header"""
    display.print_header(mode, runtime_hours, runtime_minutes, dates_processed, dates_failed)


def show_stats(stats, today_stats):
    """Show statistics table"""
    display.print_stats_table(stats, today_stats)


def show_mode_banner(mode):
    """Show mode banner"""
    display.print_mode_banner(mode)


def show_date_processing(date_str):
    """Show date being processed"""
    display.print_date_processing(date_str)


def show_daily_stat(label, count):
    """Show daily stat line"""
    display.print_daily_stats(label, count)


def show_completion(mode, runtime):
    """Show completion banner"""
    display.print_completion_banner(mode, runtime)


def show_error(message):
    """Show error"""
    display.print_error(message)


def show_warning(message):
    """Show warning"""
    display.print_warning(message)


def show_success(message):
    """Show success"""
    display.print_success(message)


def show_info(message):
    """Show info"""
    display.print_info(message)


def show_separator():
    """Show separator line"""
    display.print_separator()


def show_progress(current, total, elapsed):
    """Show progress summary"""
    display.print_progress_summary(current, total, elapsed)