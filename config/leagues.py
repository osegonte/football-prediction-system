"""
League configuration with priority system.
Sofascore provides league rankings - we use that to prioritize.
"""

# ============================================================================
# PRIORITY TIERS
# ============================================================================

PRIORITY_1_LEAGUES = [
    # Top 5 European leagues
    'Premier League',
    'LaLiga',
    'Serie A', 
    'Bundesliga',
    'Ligue 1',
    
    # European competitions
    'UEFA Champions League',
    'UEFA Europa League',
    'UEFA Europa Conference League',
    
    # Other major leagues
    'Eredivisie',
    'Primeira Liga',
    'Championship',
    'Scottish Premiership',
]

PRIORITY_2_LEAGUES = [
    # Second tier European
    'LaLiga 2',
    'Serie B',
    '2. Bundesliga',
    'Ligue 2',
    'EFL League One',
    'EFL League Two',
    
    # Americas
    'MLS',
    'Liga MX',
    'Brasileiro Série A',
    'Argentine Liga',
    
    # Asia/Middle East
    'Saudi Pro League',
    'J1 League',
    'K League 1',
    
    # Africa
    'Egyptian Premier League',
    'South African Premier Division',
]

# Priority 3 = Everything else (automatically detected)

# ============================================================================
# COLLECTION SETTINGS
# ============================================================================

MATCHES_BACK_PRIORITY_1 = 20  # Major leagues: 20 matches
MATCHES_BACK_PRIORITY_2 = 20  # Secondary: 20 matches  
MATCHES_BACK_PRIORITY_3 = 20  # Others: 20 matches

# Date range
START_DATE = '2025-01-01'  # January 1, 2025
# END_DATE = today (automatically calculated)

# ============================================================================
# COLLECTION INTERVALS
# ============================================================================

HISTORICAL_BATCH_DELAY = 120  # 2 minutes between batches (historical)
CONTINUOUS_CHECK_INTERVAL = 600  # 10 minutes (live mode)