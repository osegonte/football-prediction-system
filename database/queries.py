"""
Database queries for Telegram bot verification.
"""
import random
from database.connection import get_connection


def get_team_last_matches_with_stats(team_name, limit=7):
    """Get team's last N matches WITH statistics if available."""
    with get_connection() as db:
        db.execute("""
            SELECT 
                tm.match_id,
                tm.match_date, 
                tm.opponent_name, 
                tm.venue, 
                tm.team_score,
                tm.opponent_score, 
                tm.result, 
                tm.tournament_name,
                ms1.ball_possession_home as poss_1st_home,
                ms1.ball_possession_away as poss_1st_away,
                ms1.total_shots_home as shots_1st_home,
                ms1.total_shots_away as shots_1st_away,
                ms1.shots_on_target_home as sot_1st_home,
                ms1.shots_on_target_away as sot_1st_away,
                ms1.passes_home as passes_1st_home,
                ms1.passes_away as passes_1st_away,
                ms1.accurate_passes_home as acc_passes_1st_home,
                ms1.accurate_passes_away as acc_passes_1st_away,
                ms2.ball_possession_home as poss_2nd_home,
                ms2.ball_possession_away as poss_2nd_away,
                ms2.total_shots_home as shots_2nd_home,
                ms2.total_shots_away as shots_2nd_away
            FROM team_matches tm
            LEFT JOIN match_statistics ms1 ON tm.match_id = ms1.match_id AND ms1.period = '1ST'
            LEFT JOIN match_statistics ms2 ON tm.match_id = ms2.match_id AND ms2.period = '2ND'
            WHERE tm.team_name ILIKE %s
            ORDER BY tm.match_date DESC
            LIMIT %s
        """, (f'%{team_name}%', limit))
        
        results = db.fetchall()
        matches = []
        for r in results:
            match = {
                'match_id': r[0],
                'date': r[1],
                'opponent': r[2],
                'venue': r[3],
                'team_score': r[4],
                'opponent_score': r[5],
                'result': r[6],
                'tournament': r[7],
                'has_stats': r[8] is not None  # Check if stats exist
            }
            
            if match['has_stats']:
                match['stats'] = {
                    'first_half': {
                        'possession': f"{r[8]} - {r[9]}",
                        'shots': f"{r[10]} - {r[11]}",
                        'shots_on_target': f"{r[12]} - {r[13]}",
                        'passes': f"{r[14]} ({r[16]}) - {r[15]} ({r[17]})"
                    },
                    'second_half': {
                        'possession': f"{r[18]} - {r[19]}",
                        'shots': f"{r[20]} - {r[21]}"
                    }
                }
            
            matches.append(match)
        return matches


def get_database_stats():
    """Get database statistics."""
    with get_connection() as db:
        db.execute("SELECT COUNT(*) FROM fixtures")
        fixtures_count = db.fetchone()[0]
        
        db.execute("SELECT COUNT(DISTINCT team_id) FROM team_matches")
        teams_count = db.fetchone()[0]
        
        db.execute("SELECT COUNT(*) FROM team_matches")
        matches_count = db.fetchone()[0]
        
        db.execute("SELECT COUNT(DISTINCT match_id) FROM match_statistics")
        stats_count = db.fetchone()[0]
        
        db.execute("SELECT MAX(scraped_at) FROM fixtures")
        last_scrape = db.fetchone()[0]
        
        return {
            'fixtures': fixtures_count,
            'teams': teams_count,
            'matches': matches_count,
            'stats': stats_count,
            'last_scrape': last_scrape
        }


def get_verification_sample():
    """Get a comprehensive verification sample with stats."""
    with get_connection() as db:
        db.execute("""
            SELECT f.match_id, f.date, f.home_team_name, f.away_team_name,
                   f.home_team_id, f.away_team_id, f.tournament_name, f.status
            FROM fixtures f
            WHERE f.status = 'notstarted'
              AND EXISTS (SELECT 1 FROM team_matches tm WHERE tm.team_id = f.home_team_id)
              AND EXISTS (SELECT 1 FROM team_matches tm WHERE tm.team_id = f.away_team_id)
            ORDER BY RANDOM()
            LIMIT 1
        """)
        fixture = db.fetchone()
        
        if not fixture:
            return None
        
        match_id, date, home_team, away_team, home_id, away_id, tournament, status = fixture
        
        # Get both teams' recent matches WITH stats
        home_matches = get_team_last_matches_with_stats(home_team, 7)
        away_matches = get_team_last_matches_with_stats(away_team, 7)
        
        return {
            'fixture': {
                'match_id': match_id,
                'date': date,
                'home_team': home_team,
                'away_team': away_team,
                'tournament': tournament,
                'status': status
            },
            'home_history': home_matches,
            'away_history': away_matches
        }


def get_team_detailed_stats(team_name, limit=3):
    """Get detailed match statistics for a team."""
    with get_connection() as db:
        # Get team's recent matches with full stats
        db.execute("""
            SELECT 
                tm.match_id,
                tm.match_date,
                tm.opponent_name,
                tm.team_score,
                tm.opponent_score,
                tm.venue,
                tm.result
            FROM team_matches tm
            WHERE tm.team_name ILIKE %s
              AND EXISTS (
                  SELECT 1 FROM match_statistics ms 
                  WHERE ms.match_id = tm.match_id
              )
            ORDER BY tm.match_date DESC
            LIMIT %s
        """, (f'%{team_name}%', limit))
        
        matches = []
        for row in db.fetchall():
            match_id = row[0]
            
            # Get full statistics for this match
            db.execute("""
                SELECT 
                    period,
                    ball_possession_home, ball_possession_away,
                    expected_goals_home, expected_goals_away,
                    total_shots_home, total_shots_away,
                    shots_on_target_home, shots_on_target_away,
                    shots_off_target_home, shots_off_target_away,
                    blocked_shots_home, blocked_shots_away,
                    shots_inside_box_home, shots_inside_box_away,
                    shots_outside_box_home, shots_outside_box_away,
                    big_chances_home, big_chances_away,
                    big_chances_missed_home, big_chances_missed_away,
                    passes_home, passes_away,
                    accurate_passes_home, accurate_passes_away,
                    tackles_home, tackles_away,
                    interceptions_home, interceptions_away,
                    clearances_home, clearances_away,
                    goalkeeper_saves_home, goalkeeper_saves_away,
                    corner_kicks_home, corner_kicks_away,
                    fouls_home, fouls_away
                FROM match_statistics
                WHERE match_id = %s
                ORDER BY period
            """, (match_id,))
            
            stats_rows = db.fetchall()
            
            match_stats = {
                'match_id': match_id,
                'date': row[1],
                'opponent': row[2],
                'score': f"{row[3]}-{row[4]}",
                'venue': row[5],
                'result': row[6],
                'periods': {}
            }
            
            for stat_row in stats_rows:
                period = stat_row[0]
                match_stats['periods'][period] = {
                    'possession': f"{stat_row[1]} - {stat_row[2]}",
                    'xg': f"{stat_row[3]} - {stat_row[4]}",
                    'shots': f"{stat_row[5]} - {stat_row[6]}",
                    'shots_on_target': f"{stat_row[7]} - {stat_row[8]}",
                    'shots_off_target': f"{stat_row[9]} - {stat_row[10]}",
                    'blocked_shots': f"{stat_row[11]} - {stat_row[12]}",
                    'shots_inside_box': f"{stat_row[13]} - {stat_row[14]}",
                    'shots_outside_box': f"{stat_row[15]} - {stat_row[16]}",
                    'big_chances': f"{stat_row[17]} - {stat_row[18]}",
                    'big_chances_missed': f"{stat_row[19]} - {stat_row[20]}",
                    'passes': f"{stat_row[21]} ({stat_row[23]}) - {stat_row[22]} ({stat_row[24]})",
                    'tackles': f"{stat_row[25]} - {stat_row[26]}",
                    'interceptions': f"{stat_row[27]} - {stat_row[28]}",
                    'clearances': f"{stat_row[29]} - {stat_row[30]}",
                    'saves': f"{stat_row[31]} - {stat_row[32]}",
                    'corners': f"{stat_row[33]} - {stat_row[34]}",
                    'fouls': f"{stat_row[35]} - {stat_row[36]}"
                }
            
            matches.append(match_stats)
        
        return matches
