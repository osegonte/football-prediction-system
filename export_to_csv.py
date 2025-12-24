"""
Export all collected data to CSV files for analysis.
"""

import csv
from datetime import datetime
from database.connection import get_connection

def export_fixtures():
    """Export all fixtures to CSV."""
    with get_connection() as db:
        db.execute("""
            SELECT match_id, date, home_team_name, away_team_name, 
                   tournament_name, status, home_score, away_score
            FROM fixtures
            ORDER BY date, start_timestamp
        """)
        
        with open('data/fixtures.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['match_id', 'date', 'home_team', 'away_team', 
                           'tournament', 'status', 'home_score', 'away_score'])
            writer.writerows(db.fetchall())
    
    print("✅ Exported fixtures.csv")


def export_team_matches():
    """Export all team match history to CSV."""
    with get_connection() as db:
        db.execute("""
            SELECT team_id, team_name, match_id, match_date, 
                   opponent_name, venue, team_score, opponent_score, 
                   result, tournament_name
            FROM team_matches
            ORDER BY team_id, match_date DESC
        """)
        
        with open('data/team_matches.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['team_id', 'team_name', 'match_id', 'date', 
                           'opponent', 'venue', 'team_score', 'opponent_score', 
                           'result', 'tournament'])
            writer.writerows(db.fetchall())
    
    print("✅ Exported team_matches.csv")


def export_match_statistics():
    """Export match statistics to CSV."""
    with get_connection() as db:
        db.execute("""
            SELECT match_id, period, ball_possession_home, ball_possession_away,
                   expected_goals_home, expected_goals_away,
                   total_shots_home, total_shots_away,
                   shots_on_target_home, shots_on_target_away,
                   passes_home, passes_away,
                   accurate_passes_home, accurate_passes_away,
                   tackles_home, tackles_away,
                   corner_kicks_home, corner_kicks_away
            FROM match_statistics
            ORDER BY match_id, period
        """)
        
        with open('data/match_statistics.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['match_id', 'period', 'possession_home', 'possession_away',
                           'xg_home', 'xg_away', 'shots_home', 'shots_away',
                           'shots_on_target_home', 'shots_on_target_away',
                           'passes_home', 'passes_away',
                           'accurate_passes_home', 'accurate_passes_away',
                           'tackles_home', 'tackles_away',
                           'corners_home', 'corners_away'])
            writer.writerows(db.fetchall())
    
    print("✅ Exported match_statistics.csv")


def export_stats():
    """Show export statistics."""
    with get_connection() as db:
        db.execute("SELECT COUNT(*) FROM fixtures")
        fixtures = db.fetchone()[0]
        
        db.execute("SELECT COUNT(DISTINCT team_id) FROM team_matches")
        teams = db.fetchone()[0]
        
        db.execute("SELECT COUNT(*) FROM team_matches")
        matches = db.fetchone()[0]
        
        db.execute("SELECT COUNT(DISTINCT match_id) FROM match_statistics")
        stats = db.fetchone()[0]
    
    print("\n" + "="*60)
    print("📊 EXPORT SUMMARY")
    print("="*60)
    print(f"Fixtures exported: {fixtures}")
    print(f"Teams: {teams}")
    print(f"Team match history: {matches}")
    print(f"Matches with detailed stats: {stats}")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n📤 Exporting database to CSV files...")
    print("="*60 + "\n")
    
    export_fixtures()
    export_team_matches()
    export_match_statistics()
    export_stats()
    
    print("✅ All data exported to data/ folder")
    print("\nFiles created:")
    print("  - data/fixtures.csv")
    print("  - data/team_matches.csv")
    print("  - data/match_statistics.csv")
    print("\n")
