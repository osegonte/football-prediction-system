"""
Telegram Monitor - Enhanced with Database Stats
Place in: monitoring/telegram_monitor.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import asyncio
from datetime import datetime, timedelta
import logging

from telegram import Bot
from telegram.error import TelegramError
from database.connection import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramMonitor:
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        
        self.bot = Bot(token=self.bot_token)
        self.last_stats = {}
        self.start_time = datetime.now()
        
        logger.info("Telegram Monitor initialized")
    
    async def send_message(self, message, silent=False):
        """Send message with retry"""
        for attempt in range(3):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown',
                    disable_notification=silent
                )
                return True
            except TelegramError as e:
                logger.error(f"Telegram error (attempt {attempt+1}): {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
        return False
    
    async def get_stats(self):
        """Get database statistics"""
        try:
            with get_connection() as db:
                stats = {}
                
                # Counts
                for table in ['fixtures', 'team_matches', 'match_statistics', 'player_statistics']:
                    db.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f'{table}_count'] = db.fetchone()[0]
                
                # Today's additions
                db.execute("SELECT COUNT(*) FROM fixtures WHERE scraped_at::date = CURRENT_DATE")
                stats['fixtures_today'] = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM team_matches WHERE scraped_at::date = CURRENT_DATE")
                stats['team_matches_today'] = db.fetchone()[0]
                
                db.execute("SELECT COUNT(*) FROM match_statistics WHERE scraped_at::date = CURRENT_DATE")
                stats['match_stats_today'] = db.fetchone()[0]
                
                # Date range
                db.execute("SELECT MIN(date), MAX(date) FROM fixtures")
                date_range = db.fetchone()
                stats['date_min'] = date_range[0]
                stats['date_max'] = date_range[1]
                
                # Recent errors
                db.execute("""
                    SELECT COUNT(*) FROM scraping_log 
                    WHERE status = 'error' 
                    AND scraped_at > NOW() - INTERVAL '1 hour'
                """)
                stats['errors_hour'] = db.fetchone()[0]
                
                return stats
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return None
    
    async def send_startup(self):
        """Send startup notification"""
        message = f"""
*Football Collector Started*

Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Server: ThinkPad
Mode: Auto-detect

Updates every 30 minutes.
"""
        await self.send_message(message)
        logger.info("Sent startup message")
    
    async def send_progress(self):
        """Send progress update"""
        stats = await self.get_stats()
        if not stats:
            await self.send_message("Error: Could not fetch stats")
            return
        
        # Calculate growth
        growth = {}
        for key in ['fixtures_count', 'team_matches_count', 'match_statistics_count']:
            current = stats[key]
            previous = self.last_stats.get(key, 0)
            growth[key] = current - previous
        
        self.last_stats = stats
        
        # Runtime
        runtime = datetime.now() - self.start_time
        hours = int(runtime.total_seconds() / 3600)
        minutes = int((runtime.total_seconds() % 3600) / 60)
        
        message = f"""
*Progress Update*

Runtime: {hours}h {minutes}m

*Database:*
Fixtures: {stats['fixtures_count']:,} (+{growth['fixtures_count']:,})
Team Matches: {stats['team_matches_count']:,} (+{growth['team_matches_count']:,})
Match Stats: {stats['match_statistics_count']:,} (+{growth['match_statistics_count']:,})
Players: {stats['player_statistics_count']:,}

*Today:*
Fixtures: {stats['fixtures_today']:,}
Team Matches: {stats['team_matches_today']:,}
Match Stats: {stats['match_stats_today']:,}

*Coverage:*
{stats['date_min']} → {stats['date_max']}
"""
        
        if stats['errors_hour'] > 0:
            message += f"\nErrors (last hour): {stats['errors_hour']}"
        
        await self.send_message(message, silent=True)
        logger.info("Sent progress update")
    
    async def send_daily_summary(self):
        """Send daily summary"""
        stats = await self.get_stats()
        if not stats:
            return
        
        runtime = datetime.now() - self.start_time
        days = runtime.days
        
        message = f"""
*Daily Summary - Day {days + 1}*

*Total:*
Fixtures: {stats['fixtures_count']:,}
Team Matches: {stats['team_matches_count']:,}
Match Stats: {stats['match_statistics_count']:,}

*Today:*
Fixtures: {stats['fixtures_today']:,}
Team Matches: {stats['team_matches_today']:,}
Match Stats: {stats['match_stats_today']:,}

*Coverage:*
{stats['date_min']} → {stats['date_max']}

Runtime: {days}d {runtime.seconds // 3600}h
"""
        
        await self.send_message(message)
        logger.info("Sent daily summary")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        await self.send_startup()
        
        last_progress = datetime.now()
        last_daily = datetime.now()
        
        try:
            while True:
                now = datetime.now()
                
                # Progress every 30 minutes
                if (now - last_progress).total_seconds() > 1800:
                    await self.send_progress()
                    last_progress = now
                
                # Daily summary at midnight
                if now.hour == 0 and (now - last_daily).days >= 1:
                    await self.send_daily_summary()
                    last_daily = now
                
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("Monitoring stopped")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await self.send_message(f"Error: {e}")


async def main():
    monitor = TelegramMonitor()
    await monitor.monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())