"""
Quick script to scrape Friday + Saturday fixtures and team history.
Collects basic match data (scores, dates, results) without detailed stats.
"""

import sys
from datetime import datetime, timedelta

from core.coordinator import ScraperCoordinator

def main():
    print("\n" + "="*80)
    print("⚽ WEEKEND DATA COLLECTION")
    print("="*80)
    print("Scraping Friday (Dec 12) + Saturday (Dec 13)")
    print("Collecting: Fixtures + Team History (7 matches each)")
    print("="*80 + "\n")
    
    coordinator = ScraperCoordinator()
    
    # Friday (Dec 12)
    print("\n📅 FRIDAY - December 12, 2025")
    print("="*60)
    friday = datetime(2025, 12, 12)
    friday_fixtures = coordinator.scrape_daily_fixtures(friday)
    print(f"✅ {len(friday_fixtures)} fixtures")
    
    # Extract Friday teams
    friday_teams = set()
    for f in friday_fixtures:
        friday_teams.add(f['home_team_id'])
        friday_teams.add(f['away_team_id'])
    
    print(f"👥 {len(friday_teams)} teams")
    
    # Scrape Friday team history
    print("📊 Scraping team history...")
    friday_data = coordinator.scrape_team_history(list(friday_teams), matches_per_team=7)
    print(f"✅ {len(friday_data)} teams complete\n")
    
    # Saturday (Dec 13)
    print("\n📅 SATURDAY - December 13, 2025")
    print("="*60)
    saturday = datetime(2025, 12, 13)
    saturday_fixtures = coordinator.scrape_daily_fixtures(saturday)
    print(f"✅ {len(saturday_fixtures)} fixtures")
    
    # Extract Saturday teams
    saturday_teams = set()
    for f in saturday_fixtures:
        saturday_teams.add(f['home_team_id'])
        saturday_teams.add(f['away_team_id'])
    
    print(f"👥 {len(saturday_teams)} teams")
    
    # Scrape Saturday team history
    print("📊 Scraping team history...")
    saturday_data = coordinator.scrape_team_history(list(saturday_teams), matches_per_team=7)
    print(f"✅ {len(saturday_data)} teams complete\n")
    
    # Summary
    print("\n" + "="*80)
    print("✅ WEEKEND COLLECTION COMPLETE")
    print("="*80)
    coordinator.print_summary()
    
    print(f"\n📦 Data Collected:")
    print(f"   Friday Fixtures: {len(friday_fixtures)}")
    print(f"   Friday Teams: {len(friday_teams)}")
    print(f"   Saturday Fixtures: {len(saturday_fixtures)}")
    print(f"   Saturday Teams: {len(saturday_teams)}")
    print(f"   Total Teams: {len(friday_teams) + len(saturday_teams)}")
    print("\n" + "="*80 + "\n")
    
    print("💾 Data ready for processing!")
    print("📊 Use /verify in Telegram to check quality")
    print("\n")


if __name__ == "__main__":
    main()
