"""
COMPREHENSIVE FOOTBALL DATA COLLECTOR
Single script that collects ALL data from Jan 1, 2025 → Today

What it does:
1. Scrapes all fixtures (Jan 1 → Today)
2. For each unique team:
   - 10 baseline matches (before Jan 1, 2025)
   - All 2025 matches
   - Match statistics (detailed stats)
   - Player statistics (individual players)
3. Tracks progress in database
4. Resumes automatically if interrupted
5. Runs until complete

Usage:
  python collector.py
"""

import logging
from datetime import datetime, timedelta
import time
from pathlib import Path

from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection
from config.leagues import START_DATE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveCollector:
    """Single collector for all football data."""
    
    def __init__(self):
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        
        self.start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
        self.end_date = datetime.now()
        
        logger.info("Collector initialized")
        logger.info(f"Range: {self.start_date.date()} → {self.end_date.date()}")
    
    def get_progress(self):
        """Get current collection progress."""
        
        with get_connection() as db:
            # Fixtures progress
            db.execute("SELECT COUNT(*), COUNT(DISTINCT date) FROM fixtures")
            fixture_count, days_with_fixtures = db.fetchone()
            
            # Teams progress
            db.execute("""
                SELECT COUNT(DISTINCT team_id) FROM (
                    SELECT home_team_id as team_id FROM fixtures
                    UNION
                    SELECT away_team_id as team_id FROM fixtures
                ) teams
            """)
            total_teams = db.fetchone()[0]
            
            db.execute("""
                SELECT COUNT(DISTINCT team_id) FROM team_matches
                WHERE match_year < 2025
            """)
            teams_with_baseline = db.fetchone()[0]
            
            # Match stats progress
            db.execute("SELECT COUNT(DISTINCT match_id) FROM match_statistics")
            matches_with_stats = db.fetchone()[0]
            
            # Player stats progress
            db.execute("SELECT COUNT(DISTINCT match_id) FROM player_statistics")
            matches_with_players = db.fetchone()[0]
            
            return {
                'fixtures': fixture_count,
                'days_collected': days_with_fixtures,
                'total_teams': total_teams,
                'teams_with_baseline': teams_with_baseline,
                'matches_with_stats': matches_with_stats,
                'matches_with_players': matches_with_players
            }
    
    def collect_fixtures(self):
        """Collect all fixtures from start_date to end_date."""
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 1: FIXTURES COLLECTION")
        logger.info("="*80)
        
        total_days = (self.end_date - self.start_date).days + 1
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # Check if already collected
            with get_connection() as db:
                db.execute("SELECT COUNT(*) FROM fixtures WHERE date = %s", (current_date.date(),))
                if db.fetchone()[0] > 0:
                    logger.info(f"✓ {current_date.date()} already collected")
                    current_date += timedelta(days=1)
                    continue
            
            # Scrape fixtures
            logger.info(f"📅 {current_date.date()}")
            fixtures = self.coordinator.scrape_daily_fixtures(current_date)
            
            if fixtures:
                logger.info(f"  ✅ {len(fixtures)} fixtures")
            
            current_date += timedelta(days=1)
            time.sleep(2)
        
        progress = self.get_progress()
        logger.info(f"\n✅ Fixtures complete: {progress['fixtures']} fixtures, {progress['days_collected']} days")
    
    def get_teams_needing_baseline(self):
        """Get teams that need baseline data."""
        
        with get_connection() as db:
            db.execute("""
                SELECT DISTINCT team_id, team_name FROM (
                    SELECT home_team_id as team_id, home_team_name as team_name FROM fixtures
                    UNION
                    SELECT away_team_id as team_id, away_team_name as team_name FROM fixtures
                ) all_teams
                WHERE team_id NOT IN (
                    SELECT DISTINCT team_id FROM team_matches
                    WHERE match_year < 2025
                )
                ORDER BY team_id
            """)
            
            return [(row[0], row[1]) for row in db.fetchall()]
    
    def collect_team_baseline(self):
        """Collect baseline data (10 matches before 2025) for all teams."""
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 2: TEAM BASELINE COLLECTION")
        logger.info("="*80)
        
        teams = self.get_teams_needing_baseline()
        logger.info(f"Teams needing baseline: {len(teams)}")
        
        for i, (team_id, team_name) in enumerate(teams, 1):
            logger.info(f"[{i}/{len(teams)}] ⚽ {team_name} (ID: {team_id})")
            
            # Scrape 10 matches back + all 2025 matches
            self.coordinator.scrape_team_history([team_id], matches_per_team=50)
            
            time.sleep(5)
            
            if i % 10 == 0:
                progress = self.get_progress()
                logger.info(f"  Progress: {progress['teams_with_baseline']}/{progress['total_teams']} teams")
        
        progress = self.get_progress()
        logger.info(f"\n✅ Baseline complete: {progress['teams_with_baseline']}/{progress['total_teams']} teams")
    
    def get_matches_needing_stats(self):
        """Get finished matches that need statistics."""
        
        with get_connection() as db:
            db.execute("""
                SELECT f.match_id, f.home_team_name, f.away_team_name, f.date
                FROM fixtures f
                LEFT JOIN match_statistics ms ON f.match_id = ms.match_id
                WHERE f.status = 'finished'
                  AND ms.match_id IS NULL
                ORDER BY f.date DESC
            """)
            
            return db.fetchall()
    
    def collect_match_statistics(self):
        """Collect detailed match statistics."""
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 3: MATCH STATISTICS COLLECTION")
        logger.info("="*80)
        
        matches = self.get_matches_needing_stats()
        logger.info(f"Matches needing stats: {len(matches)}")
        
        for i, (match_id, home, away, date) in enumerate(matches, 1):
            logger.info(f"[{i}/{len(matches)}] {home} vs {away} ({date})")
            
            try:
                # Scrape match stats
                match_stats = self.match_stats_scraper.scrape(match_id)
                
                if match_stats:
                    for half_stats in match_stats:
                        try:
                            with get_connection() as db:
                                cols = list(half_stats.keys())
                                placeholders = ", ".join([f"%({col})s" for col in cols])
                                col_names = ", ".join(cols)
                                
                                db.execute(f"""
                                    INSERT INTO match_statistics ({col_names})
                                    VALUES ({placeholders})
                                    ON CONFLICT (match_id, period) DO NOTHING
                                """, half_stats)
                        except Exception as e:
                            logger.warning(f"  Error inserting: {e}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"  Error scraping: {e}")
                continue
            
            if i % 50 == 0:
                progress = self.get_progress()
                logger.info(f"  Progress: {progress['matches_with_stats']} matches with stats")
        
        progress = self.get_progress()
        logger.info(f"\n✅ Match stats complete: {progress['matches_with_stats']} matches")
    
    def get_matches_needing_players(self):
        """Get matches that need player statistics."""
        
        with get_connection() as db:
            db.execute("""
                SELECT DISTINCT ms.match_id
                FROM match_statistics ms
                LEFT JOIN player_statistics ps ON ms.match_id = ps.match_id
                WHERE ps.match_id IS NULL
                ORDER BY ms.match_id DESC
            """)
            
            return [row[0] for row in db.fetchall()]
    
    def collect_player_statistics(self):
        """Collect player statistics."""
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 4: PLAYER STATISTICS COLLECTION")
        logger.info("="*80)
        
        matches = self.get_matches_needing_players()
        logger.info(f"Matches needing player stats: {len(matches)}")
        
        for i, match_id in enumerate(matches, 1):
            logger.info(f"[{i}/{len(matches)}] Match {match_id}")
            
            try:
                # Scrape player stats
                player_stats = self.player_stats_scraper.scrape(match_id)
                
                if player_stats:
                    for player in player_stats:
                        try:
                            with get_connection() as db:
                                cols = list(player.keys())
                                placeholders = ", ".join([f"%({col})s" for col in cols])
                                col_names = ", ".join(cols)
                                
                                db.execute(f"""
                                    INSERT INTO player_statistics ({col_names})
                                    VALUES ({placeholders})
                                    ON CONFLICT (match_id, player_id) DO NOTHING
                                """, player)
                        except Exception as e:
                            logger.warning(f"  Error inserting player: {e}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"  Error scraping: {e}")
                continue
            
            if i % 50 == 0:
                progress = self.get_progress()
                logger.info(f"  Progress: {progress['matches_with_players']} matches")
        
        progress = self.get_progress()
        logger.info(f"\n✅ Player stats complete: {progress['matches_with_players']} matches")
    
    def run(self):
        """Run complete collection process."""
        
        print("\n" + "="*80)
        print("⚽ COMPREHENSIVE FOOTBALL DATA COLLECTOR")
        print("="*80)
        print(f"\n📅 Range: {self.start_date.date()} → {self.end_date.date()}")
        print(f"\n📊 What this does:")
        print(f"   1. Collect all fixtures (Jan 1 → Today)")
        print(f"   2. Collect team baseline (10 matches before 2025)")
        print(f"   3. Collect all 2025 team matches")
        print(f"   4. Collect match statistics (detailed stats)")
        print(f"   5. Collect player statistics (individual performance)")
        print(f"\n⏱️  Estimated time: 2-3 days")
        print(f"✨ Resumes automatically if interrupted")
        print("="*80 + "\n")
        
        try:
            # Stage 1: Fixtures
            self.collect_fixtures()
            
            # Stage 2: Team baseline
            self.collect_team_baseline()
            
            # Stage 3: Match statistics
            self.collect_match_statistics()
            
            # Stage 4: Player statistics
            self.collect_player_statistics()
            
            # Final summary
            progress = self.get_progress()
            
            print("\n" + "="*80)
            print("🎉 COLLECTION COMPLETE!")
            print("="*80)
            print(f"\n📊 FINAL STATISTICS:")
            print(f"   Fixtures: {progress['fixtures']}")
            print(f"   Teams: {progress['total_teams']}")
            print(f"   Teams with baseline: {progress['teams_with_baseline']}")
            print(f"   Matches with stats: {progress['matches_with_stats']}")
            print(f"   Matches with players: {progress['matches_with_players']}")
            print("="*80 + "\n")
            
            logger.info("✅ ALL DATA COLLECTION COMPLETE!")
            
        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopped by user")
            logger.info("Run again to resume from where it left off")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise


def main():
    collector = ComprehensiveCollector()
    collector.run()


if __name__ == "__main__":
    main()