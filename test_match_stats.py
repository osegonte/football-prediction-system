"""
Test script to scrape match statistics for specific match IDs.
Tests with Eintracht Frankfurt's last 7 matches.
"""

import sys
import json
from scrapers.match_stats_scraper import MatchStatsScraper

# Frankfurt's match IDs from database
FRANKFURT_MATCHES = [
    14566651,  # vs Barcelona
    14065167,  # vs RB Leipzig
    14065157,  # vs VfL Wolfsburg
    14566755,  # vs Atalanta
    14065155,  # vs 1. FC Köln
    14065140,  # vs 1. FSV Mainz 05
    14566900,  # vs Napoli
]

def test_single_match():
    """Test scraping stats for one match."""
    print("\n" + "="*80)
    print("🧪 TEST: Single Match Statistics")
    print("="*80)
    
    scraper = MatchStatsScraper()
    match_id = FRANKFURT_MATCHES[0]  # Barcelona match
    
    print(f"\nScraping match {match_id} (Frankfurt vs Barcelona)...")
    
    stats = scraper.get_match_statistics(match_id)
    
    if stats:
        print("\n✅ SUCCESS! Stats collected:")
        print("\n📋 Data Structure:")
        print(json.dumps(stats, indent=2, default=str))
        return True
    else:
        print("\n❌ FAILED: No stats returned")
        return False


if __name__ == "__main__":
    print("\n🏟️  MATCH STATISTICS SCRAPER TEST")
    print("="*80)
    print("Testing with Eintracht Frankfurt vs Barcelona")
    print("="*80)
    
    test_single_match()
