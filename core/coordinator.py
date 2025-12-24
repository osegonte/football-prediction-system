"""
Scraper Coordinator - Master orchestrator that manages all scrapers
with intelligent batching and request distribution.
Now with database integration!
"""
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

from core.settings import BATCH_SIZE, BATCH_PAUSE, DEFAULT_MATCHES_PER_TEAM
from core.request_manager import RequestManager

# Import database functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.insert import insert_fixtures, insert_team_matches, insert_scraping_log, get_stats

logger = logging.getLogger(__name__)


class ScraperCoordinator:
    """
    Coordinates all scraping operations with intelligent batching
    and request management. Now saves data to database!
    """
    
    def __init__(self):
        self.request_manager = RequestManager()
        logger.info("ScraperCoordinator initialized")
    
    def batch_items(self, items: List, batch_size: int = BATCH_SIZE) -> List[List]:
        """
        Split items into batches for distributed processing.
        """
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Split {len(items)} items into {len(batches)} batches of {batch_size}")
        return batches
    
    def process_with_batching(self, items: List, process_func, batch_size: int = BATCH_SIZE):
        """
        Process items in batches with pauses between batches.
        """
        batches = self.batch_items(items, batch_size)
        
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} items)")
            
            for item in batch:
                try:
                    process_func(item)
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
            
            # Pause between batches (except after last batch)
            if batch_num < len(batches):
                logger.info(f"Batch {batch_num} complete. Pausing for {BATCH_PAUSE} seconds...")
                time.sleep(BATCH_PAUSE)
        
        logger.info("All batches processed")
    
    def scrape_daily_fixtures(self, date: datetime = None):
        """
        Scrape all fixtures for a given date and save to database.
        """
        if date is None:
            date = datetime.now()
        
        start_time = time.time()
        logger.info(f"Starting fixture scrape for {date.strftime('%Y-%m-%d')}")
        
        from scrapers.fixtures_scraper import FixturesScraper
        
        scraper = FixturesScraper()
        fixtures = scraper.get_fixtures_by_date(date)
        
        logger.info(f"Scraped {len(fixtures)} fixtures")
        
        # Save to database
        if fixtures:
            inserted, duplicates = insert_fixtures(fixtures)
            logger.info(f"Database: {inserted} new fixtures, {duplicates} duplicates")
            
            # Log this scraping operation
            duration = int(time.time() - start_time)
            insert_scraping_log(
                scrape_date=date.date(),
                scrape_type='fixtures',
                records_collected=inserted,
                records_failed=duplicates,
                duration_seconds=duration
            )
        
        return fixtures
    
    def scrape_team_history(self, team_ids: List[int], matches_per_team: int = DEFAULT_MATCHES_PER_TEAM):
        """
        Scrape historical matches for multiple teams with batching.
        Saves all data to database.
        """
        start_time = time.time()
        logger.info(f"Starting team history scrape for {len(team_ids)} teams")
        
        from scrapers.team_stats_scraper import TeamStatsScraper
        
        scraper = TeamStatsScraper()
        results = []
        
        def process_team(team_id):
            team_data = scraper.get_team_last_matches(team_id, limit=matches_per_team)
            if team_data:
                results.append(team_data)
                logger.info(f"Scraped {len(team_data['matches'])} matches for team {team_id}")
        
        # Process teams in batches
        self.process_with_batching(team_ids, process_team)
        
        logger.info(f"Team history scrape complete. Collected data for {len(results)} teams")
        
        # Save to database
        if results:
            inserted, duplicates = insert_team_matches(results)
            logger.info(f"Database: {inserted} new matches, {duplicates} duplicates")
            
            # Log this scraping operation
            duration = int(time.time() - start_time)
            insert_scraping_log(
                scrape_date=datetime.now().date(),
                scrape_type='team_history',
                records_collected=inserted,
                records_failed=duplicates,
                duration_seconds=duration
            )
        
        return results
    
    def scrape_match_statistics(self, match_ids: List[int]):
        """
        Scrape statistics for multiple matches with batching.
        """
        logger.info(f"Starting match statistics scrape for {len(match_ids)} matches")
        
        from scrapers.match_stats_scraper import MatchStatsScraper
        
        scraper = MatchStatsScraper()
        results = []
        
        def process_match(match_id):
            match_stats = scraper.get_match_statistics(match_id)
            if match_stats:
                results.append(match_stats)
                logger.info(f"Scraped statistics for match {match_id}")
        
        # Process matches in batches
        self.process_with_batching(match_ids, process_match)
        
        logger.info(f"Match statistics scrape complete. Collected data for {len(results)} matches")
        
        # TODO: Add database insert for match statistics
        
        return results
    
    def scrape_player_stats(self, match_ids: List[int]):
        """
        Scrape player lineups and stats for multiple matches with batching.
        """
        logger.info(f"Starting player stats scrape for {len(match_ids)} matches")
        
        from scrapers.player_stats_scraper import PlayerStatsScraper
        
        scraper = PlayerStatsScraper()
        results = []
        
        def process_match(match_id):
            lineups = scraper.get_match_lineups(match_id)
            if lineups:
                results.append(lineups)
                logger.info(f"Scraped player stats for match {match_id}")
        
        # Process matches in batches
        self.process_with_batching(match_ids, process_match)
        
        logger.info(f"Player stats scrape complete. Collected data for {len(results)} matches")
        
        # TODO: Add database insert for player statistics
        
        return results
    
    def print_summary(self):
        """Print summary of scraping session with database stats."""
        print(f"\n{'='*60}")
        print(f"SCRAPING SESSION SUMMARY")
        print(f"{'='*60}")
        
        # Request statistics
        self.request_manager.print_stats()
        
        # Database statistics
        try:
            db_stats = get_stats()
            print(f"\n{'='*50}")
            print(f"DATABASE STATISTICS")
            print(f"{'='*50}")
            print(f"Total Fixtures:      {db_stats['fixtures']}")
            print(f"Total Teams:         {db_stats['teams']}")
            print(f"Total Matches:       {db_stats['matches']}")
            print(f"{'='*50}\n")
        except Exception as e:
            logger.error(f"Could not fetch database stats: {e}")
