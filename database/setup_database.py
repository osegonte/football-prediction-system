"""
Database Setup Script
Place in: database/setup_database.py

Run: python database/setup_database.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def create_tables():
    """Create all database tables"""
    
    tables_sql = """
    -- Fixtures table
    CREATE TABLE IF NOT EXISTS fixtures (
        fixture_id SERIAL PRIMARY KEY,
        match_id BIGINT UNIQUE NOT NULL,
        date DATE NOT NULL,
        home_team_id INT NOT NULL,
        home_team_name VARCHAR(255),
        away_team_id INT NOT NULL,
        away_team_name VARCHAR(255),
        home_score INT,
        away_score INT,
        status VARCHAR(50),
        tournament_id INT,
        tournament_name VARCHAR(255),
        round_info VARCHAR(100),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Teams table
    CREATE TABLE IF NOT EXISTS teams (
        id SERIAL PRIMARY KEY,
        team_id INT UNIQUE NOT NULL,
        team_name VARCHAR(255),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Team matches table
    CREATE TABLE IF NOT EXISTS team_matches (
        id SERIAL PRIMARY KEY,
        team_id INT NOT NULL,
        match_id BIGINT NOT NULL,
        date DATE,
        opponent VARCHAR(255),
        home_away VARCHAR(10),
        score VARCHAR(20),
        result VARCHAR(10),
        tournament VARCHAR(255),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(team_id, match_id)
    );
    
    -- Match statistics table
    CREATE TABLE IF NOT EXISTS match_statistics (
        id SERIAL PRIMARY KEY,
        match_id BIGINT NOT NULL,
        period VARCHAR(10) NOT NULL,
        ball_possession_home FLOAT,
        ball_possession_away FLOAT,
        total_shots_home INT,
        total_shots_away INT,
        shots_on_target_home INT,
        shots_on_target_away INT,
        shots_off_target_home INT,
        shots_off_target_away INT,
        blocked_shots_home INT,
        blocked_shots_away INT,
        corner_kicks_home INT,
        corner_kicks_away INT,
        offsides_home INT,
        offsides_away INT,
        fouls_home INT,
        fouls_away INT,
        throw_ins_home INT,
        throw_ins_away INT,
        goalkeeper_saves_home INT,
        goalkeeper_saves_away INT,
        goal_kicks_home INT,
        goal_kicks_away INT,
        total_passes_home INT,
        total_passes_away INT,
        accurate_passes_home INT,
        accurate_passes_away INT,
        tackles_home INT,
        tackles_away INT,
        attacks_home INT,
        attacks_away INT,
        dangerous_attacks_home INT,
        dangerous_attacks_away INT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(match_id, period)
    );
    
    -- Player statistics table
    CREATE TABLE IF NOT EXISTS player_statistics (
        id SERIAL PRIMARY KEY,
        match_id BIGINT NOT NULL,
        team_id INT NOT NULL,
        team_name VARCHAR(255),
        player_id INT NOT NULL,
        player_name VARCHAR(255) NOT NULL,
        position VARCHAR(10),
        shirt_number INT,
        substitute BOOLEAN,
        minutes_played INT,
        rating FLOAT,
        goals INT,
        assists INT,
        total_shots INT,
        shots_on_target INT,
        big_chances_missed INT,
        hit_woodwork INT,
        offsides INT,
        dispossessed INT,
        total_passes INT,
        key_passes INT,
        accurate_passes INT,
        dribbles_attempted INT,
        dribbles_successful INT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(match_id, player_id)
    );
    
    -- Scraping log table
    CREATE TABLE IF NOT EXISTS scraping_log (
        id SERIAL PRIMARY KEY,
        scrape_type VARCHAR(50),
        status VARCHAR(50),
        records_count INT,
        error_message TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(date);
    CREATE INDEX IF NOT EXISTS idx_fixtures_match_id ON fixtures(match_id);
    CREATE INDEX IF NOT EXISTS idx_team_matches_team_id ON team_matches(team_id);
    CREATE INDEX IF NOT EXISTS idx_team_matches_match_id ON team_matches(match_id);
    CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON match_statistics(match_id);
    CREATE INDEX IF NOT EXISTS idx_player_stats_match_id ON player_statistics(match_id);
    CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_statistics(player_id);
    """
    
    try:
        with get_connection() as db:
            # Execute all SQL statements
            db.execute(tables_sql)
        
        print("✓ Database schema created successfully")
        print("\nTables created:")
        print("  - fixtures")
        print("  - teams")
        print("  - team_matches")
        print("  - match_statistics")
        print("  - player_statistics")
        print("  - scraping_log")
        print("\nIndexes created for performance")
        print("\nDatabase is ready!")
        
        return True
    
    except Exception as e:
        print(f"✗ Error creating database schema: {e}")
        return False


def verify_tables():
    """Verify all tables exist"""
    try:
        with get_connection() as db:
            db.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in db.fetchall()]
        
        expected = ['fixtures', 'teams', 'team_matches', 'match_statistics', 'player_statistics', 'scraping_log']
        
        print("\nVerification:")
        all_exist = True
        for table in expected:
            exists = table in tables
            status = "✓" if exists else "✗"
            print(f"  {status} {table}")
            if not exists:
                all_exist = False
        
        if all_exist:
            print("\n✓ All tables verified successfully")
        else:
            print("\n✗ Some tables are missing")
        
        return all_exist
    
    except Exception as e:
        print(f"✗ Error verifying tables: {e}")
        return False


def main():
    print("="*60)
    print("Football Data Collector - Database Setup")
    print("="*60)
    print()
    
    # Create tables
    if create_tables():
        # Verify
        verify_tables()
        print()
        print("="*60)
        print("Setup complete! Ready to run collector.py")
        print("="*60)
        return 0
    else:
        print()
        print("="*60)
        print("Setup failed! Check error messages above")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit(main())