"""
Enhanced Telegram Bot for Football Data Collection System
Features: Progress monitoring, database search, auto-notifications
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import get_database_stats
from database.insert import get_active_session, get_last_session
from database.connection import get_connection

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with enhanced info."""
    welcome_text = """
⚽ **Football Data Collection System**
━━━━━━━━━━━━━━━━━━━━━━━━━

**📊 Monitoring Commands:**
/status - System overview
/progress - Live scraping progress
/db - Database statistics
/health - System health check

**🔍 Search Commands:**
/search [team] - Find team in database
/stats [team] - Quick team statistics
/recent - Last 10 collected matches

**ℹ️ Help:**
/help - Show detailed help

━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot ready and monitoring!
    """
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed help."""
    help_text = """
**📚 COMMAND REFERENCE**
━━━━━━━━━━━━━━━━━━━━━━━━━

**Monitoring:**
- /status - Current system status
- /progress - Live scraping with progress bar
- /db - Database record counts
- /health - System diagnostics

**Search:**
- /search Liverpool - Find team
- /stats Arsenal - Team statistics
- /recent - Last 10 matches collected

**Examples:**
/search "Manchester United"
/stats Chelsea
    """
    await update.message.reply_text(help_text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System status overview."""
    try:
        # Check active scraping
        active = get_active_session()
        
        # Get database stats
        db_stats = get_database_stats()
        
        if active:
            status_emoji = "🔄"
            status_text = "SCRAPING IN PROGRESS"
        else:
            status_emoji = "✅"
            status_text = "IDLE - Ready to scrape"
        
        message = f"""
{status_emoji} **SYSTEM STATUS**
━━━━━━━━━━━━━━━━━━━━━━━━━

**Status:** {status_text}

**Database:**
- Fixtures: {db_stats['fixtures']:,}
- Teams: {db_stats['teams']:,}
- Matches: {db_stats['matches']:,}
- With Stats: {db_stats['stats']:,}

**Last Update:** {db_stats['last_scrape'].strftime('%d %b %Y, %H:%M') if db_stats['last_scrape'] else 'Never'}

━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in status: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live scraping progress."""
    try:
        active = get_active_session()
        
        if active:
            teams_done = active['teams_completed'] or 0
            total_teams = active['total_teams']
            progress_pct = (teams_done / total_teams * 100) if total_teams > 0 else 0
            
            # Progress bar
            bar_length = 20
            filled = int(bar_length * progress_pct / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Time elapsed
            elapsed_min = active['elapsed_seconds'] // 60
            elapsed_sec = active['elapsed_seconds'] % 60
            
            # Estimate remaining
            if teams_done > 0:
                avg_per_team = active['elapsed_seconds'] / teams_done
                remaining_teams = total_teams - teams_done
                remaining_sec = int(avg_per_team * remaining_teams)
                remaining_min = remaining_sec // 60
                eta = f"~{remaining_min} min remaining"
            else:
                eta = "Calculating..."
            
            message = f"""
⏳ **SCRAPING IN PROGRESS**
━━━━━━━━━━━━━━━━━━━━━━━━━

{bar} {progress_pct:.1f}%

**Teams:** {teams_done}/{total_teams}
**Date:** {active['scrape_date']}
**Strategy:** {active['strategy']}
{f"**League:** {active['league_filter']}" if active['league_filter'] else ""}

**Time Elapsed:** {elapsed_min}m {elapsed_sec}s
**ETA:** {eta}

━━━━━━━━━━━━━━━━━━━━━━━━━
            """
        else:
            last = get_last_session()
            if last:
                duration_min = (last['duration_seconds'] or 0) // 60
                message = f"""
✅ **LAST SESSION**
━━━━━━━━━━━━━━━━━━━━━━━━━

**Date:** {last['scrape_date']}
**Teams:** {last['total_teams']}
**Matches/Team:** {last['matches_per_team']}
**Duration:** {duration_min} minutes
**Status:** {last['status']}

━━━━━━━━━━━━━━━━━━━━━━━━━
No scraping currently active.
                """
            else:
                message = "ℹ️ No scraping data found. Run a scrape first!"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in progress: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Database statistics."""
    try:
        stats = get_database_stats()
        
        message = f"""
💾 **DATABASE STATISTICS**
━━━━━━━━━━━━━━━━━━━━━━━━━

📅 **Fixtures:** {stats['fixtures']:,}
👥 **Teams:** {stats['teams']:,}
⚽ **Matches:** {stats['matches']:,}
📊 **With Stats:** {stats['stats']:,}

🕐 **Last Update:**
{stats['last_scrape'].strftime('%d %b %Y, %H:%M') if stats['last_scrape'] else 'Never'}

━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in db_command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for a team in database."""
    if not context.args:
        await update.message.reply_text("❌ Usage: /search [team name]\n\nExample: /search Liverpool")
        return
    
    team_name = ' '.join(context.args)
    
    try:
        with get_connection() as db:
            db.execute("""
                SELECT team_name, COUNT(*) as match_count
                FROM team_matches
                WHERE team_name ILIKE %s
                GROUP BY team_name
                ORDER BY match_count DESC
                LIMIT 5
            """, (f'%{team_name}%',))
            
            results = db.fetchall()
        
        if not results:
            await update.message.reply_text(f"❌ No teams found matching '{team_name}'")
            return
        
        message = f"🔍 **SEARCH RESULTS: '{team_name}'**\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for team, count in results:
            message += f"• {team} ({count} matches)\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\nUse /stats [team] for details"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick team statistics."""
    if not context.args:
        await update.message.reply_text("❌ Usage: /stats [team name]\n\nExample: /stats Arsenal")
        return
    
    team_name = ' '.join(context.args)
    
    try:
        with get_connection() as db:
            # Get team matches
            db.execute("""
                SELECT 
                    team_name,
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) as losses,
                    AVG(team_score) as avg_gf,
                    AVG(opponent_score) as avg_ga
                FROM team_matches
                WHERE team_name ILIKE %s
                GROUP BY team_name
                LIMIT 1
            """, (f'%{team_name}%',))
            
            result = db.fetchone()
        
        if not result:
            await update.message.reply_text(f"❌ No data found for '{team_name}'")
            return
        
        team, matches, w, d, l, gf, ga = result
        
        # Get last 7 results
        with get_connection() as db:
            db.execute("""
                SELECT result
                FROM team_matches
                WHERE team_name ILIKE %s
                ORDER BY match_date DESC
                LIMIT 7
            """, (f'%{team_name}%',))
            form = [r[0] for r in db.fetchall()]
        
        form_str = ' '.join(form) if form else 'N/A'
        
        message = f"""
📊 **{team.upper()}**
━━━━━━━━━━━━━━━━━━━━━━━━━

**Record:** {w}W {d}D {l}L ({matches} matches)

**Goals:**
- For: {gf:.1f} per match
- Against: {ga:.1f} per match

**Last 7:** {form_str}

━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last 10 collected matches."""
    try:
        with get_connection() as db:
            db.execute("""
                SELECT 
                    team_name,
                    opponent_name,
                    team_score,
                    opponent_score,
                    result,
                    match_date,
                    venue
                FROM team_matches
                ORDER BY scraped_at DESC
                LIMIT 10
            """)
            
            matches = db.fetchall()
        
        if not matches:
            await update.message.reply_text("❌ No matches found")
            return
        
        message = "📅 **LAST 10 COLLECTED MATCHES**\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for team, opp, gf, ga, result, date, venue in matches:
            result_emoji = "✅" if result == 'W' else "❌" if result == 'L' else "➖"
            venue_str = "H" if venue == "Home" else "A"
            message += f"{result_emoji} {team} {gf}-{ga} {opp} ({venue_str})\n"
            message += f"   {date}\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in recent: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System health check."""
    try:
        checks = []
        
        # Check database connection
        try:
            with get_connection() as db:
                db.execute("SELECT 1")
            checks.append("✅ Database: Connected")
        except:
            checks.append("❌ Database: Connection failed")
        
        # Check data freshness
        stats = get_database_stats()
        if stats['last_scrape']:
            hours_ago = (datetime.now() - stats['last_scrape']).total_seconds() / 3600
            if hours_ago < 24:
                checks.append(f"✅ Data: Fresh ({int(hours_ago)}h old)")
            else:
                checks.append(f"⚠️ Data: Stale ({int(hours_ago)}h old)")
        else:
            checks.append("⚠️ Data: No scrapes yet")
        
        # Check data volume
        if stats['fixtures'] > 100 and stats['teams'] > 50:
            checks.append(f"✅ Volume: Good ({stats['fixtures']} fixtures)")
        else:
            checks.append(f"⚠️ Volume: Low ({stats['fixtures']} fixtures)")
        
        message = "🏥 **SYSTEM HEALTH**\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += '\n'.join(checks)
        message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in health: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main():
    """Start the enhanced bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add all command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("progress", progress))
    application.add_handler(CommandHandler("db", db_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("recent", recent_command))
    application.add_handler(CommandHandler("health", health_command))
    
    logger.info("Enhanced bot starting...")
    print("✅ Enhanced Football Data Bot running!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Commands:")
    print("  /status - System overview")
    print("  /progress - Live scraping progress")
    print("  /search [team] - Find team")
    print("  /stats [team] - Team statistics")
    print("  /recent - Last 10 matches")
    print("  /health - System health")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()