-- Football Data Collection System - Database Schema
-- Created: December 10, 2025
-- PostgreSQL 15

-- ============================================================================
-- TABLE 1: fixtures
-- Master list of all matches (upcoming + finished)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fixtures (
    match_id BIGINT PRIMARY KEY,
    date DATE NOT NULL,
    start_timestamp BIGINT,
    home_team_id INTEGER NOT NULL,
    home_team_name VARCHAR(255) NOT NULL,
    away_team_id INTEGER NOT NULL,
    away_team_name VARCHAR(255) NOT NULL,
    tournament_name VARCHAR(255),
    tournament_id INTEGER,
    country VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(date);
CREATE INDEX IF NOT EXISTS idx_fixtures_home_team ON fixtures(home_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_away_team ON fixtures(away_team_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_status ON fixtures(status);
CREATE INDEX IF NOT EXISTS idx_fixtures_tournament ON fixtures(tournament_id);

-- ============================================================================
-- TABLE 2: team_matches
-- Historical performance for each team
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_matches (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    match_id BIGINT NOT NULL,
    match_date DATE NOT NULL,
    match_timestamp BIGINT,
    match_year INTEGER,
    opponent_id INTEGER NOT NULL,
    opponent_name VARCHAR(255) NOT NULL,
    venue VARCHAR(10) NOT NULL CHECK (venue IN ('Home', 'Away')),
    team_score INTEGER NOT NULL,
    opponent_score INTEGER NOT NULL,
    result CHAR(1) NOT NULL CHECK (result IN ('W', 'D', 'L')),
    tournament_name VARCHAR(255),
    tournament_id INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, match_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_team_matches_team ON team_matches(team_id, match_date DESC);
CREATE INDEX IF NOT EXISTS idx_team_matches_match ON team_matches(match_id);
CREATE INDEX IF NOT EXISTS idx_team_matches_date ON team_matches(match_date);

-- ============================================================================
-- TABLE 3: match_statistics
-- Detailed stats (First Half + Second Half)
-- ============================================================================

CREATE TABLE IF NOT EXISTS match_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,
    period VARCHAR(10) NOT NULL CHECK (period IN ('1ST', '2ND')),
    
    -- Possession & Expected Goals
    ball_possession_home VARCHAR(10),
    ball_possession_away VARCHAR(10),
    expected_goals_home NUMERIC(4,2),
    expected_goals_away NUMERIC(4,2),
    
    -- Shots
    total_shots_home INTEGER,
    total_shots_away INTEGER,
    shots_on_target_home INTEGER,
    shots_on_target_away INTEGER,
    shots_off_target_home INTEGER,
    shots_off_target_away INTEGER,
    blocked_shots_home INTEGER,
    blocked_shots_away INTEGER,
    shots_inside_box_home INTEGER,
    shots_inside_box_away INTEGER,
    shots_outside_box_home INTEGER,
    shots_outside_box_away INTEGER,
    hit_woodwork_home INTEGER,
    hit_woodwork_away INTEGER,
    
    -- Attacks & Chances
    big_chances_home INTEGER,
    big_chances_away INTEGER,
    big_chances_missed_home INTEGER,
    big_chances_missed_away INTEGER,
    
    -- Passing
    passes_home INTEGER,
    passes_away INTEGER,
    accurate_passes_home INTEGER,
    accurate_passes_away INTEGER,
    key_passes_home INTEGER,
    key_passes_away INTEGER,
    
    -- Defending
    tackles_home INTEGER,
    tackles_away INTEGER,
    interceptions_home INTEGER,
    interceptions_away INTEGER,
    clearances_home INTEGER,
    clearances_away INTEGER,
    
    -- Duels
    duels_won_home INTEGER,
    duels_won_away INTEGER,
    ground_duels_won_home INTEGER,
    ground_duels_won_away INTEGER,
    aerial_duels_won_home INTEGER,
    aerial_duels_won_away INTEGER,
    
    -- Goalkeeper
    goalkeeper_saves_home INTEGER,
    goalkeeper_saves_away INTEGER,
    
    -- Set Pieces
    corner_kicks_home INTEGER,
    corner_kicks_away INTEGER,
    fouls_home INTEGER,
    fouls_away INTEGER,
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, period)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_match_stats_match ON match_statistics(match_id);
CREATE INDEX IF NOT EXISTS idx_match_stats_period ON match_statistics(period);

-- ============================================================================
-- TABLE 4: player_statistics
-- Individual player performance
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,
    team_id INTEGER NOT NULL,
    team_name VARCHAR(255),
    player_id INTEGER NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    position VARCHAR(10),
    jersey_number INTEGER,
    is_substitute BOOLEAN DEFAULT FALSE,
    
    -- Performance Metrics
    minutes_played INTEGER,
    rating NUMERIC(3,1),
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    
    -- Shooting
    total_shots INTEGER DEFAULT 0,
    
    -- Passing
    accurate_passes INTEGER DEFAULT 0,
    total_passes INTEGER DEFAULT 0,
    
    -- Defending
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    
    -- Duels
    duels_won INTEGER DEFAULT 0,
    duels_total INTEGER DEFAULT 0,
    
    -- Discipline
    fouls_committed INTEGER DEFAULT 0,
    was_fouled INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_player_stats_match ON player_statistics(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_statistics(team_id);

-- ============================================================================
-- TABLE 5: scraping_log
-- Track scraping operations
-- ============================================================================

CREATE TABLE IF NOT EXISTS scraping_log (
    id SERIAL PRIMARY KEY,
    scrape_date DATE NOT NULL,
    scrape_type VARCHAR(50) NOT NULL,
    records_collected INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    success_rate NUMERIC(5,2),
    duration_seconds INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX IF NOT EXISTS idx_scraping_log_date ON scraping_log(scrape_date DESC);
CREATE INDEX IF NOT EXISTS idx_scraping_log_type ON scraping_log(scrape_type);

-- ============================================================================
-- VIEWS (Helpful queries)
-- ============================================================================

-- View: Upcoming matches
CREATE OR REPLACE VIEW upcoming_matches AS
SELECT * FROM fixtures 
WHERE status = 'scheduled' 
ORDER BY date, start_timestamp;

-- View: Recent team performance (last 7 matches)
CREATE OR REPLACE VIEW team_recent_form AS
SELECT 
    team_id,
    team_name,
    COUNT(*) as matches_played,
    SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) as losses,
    AVG(team_score) as avg_goals_scored,
    AVG(opponent_score) as avg_goals_conceded
FROM team_matches
GROUP BY team_id, team_name;

-- ============================================================================
-- GRANT PERMISSIONS (if needed for remote access)
-- ============================================================================

-- Will be configured when setting up remote access

