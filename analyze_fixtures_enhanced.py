"""
ENHANCED GOALS-ONLY ANALYSIS SYSTEM
Includes: Momentum, Trends, Opponent Quality, H2H, League Normalization, Match Archetypes

Version: 2.0 - Production Ready
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.connection import get_connection

# ============================================================================
# CONFIGURATION
# ============================================================================

WINDOW_SIZE = 7
TOP_N = 7

# Enhanced category weights
CATEGORY_WEIGHTS = {
    'over_15': {
        'combined_attack': 0.20,
        'combined_defense_weak': 0.20,
        'combined_openness': 0.15,
        'both_score_1p': 0.15,
        'attack_momentum': 0.10,
        'archetype_boost': 0.10,
        'dryness': -0.10
    },
    'over_25': {
        'combined_attack': 0.25,
        'combined_defense_weak': 0.20,
        'combined_openness': 0.20,
        'pressure_total': 0.10,
        'attack_momentum': 0.10,
        'archetype_boost': 0.10,
        'dryness': -0.15
    },
    'over_35': {
        'combined_attack': 0.25,
        'combined_defense_weak': 0.25,
        'high_openness': 0.20,
        'extreme_rate': 0.10,
        'chaos_boost': 0.15,
        'attack_momentum': 0.05
    },
    'over_45': {
        'extreme_potential': 0.35,
        'combined_attack': 0.25,
        'combined_defense_weak': 0.25,
        'chaos_boost': 0.15
    },
    'under_15': {
        'dryness_index': 0.35,
        'both_strong_defense': 0.25,
        'low_attack': 0.20,
        'tight_game_boost': 0.15,
        'zero_zero_rate': 0.05
    },
    'under_25': {
        'dryness_index': 0.25,
        'combined_defense_strong': 0.25,
        'low_openness': 0.20,
        'tight_game_boost': 0.15,
        'low_attack': 0.15
    },
    'gg': {
        'both_attack_strong': 0.30,
        'both_defense_weak': 0.25,
        'balanced_pressure': 0.15,
        'attack_momentum_both': 0.15,
        'open_game_boost': 0.10,
        'dryness': -0.10
    },
    'home_win': {
        'home_attack_advantage': 0.30,
        'away_defense_weak': 0.20,
        'home_pressure_dominance': 0.20,
        'home_form': 0.15,
        'domination_boost': 0.15
    },
    'away_win': {
        'away_attack_advantage': 0.30,
        'home_defense_weak': 0.20,
        'away_pressure_dominance': 0.20,
        'away_form': 0.15,
        'domination_boost': 0.15
    },
    'draw': {
        'balanced_strength': 0.35,
        'low_pressure_diff': 0.25,
        'mid_range_goals': 0.20,
        'balanced_boost': 0.20
    },
    'over25_gg': {
        'combined_attack': 0.20,
        'both_attack_strong': 0.20,
        'both_defense_weak': 0.20,
        'high_openness': 0.20,
        'open_game_boost': 0.15,
        'attack_momentum_both': 0.05
    },
    'home_over25': {
        'home_attack_strong': 0.25,
        'away_defense_weak': 0.25,
        'combined_attack': 0.20,
        'home_dominance': 0.15,
        'home_form': 0.10,
        'domination_boost': 0.05
    },
    'away_over25': {
        'away_attack_strong': 0.25,
        'home_defense_weak': 0.25,
        'combined_attack': 0.20,
        'away_dominance': 0.15,
        'away_form': 0.10,
        'domination_boost': 0.05
    },
    'home_gg': {
        'home_attack_strong': 0.25,
        'away_attack_decent': 0.25,
        'both_defense_weak': 0.20,
        'home_pressure': 0.15,
        'home_form': 0.10,
        'open_game_boost': 0.05
    },
    'away_gg': {
        'away_attack_strong': 0.25,
        'home_attack_decent': 0.25,
        'both_defense_weak': 0.20,
        'away_pressure': 0.15,
        'away_form': 0.10,
        'open_game_boost': 0.05
    }
}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data():
    """Load all necessary data."""
    print("\n" + "="*80)
    print("📥 LOADING DATA")
    print("="*80 + "\n")
    
    with get_connection() as db:
        # Upcoming fixtures
        db.execute("""
            SELECT match_id, date, home_team_id, home_team_name,
                   away_team_id, away_team_name, tournament_name, tournament_id
            FROM fixtures
            WHERE status = 'notstarted'
            ORDER BY date
        """)
        fixtures = pd.DataFrame(
            db.fetchall(),
            columns=['match_id', 'date', 'home_id', 'home_team',
                    'away_id', 'away_team', 'tournament', 'tournament_id']
        )
        
        # Team match history with opponent info
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
        
        # H2H data
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
    
    print(f"✅ {len(fixtures)} upcoming fixtures")
    print(f"✅ {len(matches)} team matches")
    print(f"✅ {len(h2h)} H2H records\n")
    
    return fixtures, matches, h2h


# ============================================================================
# LEAGUE NORMALIZATION
# ============================================================================

def compute_league_context(matches):
    """Calculate league averages for normalization."""
    print("="*80)
    print("🌍 COMPUTING LEAGUE CONTEXT")
    print("="*80 + "\n")
    
    # Calculate per-league averages
    matches['tg'] = matches['gf'] + matches['ga']
    
    league_stats = matches.groupby('tournament').agg({
        'gf': 'mean',
        'ga': 'mean',
        'tg': 'mean'
    }).reset_index()
    
    league_stats.columns = ['tournament', 'league_avg_gf', 'league_avg_ga', 'league_avg_tg']
    
    print(f"✅ Computed stats for {len(league_stats)} leagues\n")
    print("Top 5 leagues by avg goals:")
    print(league_stats.nlargest(5, 'league_avg_tg')[['tournament', 'league_avg_tg']])
    print()
    
    return league_stats


# ============================================================================
# ENHANCED TEAM PROFILES
# ============================================================================

def compute_enhanced_profiles(matches, league_stats):
    """Compute team profiles with all enhancements."""
    print("="*80)
    print("📊 COMPUTING ENHANCED TEAM PROFILES")
    print("="*80 + "\n")
    
    profiles = []
    
    for team_id in matches['team_id'].unique():
        team_data = matches[matches['team_id'] == team_id].head(WINDOW_SIZE)
        
        if len(team_data) < 3:
            continue
        
        team_name = team_data.iloc[0]['team_name']
        tournament = team_data.iloc[0]['tournament']
        
        # Get league context
        league_ctx = league_stats[league_stats['tournament'] == tournament]
        if not league_ctx.empty:
            league_avg_tg = league_ctx.iloc[0]['league_avg_tg']
            league_avg_gf = league_ctx.iloc[0]['league_avg_gf']
            league_avg_ga = league_ctx.iloc[0]['league_avg_ga']
        else:
            league_avg_tg = 2.5
            league_avg_gf = 1.25
            league_avg_ga = 1.25
        
        # Venue splits
        home_data = team_data[team_data['venue'] == 'Home']
        away_data = team_data[team_data['venue'] == 'Away']
        
        # ===== BASIC ATTACK/DEFENSE =====
        gf_overall = team_data['gf'].mean()
        gf_home = home_data['gf'].mean() if len(home_data) > 0 else gf_overall
        gf_away = away_data['gf'].mean() if len(away_data) > 0 else gf_overall
        
        ga_overall = team_data['ga'].mean()
        ga_home = home_data['ga'].mean() if len(home_data) > 0 else ga_overall
        ga_away = away_data['ga'].mean() if len(away_data) > 0 else ga_overall
        
        # ===== OPPONENT QUALITY ADJUSTMENT =====
        # Get opponent defensive strength for each match
        opponent_ga_list = []
        for _, match in team_data.iterrows():
            opp_data = matches[matches['team_id'] == match['opp_id']].head(7)
            if len(opp_data) > 0:
                opp_ga = opp_data['ga'].mean()
                opponent_ga_list.append(opp_ga)
        
        if opponent_ga_list:
            avg_opp_ga = np.mean(opponent_ga_list)
            # Adjust attack based on opponent quality
            quality_adjusted_attack = gf_overall / max(avg_opp_ga, 0.5)
        else:
            quality_adjusted_attack = gf_overall
        
        # ===== MOMENTUM & TRENDS =====
        if len(team_data) >= 5:
            last_3 = team_data.head(3)
            
            # Attack trend
            recent_gf = last_3['gf'].mean()
            attack_momentum = (recent_gf - gf_overall) / max(gf_overall, 0.5)
            
            # Defense trend
            recent_ga = last_3['ga'].mean()
            defense_momentum = (ga_overall - recent_ga) / max(ga_overall, 0.5)
            
            # Openness trend
            team_data['tg'] = team_data['gf'] + team_data['ga']
            recent_tg = last_3['tg'].mean() if 'tg' not in last_3.columns else (last_3['gf'] + last_3['ga']).mean()
            overall_tg = team_data['tg'].mean()
            openness_momentum = recent_tg - overall_tg
        else:
            attack_momentum = 0
            defense_momentum = 0
            openness_momentum = 0
            recent_gf = gf_overall
            recent_ga = ga_overall
        
        # ===== CONSISTENCY / VARIANCE =====
        gf_std = team_data['gf'].std()
        consistency_attack = 1 / (1 + gf_std)
        
        team_data['tg'] = team_data['gf'] + team_data['ga']
        tg_std = team_data['tg'].std()
        chaos_index = tg_std / max(team_data['tg'].mean(), 1.0)
        
        # ===== MATCH CHARACTERISTICS =====
        tg_avg = team_data['tg'].mean()
        over15_rate = (team_data['tg'] >= 2).mean()
        over25_rate = (team_data['tg'] >= 3).mean()
        over35_rate = (team_data['tg'] >= 4).mean()
        
        under15_rate = (team_data['tg'] <= 1).mean()
        extreme_rate = (team_data['tg'] >= 4).mean()
        zero_zero_rate = ((team_data['gf'] == 0) & (team_data['ga'] == 0)).mean()
        
        score_1p_rate = (team_data['gf'] >= 1).mean()
        score_2p_rate = (team_data['gf'] >= 2).mean()
        concede_1p_rate = (team_data['ga'] >= 1).mean()
        clean_sheet_rate = (team_data['ga'] == 0).mean()
        
        # ===== LEAGUE-NORMALIZED METRICS =====
        attack_relative = gf_overall / league_avg_gf
        defense_relative = ga_overall / league_avg_ga
        openness_relative = tg_avg / league_avg_tg
        
        # ===== FORM =====
        form_combined = attack_momentum + defense_momentum
        
        profiles.append({
            'team_id': team_id,
            'team_name': team_name,
            'tournament': tournament,
            
            # Basic metrics
            'attack_overall': gf_overall,
            'attack_home': gf_home,
            'attack_away': gf_away,
            'defense_overall': ga_overall,
            'defense_home': ga_home,
            'defense_away': ga_away,
            
            # Quality-adjusted
            'attack_quality_adj': quality_adjusted_attack,
            
            # Momentum
            'attack_momentum': attack_momentum,
            'defense_momentum': defense_momentum,
            'openness_momentum': openness_momentum,
            'form_combined': form_combined,
            
            # Consistency
            'consistency_attack': consistency_attack,
            'chaos_index': chaos_index,
            
            # Rates
            'score_1p_rate': score_1p_rate,
            'score_2p_rate': score_2p_rate,
            'concede_1p_rate': concede_1p_rate,
            'clean_sheet_rate': clean_sheet_rate,
            
            # Match characteristics
            'tg_avg': tg_avg,
            'over15_rate': over15_rate,
            'over25_rate': over25_rate,
            'over35_rate': over35_rate,
            'under15_rate': under15_rate,
            'extreme_rate': extreme_rate,
            'zero_zero_rate': zero_zero_rate,
            
            # League-relative
            'attack_relative': attack_relative,
            'defense_relative': defense_relative,
            'openness_relative': openness_relative,
            
            # League context
            'league_avg_tg': league_avg_tg
        })
    
    df = pd.DataFrame(profiles)
    print(f"✅ {len(df)} enhanced team profiles created\n")
    
    return df


# ============================================================================
# H2H ANALYSIS
# ============================================================================

def get_h2h_modifier(home_id, away_id, h2h_data):
    """Calculate H2H modifier for a fixture."""
    # Ensure correct ordering
    team1 = min(home_id, away_id)
    team2 = max(home_id, away_id)
    
    # Get last 5 H2H matches
    h2h_matches = h2h_data[
        (h2h_data['team1_id'] == team1) & 
        (h2h_data['team2_id'] == team2)
    ].head(5)
    
    if len(h2h_matches) < 2:
        return 0.0  # Not enough H2H data
    
    h2h_tg_avg = h2h_matches['total_goals'].mean()
    return h2h_tg_avg


# ============================================================================
# FIXTURE INTERACTIONS WITH ALL ENHANCEMENTS
# ============================================================================

def compute_enhanced_fixtures(fixtures, profiles, h2h_data):
    """Create fixture metrics with all enhancements."""
    print("="*80)
    print("🔄 COMPUTING ENHANCED FIXTURE METRICS")
    print("="*80 + "\n")
    
    rows = []
    
    for _, fix in fixtures.iterrows():
        home = profiles[profiles['team_id'] == fix['home_id']]
        away = profiles[profiles['team_id'] == fix['away_id']]
        
        if home.empty or away.empty:
            continue
        
        h = home.iloc[0]
        a = away.iloc[0]
        
        # ===== CONTEXTUAL ATTACK/DEFENSE =====
        home_attack = h['attack_home']
        away_defense = a['defense_away']
        home_pressure = home_attack * max(2.5 - away_defense, 0.5)
        
        away_attack = a['attack_away']
        home_defense = h['defense_home']
        away_pressure = away_attack * max(2.5 - home_defense, 0.5)
        
        pressure_total = home_pressure + away_pressure
        pressure_diff = abs(home_pressure - away_pressure)
        pressure_ratio = home_pressure / max(away_pressure, 0.1)
        
        # ===== COMBINED METRICS =====
        combined_attack = (home_attack + away_attack) / 2
        combined_defense_weak = (away_defense + home_defense) / 2
        combined_defense_strong = 2.5 - combined_defense_weak
        combined_openness = (h['over25_rate'] + a['over25_rate']) / 2
        
        # Quality-adjusted
        combined_attack_quality = (h['attack_quality_adj'] + a['attack_quality_adj']) / 2
        
        # ===== MOMENTUM =====
        attack_momentum = (h['attack_momentum'] + a['attack_momentum']) / 2
        attack_momentum_both = min(h['attack_momentum'], a['attack_momentum'])
        
        # ===== MATCH ARCHETYPE =====
        if pressure_ratio > 2.0:
            archetype = "HOME_DOMINATION"
            domination_boost = 1.0
            balanced_boost = 0.0
        elif pressure_ratio < 0.5:
            archetype = "AWAY_DOMINATION"
            domination_boost = 1.0
            balanced_boost = 0.0
        elif 0.8 < pressure_ratio < 1.2:
            archetype = "BALANCED"
            domination_boost = 0.0
            balanced_boost = 1.0
        else:
            archetype = "SLIGHT_FAVORITE"
            domination_boost = 0.5
            balanced_boost = 0.5
        
        # Sub-classification
        if combined_defense_weak > 1.5:
            sub_type = "OPEN"
            open_game_boost = 1.0
            tight_game_boost = 0.0
            chaos_boost = (h['chaos_index'] + a['chaos_index']) / 2
        elif combined_defense_strong > 1.2:
            sub_type = "TIGHT"
            open_game_boost = 0.0
            tight_game_boost = 1.0
            chaos_boost = 0.0
        else:
            sub_type = "NEUTRAL"
            open_game_boost = 0.5
            tight_game_boost = 0.5
            chaos_boost = (h['chaos_index'] + a['chaos_index']) / 2
        
        archetype_full = f"{archetype}_{sub_type}"
        archetype_boost = open_game_boost if "OPEN" in archetype_full else tight_game_boost
        
        # ===== H2H MODIFIER =====
        h2h_tg = get_h2h_modifier(fix['home_id'], fix['away_id'], h2h_data)
        expected_tg = (h['tg_avg'] + a['tg_avg']) / 2
        
        if h2h_tg > 0:
            h2h_modifier = (h2h_tg - expected_tg) / max(expected_tg, 1.0)
            h2h_modifier = np.clip(h2h_modifier, -0.2, 0.2)  # Cap at ±20%
        else:
            h2h_modifier = 0.0
        
        # ===== OTHER DIMENSIONS =====
        dryness_index = (h['under15_rate'] + a['under15_rate']) / 2
        both_attack_strong = min(h['score_1p_rate'], a['score_1p_rate'])
        both_defense_weak = min(h['concede_1p_rate'], a['concede_1p_rate'])
        balanced_pressure = 1 - (pressure_diff / max(pressure_total, 0.01))
        
        high_openness = (h['over35_rate'] + a['over35_rate']) / 2
        extreme_potential = combined_attack * combined_defense_weak
        
        # Result-related
        home_attack_advantage = home_attack - away_attack
        away_attack_advantage = away_attack - home_attack
        home_pressure_dominance = home_pressure / max(pressure_total, 0.01)
        away_pressure_dominance = away_pressure / max(pressure_total, 0.01)
        balanced_strength = 1 - abs(pressure_diff) / max(pressure_total, 0.01)
        
        rows.append({
            'match_id': fix['match_id'],
            'date': fix['date'],
            'home_team': fix['home_team'],
            'away_team': fix['away_team'],
            'tournament': fix['tournament'],
            'archetype': archetype_full,
            
            # Core dimensions
            'combined_attack': combined_attack,
            'combined_attack_quality': combined_attack_quality,
            'combined_defense_weak': combined_defense_weak,
            'combined_defense_strong': combined_defense_strong,
            'combined_openness': combined_openness,
            'high_openness': high_openness,
            'pressure_total': pressure_total,
            'dryness': dryness_index,
            'dryness_index': dryness_index,
            'both_score_1p': both_attack_strong,
            'extreme_rate': (h['extreme_rate'] + a['extreme_rate']) / 2,
            'extreme_potential': extreme_potential,
            'zero_zero_rate': (h['zero_zero_rate'] + a['zero_zero_rate']) / 2,
            
            # Momentum
            'attack_momentum': attack_momentum,
            'attack_momentum_both': attack_momentum_both,
            
            # Archetype boosts
            'archetype_boost': archetype_boost,
            'domination_boost': domination_boost,
            'balanced_boost': balanced_boost,
            'open_game_boost': open_game_boost,
            'tight_game_boost': tight_game_boost,
            'chaos_boost': chaos_boost,
            
            # H2H
            'h2h_modifier': h2h_modifier,
            'h2h_tg': h2h_tg,
            
            # Under dimensions
            'both_strong_defense': combined_defense_strong,
            'low_attack': 2.5 - combined_attack,
            'low_openness': 1 - combined_openness,
            
            # GG dimensions
            'both_attack_strong': both_attack_strong,
            'both_defense_weak': both_defense_weak,
            'balanced_pressure': balanced_pressure,
            
            # Result dimensions
            'home_attack_advantage': home_attack_advantage,
            'away_attack_advantage': away_attack_advantage,
            'away_defense_weak': away_defense,
            'home_defense_weak': home_defense,
            'home_pressure_dominance': home_pressure_dominance,
            'away_pressure_dominance': away_pressure_dominance,
            'balanced_strength': balanced_strength,
            'low_pressure_diff': 1 - (pressure_diff / max(pressure_total, 0.01)),
            'mid_range_goals': 1 - abs(combined_attack - 1.5),
            'home_form': h['form_combined'],
            'away_form': a['form_combined'],
            
            # Combo dimensions
            'home_attack_strong': home_attack,
            'away_attack_strong': away_attack,
            'home_attack_decent': max(0, home_attack - 1.0),
            'away_attack_decent': max(0, away_attack - 1.0),
            'home_dominance': home_pressure_dominance,
            'away_dominance': away_pressure_dominance,
            'home_pressure': home_pressure,
            'away_pressure': away_pressure
        })
    
    df = pd.DataFrame(rows)
    print(f"✅ {len(df)} enhanced fixture metrics computed\n")
    
    # Show archetype distribution
    print("Match Archetype Distribution:")
    print(df['archetype'].value_counts())
    print()
    
    return df


# ============================================================================
# SCORING WITH H2H ADJUSTMENT
# ============================================================================

def score_categories(df):
    """Score all categories with H2H adjustment."""
    print("="*80)
    print("📊 SCORING ALL CATEGORIES (WITH H2H)")
    print("="*80 + "\n")
    
    for category, weights in CATEGORY_WEIGHTS.items():
        score = pd.Series(0.0, index=df.index)
        
        for dimension, weight in weights.items():
            if dimension in df.columns:
                col = df[dimension]
                if col.max() > col.min():
                    normalized = (col - col.min()) / (col.max() - col.min())
                else:
                    normalized = col
                
                score += weight * normalized
        
        # Normalize to 0-1
        if score.max() > score.min():
            score = (score - score.min()) / (score.max() - score.min())
        
        # Apply H2H modifier (5-10% adjustment)
        if 'over' in category or 'gg' in category:
            score = score * (1 + 0.1 * df['h2h_modifier'])
        
        # Clip to 0-1
        score = score.clip(0, 1)
        
        # Convert to percentage
        if score.max() > 0:
            percentage = 100 * score / score.max()
        else:
            percentage = score
        
        df[f'{category}_pct'] = percentage
        print(f"✅ {category}")
    
    print()
    return df


# ============================================================================
# OUTPUT
# ============================================================================

def display_rankings(df, categories, top_n=7):
    """Display top fixtures with archetype info."""
    print("\n" + "="*80)
    print("🏆 TOP FIXTURES PER CATEGORY")
    print("="*80)
    
    for category in categories:
        pct_col = f'{category}_pct'
        
        if pct_col not in df.columns:
            continue
        
        ranked = df.sort_values(pct_col, ascending=False).head(top_n)
        
        print(f"\n{'─'*80}")
        print(f"📊 {category.upper().replace('_', ' ')}")
        print(f"{'─'*80}\n")
        
        for i, (_, m) in enumerate(ranked.iterrows(), 1):
            h2h_str = f" [H2H: {m['h2h_tg']:.1f}]" if m['h2h_tg'] > 0 else ""
            print(f"{i}. [{m[pct_col]:.0f}%] {m['home_team']} vs {m['away_team']}")
            print(f"   {m['tournament']} | {m['date']} | {m['archetype']}{h2h_str}\n")


def export_results(df):
    """Export to CSV."""
    export_cols = ['match_id', 'date', 'home_team', 'away_team', 'tournament', 'archetype']
    pct_cols = [col for col in df.columns if col.endswith('_pct')]
    export_cols.extend(pct_cols)
    export_cols.extend(['h2h_tg', 'h2h_modifier'])
    
    df[export_cols].to_csv('data/enhanced_analysis.csv', index=False)
    print("\n✅ Enhanced analysis exported to data/enhanced_analysis.csv\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("⚽ ENHANCED MULTI-CATEGORY FIXTURE ANALYSIS")
    print("   Features: Momentum, Quality Adjustment, H2H, League Normalization")
    print("="*80)
    
    # Load
    fixtures, matches, h2h = load_data()
    
    # League context
    league_stats = compute_league_context(matches)
    
    # Enhanced profiles
    profiles = compute_enhanced_profiles(matches, league_stats)
    
    # Enhanced fixtures
    metrics = compute_enhanced_fixtures(fixtures, profiles, h2h)
    
    # Score with H2H
    results = score_categories(metrics)
    
    # Display
    categories = list(CATEGORY_WEIGHTS.keys())
    display_rankings(results, categories, TOP_N)
    
    # Export
    export_results(results)
    
    print("="*80)
    print("✅ ENHANCED ANALYSIS COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
