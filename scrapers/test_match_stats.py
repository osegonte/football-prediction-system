from scrapers.team_stats_scraper import TeamStatsScraper
from scrapers.match_stats_scraper import MatchStatsScraper

# Get Newcastle's recent matches
team_scraper = TeamStatsScraper()
team_data = team_scraper.get_team_last_matches(team_id=39, limit=5)

if team_data and team_data['matches']:
    # Get the most recent match
    recent_match = team_data['matches'][0]
    match_id = recent_match['match_id']
    
    print(f"\n{'='*80}")
    print(f"Testing with Newcastle's most recent match:")
    print(f"Date: {recent_match['date']}")
    print(f"Opponent: {recent_match['opponent']}")
    print(f"Score: {recent_match['team_score']}-{recent_match['opponent_score']}")
    print(f"Match ID: {match_id}")
    print(f"{'='*80}\n")
    
    # Now get statistics for this match
    stats_scraper = MatchStatsScraper()
    stats = stats_scraper.get_match_statistics(match_id)
    stats_scraper.display_match_statistics(stats)
else:
    print("❌ Could not fetch team data")
