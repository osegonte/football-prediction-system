"""
Database insert functions with session tracking for monitoring.
"""
import logging
import uuid
from datetime import datetime
from database.connection import get_connection

logger = logging.getLogger(__name__)


def create_scraping_session(scrape_date, strategy, league_filter=None, total_fixtures=0, total_teams=0, matches_per_team=7):
    """Create a new scraping session for tracking."""
    session_id = str(uuid.uuid4())[:8]
    
    with get_connection() as db:
        db.execute("""
            INSERT INTO scraping_sessions (
                session_id, scrape_date, strategy, league_filter,
                total_fixtures, total_teams, matches_per_team, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'in_progress')
        """, (session_id, scrape_date, strategy, league_filter, total_fixtures, total_teams, matches_per_team))
        db.commit()
    
    logger.info(f"Created scraping session: {session_id}")
    return session_id


def update_session_progress(session_id, teams_completed=None, status=None):
    """Update scraping session progress."""
    with get_connection() as db:
        if teams_completed is not None:
            db.execute("""
                UPDATE scraping_sessions 
                SET teams_completed = %s
                WHERE session_id = %s
            """, (teams_completed, session_id))
        
        if status:
            if status == 'completed':
                db.execute("""
                    UPDATE scraping_sessions 
                    SET status = %s, completed_at = NOW()
                    WHERE session_id = %s
                """, (status, session_id))
            else:
                db.execute("""
                    UPDATE scraping_sessions 
                    SET status = %s
                    WHERE session_id = %s
                """, (status, session_id))
        
        db.commit()


def get_active_session():
    """Get current active scraping session."""
    with get_connection() as db:
        db.execute("""
            SELECT session_id, scrape_date, strategy, league_filter,
                   total_fixtures, total_teams, teams_completed, matches_per_team,
                   status, started_at,
                   EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER as elapsed_seconds
            FROM scraping_sessions
            WHERE status = 'in_progress'
            ORDER BY started_at DESC
            LIMIT 1
        """)
        result = db.fetchone()
        
        if result:
            return {
                'session_id': result[0],
                'scrape_date': result[1],
                'strategy': result[2],
                'league_filter': result[3],
                'total_fixtures': result[4],
                'total_teams': result[5],
                'teams_completed': result[6],
                'matches_per_team': result[7],
                'status': result[8],
                'started_at': result[9],
                'elapsed_seconds': result[10]
            }
        return None


def get_last_session():
    """Get last completed session."""
    with get_connection() as db:
        db.execute("""
            SELECT session_id, scrape_date, strategy, league_filter,
                   total_fixtures, total_teams, matches_per_team, status, 
                   started_at, completed_at,
                   EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER as duration_seconds
            FROM scraping_sessions
            ORDER BY started_at DESC
            LIMIT 1
        """)
        result = db.fetchone()
        
        if result:
            return {
                'session_id': result[0],
                'scrape_date': result[1],
                'strategy': result[2],
                'league_filter': result[3],
                'total_fixtures': result[4],
                'total_teams': result[5],
                'matches_per_team': result[6],
                'status': result[7],
                'started_at': result[8],
                'completed_at': result[9],
                'duration_seconds': result[10]
            }
        return None


def insert_fixtures(fixtures_list):
    """Insert fixtures into database."""
    if not fixtures_list:
        return 0, 0
    
    inserted = 0
    duplicates = 0
    
    with get_connection() as db:
        for fixture in fixtures_list:
            try:
                db.execute("SELECT match_id FROM fixtures WHERE match_id = %s", (fixture['match_id'],))
                if db.fetchone():
                    duplicates += 1
                    continue
                
                db.execute("""
                    INSERT INTO fixtures (
                        match_id, date, start_timestamp, home_team_id, home_team_name,
                        away_team_id, away_team_name, tournament_name, tournament_id,
                        country, status, home_score, away_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fixture['match_id'],
                    datetime.fromtimestamp(fixture['start_timestamp']).date() if fixture.get('start_timestamp') else None,
                    fixture.get('start_timestamp'),
                    fixture['home_team_id'],
                    fixture['home_team'],
                    fixture['away_team_id'],
                    fixture['away_team'],
                    fixture.get('tournament'),
                    fixture.get('tournament_id'),
                    fixture.get('country'),
                    fixture.get('status', 'scheduled'),
                    fixture.get('home_score'),
                    fixture.get('away_score')
                ))
                inserted += 1
                
            except Exception as e:
                logger.error(f"Error inserting fixture {fixture.get('match_id')}: {e}")
        
        db.commit()
    
    logger.info(f"Fixtures: {inserted} inserted, {duplicates} duplicates skipped")
    return inserted, duplicates


def insert_team_matches(team_data_list):
    """Insert team match history into database."""
    if not team_data_list:
        return 0, 0
    
    inserted = 0
    duplicates = 0
    
    with get_connection() as db:
        for team_data in team_data_list:
            team_id = team_data['team_id']
            team_name = team_data['team_name']
            
            for match in team_data['matches']:
                try:
                    db.execute(
                        "SELECT id FROM team_matches WHERE team_id = %s AND match_id = %s",
                        (team_id, match['match_id'])
                    )
                    if db.fetchone():
                        duplicates += 1
                        continue
                    
                    db.execute("""
                        INSERT INTO team_matches (
                            team_id, team_name, match_id, match_date, match_timestamp,
                            match_year, opponent_id, opponent_name, venue, team_score,
                            opponent_score, result, tournament_name, tournament_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        team_id,
                        team_name,
                        match['match_id'],
                        datetime.fromtimestamp(match['timestamp']).date() if match.get('timestamp') else None,
                        match.get('timestamp'),
                        match.get('year'),
                        match.get('opponent_id'),
                        match['opponent'],
                        match['venue'],
                        match['team_score'],
                        match['opponent_score'],
                        match['result'],
                        match.get('tournament'),
                        match.get('tournament_id')
                    ))
                    inserted += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting team match for {team_name}: {e}")
        
        db.commit()
    
    logger.info(f"Team matches: {inserted} inserted, {duplicates} duplicates skipped")
    return inserted, duplicates


def insert_scraping_log(scrape_date, scrape_type, records_collected, records_failed=0, duration_seconds=0, error_message=None):
    """Insert scraping log entry."""
    with get_connection() as db:
        success_rate = (records_collected / (records_collected + records_failed) * 100) if (records_collected + records_failed) > 0 else 0
        
        db.execute("""
            INSERT INTO scraping_log (
                scrape_date, scrape_type, records_collected, records_failed,
                success_rate, duration_seconds, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            scrape_date,
            scrape_type,
            records_collected,
            records_failed,
            success_rate,
            duration_seconds,
            error_message
        ))
        db.commit()
    
    logger.info(f"Scraping log: {scrape_type} - {records_collected} records")


def get_stats():
    """Get database statistics."""
    with get_connection() as db:
        db.execute("SELECT COUNT(*) FROM fixtures")
        fixtures = db.fetchone()[0]
        
        db.execute("SELECT COUNT(DISTINCT team_id) FROM team_matches")
        teams = db.fetchone()[0]
        
        db.execute("SELECT COUNT(*) FROM team_matches")
        matches = db.fetchone()[0]
        
        return {
            'fixtures': fixtures,
            'teams': teams,
            'matches': matches
        }


def insert_match_statistics(match_stats_list):
    """
    Insert match statistics into database.
    Returns: (inserted_count, duplicate_count)
    """
    if not match_stats_list:
        return 0, 0
    
    inserted = 0
    duplicates = 0
    
    with get_connection() as db:
        for match_stats in match_stats_list:
            match_id = match_stats['match_id']
            
            # Process first half
            if 'first_half' in match_stats:
                try:
                    # Check if exists
                    db.execute(
                        "SELECT id FROM match_statistics WHERE match_id = %s AND period = '1ST'",
                        (match_id,)
                    )
                    if db.fetchone():
                        duplicates += 1
                    else:
                        # Insert first half
                        stats = match_stats['first_half']
                        db.execute("""
                            INSERT INTO match_statistics (
                                match_id, period,
                                ball_possession_home, ball_possession_away,
                                expected_goals_home, expected_goals_away,
                                total_shots_home, total_shots_away,
                                shots_on_target_home, shots_on_target_away,
                                shots_off_target_home, shots_off_target_away,
                                blocked_shots_home, blocked_shots_away,
                                shots_inside_box_home, shots_inside_box_away,
                                shots_outside_box_home, shots_outside_box_away,
                                hit_woodwork_home, hit_woodwork_away,
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
                            ) VALUES (
                                %s, '1ST',
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            match_id,
                            stats.get('Ball possession_home'),
                            stats.get('Ball possession_away'),
                            stats.get('Expected goals_home'),
                            stats.get('Expected goals_away'),
                            stats.get('Total shots_home'),
                            stats.get('Total shots_away'),
                            stats.get('Shots on target_home'),
                            stats.get('Shots on target_away'),
                            stats.get('Shots off target_home'),
                            stats.get('Shots off target_away'),
                            stats.get('Blocked shots_home'),
                            stats.get('Blocked shots_away'),
                            stats.get('Shots inside box_home'),
                            stats.get('Shots inside box_away'),
                            stats.get('Shots outside box_home'),
                            stats.get('Shots outside box_away'),
                            stats.get('Hit woodwork_home'),
                            stats.get('Hit woodwork_away'),
                            stats.get('Big chances_home'),
                            stats.get('Big chances_away'),
                            stats.get('Big chances missed_home'),
                            stats.get('Big chances missed_away'),
                            stats.get('Passes_home'),
                            stats.get('Passes_away'),
                            stats.get('Accurate passes_home'),
                            stats.get('Accurate passes_away'),
                            stats.get('Total tackles_home'),
                            stats.get('Total tackles_away'),
                            stats.get('Interceptions_home'),
                            stats.get('Interceptions_away'),
                            stats.get('Clearances_home'),
                            stats.get('Clearances_away'),
                            stats.get('Total saves_home'),
                            stats.get('Total saves_away'),
                            stats.get('Corner kicks_home'),
                            stats.get('Corner kicks_away'),
                            stats.get('Fouls_home'),
                            stats.get('Fouls_away')
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error inserting first half stats for match {match_id}: {e}")
            
            # Process second half
            if 'second_half' in match_stats:
                try:
                    # Check if exists
                    db.execute(
                        "SELECT id FROM match_statistics WHERE match_id = %s AND period = '2ND'",
                        (match_id,)
                    )
                    if db.fetchone():
                        duplicates += 1
                    else:
                        # Insert second half
                        stats = match_stats['second_half']
                        db.execute("""
                            INSERT INTO match_statistics (
                                match_id, period,
                                ball_possession_home, ball_possession_away,
                                expected_goals_home, expected_goals_away,
                                total_shots_home, total_shots_away,
                                shots_on_target_home, shots_on_target_away,
                                shots_off_target_home, shots_off_target_away,
                                blocked_shots_home, blocked_shots_away,
                                shots_inside_box_home, shots_inside_box_away,
                                shots_outside_box_home, shots_outside_box_away,
                                hit_woodwork_home, hit_woodwork_away,
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
                            ) VALUES (
                                %s, '2ND',
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            match_id,
                            stats.get('Ball possession_home'),
                            stats.get('Ball possession_away'),
                            stats.get('Expected goals_home'),
                            stats.get('Expected goals_away'),
                            stats.get('Total shots_home'),
                            stats.get('Total shots_away'),
                            stats.get('Shots on target_home'),
                            stats.get('Shots on target_away'),
                            stats.get('Shots off target_home'),
                            stats.get('Shots off target_away'),
                            stats.get('Blocked shots_home'),
                            stats.get('Blocked shots_away'),
                            stats.get('Shots inside box_home'),
                            stats.get('Shots inside box_away'),
                            stats.get('Shots outside box_home'),
                            stats.get('Shots outside box_away'),
                            stats.get('Hit woodwork_home'),
                            stats.get('Hit woodwork_away'),
                            stats.get('Big chances_home'),
                            stats.get('Big chances_away'),
                            stats.get('Big chances missed_home'),
                            stats.get('Big chances missed_away'),
                            stats.get('Passes_home'),
                            stats.get('Passes_away'),
                            stats.get('Accurate passes_home'),
                            stats.get('Accurate passes_away'),
                            stats.get('Total tackles_home'),
                            stats.get('Total tackles_away'),
                            stats.get('Interceptions_home'),
                            stats.get('Interceptions_away'),
                            stats.get('Clearances_home'),
                            stats.get('Clearances_away'),
                            stats.get('Total saves_home'),
                            stats.get('Total saves_away'),
                            stats.get('Corner kicks_home'),
                            stats.get('Corner kicks_away'),
                            stats.get('Fouls_home'),
                            stats.get('Fouls_away')
                        ))
                        inserted += 1
                
                except Exception as e:
                    logger.error(f"Error inserting second half stats for match {match_id}: {e}")
        
        db.commit()
    
    logger.info(f"Match statistics: {inserted} periods inserted, {duplicates} duplicates skipped")
    return inserted, duplicates
