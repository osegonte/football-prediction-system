"""
TELEGRAM MONITOR BOT
Live progress monitoring for data collection

Commands:
  /start - Welcome & help
  /status - Current collection status
  /progress - Live progress bar with stats
  /teams - Team collection progress
  /stats - Database statistics
  /latest - Latest collected data

Usage:
  python telegram_monitor.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

from database.connection import get_connection

# Load environment
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_collection_stats():
    """Get current collection statistics."""
    
    try:
        with get_connection() as db:
            # Fixtures
            db.execute("SELECT COUNT(*), COUNT(DISTINCT date) FROM fixtures")
            fixture_count, days_collected = db.fetchone()
            
            # Teams
            db.execute("""
                SELECT COUNT(DISTINCT team_id) FROM (
                    SELECT home_team_id as team_id FROM fixtures
                    UNION SELECT away_team_id as team_id FROM fixtures
                ) teams
            """)
            total_teams = db.fetchone()[0]
            
            db.execute("""
                SELECT COUNT(DISTINCT team_id) FROM team_matches
                WHERE match_year < 2025
            """)
            teams_with_baseline = db.fetchone()[0]
            
            # Match stats
            db.execute("SELECT COUNT(DISTINCT match_id) FROM match_statistics")
            matches_with_stats = db.fetchone()[0]
            
            # Player stats
            db.execute("SELECT COUNT(DISTINCT match_id) FROM player_statistics")
            matches_with_players = db.fetchone()[0]
            
            # Team matches
            db.execute("SELECT COUNT(*) FROM team_matches")
            total_team_matches = db.fetchone()[0]
            
            return {
                'fixtures': fixture_count,
                'days_collected': days_collected,
                'total_teams': total_teams,
                'teams_with_baseline': teams_with_baseline,
                'matches_with_stats': matches_with_stats,
                'matches_with_players': matches_with_players,
                'team_matches': total_team_matches
            }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None


def create_progress_bar(current, total, length=20):
    """Create a text progress bar."""
    
    if total == 0:
        return "░" * length + " 0%"
    
    percentage = min(100, (current / total) * 100)
    filled = int((current / total) * length)
    
    bar = "▓" * filled + "░" * (length - filled)
    return f"{bar} {percentage:.1f}%"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show help."""
    
    help_text = """
⚽ **FOOTBALL DATA COLLECTOR MONITOR**

📊 **Commands:**
/status - Collection status overview
/progress - Live progress with visual bars
/teams - Team collection details
/stats - Full database statistics
/latest - Latest collected data

🔄 Updates available 24/7
🤖 Bot running on ThinkPad
    """
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command - quick overview."""
    
    stats = get_collection_stats()
    
    if not stats:
        await update.message.reply_text("❌ Error connecting to database")
        return
    
    status_text = f"""
📊 **COLLECTION STATUS**

✅ Fixtures: {stats['fixtures']:,}
📅 Days collected: {stats['days_collected']}
⚽ Teams: {stats['total_teams']:,}
📊 Team matches: {stats['team_matches']:,}
📈 Match statistics: {stats['matches_with_stats']:,}
👥 Player records: {stats['matches_with_players']:,}

🕒 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await update.message.reply_text(status_text)


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Progress command - visual progress bars."""
    
    stats = get_collection_stats()
    
    if not stats:
        await update.message.reply_text("❌ Error connecting to database")
        return
    
    # Calculate target (Jan 1 → Today)
    start_date = datetime(2025, 1, 1)
    total_days = (datetime.now() - start_date).days + 1
    
    # Progress bars
    days_bar = create_progress_bar(stats['days_collected'], total_days)
    teams_bar = create_progress_bar(stats['teams_with_baseline'], stats['total_teams'])
    
    progress_text = f"""
📊 **COLLECTION PROGRESS**

**Fixtures Collection**
{days_bar}
{stats['days_collected']}/{total_days} days

**Team Baseline**
{teams_bar}
{stats['teams_with_baseline']:,}/{stats['total_teams']:,} teams

**Statistics**
▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░ In Progress
Match stats: {stats['matches_with_stats']:,}
Player stats: {stats['matches_with_players']:,}

🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await update.message.reply_text(progress_text)


async def teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teams command - team collection details."""
    
    try:
        with get_connection() as db:
            # Top teams by match count
            db.execute("""
                SELECT team_name, COUNT(*) as match_count,
                       COUNT(CASE WHEN match_year < 2025 THEN 1 END) as baseline,
                       COUNT(CASE WHEN match_year = 2025 THEN 1 END) as yr_2025
                FROM team_matches
                GROUP BY team_name
                ORDER BY match_count DESC
                LIMIT 10
            """)
            
            top_teams = db.fetchall()
        
        teams_text = "⚽ **TOP 10 TEAMS BY MATCHES**\n\n"
        
        for i, (name, total, baseline, yr_2025) in enumerate(top_teams, 1):
            teams_text += f"{i}. {name}\n"
            teams_text += f"   Total: {total} | Baseline: {baseline} | 2025: {yr_2025}\n\n"
        
        await update.message.reply_text(teams_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command - full database statistics."""
    
    try:
        with get_connection() as db:
            # Get comprehensive stats
            db.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM fixtures) as fixtures,
                    (SELECT COUNT(*) FROM team_matches) as team_matches,
                    (SELECT COUNT(*) FROM match_statistics) as match_stats,
                    (SELECT COUNT(*) FROM player_statistics) as player_stats,
                    (SELECT COUNT(DISTINCT tournament_name) FROM fixtures) as tournaments,
                    (SELECT MAX(date) FROM fixtures) as latest_date
            """)
            
            row = db.fetchone()
        
        stats_text = f"""
📊 **FULL DATABASE STATISTICS**

**Tables:**
├─ Fixtures: {row[0]:,}
├─ Team Matches: {row[1]:,}
├─ Match Statistics: {row[2]:,}
└─ Player Statistics: {row[3]:,}

**Coverage:**
├─ Tournaments: {row[4]}
└─ Latest date: {row[5]}

🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(stats_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def latest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Latest command - show latest collected data."""
    
    try:
        with get_connection() as db:
            # Latest fixtures
            db.execute("""
                SELECT date, home_team_name, away_team_name, home_score, away_score
                FROM fixtures
                ORDER BY scraped_at DESC
                LIMIT 5
            """)
            
            latest_fixtures = db.fetchall()
        
        latest_text = "🆕 **LATEST FIXTURES COLLECTED**\n\n"
        
        for date, home, away, home_score, away_score in latest_fixtures:
            score = f"{home_score}-{away_score}" if home_score is not None else "vs"
            latest_text += f"📅 {date}\n{home} {score} {away}\n\n"
        
        await update.message.reply_text(latest_text)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


def main():
    """Start the bot."""
    
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("teams", teams_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("latest", latest_command))
    
    # Start bot
    logger.info("✅ Telegram Monitor Bot started")
    logger.info(f"📱 Send /start to your bot to begin monitoring")
    
    app.run_polling()


if __name__ == "__main__":
    main()