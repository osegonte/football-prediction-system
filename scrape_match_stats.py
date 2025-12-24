"""
Match Statistics Scraper - Production script for collecting detailed match stats.

Usage:
    python scrape_match_stats.py --team "Eintracht Frankfurt" --matches 7
    python scrape_match_stats.py --league "Bundesliga" --matches 5
    python scrape_match_stats.py --all  # All teams in database
"""

import argparse
import logging
from datetime import datetime

from scrapers.match_stats_scraper import MatchStatsScraper
from database.connection import get_connection
from database.insert import insert_match_statistics

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_match_ids_for_team(team_name, limit=7):
    """Get match IDs for a specific team."""
    with get_connection() as db:
        db.execute("""
            SELECT match_id, match_date, opponent_name, team_score, opponent_score
            FROM team_matches
            WHERE team_name ILIKE %s
            ORDER BY match_date DESC
            LIMIT %s
        """, (f'%{team_name}%', limit))
        
        results = db.fetchall()
        matches = []
        for r in results:
            matches.append({
                'match_id': r[0],
                'date': r[1],
                'opponent': r[2],
                'score': f"{r[3]}-{r[4]}"
            })
        return matches


def get_match_ids_for_league(league_name, matches_per_team=5):
    """Get match IDs for all teams in a league."""
    with get_connection() as db:
        # Get teams that played in this league
        db.execute("""
            SELECT DISTINCT team_id, team_name
            FROM team_matches
            WHERE tournament_name ILIKE %s
        """, (f'%{league_name}%',))
        
        teams = db.fetchall()
        
        all_matches = []
        for team_id, team_name in teams:
            # Get recent matches for each team
            db.execute("""
                SELECT match_id, match_date, opponent_name, team_score, opponent_score
                FROM team_matches
                WHERE team_id = %s
                ORDER BY match_date DESC
                LIMIT %s
            """, (team_id, matches_per_team))
            
            results = db.fetchall()
            for r in results:
                all_matches.append({
                    'match_id': r[0],
                    'team': team_name,
                    'date': r[1],
                    'opponent': r[2],
                    'score': f"{r[3]}-{r[4]}"
                })
        
        return all_matches


def get_all_match_ids(limit_per_team=7):
    """Get match IDs for all teams in database."""
    with get_connection() as db:
        db.execute("SELECT DISTINCT team_id, team_name FROM team_matches")
        teams = db.fetchall()
        
        all_matches = []
        for team_id, team_name in teams:
            db.execute("""
                SELECT match_id, match_date, opponent_name
                FROM team_matches
                WHERE team_id = %s
                ORDER BY match_date DESC
                LIMIT %s
            """, (team_id, limit_per_team))
            
            results = db.fetchall()
            for r in results:
                all_matches.append({
                    'match_id': r[0],
                    'team': team_name,
                    'date': r[1],
                    'opponent': r[2]
                })
        
        return all_matches


def main():
    parser = argparse.ArgumentParser(description='Scrape detailed match statistics')
    parser.add_argument('--team', type=str, help='Team name to scrape stats for')
    parser.add_argument('--league', type=str, help='League name to scrape stats for')
    parser.add_argument('--all', action='store_true', help='Scrape all teams in database')
    parser.add_argument('--matches', type=int, default=7, help='Number of matches per team (default: 7)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("📊 MATCH STATISTICS SCRAPER")
    print("="*80 + "\n")
    
    # Determine which matches to scrape
    matches = []
    
    if args.team:
        print(f"🔍 Finding matches for: {args.team}")
        matches = get_match_ids_for_team(args.team, args.matches)
        print(f"✅ Found {len(matches)} matches\n")
    
    elif args.league:
        print(f"🔍 Finding matches for league: {args.league}")
        matches = get_match_ids_for_league(args.league, args.matches)
        print(f"✅ Found {len(matches)} matches across multiple teams\n")
    
    elif args.all:
        print(f"🔍 Finding matches for ALL teams")
        matches = get_all_match_ids(args.matches)
        print(f"✅ Found {len(matches)} matches\n")
    
    else:
        print("❌ Error: Must specify --team, --league, or --all")
        parser.print_help()
        return
    
    if not matches:
        print("❌ No matches found")
        return
    
    # Remove duplicates (same match from different team perspectives)
    unique_match_ids = list(set(m['match_id'] for m in matches))
    print(f"📊 Unique matches to scrape: {len(unique_match_ids)}")
    
    # Confirm
    response = input(f"\n▶️  Scrape statistics for {len(unique_match_ids)} matches? (yes/no) [yes]: ").strip().lower()
    if response and response not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    # Scrape statistics
    print("\n" + "="*80)
    print("⚽ SCRAPING MATCH STATISTICS")
    print("="*80 + "\n")
    
    scraper = MatchStatsScraper()
    stats_collected = []
    
    for i, match_id in enumerate(unique_match_ids, 1):
        print(f"[{i}/{len(unique_match_ids)}] Match {match_id}... ", end="", flush=True)
        
        stats = scraper.get_match_statistics(match_id)
        
        if stats:
            stats_collected.append(stats)
            print("✅")
        else:
            print("❌ Failed")
    
    # Save to database
    if stats_collected:
        print(f"\n💾 Saving {len(stats_collected)} matches to database...")
        inserted, duplicates = insert_match_statistics(stats_collected)
        print(f"✅ Inserted: {inserted} periods")
        print(f"⚠️  Duplicates skipped: {duplicates} periods")
    
    # Summary
    print("\n" + "="*80)
    print("✅ SCRAPING COMPLETE")
    print("="*80)
    print(f"📊 Matches scraped: {len(stats_collected)}/{len(unique_match_ids)}")
    print(f"💾 Periods stored: {inserted}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
