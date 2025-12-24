"""
Telegram Bot for Football Data Verification & Monitoring
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.queries import get_verification_sample, get_database_stats, get_team_detailed_stats
from database.insert import get_active_session, get_last_session
from database.connection import get_connection

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Conversation states
SELECTING_TEAM = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    welcome_text = """
🏟️ **Football Data Verification Bot**

**Commands:**
/verify - Quick verification sample
/verifystats - Detailed match statistics (interactive)
/status - Database statistics
/progress - Scraping progress
/help - Show this help message
    """
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command."""
    help_text = """
**Commands:**

/verify - Quick verification
  • Random fixture with basic stats

/verifystats - Detailed statistics (NEW!)
  • Shows teams with stats
  • Select team interactively
  • See ALL collected statistics

/status - Database info
/progress - Scraping progress
    """
    await update.message.reply_text(help_text)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick verification."""
    await update.message.reply_text("🔍 Fetching verification sample...")
    
    try:
        sample = get_verification_sample()
        
        if not sample:
            await update.message.reply_text("❌ No data available. Run scraper first!")
            return
        
        fixture = sample['fixture']
        home_history = sample['home_history']
        away_history = sample['away_history']
        
        home_with_stats = sum(1 for m in home_history if m.get('has_stats'))
        away_with_stats = sum(1 for m in away_history if m.get('has_stats'))
        
        message = f"""
🔍 **VERIFICATION SAMPLE**
{'━' * 30}

📅 **FIXTURE**
{fixture['home_team']} vs {fixture['away_team']}
Date: {fixture['date']}
League: {fixture['tournament']}

{'━' * 30}

📊 **{fixture['home_team'].upper()}**
Last 7: {', '.join([m['result'] for m in home_history[:7]])}
Stats available: {home_with_stats}/7 matches

📊 **{fixture['away_team'].upper()}**
Last 7: {', '.join([m['result'] for m in away_history[:7]])}
Stats available: {away_with_stats}/7 matches

{'━' * 30}

Use /verifystats for detailed statistics!
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in verify: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def verifystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show teams with statistics available."""
    await update.message.reply_text("🔍 Finding teams with statistics...")
    
    try:
        with get_connection() as db:
            db.execute("""
                SELECT DISTINCT tm.team_name, COUNT(DISTINCT ms.match_id) as stat_count
                FROM team_matches tm
                JOIN match_statistics ms ON tm.match_id = ms.match_id
                GROUP BY tm.team_name
                ORDER BY stat_count DESC, tm.team_name
            """)
            
            teams = db.fetchall()
        
        if not teams:
            await update.message.reply_text("❌ No teams with statistics found. Run match stats scraper first!")
            return ConversationHandler.END
        
        # Store teams in context
        context.user_data['teams'] = teams
        
        # Build selection message
        message = "📊 **TEAMS WITH STATISTICS**\n"
        message += "━" * 30 + "\n\n"
        
        for i, (team_name, count) in enumerate(teams, 1):
            message += f"{i}. {team_name} ({count} matches)\n"
        
        message += "\n" + "━" * 30 + "\n"
        message += "**Reply with team number to see stats**\n"
        message += "Or type /cancel to exit"
        
        await update.message.reply_text(message)
        
        return SELECTING_TEAM
        
    except Exception as e:
        logger.error(f"Error in verifystats: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END


async def team_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle team selection."""
    try:
        selection = int(update.message.text)
        teams = context.user_data.get('teams', [])
        
        if selection < 1 or selection > len(teams):
            await update.message.reply_text(f"❌ Invalid selection. Choose 1-{len(teams)}")
            return SELECTING_TEAM
        
        team_name = teams[selection - 1][0]
        
        await update.message.reply_text(f"📊 Fetching detailed stats for {team_name}...")
        
        # Get detailed stats
        matches = get_team_detailed_stats(team_name, limit=3)
        
        if not matches:
            await update.message.reply_text(f"❌ No stats found for {team_name}")
            return ConversationHandler.END
        
        # Build detailed message
        for match in matches:
            message = f"""
📊 **{team_name.upper()} STATISTICS**
{'━' * 40}

**Match:** vs {match['opponent']}
**Score:** {match['score']} ({match['result']})
**Date:** {match['date']}
**Venue:** {match['venue']}

{'━' * 40}
"""
            
            for period in ['1ST', '2ND']:
                if period in match['periods']:
                    stats = match['periods'][period]
                    message += f"\n**{period} HALF:**\n"
                    message += f"⚽ Possession: {stats['possession']}\n"
                    message += f"🎯 xG: {stats['xg']}\n"
                    message += f"🎯 Shots: {stats['shots']}\n"
                    message += f"🎯 On Target: {stats['shots_on_target']}\n"
                    message += f"🎯 Off Target: {stats['shots_off_target']}\n"
                    message += f"🚫 Blocked: {stats['blocked_shots']}\n"
                    message += f"📦 Inside Box: {stats['shots_inside_box']}\n"
                    message += f"📦 Outside Box: {stats['shots_outside_box']}\n"
                    message += f"⭐ Big Chances: {stats['big_chances']}\n"
                    message += f"❌ BC Missed: {stats['big_chances_missed']}\n"
                    message += f"📊 Passes: {stats['passes']}\n"
                    message += f"🏃 Tackles: {stats['tackles']}\n"
                    message += f"🔄 Interceptions: {stats['interceptions']}\n"
                    message += f"🛡️ Clearances: {stats['clearances']}\n"
                    message += f"🧤 Saves: {stats['saves']}\n"
                    message += f"🚩 Corners: {stats['corners']}\n"
                    message += f"⚠️ Fouls: {stats['fouls']}\n"
            
            message += "\n" + "━" * 40 + "\n"
            message += "✅ Verify on Sofascore.com\n"
            
            await update.message.reply_text(message)
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a number")
        return SELECTING_TEAM
    except Exception as e:
        logger.error(f"Error in team_selected: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation."""
    await update.message.reply_text("❌ Cancelled")
    return ConversationHandler.END


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show database status."""
    try:
        stats = get_database_stats()
        
        last_scrape = stats['last_scrape'].strftime('%d %b %Y, %H:%M') if stats['last_scrape'] else 'Never'
        
        message = f"""
💾 **DATABASE STATUS**
{'━' * 30}

�� Fixtures: {stats['fixtures']}
👥 Teams: {stats['teams']}
⚽ Matches: {stats['matches']}
📈 With Stats: {stats['stats']}
🕐 Last Scrape: {last_scrape}

{'━' * 30}
        """
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in status: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show scraping progress."""
    try:
        active = get_active_session()
        
        if active:
            teams_completed = active['teams_completed'] or 0
            total_teams = active['total_teams']
            progress_pct = (teams_completed / total_teams * 100) if total_teams > 0 else 0
            
            bar_length = 20
            filled = int(bar_length * progress_pct / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            message = f"""
⏳ **SCRAPING IN PROGRESS**
{'━' * 30}

{bar} {progress_pct:.1f}%

👥 Teams: {teams_completed}/{total_teams}
📅 Date: {active['scrape_date']}

{'━' * 30}
            """
        else:
            last = get_last_session()
            if last:
                message = f"""
✅ **LAST SESSION**
{'━' * 30}

📅 Date: {last['scrape_date']}
👥 Teams: {last['total_teams']}
⏱️ Duration: {(last['duration_seconds'] or 0) // 60} min

{'━' * 30}
                """
            else:
                message = "ℹ️ No scraping data found"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error in progress: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


def main():
    """Start bot."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for verifystats
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('verifystats', verifystats)],
        states={
            SELECTING_TEAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, team_selected)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("progress", progress))
    
    logger.info("Bot starting...")
    print("✅ Bot running!")
    print("Commands: /verify, /verifystats, /status, /progress")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
