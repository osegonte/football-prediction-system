-- ============================================================================
-- COMPREHENSIVE FOOTBALL DATABASE SCHEMA
-- ============================================================================
-- Purpose: Store all football match data for ML-based betting analysis
-- Coverage: Jan 1, 2025 onwards
-- Design: Normalized, no duplicates, complete data capture
-- ============================================================================

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS player_statistics CASCADE;
DROP TABLE IF EXISTS match_statistics CASCADE;
DROP TABLE IF EXISTS team_matches CASCADE;
DROP TABLE IF EXISTS fixtures CASCADE;
DROP TABLE IF EXISTS scraping_log CASCADE;
DROP TABLE IF EXISTS scraping_sessions CASCADE;

-- ============================================================================
-- TABLE 1: fixtures - All scheduled/played matches
-- ============================================================================
CREATE TABLE fixtures (
    match_id BIGINT PRIMARY KEY,           -- Sofascore unique match ID
    date DATE NOT NULL,                    -- Match date (YYYY-MM-DD)
    start_timestamp BIGINT,                -- Unix timestamp of kickoff
    home_team_id BIGINT NOT NULL,          -- Home team ID
    home_team_name VARCHAR(255) NOT NULL,  -- Home team name
    away_team_id BIGINT NOT NULL,          -- Away team ID
    away_team_name VARCHAR(255) NOT NULL,  -- Away team name
    tournament_name VARCHAR(255),          -- League/competition name
    tournament_id BIGINT,                  -- Tournament ID
    country VARCHAR(100),                  -- Country
    status VARCHAR(50),                    -- Match status (notstarted, finished, etc.)
    home_score INT,                        -- Final home score
    away_score INT,                        -- Final away score
    scraped_at TIMESTAMP DEFAULT NOW()     -- When data was collected
);

-- Indexes for fast queries
CREATE INDEX idx_fixtures_date ON fixtures(date);
CREATE INDEX idx_fixtures_home_team ON fixtures(home_team_id);
CREATE INDEX idx_fixtures_away_team ON fixtures(away_team_id);
CREATE INDEX idx_fixtures_status ON fixtures(status);
CREATE INDEX idx_fixtures_tournament ON fixtures(tournament_id);

COMMENT ON TABLE fixtures IS 'All football fixtures/matches from Sofascore';

-- ============================================================================
-- TABLE 2: team_matches - Team match history (baseline + 2025)
-- ============================================================================
CREATE TABLE team_matches (
    id SERIAL PRIMARY KEY,                 -- Auto-increment ID
    team_id BIGINT NOT NULL,               -- Team ID
    team_name VARCHAR(255) NOT NULL,       -- Team name
    match_id BIGINT NOT NULL,              -- Match ID
    match_date DATE NOT NULL,              -- When match was played
    match_timestamp BIGINT,                -- Unix timestamp
    match_year INT,                        -- Year (for filtering)
    opponent_id BIGINT,                    -- Opponent team ID
    opponent_name VARCHAR(255) NOT NULL,   -- Opponent name
    venue VARCHAR(10) NOT NULL,            -- 'Home' or 'Away'
    team_score INT NOT NULL,               -- Goals scored by team
    opponent_score INT NOT NULL,           -- Goals scored by opponent
    result VARCHAR(1) NOT NULL,            -- 'W', 'D', or 'L'
    tournament_name VARCHAR(255),          -- League name
    tournament_id BIGINT,                  -- Tournament ID
    scraped_at TIMESTAMP DEFAULT NOW(),    -- When collected
    
    UNIQUE(team_id, match_id)              -- Prevent duplicates
);

-- Indexes for fast queries
CREATE INDEX idx_team_matches_team ON team_matches(team_id);
CREATE INDEX idx_team_matches_date ON team_matches(team_id, match_date DESC);
CREATE INDEX idx_team_matches_match ON team_matches(match_id);
CREATE INDEX idx_team_matches_year ON team_matches(match_year);

COMMENT ON TABLE team_matches IS 'Historical match records per team (10 baseline + all 2025)';

-- ============================================================================
-- TABLE 3: match_statistics - Detailed match stats (1st & 2nd half)
-- ============================================================================
CREATE TABLE match_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,              -- Match ID
    period VARCHAR(3) NOT NULL,            -- '1ST' or '2ND' (first/second half)
    
    -- Possession
    ball_possession_home VARCHAR(10),      -- "58%" format
    ball_possession_away VARCHAR(10),
    
    -- Expected Goals (xG)
    expected_goals_home VARCHAR(10),       -- "1.45" format
    expected_goals_away VARCHAR(10),
    
    -- Shots
    total_shots_home VARCHAR(10),
    total_shots_away VARCHAR(10),
    shots_on_target_home VARCHAR(10),
    shots_on_target_away VARCHAR(10),
    shots_off_target_home VARCHAR(10),
    shots_off_target_away VARCHAR(10),
    blocked_shots_home VARCHAR(10),
    blocked_shots_away VARCHAR(10),
    shots_inside_box_home VARCHAR(10),
    shots_inside_box_away VARCHAR(10),
    shots_outside_box_home VARCHAR(10),
    shots_outside_box_away VARCHAR(10),
    hit_woodwork_home VARCHAR(10),
    hit_woodwork_away VARCHAR(10),
    
    -- Big Chances
    big_chances_home VARCHAR(10),
    big_chances_away VARCHAR(10),
    big_chances_missed_home VARCHAR(10),
    big_chances_missed_away VARCHAR(10),
    
    -- Passes
    passes_home VARCHAR(10),               -- "421" format
    passes_away VARCHAR(10),
    accurate_passes_home VARCHAR(10),      -- "379" format
    accurate_passes_away VARCHAR(10),
    passes_pct_home VARCHAR(10),           -- "90%" format
    passes_pct_away VARCHAR(10),
    
    -- Crossing
    crosses_home VARCHAR(10),
    crosses_away VARCHAR(10),
    accurate_crosses_home VARCHAR(10),
    accurate_crosses_away VARCHAR(10),
    
    -- Long balls
    long_balls_home VARCHAR(10),
    long_balls_away VARCHAR(10),
    accurate_long_balls_home VARCHAR(10),
    accurate_long_balls_away VARCHAR(10),
    
    -- Defensive
    tackles_home VARCHAR(10),
    tackles_away VARCHAR(10),
    interceptions_home VARCHAR(10),
    interceptions_away VARCHAR(10),
    clearances_home VARCHAR(10),
    clearances_away VARCHAR(10),
    
    -- Duels
    ground_duels_won_home VARCHAR(10),
    ground_duels_won_away VARCHAR(10),
    aerial_duels_won_home VARCHAR(10),
    aerial_duels_won_away VARCHAR(10),
    
    -- Dribbles
    dribble_attempts_home VARCHAR(10),
    dribble_attempts_away VARCHAR(10),
    successful_dribbles_home VARCHAR(10),
    successful_dribbles_away VARCHAR(10),
    
    -- Goalkeeping
    goalkeeper_saves_home VARCHAR(10),
    goalkeeper_saves_away VARCHAR(10),
    
    -- Set Pieces
    corner_kicks_home VARCHAR(10),
    corner_kicks_away VARCHAR(10),
    offsides_home VARCHAR(10),
    offsides_away VARCHAR(10),
    
    -- Discipline
    fouls_home VARCHAR(10),
    fouls_away VARCHAR(10),
    yellow_cards_home VARCHAR(10),
    yellow_cards_away VARCHAR(10),
    red_cards_home VARCHAR(10),
    red_cards_away VARCHAR(10),
    
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(match_id, period)               -- One entry per half
);

CREATE INDEX idx_match_stats_match ON match_statistics(match_id);
CREATE INDEX idx_match_stats_period ON match_statistics(match_id, period);

COMMENT ON TABLE match_statistics IS 'Detailed match statistics split by halves (1ST + 2ND)';

-- ============================================================================
-- TABLE 4: player_statistics - Individual player performance
-- ============================================================================
CREATE TABLE player_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL,
    player_id BIGINT NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    team_id BIGINT NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    position VARCHAR(50),                  -- 'F', 'M', 'D', 'G'
    shirt_number INT,
    substitute BOOLEAN DEFAULT FALSE,      -- Started or came on as sub
    
    -- Match Stats
    minutes_played INT,
    rating DECIMAL(3,1),                   -- Sofascore rating (e.g., 7.5)
    
    -- Attacking
    goals INT DEFAULT 0,
    assists INT DEFAULT 0,
    total_shots INT DEFAULT 0,
    shots_on_target INT DEFAULT 0,
    
    -- Passing
    passes_total INT DEFAULT 0,
    passes_accurate INT DEFAULT 0,
    key_passes INT DEFAULT 0,
    crosses_total INT DEFAULT 0,
    crosses_accurate INT DEFAULT 0,
    long_balls_total INT DEFAULT 0,
    long_balls_accurate INT DEFAULT 0,
    
    -- Dribbling
    dribbles_attempted INT DEFAULT 0,
    dribbles_successful INT DEFAULT 0,
    
    -- Defensive
    tackles INT DEFAULT 0,
    interceptions INT DEFAULT 0,
    clearances INT DEFAULT 0,
    blocked_shots INT DEFAULT 0,
    
    -- Duels
    duels_total INT DEFAULT 0,
    duels_won INT DEFAULT 0,
    aerial_duels_total INT DEFAULT 0,
    aerial_duels_won INT DEFAULT 0,
    ground_duels_total INT DEFAULT 0,
    ground_duels_won INT DEFAULT 0,
    
    -- Discipline
    fouls_committed INT DEFAULT 0,
    fouls_drawn INT DEFAULT 0,
    yellow_card BOOLEAN DEFAULT FALSE,
    red_card BOOLEAN DEFAULT FALSE,
    
    -- Goalkeeping (for goalkeepers)
    saves INT DEFAULT 0,
    
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(match_id, player_id)
);

CREATE INDEX idx_player_stats_match ON player_statistics(match_id);
CREATE INDEX idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX idx_player_stats_team ON player_statistics(team_id);
CREATE INDEX idx_player_stats_rating ON player_statistics(rating DESC);

COMMENT ON TABLE player_statistics IS 'Individual player performance statistics per match';

-- ============================================================================
-- TABLE 5: scraping_log - Audit trail for data collection
-- ============================================================================
CREATE TABLE scraping_log (
    id SERIAL PRIMARY KEY,
    scrape_date DATE NOT NULL,             -- Date of scraping operation
    scrape_type VARCHAR(50) NOT NULL,      -- 'fixtures', 'team_history', 'match_stats', 'player_stats'
    records_collected INT DEFAULT 0,       -- How many records scraped
    records_failed INT DEFAULT 0,          -- How many failed
    success_rate DECIMAL(5,2),             -- Percentage (0.00-100.00)
    duration_seconds INT,                  -- How long it took
    error_message TEXT,                    -- Any errors encountered
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scraping_log_date ON scraping_log(scrape_date);
CREATE INDEX idx_scraping_log_type ON scraping_log(scrape_type);

COMMENT ON TABLE scraping_log IS 'Audit trail of all scraping operations';

-- ============================================================================
-- TABLE 6: scraping_sessions - Progress tracking for long operations
-- ============================================================================
CREATE TABLE scraping_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,    -- UUID for this session
    session_type VARCHAR(50) NOT NULL,         -- 'fixtures', 'teams'
    scrape_date DATE,                          -- Target date (for fixtures)
    team_id BIGINT,                            -- Team ID (for team collection)
    team_name VARCHAR(255),                    -- Team name
    total_items INT DEFAULT 0,                 -- Total items to process
    items_completed INT DEFAULT 0,             -- Items processed so far
    status VARCHAR(20) DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'failed'
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    estimated_duration_seconds INT,
    notes TEXT
);

CREATE INDEX idx_sessions_status ON scraping_sessions(status);
CREATE INDEX idx_sessions_type ON scraping_sessions(session_type);
CREATE INDEX idx_sessions_team ON scraping_sessions(team_id);

COMMENT ON TABLE scraping_sessions IS 'Track progress of long-running collection sessions';

-- ============================================================================
-- VIEWS: Useful queries for analysis
-- ============================================================================

-- View: Teams with their collection status
CREATE OR REPLACE VIEW team_collection_status AS
SELECT 
    t.team_id,
    t.team_name,
    COUNT(tm.id) as total_matches,
    COUNT(CASE WHEN tm.match_year = 2025 THEN 1 END) as matches_2025,
    COUNT(CASE WHEN tm.match_year < 2025 THEN 1 END) as baseline_matches,
    MAX(tm.match_date) as latest_match_date,
    MIN(tm.match_date) as earliest_match_date
FROM (
    SELECT DISTINCT team_id, team_name FROM team_matches
) t
LEFT JOIN team_matches tm ON t.team_id = tm.team_id
GROUP BY t.team_id, t.team_name
ORDER BY total_matches DESC;

-- View: Match completion status
CREATE OR REPLACE VIEW match_completion_status AS
SELECT 
    f.match_id,
    f.date,
    f.home_team_name,
    f.away_team_name,
    f.status,
    CASE WHEN ms.match_id IS NOT NULL THEN TRUE ELSE FALSE END as has_match_stats,
    CASE WHEN ps.match_id IS NOT NULL THEN TRUE ELSE FALSE END as has_player_stats
FROM fixtures f
LEFT JOIN (SELECT DISTINCT match_id FROM match_statistics) ms ON f.match_id = ms.match_id
LEFT JOIN (SELECT DISTINCT match_id FROM player_statistics) ps ON f.match_id = ps.match_id
ORDER BY f.date DESC;

-- View: Daily collection summary
CREATE OR REPLACE VIEW daily_collection_summary AS
SELECT 
    date,
    COUNT(*) as total_fixtures,
    COUNT(DISTINCT home_team_id) + COUNT(DISTINCT away_team_id) as unique_teams,
    COUNT(DISTINCT tournament_name) as tournaments,
    COUNT(CASE WHEN status = 'finished' THEN 1 END) as finished_matches,
    COUNT(CASE WHEN status = 'notstarted' THEN 1 END) as upcoming_matches
FROM fixtures
GROUP BY date
ORDER BY date;

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function: Get team statistics
CREATE OR REPLACE FUNCTION get_team_stats(p_team_id BIGINT)
RETURNS TABLE (
    total_matches INT,
    wins INT,
    draws INT,
    losses INT,
    goals_scored INT,
    goals_conceded INT,
    win_percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INT as total_matches,
        COUNT(CASE WHEN result = 'W' THEN 1 END)::INT as wins,
        COUNT(CASE WHEN result = 'D' THEN 1 END)::INT as draws,
        COUNT(CASE WHEN result = 'L' THEN 1 END)::INT as losses,
        SUM(team_score)::INT as goals_scored,
        SUM(opponent_score)::INT as goals_conceded,
        (COUNT(CASE WHEN result = 'W' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0))::DECIMAL(5,2) as win_percentage
    FROM team_matches
    WHERE team_id = p_team_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL GRANTS (for multi-user setup)
-- ============================================================================

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO osegonte;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO osegonte;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;