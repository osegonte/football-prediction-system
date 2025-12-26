"""
Enhanced Retro Terminal UI - Beautiful Live Dashboard
Place in: display/terminal_ui.py

Features:
- Animated progress bars
- Live stats updates
- Real-time counters
- Visual indicators
- Clean retro aesthetic
"""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.text import Text
from datetime import datetime
import time

console = Console()


class EnhancedRetroDisplay:
    """Enhanced retro terminal UI with live updates"""
    
    def __init__(self):
        self.console = console
        self.start_time = datetime.now()
        self.layout = Layout()
        
    def create_live_dashboard(self, mode, stats, today_stats, current_date=None, total_days=0):
        """
        Create live updating dashboard
        
        Args:
            mode: 'comprehensive' or 'daily'
            stats: Overall stats dict
            today_stats: Today's stats dict
            current_date: Current date being processed
            total_days: Total days to process
        """
        # Calculate runtime
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() / 3600)
        minutes = int((elapsed.total_seconds() % 3600) / 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        # Mode display
        mode_display = "COMPREHENSIVE COLLECTION" if mode == 'comprehensive' else "DAILY UPDATE"
        
        # Create header
        header_text = f"""
╔══════════════════════════════════════════════════════════════════╗
║  FOOTBALL DATA COLLECTOR - {mode_display:^24}  ║
╠══════════════════════════════════════════════════════════════════╣
║  Runtime: {hours:02d}h {minutes:02d}m {seconds:02d}s                                              ║"""
        
        if mode == 'comprehensive' and total_days > 0:
            progress_pct = (stats['dates_processed'] / total_days * 100) if total_days > 0 else 0
            header_text += f"""
║  Progress: {stats['dates_processed']:3d}/{total_days:3d} days ({progress_pct:5.1f}%)                              ║"""
        
        header_text += f"""
║  Status: {stats['dates_processed']:3d} processed, {stats['dates_failed']:3d} failed                       ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        # Create stats table
        stats_table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
        stats_table.add_column("METRIC", style="cyan", width=25)
        stats_table.add_column("TOTAL", justify="right", style="green", width=15)
        stats_table.add_column("TODAY", justify="right", style="yellow", width=12)
        stats_table.add_column("RATE", justify="right", style="magenta", width=12)
        
        # Calculate rates
        runtime_hours = elapsed.total_seconds() / 3600 if elapsed.total_seconds() > 0 else 1
        fixtures_rate = stats['fixtures'] / runtime_hours if runtime_hours > 0 else 0
        matches_rate = stats['team_matches'] / runtime_hours if runtime_hours > 0 else 0
        
        stats_table.add_row(
            "Fixtures",
            f"{stats['fixtures']:,}",
            f"{today_stats['fixtures_today']:,}",
            f"{fixtures_rate:.0f}/hr"
        )
        stats_table.add_row(
            "Team Matches",
            f"{stats['team_matches']:,}",
            f"{today_stats['team_matches_today']:,}",
            f"{matches_rate:.0f}/hr"
        )
        stats_table.add_row(
            "Match Statistics",
            f"{stats['match_stats']:,}",
            f"{today_stats['match_stats_today']:,}",
            f"--"
        )
        stats_table.add_row(
            "Player Statistics",
            f"{stats['player_stats']:,}",
            f"--",
            f"--"
        )
        
        # Current activity
        if current_date:
            activity = f"\n[cyan]>>> Processing: {current_date}[/cyan]\n"
        else:
            activity = ""
        
        # Combine everything
        display = header_text + "\n" + activity
        
        return display, stats_table
    
    def create_progress_bar(self, current, total, description="Progress"):
        """Create animated progress bar"""
        if total == 0:
            return ""
        
        percentage = (current / total * 100)
        filled = int(40 * current / total)
        bar = '█' * filled + '░' * (40 - filled)
        
        return f"\n[cyan]{description}[/cyan]  [{bar}]  {percentage:5.1f}%  ({current}/{total})\n"
    
    def show_startup_banner(self, mode):
        """Show enhanced startup banner"""
        if mode == 'comprehensive':
            banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ███████╗ ██████╗  ██████╗ ████████╗██████╗  █████╗ ██╗      ║
║     ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝██╔══██╗██╔══██╗██║      ║
║     █████╗  ██║   ██║██║   ██║   ██║   ██████╔╝███████║██║      ║
║     ██╔══╝  ██║   ██║██║   ██║   ██║   ██╔══██╗██╔══██║██║      ║
║     ██║     ╚██████╔╝╚██████╔╝   ██║   ██████╔╝██║  ██║███████╗ ║
║     ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝ ║
║                                                                  ║
║              DATA COLLECTOR - COMPREHENSIVE MODE                 ║
║                                                                  ║
║              Collecting: 2025-01-01 --> Today                    ║
║              Estimated Runtime: 2-3 days                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        else:
            banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              FOOTBALL DATA COLLECTOR                             ║
║              DAILY UPDATE MODE                                   ║
║                                                                  ║
║              Collecting Today's Matches + Updates                ║
║              Estimated Runtime: 5-10 minutes                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        self.console.print(banner, style="bold cyan")
        self.console.print()
    
    def show_completion_banner(self, mode, runtime, stats):
        """Show enhanced completion banner"""
        hours = int(runtime.total_seconds() / 3600)
        minutes = int((runtime.total_seconds() % 3600) / 60)
        
        if mode == 'comprehensive':
            banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              ✓✓✓ COMPREHENSIVE COLLECTION COMPLETE ✓✓✓          ║
║                                                                  ║
║              Runtime: {hours:02d}h {minutes:02d}m                                    ║
║                                                                  ║
║              Final Statistics:                                   ║
║              - Fixtures: {stats['fixtures']:,}                   
║              - Team Matches: {stats['team_matches']:,}           
║              - Match Statistics: {stats['match_stats']:,}        
║                                                                  ║
║              >>> Switching to DAILY mode for future runs <<<    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        else:
            banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              ✓✓✓ DAILY COLLECTION COMPLETE ✓✓✓                  ║
║                                                                  ║
║              Runtime: {minutes:02d}m                                         ║
║              Updates: {stats['fixtures']} fixtures, {stats['match_stats']} match stats     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        self.console.print(banner, style="bold green")
    
    def show_error(self, message):
        """Show error with visual emphasis"""
        self.console.print(f"\n[bold red]!!! ERROR !!![/bold red]")
        self.console.print(f"[red]{message}[/red]\n")
    
    def show_warning(self, message):
        """Show warning"""
        self.console.print(f"[yellow]⚠ WARNING: {message}[/yellow]")
    
    def show_success(self, message):
        """Show success"""
        self.console.print(f"[green]✓ {message}[/green]")
    
    def show_processing_date(self, date_str, batch_num=None, total_batches=None):
        """Show date being processed with visual indicator"""
        if batch_num and total_batches:
            self.console.print(f"\n[cyan]>>> [{batch_num}/{total_batches}] Processing: {date_str}[/cyan]")
        else:
            self.console.print(f"\n[cyan]>>> Processing: {date_str}[/cyan]")
    
    def show_stage(self, stage_name, items_count=None):
        """Show current stage"""
        if items_count:
            self.console.print(f"[yellow]▶ {stage_name}: {items_count} items[/yellow]")
        else:
            self.console.print(f"[yellow]▶ {stage_name}[/yellow]")
    
    def show_stage_complete(self, stage_name, count):
        """Show stage completion"""
        self.console.print(f"[green]✓ {stage_name}: {count:,} collected[/green]")


# Global instance
display = EnhancedRetroDisplay()


# Convenience functions
def show_startup_banner(mode):
    """Show startup banner"""
    display.show_startup_banner(mode)


def create_live_dashboard(mode, stats, today_stats, current_date=None, total_days=0):
    """Create live dashboard"""
    return display.create_live_dashboard(mode, stats, today_stats, current_date, total_days)


def create_progress_bar(current, total, description="Progress"):
    """Create progress bar"""
    return display.create_progress_bar(current, total, description)


def show_completion_banner(mode, runtime, stats):
    """Show completion banner"""
    display.show_completion_banner(mode, runtime, stats)


def show_error(message):
    """Show error"""
    display.show_error(message)


def show_warning(message):
    """Show warning"""
    display.show_warning(message)


def show_success(message):
    """Show success"""
    display.show_success(message)


def show_processing_date(date_str, batch_num=None, total_batches=None):
    """Show processing date"""
    display.show_processing_date(date_str, batch_num, total_batches)


def show_stage(stage_name, items_count=None):
    """Show stage"""
    display.show_stage(stage_name, items_count)


def show_stage_complete(stage_name, count):
    """Show stage complete"""
    display.show_stage_complete(stage_name, count)