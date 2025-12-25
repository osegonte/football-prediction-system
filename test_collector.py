"""
TEST COLLECTOR - 30 Minute Verification
Tests the complete collection system on a random day

What it does:
1. Picks a random recent day
2. Collects fixtures for that day
3. Processes 50% of teams (or until 30 mins elapsed)
4. Scrapes match stats for finished matches
5. Scrapes player stats
6. Exports CSV for manual verification

Usage:
  python test_collector.py
"""

import logging
from datetime import datetime, timedelta
import time
import csv
import random
from pathlib import Path

from core.coordinator import ScraperCoordinator
from scrapers.match_stats_scraper import MatchStatsScraper
from scrapers.player_stats_scraper import PlayerStatsScraper
from database.connection import get_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CSV export directory
CSV_DIR = Path("data/test")
CSV_DIR.mkdir(parents=True, exist_ok=True)

# Test limits
MAX_DURATION = 30 * 60  # 30 minutes in seconds
MAX_TEAMS = None  # Will be set to 50% of teams found


class TestCollector:
    """Quick test collector for verification."""
    
    def __init__(self):
        self.coordinator = ScraperCoordinator()
        self.match_stats_scraper = MatchStatsScraper()
        self.player_stats_scraper = PlayerStatsScraper()
        self.start_time = time.time()
        
        logger.info("Test Collector initialized")
    
    def time_elapsed(self):
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def time_remaining(self):
        """Get remaining time in seconds."""
        return MAX_DURATION - self.time_elapsed()
    
    def pick_random_day(self):
        """Pick a random day from last 30 days."""
        
        # Pick a day 7-30 days ago (avoid very recent days with no finished matches)
        days_ago = random.randint(7, 30)
        test_date = datetime.now() - timedelta(days=days_ago)
        
        logger.info(f"Random test date: {test_date.date()}")
        return test_date
    
    def run(self):
        """Run test collection."""
        
        print("\n" + "="*80)
        print("🧪 TEST COLLECTOR - 30 Minute Verification")
        print("="*80)
        print(f"\n📊 What this does:")
        print(f"   1. Pick random recent day")
        print(f"   2. Collect fixtures for that day")
        print(f"   3. Process 50% of teams (comprehensive)")
        print(f"   4. Export CSV for manual verification")
        print(f"\n⏱️  Max duration: 30 minutes")
        print(f"✨ Stops automatically after 30 mins or 50% teams processed")
        print("="*80 + "\n")
        
        # Pick random day
        test_date = self.pick_random_day()
        date_str = test_date.strftime('%Y_%m_%d')
        
        stats = {
            'fixtures': 0,
            'teams': 0,
            'team_matches': 0,
            'match_stats': 0,
            'player_stats': 0
        }
        
        # ===================================================================
        # STAGE 1: Collect Fixtures
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 1: FIXTURES FOR {test_date.date()}")
        logger.info(f"{'='*80}")
        
        fixtures = self.coordinator.scrape_daily_fixtures(test_date)
        
        if not fixtures:
            logger.error(f"No fixtures found for {test_date.date()}")
            return
        
        stats['fixtures'] = len(fixtures)
        logger.info(f"✅ {len(fixtures)} fixtures collected")
        logger.info(f"⏱️  Elapsed: {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        # ===================================================================
        # STAGE 2: Extract Teams
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 2: TEAM EXTRACTION")
        logger.info(f"{'='*80}")
        
        team_ids = set()
        for f in fixtures:
            team_ids.add((f['home_team_id'], f['home_team_name']))
            team_ids.add((f['away_team_id'], f['away_team_name']))
        
        teams = list(team_ids)
        stats['teams'] = len(teams)
        
        # Process 50% of teams
        global MAX_TEAMS
        MAX_TEAMS = max(1, len(teams) // 2)
        
        logger.info(f"Total teams: {len(teams)}")
        logger.info(f"Will process: {MAX_TEAMS} teams (50%)")
        logger.info(f"⏱️  Elapsed: {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        # ===================================================================
        # STAGE 3: Collect Team Data
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 3: TEAM DATA COLLECTION")
        logger.info(f"{'='*80}")
        
        teams_processed = 0
        
        for i, (team_id, team_name) in enumerate(teams[:MAX_TEAMS], 1):
            # Check time limit
            if self.time_remaining() < 60:
                logger.warning(f"⏱️  Time limit approaching, stopping at {i-1} teams")
                break
            
            logger.info(f"[{i}/{MAX_TEAMS}] ⚽ {team_name}")
            
            # Scrape team history (10 baseline + 2025 matches)
            self.coordinator.scrape_team_history([team_id], matches_per_team=30)
            
            teams_processed += 1
            time.sleep(3)
            
            # Count matches collected
            with get_connection() as db:
                db.execute("SELECT COUNT(*) FROM team_matches WHERE team_id = %s", (team_id,))
                team_match_count = db.fetchone()[0]
                stats['team_matches'] += team_match_count
            
            logger.info(f"  ✓ {team_match_count} matches | ⏱️  {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        logger.info(f"\n✅ Processed {teams_processed} teams")
        logger.info(f"✅ {stats['team_matches']} team matches collected")
        logger.info(f"⏱️  Elapsed: {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        # ===================================================================
        # STAGE 4: Match Statistics
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 4: MATCH STATISTICS")
        logger.info(f"{'='*80}")
        
        # Get finished matches from collected fixtures
        with get_connection() as db:
            db.execute("""
                SELECT match_id FROM fixtures
                WHERE date = %s AND status = 'finished'
                LIMIT 20
            """, (test_date.date(),))
            
            finished_matches = [row[0] for row in db.fetchall()]
        
        logger.info(f"Finished matches to process: {len(finished_matches)}")
        
        for i, match_id in enumerate(finished_matches, 1):
            # Check time limit
            if self.time_remaining() < 30:
                logger.warning(f"⏱️  Time limit approaching, stopping match stats")
                break
            
            logger.info(f"[{i}/{len(finished_matches)}] Match {match_id}")
            
            try:
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
                            logger.warning(f"  Error: {e}")
                    
                    stats['match_stats'] += 1
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"  Error: {e}")
                continue
        
        logger.info(f"✅ {stats['match_stats']} matches with statistics")
        logger.info(f"⏱️  Elapsed: {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        # ===================================================================
        # STAGE 5: Player Statistics
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 5: PLAYER STATISTICS")
        logger.info(f"{'='*80}")
        
        # Get matches that have match stats
        with get_connection() as db:
            db.execute("""
                SELECT DISTINCT match_id FROM match_statistics
                WHERE match_id IN (
                    SELECT match_id FROM fixtures WHERE date = %s
                )
                LIMIT 10
            """, (test_date.date(),))
            
            matches_for_players = [row[0] for row in db.fetchall()]
        
        logger.info(f"Matches to get player stats: {len(matches_for_players)}")
        
        for i, match_id in enumerate(matches_for_players, 1):
            # Check time limit
            if self.time_remaining() < 20:
                logger.warning(f"⏱️  Time limit approaching, stopping player stats")
                break
            
            logger.info(f"[{i}/{len(matches_for_players)}] Match {match_id}")
            
            try:
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
                            logger.warning(f"  Error: {e}")
                    
                    stats['player_stats'] += len(player_stats)
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"  Error: {e}")
                continue
        
        logger.info(f"✅ {stats['player_stats']} player records")
        logger.info(f"⏱️  Elapsed: {self.time_elapsed():.0f}s / {MAX_DURATION}s")
        
        # ===================================================================
        # STAGE 6: Export CSV
        # ===================================================================
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STAGE 6: EXPORT CSV")
        logger.info(f"{'='*80}")
        
        self.export_test_data(test_date)
        
        # ===================================================================
        # SUMMARY
        # ===================================================================
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETE!")
        print("="*80)
        print(f"\n📊 STATISTICS:")
        print(f"   Date tested: {test_date.date()}")
        print(f"   Fixtures: {stats['fixtures']}")
        print(f"   Teams processed: {teams_processed}/{stats['teams']}")
        print(f"   Team matches: {stats['team_matches']}")
        print(f"   Match statistics: {stats['match_stats']}")
        print(f"   Player records: {stats['player_stats']}")
        print(f"\n⏱️  Time taken: {self.time_elapsed():.0f} seconds ({self.time_elapsed()/60:.1f} minutes)")
        print(f"\n📂 Test data exported to: {CSV_DIR.absolute()}")
        print("="*80 + "\n")
        
        logger.info("✅ Test verification complete - Check CSV files for data quality")
    
    def export_test_data(self, test_date):
        """Export test data to CSV files."""
        
        date_str = test_date.strftime('%Y_%m_%d')
        
        exports = [
            ('fixtures', f"""
                SELECT * FROM fixtures
                WHERE date = '{test_date.date()}'
            """),
            ('team_matches', f"""
                SELECT * FROM team_matches
                WHERE scraped_at::date = CURRENT_DATE
                ORDER BY team_id, match_date DESC
            """),
            ('match_statistics', f"""
                SELECT * FROM match_statistics
                WHERE scraped_at::date = CURRENT_DATE
            """),
            ('player_statistics', f"""
                SELECT * FROM player_statistics
                WHERE scraped_at::date = CURRENT_DATE
                LIMIT 1000
            """),
        ]
        
        for table_name, query in exports:
            try:
                filename = CSV_DIR / f"test_{date_str}_{table_name}.csv"
                
                with get_connection() as db:
                    db.execute(query)
                    rows = db.fetchall()
                    
                    if rows:
                        columns = [desc[0] for desc in db.cursor.description]
                        
                        with open(filename, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(columns)
                            writer.writerows(rows)
                        
                        logger.info(f"  ✅ {table_name}: {len(rows)} rows → {filename.name}")
                    else:
                        logger.info(f"  ℹ️  {table_name}: No data")
            
            except Exception as e:
                logger.error(f"  ❌ Error exporting {table_name}: {e}")


def main():
    collector = TestCollector()
    
    try:
        collector.run()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test stopped by user")
    except Exception as e:
        logger.error(f"Test error: {e}")
        raise


if __name__ == "__main__":
    main()