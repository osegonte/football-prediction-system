"""
Test all 7 Frankfurt matches with stats collection.
"""

from scrapers.match_stats_scraper import MatchStatsScraper
import time

FRANKFURT_MATCHES = [
    (14566651, "Barcelona"),
    (14065167, "RB Leipzig"),
    (14065157, "VfL Wolfsburg"),
    (14566755, "Atalanta"),
    (14065155, "1. FC Köln"),
    (14065140, "1. FSV Mainz 05"),
    (14566900, "Napoli"),
]

scraper = MatchStatsScraper()
start = time.time()

print("\n🏟️  Scraping 7 Frankfurt matches...\n")

for i, (match_id, opponent) in enumerate(FRANKFURT_MATCHES, 1):
    print(f"[{i}/7] {opponent}... ", end="", flush=True)
    stats = scraper.get_match_statistics(match_id)
    if stats:
        print(f"✅ ({len(stats['first_half'])} stats)")
    else:
        print("❌ Failed")

elapsed = time.time() - start
print(f"\n⏱️  Total time: {elapsed:.1f} seconds")
print(f"📊 Average: {elapsed/7:.1f} seconds per match")
