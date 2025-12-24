"""
MASTER GOALS-ONLY ANALYSIS SYSTEM
Exports ONE comprehensive CSV with all metrics for today + tomorrow's fixtures.

Column count: ~148 columns
Row count: All upcoming fixtures in database

Output: master_analysis.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.connection import get_connection

print("\n" + "="*80)
print("⚽ MASTER GOALS-ONLY ANALYSIS SYSTEM")
print("   Target: Today + Tomorrow Fixtures")
print("="*80 + "\n")

# ============================================================================
# CONFIGURATION
# ============================================================================

WINDOW_SIZE = 7
EPSILON = 0.01  # For ratio calculations

# ============================================================================
# LOAD DATA
# ============================================================================

print("📥 Loading data from database...")

with get_connection() as db:
    # Get today + tomorrow fixtures
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    db.execute("""
        SELECT match_id, date, home_team_id, home_team_name,
               away_team_id, away_team_name, tournament_name, tournament_id
        FROM fixtures
        WHERE status = 'notstarted'
          AND date >= %s
          AND date <= %s
        ORDER BY date, start_timestamp
    """, (today, tomorrow))
    
    fixtures = pd.DataFrame(
        db.fetchall(),
        columns=['match_id', 'date', 'home_id', 'home_team',
                'away_id', 'away_team', 'tournament', 'tournament_id']
    )
    
    # Get all team match history
    db.execute("""
        SELECT team_id, team_name, match_id, match_date, venue,
               team_score, opponent_score, opponent_id, opponent_name,
               result, tournament_name
        FROM team_matches
        ORDER BY team_id, match_date DESC
    """)
    
    matches = pd.DataFrame(
        db.fetchall(),
        columns=['team_id', 'team_name', 'match_id', 'date', 'venue',
                'gf', 'ga', 'opp_id', 'opp_name', 'result', 'tournament']
    )
    
    # Get H2H data
    db.execute("""
        SELECT 
            LEAST(t1.team_id, t2.team_id) as team1_id,
            GREATEST(t1.team_id, t2.team_id) as team2_id,
            t1.match_id,
            t1.team_score + t2.team_score as total_goals,
            t1.match_date
        FROM team_matches t1
        JOIN team_matches t2 ON t1.match_id = t2.match_id
        WHERE t1.team_id < t2.team_id
        ORDER BY team1_id, team2_id, t1.match_date DESC
    """)
    
    h2h = pd.DataFrame(
        db.fetchall(),
        columns=['team1_id', 'team2_id', 'match_id', 'total_goals', 'date']
    )

print(f"✅ {len(fixtures)} fixtures (today + tomorrow)")
print(f"✅ {len(matches)} team matches")
print(f"✅ {len(h2h)} H2H records\n")

# ============================================================================
# LEAGUE CONTEXT
# ============================================================================

print("🌍 Computing league context...")

matches['tg'] = matches['gf'] + matches['ga']
league_stats = matches.groupby('tournament').agg({
    'gf': 'mean',
    'ga': 'mean',
    'tg': 'mean'
}).reset_index()
league_stats.columns = ['tournament', 'league_gf_avg', 'league_ga_avg', 'league_tg_avg']

print(f"✅ {len(league_stats)} leagues analyzed\n")

# ============================================================================
# TEAM PROFILE FUNCTION
# ============================================================================

def compute_team_profile(team_id, matches_df, league_stats_df):
    """Compute complete team profile with all metrics."""
    
    team_data = matches_df[matches_df['team_id'] == team_id].head(WINDOW_SIZE)
    
    if len(team_data) == 0:
        return None
    
    team_name = team_data.iloc[0]['team_name']
    tournament = team_data.iloc[0]['tournament']
    
    # League context
    league_ctx = league_stats_df[league_stats_df['tournament'] == tournament]
    if not league_ctx.empty:
        league_tg_avg = league_ctx.iloc[0]['league_tg_avg']
        league_gf_avg = league_ctx.iloc[0]['league_gf_avg']
        league_ga_avg = league_ctx.iloc[0]['league_ga_avg']
    else:
        league_tg_avg = 2.5
        league_gf_avg = 1.25
        league_ga_avg = 1.25
    
    # Venue splits
    home_data = team_data[team_data['venue'] == 'Home']
    away_data = team_data[team_data['venue'] == 'Away']
    
    # Sample sizes
    total_n = len(team_data)
    home_n = len(home_data)
    away_n = len(away_data)
    
    # Raw data strings
    last7_scores = ", ".join([f"{row['gf']}-{row['ga']}" for _, row in team_data.iterrows()])
    team_data['tg'] = team_data['gf'] + team_data['ga']
    last7_tg = ", ".join([str(int(tg)) for tg in team_data['tg']])
    
    # Attack
    gf_avg = team_data['gf'].mean()
    gf_home = home_data['gf'].mean() if home_n > 0 else gf_avg
    gf_away = away_data['gf'].mean() if away_n > 0 else gf_avg
    score_1p_rate = (team_data['gf'] >= 1).mean()
    score_2p_rate = (team_data['gf'] >= 2).mean()
    gf_relative = gf_avg / league_gf_avg if league_gf_avg > 0 else 1.0
    
    # Defense
    ga_avg = team_data['ga'].mean()
    ga_home = home_data['ga'].mean() if home_n > 0 else ga_avg
    ga_away = away_data['ga'].mean() if away_n > 0 else ga_avg
    concede_1p_rate = (team_data['ga'] >= 1).mean()
    clean_sheet_rate = (team_data['ga'] == 0).mean()
    ga_relative = ga_avg / league_ga_avg if league_ga_avg > 0 else 1.0
    
    # Openness
    tg_avg = team_data['tg'].mean()
    over15_rate = (team_data['tg'] >= 2).mean()
    over25_rate = (team_data['tg'] >= 3).mean()
    over35_rate = (team_data['tg'] >= 4).mean()
    tg_relative = tg_avg / league_tg_avg if league_tg_avg > 0 else 1.0
    
    # Dryness
    under15_rate = (team_data['tg'] <= 1).mean()
    fts_rate = (team_data['gf'] == 0).mean()
    zero_zero_rate = ((team_data['gf'] == 0) & (team_data['ga'] == 0)).mean()
    
    # Consistency
    tg_std = team_data['tg'].std() if len(team_data) > 1 else 0.0
    extreme_rate = (team_data['tg'] >= 4).mean()
    consistency_index = 1 / (1 + tg_std)
    chaos_index = tg_std / max(tg_avg, 1.0)
    
    # Momentum
    if len(team_data) >= 5:
        last3 = team_data.head(3)
        recent_gf = last3['gf'].mean()
        recent_ga = last3['ga'].mean()
        recent_tg = last3['tg'].mean()
        
        attack_momentum = (recent_gf - gf_avg) / max(gf_avg, 0.5)
        defense_momentum = (ga_avg - recent_ga) / max(ga_avg, 0.5)
        openness_momentum = recent_tg - tg_avg
        form_combined = attack_momentum + defense_momentum
    else:
        attack_momentum = 0.0
        defense_momentum = 0.0
        openness_momentum = 0.0
        form_combined = 0.0
    
    # Dominance/Distribution
    goal_share = gf_avg / max(gf_avg + ga_avg, 1.0)
    low_bin_rate = (team_data['tg'] <= 1).mean()
    mid_bin_rate = ((team_data['tg'] >= 2) & (team_data['tg'] <= 3)).mean()
    
    return {
        # Raw
        'last7_scores': last7_scores,
        'last7_tg_list': last7_tg,
        
        # Sample sizes
        'total_matches_n': total_n,
        'home_matches_n': home_n,
        'away_matches_n': away_n,
        
        # Attack
        'gf_avg': gf_avg,
        'gf_home': gf_home,
        'gf_away': gf_away,
        'score_1p_rate': score_1p_rate,
        'score_2p_rate': score_2p_rate,
        'gf_relative': gf_relative,
        
        # Defense
        'ga_avg': ga_avg,
        'ga_home': ga_home,
        'ga_away': ga_away,
        'concede_1p_rate': concede_1p_rate,
        'clean_sheet_rate': clean_sheet_rate,
        'ga_relative': ga_relative,
        
        # Openness
        'tg_avg': tg_avg,
        'over15_rate': over15_rate,
        'over25_rate': over25_rate,
        'over35_rate': over35_rate,
        'tg_relative': tg_relative,
        
        # Dryness
        'under15_rate': under15_rate,
        'fts_rate': fts_rate,
        'zero_zero_rate': zero_zero_rate,
        
        # Consistency
        'tg_std': tg_std,
        'extreme_rate': extreme_rate,
        'consistency_index': consistency_index,
        'chaos_index': chaos_index,
        
        # Momentum
        'attack_momentum': attack_momentum,
        'defense_momentum': defense_momentum,
        'openness_momentum': openness_momentum,
        'form_combined': form_combined,
        
        # Dominance
        'goal_share': goal_share,
        'low_bin_rate': low_bin_rate,
        'mid_bin_rate': mid_bin_rate
    }

# ============================================================================
# H2H FUNCTION
# ============================================================================

def get_h2h_data(home_id, away_id, h2h_df):
    """Get H2H statistics."""
    team1 = min(home_id, away_id)
    team2 = max(home_id, away_id)
    
    h2h_matches = h2h_df[
        (h2h_df['team1_id'] == team1) & 
        (h2h_df['team2_id'] == team2)
    ].head(5)
    
    if len(h2h_matches) >= 2:
        h2h_tg_avg = h2h_matches['total_goals'].mean()
        h2h_n = len(h2h_matches)
        return h2h_tg_avg, h2h_n
    
    return 0.0, 0

# ============================================================================
# BUILD MASTER DATAFRAME
# ============================================================================

print("🔨 Building master analysis...")

# Create team profile cache
print("   Computing team profiles...")
team_profiles = {}
unique_teams = set(fixtures['home_id'].unique()) | set(fixtures['away_id'].unique())

for team_id in unique_teams:
    profile = compute_team_profile(team_id, matches, league_stats)
    if profile:
        team_profiles[team_id] = profile

print(f"   ✅ {len(team_profiles)} team profiles cached")

# Build master rows
master_rows = []
processed = 0

print("   Processing fixtures...")

for _, fix in fixtures.iterrows():
    processed += 1
    if processed % 100 == 0:
        print(f"   Progress: {processed}/{len(fixtures)} fixtures...")
    
    home_prof = team_profiles.get(fix['home_id'])
    away_prof = team_profiles.get(fix['away_id'])
    
    if not home_prof or not away_prof:
        continue
    
    # League context
    league_ctx = league_stats[league_stats['tournament'] == fix['tournament']]
    league_tg_avg = league_ctx.iloc[0]['league_tg_avg'] if not league_ctx.empty else 2.5
    
    # H2H
    h2h_tg, h2h_n = get_h2h_data(fix['home_id'], fix['away_id'], h2h)
    
    # === FIXTURE INTERACTIONS ===
    
    # Pressure
    home_pressure = home_prof['gf_home'] * max(2.5 - away_prof['ga_away'], 0.5)
    away_pressure = away_prof['gf_away'] * max(2.5 - home_prof['ga_home'], 0.5)
    pressure_total = home_pressure + away_pressure
    pressure_diff = abs(home_pressure - away_pressure)
    pressure_ratio = (home_pressure + EPSILON) / (away_pressure + EPSILON)
    
    # Combined
    combined_attack = (home_prof['gf_home'] + away_prof['gf_away']) / 2
    combined_defense_weak = (away_prof['ga_away'] + home_prof['ga_home']) / 2
    
    # Defense strength index (scaled inverse)
    max_ga = 3.0  # Assume max GA for scaling
    defense_strength_index = 1 - (combined_defense_weak / max_ga)
    defense_strength_index = max(0, min(1, defense_strength_index))
    
    combined_openness = (home_prof['over25_rate'] + away_prof['over25_rate']) / 2
    high_openness = (home_prof['over35_rate'] + away_prof['over35_rate']) / 2
    
    # Dryness
    dryness_index = (home_prof['under15_rate'] + away_prof['under15_rate']) / 2
    zero_zero_combined = (home_prof['zero_zero_rate'] + away_prof['zero_zero_rate']) / 2
    
    # Suppression overlap
    suppression_overlap = (
        min(home_prof['clean_sheet_rate'], away_prof['fts_rate']) +
        min(away_prof['clean_sheet_rate'], home_prof['fts_rate'])
    )
    
    # GG
    both_attack_strong = min(home_prof['score_1p_rate'], away_prof['score_1p_rate'])
    both_defense_weak = min(home_prof['concede_1p_rate'], away_prof['concede_1p_rate'])
    balanced_pressure = 1 - (pressure_diff / max(pressure_total, EPSILON))
    
    # Archetype
    if pressure_ratio > 2.0:
        archetype_base = "HOME_DOM"
        domination_boost = 1.0
        balanced_boost = 0.0
    elif pressure_ratio < 0.5:
        archetype_base = "AWAY_DOM"
        domination_boost = 1.0
        balanced_boost = 0.0
    elif 0.8 < pressure_ratio < 1.2:
        archetype_base = "BALANCED"
        domination_boost = 0.0
        balanced_boost = 1.0
    else:
        archetype_base = "SLIGHT_FAV"
        domination_boost = 0.5
        balanced_boost = 0.5
    
    if combined_defense_weak > 1.5:
        archetype_sub = "OPEN"
        open_game_boost = 1.0
        tight_game_boost = 0.0
    elif combined_defense_weak < 1.0:
        archetype_sub = "TIGHT"
        open_game_boost = 0.0
        tight_game_boost = 1.0
    else:
        archetype_sub = "NEUTRAL"
        open_game_boost = 0.5
        tight_game_boost = 0.5
    
    archetype = f"{archetype_base}_{archetype_sub}"
    chaos_boost = (home_prof['chaos_index'] + away_prof['chaos_index']) / 2
    archetype_boost = open_game_boost if "OPEN" in archetype else tight_game_boost
    
    # H2H modifier
    expected_tg = (home_prof['tg_avg'] + away_prof['tg_avg']) / 2
    if h2h_tg > 0:
        h2h_modifier = (h2h_tg - expected_tg) / max(expected_tg, 1.0)
        h2h_modifier = np.clip(h2h_modifier, -0.2, 0.2)
    else:
        h2h_modifier = 0.0
    
    # === QUALITY FLAGS ===
    q_home_full_7 = home_prof['total_matches_n'] >= 7
    q_away_full_7 = away_prof['total_matches_n'] >= 7
    q_home_split_ok = home_prof['home_matches_n'] >= 3 and home_prof['away_matches_n'] >= 3
    q_away_split_ok = away_prof['home_matches_n'] >= 3 and away_prof['away_matches_n'] >= 3
    q_h2h_available = h2h_n >= 2
    
    # === BUILD ROW ===
    row = {
        # Match info
        'm_match_id': fix['match_id'],
        'm_date': fix['date'],
        'm_home_id': fix['home_id'],
        'm_home_team': fix['home_team'],
        'm_away_id': fix['away_id'],
        'm_away_team': fix['away_team'],
        'm_tournament': fix['tournament'],
        'm_league_avg_tg': league_tg_avg,
    }
    
    # Home team profile
    for key, val in home_prof.items():
        row[f'h_{key}'] = val
    
    # Away team profile
    for key, val in away_prof.items():
        row[f'a_{key}'] = val
    
    # Fixture interactions
    row.update({
        'x_home_pressure': home_pressure,
        'x_away_pressure': away_pressure,
        'x_pressure_total': pressure_total,
        'x_pressure_diff': pressure_diff,
        'x_pressure_ratio': pressure_ratio,
        'x_combined_attack': combined_attack,
        'x_combined_defense_weak': combined_defense_weak,
        'x_defense_strength_index': defense_strength_index,
        'x_combined_openness': combined_openness,
        'x_high_openness': high_openness,
        'x_dryness_index': dryness_index,
        'x_zero_zero_combined': zero_zero_combined,
        'x_suppression_overlap': suppression_overlap,
        'x_both_attack_strong': both_attack_strong,
        'x_both_defense_weak': both_defense_weak,
        'x_balanced_pressure': balanced_pressure,
        'x_archetype': archetype,
        'x_archetype_boost': archetype_boost,
        'x_domination_boost': domination_boost,
        'x_balanced_boost': balanced_boost,
        'x_open_game_boost': open_game_boost,
        'x_tight_game_boost': tight_game_boost,
        'x_chaos_boost': chaos_boost,
        'x_h2h_tg_avg': h2h_tg,
        'x_h2h_modifier': h2h_modifier,
        'x_h2h_matches_n': h2h_n,
    })
    
    # Quality flags
    row.update({
        'q_home_has_full_7': q_home_full_7,
        'q_away_has_full_7': q_away_full_7,
        'q_home_split_ok': q_home_split_ok,
        'q_away_split_ok': q_away_split_ok,
        'q_h2h_available': q_h2h_available,
    })
    
    master_rows.append(row)

# Create DataFrame
df_master = pd.DataFrame(master_rows)

print(f"   ✅ {len(df_master)} fixtures processed\n")

# ============================================================================
# CATEGORY SCORING
# ============================================================================

print("📊 Computing category confidence scores...")

def normalize_col(series):
    """Normalize column to 0-1."""
    if series.max() > series.min():
        return (series - series.min()) / (series.max() - series.min())
    return series

def safe_divide(numerator, denominator):
    """Safe division for pandas Series."""
    return numerator / denominator.clip(lower=EPSILON)

# Over 1.5
score = (
    0.20 * normalize_col(df_master['x_combined_attack']) +
    0.20 * normalize_col(df_master['x_combined_defense_weak']) +
    0.15 * normalize_col(df_master['x_combined_openness']) +
    0.15 * normalize_col(df_master['x_both_attack_strong']) +
    0.10 * normalize_col(df_master['h_attack_momentum'] + df_master['a_attack_momentum']) +
    0.10 * df_master['x_archetype_boost'] -
    0.10 * normalize_col(df_master['x_dryness_index'])
)
score = normalize_col(score)
score = score * (1 + 0.1 * df_master['x_h2h_modifier'])
df_master['p_over15_conf'] = 100 * score / score.max().clip(0.01, None)

# Over 2.5
score = (
    0.25 * normalize_col(df_master['x_combined_attack']) +
    0.20 * normalize_col(df_master['x_combined_defense_weak']) +
    0.20 * normalize_col(df_master['x_combined_openness']) +
    0.10 * normalize_col(df_master['x_pressure_total']) +
    0.10 * normalize_col(df_master['h_attack_momentum'] + df_master['a_attack_momentum']) +
    0.10 * df_master['x_archetype_boost'] -
    0.15 * normalize_col(df_master['x_dryness_index'])
)
score = normalize_col(score)
score = score * (1 + 0.1 * df_master['x_h2h_modifier'])
df_master['p_over25_conf'] = 100 * score / score.max().clip(0.01, None)

# Over 3.5
score = (
    0.25 * normalize_col(df_master['x_combined_attack']) +
    0.25 * normalize_col(df_master['x_combined_defense_weak']) +
    0.20 * normalize_col(df_master['x_high_openness']) +
    0.15 * normalize_col(df_master['x_chaos_boost']) +
    0.15 * normalize_col(df_master['h_extreme_rate'] + df_master['a_extreme_rate'])
)
score = normalize_col(score)
score = score * (1 + 0.1 * df_master['x_h2h_modifier'])
df_master['p_over35_conf'] = 100 * score / score.max().clip(0.01, None)

# Over 4.5
score = (
    0.35 * normalize_col(df_master['x_combined_attack'] * df_master['x_combined_defense_weak']) +
    0.30 * normalize_col(df_master['x_combined_attack']) +
    0.25 * normalize_col(df_master['x_combined_defense_weak']) +
    0.10 * df_master['x_chaos_boost']
)
score = normalize_col(score)
df_master['p_over45_conf'] = 100 * score / score.max().clip(0.01, None)

# Under 1.5
score = (
    0.35 * normalize_col(df_master['x_dryness_index']) +
    0.25 * normalize_col(df_master['x_defense_strength_index']) +
    0.20 * normalize_col(2.5 - df_master['x_combined_attack']) +
    0.15 * df_master['x_tight_game_boost'] +
    0.05 * normalize_col(df_master['x_zero_zero_combined'])
)
score = normalize_col(score)
df_master['p_under15_conf'] = 100 * score / score.max().clip(0.01, None)

# Under 2.5
score = (
    0.25 * normalize_col(df_master['x_dryness_index']) +
    0.25 * normalize_col(df_master['x_defense_strength_index']) +
    0.20 * normalize_col(1 - df_master['x_combined_openness']) +
    0.15 * df_master['x_tight_game_boost'] +
    0.15 * normalize_col(2.5 - df_master['x_combined_attack'])
)
score = normalize_col(score)
df_master['p_under25_conf'] = 100 * score / score.max().clip(0.01, None)

# GG
score = (
    0.30 * normalize_col(df_master['x_both_attack_strong']) +
    0.25 * normalize_col(df_master['x_both_defense_weak']) +
    0.15 * normalize_col(df_master['x_balanced_pressure']) +
    0.15 * normalize_col(df_master['h_attack_momentum'].clip(0, None) + df_master['a_attack_momentum'].clip(0, None)) +
    0.10 * df_master['x_open_game_boost'] -
    0.10 * normalize_col(df_master['x_dryness_index'])
)
score = normalize_col(score)
score = score * (1 + 0.1 * df_master['x_h2h_modifier'])
df_master['p_gg_conf'] = 100 * score / score.max().clip(0.01, None)

# Home Win
home_adv = df_master['h_gf_home'] - df_master['a_gf_away']
score = (
    0.30 * normalize_col(home_adv) +
    0.20 * normalize_col(df_master['a_ga_away']) +
    0.20 * normalize_col(safe_divide(df_master['x_home_pressure'], df_master['x_pressure_total'])) +
    0.15 * normalize_col(df_master['h_form_combined']) +
    0.15 * df_master['x_domination_boost']
)
score = normalize_col(score)
df_master['p_home_win_conf'] = 100 * score / score.max().clip(0.01, None)

# Away Win
away_adv = df_master['a_gf_away'] - df_master['h_gf_home']
score = (
    0.30 * normalize_col(away_adv) +
    0.20 * normalize_col(df_master['h_ga_home']) +
    0.20 * normalize_col(safe_divide(df_master['x_away_pressure'], df_master['x_pressure_total'])) +
    0.15 * normalize_col(df_master['a_form_combined']) +
    0.15 * df_master['x_domination_boost']
)
score = normalize_col(score)
df_master['p_away_win_conf'] = 100 * score / score.max().clip(0.01, None)

# Draw
score = (
    0.35 * normalize_col(df_master['x_balanced_pressure']) +
    0.25 * normalize_col(1 - safe_divide(df_master['x_pressure_diff'], df_master['x_pressure_total'])) +
    0.20 * normalize_col(1 - abs(df_master['x_combined_attack'] - 1.5)) +
    0.20 * df_master['x_balanced_boost']
)
score = normalize_col(score)
df_master['p_draw_conf'] = 100 * score / score.max().clip(0.01, None)

# Over 2.5 + GG
score = (
    0.20 * normalize_col(df_master['x_combined_attack']) +
    0.20 * normalize_col(df_master['x_both_attack_strong']) +
    0.20 * normalize_col(df_master['x_both_defense_weak']) +
    0.20 * normalize_col(df_master['x_high_openness']) +
    0.15 * df_master['x_open_game_boost'] +
    0.05 * normalize_col(df_master['h_attack_momentum'].clip(0, None) + df_master['a_attack_momentum'].clip(0, None))
)
score = normalize_col(score)
score = score * (1 + 0.1 * df_master['x_h2h_modifier'])
df_master['p_over25_gg_conf'] = 100 * score / score.max().clip(0.01, None)

# Home + Over 2.5
score = (
    0.25 * normalize_col(df_master['h_gf_home']) +
    0.25 * normalize_col(df_master['a_ga_away']) +
    0.20 * normalize_col(df_master['x_combined_attack']) +
    0.15 * normalize_col(safe_divide(df_master['x_home_pressure'], df_master['x_pressure_total'])) +
    0.10 * normalize_col(df_master['h_form_combined']) +
    0.05 * df_master['x_domination_boost']
)
score = normalize_col(score)
df_master['p_home_over25_conf'] = 100 * score / score.max().clip(0.01, None)

# Away + Over 2.5
score = (
    0.25 * normalize_col(df_master['a_gf_away']) +
    0.25 * normalize_col(df_master['h_ga_home']) +
    0.20 * normalize_col(df_master['x_combined_attack']) +
    0.15 * normalize_col(safe_divide(df_master['x_away_pressure'], df_master['x_pressure_total'])) +
    0.10 * normalize_col(df_master['a_form_combined']) +
    0.05 * df_master['x_domination_boost']
)
score = normalize_col(score)
df_master['p_away_over25_conf'] = 100 * score / score.max().clip(0.01, None)

# Home + GG
score = (
    0.25 * normalize_col(df_master['h_gf_home']) +
    0.25 * normalize_col(df_master['a_gf_away'].clip(1.0, None)) +
    0.20 * normalize_col(df_master['x_both_defense_weak']) +
    0.15 * normalize_col(df_master['x_home_pressure']) +
    0.10 * normalize_col(df_master['h_form_combined']) +
    0.05 * df_master['x_open_game_boost']
)
score = normalize_col(score)
df_master['p_home_gg_conf'] = 100 * score / score.max().clip(0.01, None)

# Away + GG
score = (
    0.25 * normalize_col(df_master['a_gf_away']) +
    0.25 * normalize_col(df_master['h_gf_home'].clip(1.0, None)) +
    0.20 * normalize_col(df_master['x_both_defense_weak']) +
    0.15 * normalize_col(df_master['x_away_pressure']) +
    0.10 * normalize_col(df_master['a_form_combined']) +
    0.05 * df_master['x_open_game_boost']
)
score = normalize_col(score)
df_master['p_away_gg_conf'] = 100 * score / score.max().clip(0.01, None)

print(f"✅ All 15 category scores computed\n")

# ============================================================================
# EXPORT
# ============================================================================

print("💾 Exporting master CSV...")

output_file = 'data/master_analysis.csv'
df_master.to_csv(output_file, index=False)

print(f"✅ Exported: {output_file}")
print(f"   Rows: {len(df_master)}")
print(f"   Columns: {len(df_master.columns)}")

# Show column summary
print("\n📋 Column Structure:")
print(f"   Match Info (m_*): {len([c for c in df_master.columns if c.startswith('m_')])}")
print(f"   Home Team (h_*): {len([c for c in df_master.columns if c.startswith('h_')])}")
print(f"   Away Team (a_*): {len([c for c in df_master.columns if c.startswith('a_')])}")
print(f"   Interactions (x_*): {len([c for c in df_master.columns if c.startswith('x_')])}")
print(f"   Confidence (p_*): {len([c for c in df_master.columns if c.startswith('p_')])}")
print(f"   Quality Flags (q_*): {len([c for c in df_master.columns if c.startswith('q_')])}")

# Show top matches for one category
print("\n🏆 Sample: Top 5 Over 2.5 Confidence")
top5 = df_master.nlargest(5, 'p_over25_conf')[
    ['m_date', 'm_home_team', 'm_away_team', 'm_tournament', 'p_over25_conf', 'x_archetype']
]
print(top5.to_string(index=False))

print("\n" + "="*80)
print("✅ MASTER ANALYSIS COMPLETE")
print("="*80)
print(f"\n📂 Output: {output_file}")
print("🎯 Ready for filtering and analysis!\n")
