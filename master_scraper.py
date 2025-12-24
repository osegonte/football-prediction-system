"""
Master Scraper - Strategic data collection with database-driven workflow.

Supports multiple scraping strategies:
- By Date: All matches on a specific date
- By League: All matches in a league (e.g., Premier League)
- By Match Limit: First N matches (sorted by time)

Usage:
    python master_scraper.py    # Interactive mode
"""

import sys
import argparse
from datetime import datetime, timedelta
import logging

from core.coordinator import ScraperCoordinator
from database.connection import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date string into datetime object."""
    if not date_str or date_str.lower() == 'today':
        return datetime.now()
    
    if date_str.lower() == 'tomorrow':
        return datetime.now() + timedelta(days=1)
    
    if date_str.lower() == 'saturday':
        today = datetime.now()
        days_ahead = 5 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        return None


def get_fixtures_from_db(date=None, league=None, limit=None):
    """Query fixtures from database with filters."""
    with get_connection() as db:
        query = "SELECT match_id, home_team_id, away_team_id, home_team_name, away_team_name, tournament_name, date FROM fixtures WHERE 1=1"
        params = []
        
        if date:
            query += " AND date = %s"
            params.append(date)
        
        if league:
            query += " AND tournament_name ILIKE %s"
            params.append(f'%{league}%')
        
        query += " ORDER BY start_timestamp"
        
        if limit:
            query += f" LIMIT {limit}"
        
        db.execute(query, tuple(params) if params else None)
        results = db.fetchall()
        
        fixtures = []
        for r in results:
            fixtures.append({
                'match_id': r[0],
                'home_team_id': r[1],
                'away_team_id': r[2],
                'home_team_name': r[3],
                'away_team_name': r[4],
                'tournament': r[5],
                'date': r[6]
            })
        
        return fixtures


def interactive_mode():
    """Run scraper in interactive mode with strategy selection."""
    print("\n" + "="*80)
    print("⚽ FOOTBALL DATA SCRAPER - INTERACTIVE MODE")
    print("="*80 + "\n")
    
    # Ask for date
    print("📅 Which date do you want to scrape?")
    print("   Options: today, tomorrow, saturday, or YYYY-MM-DD format")
    date_input = input("   Enter date: ").strip() or 'today'
    
    target_date = parse_date(date_input)
    if not target_date:
        print("❌ Invalid date. Exiting.")
        sys.exit(1)
    
    # Ask for scraping strategy
    print(f"\n🎯 Scraping Strategy:")
    print("   1. All matches on this date (sorted by time)")
    print("   2. Specific league only (e.g., Premier League)")
    print("   3. First N matches (match limit)")
    strategy_input = input("   Enter strategy (1/2/3) [1]: ").strip() or '1'
    
    league_filter = None
    limit_matches = None
    
    if strategy_input == '2':
        print(f"\n🏆 Enter league name:")
        print("   Examples: Premier League, La Liga, Serie A, Bundesliga")
        league_filter = input("   League name: ").strip()
    
    elif strategy_input == '3':
        print(f"\n⚽ How many matches?")
        limit_input = input("   Enter match limit: ").strip()
        try:
            limit_matches = int(limit_input)
        except ValueError:
            print("❌ Invalid number. Using 20 matches.")
            limit_matches = 20
    
    # Ask for matches per team
    print(f"\n📊 How many past matches per team?")
    print("   (Recommended: 7, Maximum: 20)")
    matches_input = input("   Enter number [7]: ").strip()
    
    if matches_input == '':
        matches_per_team = 7
    else:
        try:
            matches_per_team = int(matches_input)
            if matches_per_team > 20:
                print("⚠️  Maximum is 20. Setting to 20.")
                matches_per_team = 20
        except ValueError:
            print("❌ Invalid number. Using default: 7")
            matches_per_team = 7
    
    # Confirm
    print("\n" + "="*80)
    print("📋 SCRAPING CONFIGURATION:")
    print("="*80)
    print(f"   Date: {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})")
    
    if strategy_input == '1':
        print(f"   Strategy: All matches on date (sorted by time)")
    elif strategy_input == '2':
        print(f"   Strategy: League filter - {league_filter}")
    elif strategy_input == '3':
        print(f"   Strategy: First {limit_matches} matches")
    
    print(f"   Matches per Team: {matches_per_team}")
    print("="*80 + "\n")
    
    confirm = input("▶️  Start scraping? (yes/no) [yes]: ").strip().lower()
    if confirm and confirm not in ['yes', 'y']:
        print("❌ Scraping cancelled.")
        sys.exit(0)
    
    return target_date, league_filter, limit_matches, matches_per_team


def main():
    target_date, league_filter, limit_matches, matches_per_team = interactive_mode()
    
    date_str = target_date.strftime('%Y-%m-%d')
    
    print("\n" + "="*80)
    print(f"⚽ STARTING TWO-PHASE DATA COLLECTION")
    print("="*80 + "\n")
    
    # Initialize coordinator
    coordinator = ScraperCoordinator()
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1: SCRAPE & STORE FIXTURES
    # ═══════════════════════════════════════════════════════════════════════
    
    logger.info("="*60)
    logger.info("PHASE 1: SCRAPING FIXTURES")
    logger.info("="*60)
    
    all_fixtures = coordinator.scrape_daily_fixtures(target_date)
    
    if not all_fixtures:
        logger.error("No fixtures found")
        sys.exit(1)
    
    logger.info(f"✅ Stored {len(all_fixtures)} fixtures in database")
    
    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2: QUERY DB & SCRAPE TEAMS
    # ═══════════════════════════════════════════════════════════════════════
    
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: QUERYING DATABASE & SCRAPING TEAMS")
    logger.info("="*60)
    
    # Query database with strategy
    fixtures_to_process = get_fixtures_from_db(
        date=target_date.date(),
        league=league_filter,
        limit=limit_matches
    )
    
    logger.info(f"📊 Database query returned {len(fixtures_to_process)} fixtures")
    
    if league_filter:
        logger.info(f"🏆 Filtered by league: {league_filter}")
    if limit_matches:
        logger.info(f"⚽ Limited to: {limit_matches} matches")
    
    # Extract teams
    team_ids = set()
    for fixture in fixtures_to_process:
        team_ids.add(fixture['home_team_id'])
        team_ids.add(fixture['away_team_id'])
    
    team_ids = list(team_ids)
    logger.info(f"📊 Extracted {len(team_ids)} unique teams")
    
    # Scrape team history
    logger.info(f"\nScraping team history ({matches_per_team} matches per team)...")
    team_data = coordinator.scrape_team_history(team_ids, matches_per_team=matches_per_team)
    logger.info(f"✅ Scraped history for {len(team_data)} teams")
    
    # Print summary
    print("\n" + "="*80)
    print("✅ TWO-PHASE SCRAPING COMPLETE")
    print("="*80)
    coordinator.print_summary()
    
    print(f"\n📦 Data Collected:")
    print(f"   Fixtures in Database: {len(all_fixtures)}")
    print(f"   Fixtures Processed: {len(fixtures_to_process)}")
    print(f"   Teams Scraped: {len(team_ids)}")
    print(f"   Matches per Team: {matches_per_team}")
    print(f"   ✅ All {len(fixtures_to_process)} fixtures have complete data!")
    
    print(f"\n💾 Next Steps:")
    print(f"   1. Use /verify in Telegram bot")
    print(f"   2. Verify on Sofascore.com")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
