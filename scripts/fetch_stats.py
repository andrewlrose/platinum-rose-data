import nfl_data_py as nfl
import pandas as pd
import os
import sys

# --- CONFIGURATION ---
TARGET_SEASON = 2025  # 🔥 UPDATED TO 2025
REPO_ROOT = "."

def fetch_and_process_stats():
    print(f"🔮 Bot B (The Scout): Initializing for Season {TARGET_SEASON}...")
    
    try:
        # 1. Attempt to fetch Real-Time Data
        # (This will return an empty DataFrame until Sept 2025)
        pbp = nfl.import_pbp_data([TARGET_SEASON])
    except Exception as e:
        print(f"⚠️ API Warning: {e}")
        pbp = pd.DataFrame()

    # 2. Check if we have enough data to calculate stats
    # We need regular season plays with EPA values
    valid_plays = pd.DataFrame()
    if not pbp.empty:
        valid_plays = pbp[
            (pbp['season_type'] == 'REG') & 
            (pbp['play_type'].isin(['pass', 'run'])) & 
            (pbp['epa'].notna())
        ]

    # --- BRANCH LOGIC ---
    if valid_plays.empty:
        print(f"⚠️ No actual plays found for {TARGET_SEASON} yet (Pre-Season or Wk 1).")
        print("🔄 Switching to 'Projections Mode' (Loading base_ratings_2025.csv)...")
        
        # Fallback: Load manual projections if they exist
        base_path = os.path.join(REPO_ROOT, "global", "base_ratings_2025.csv")
        
        if os.path.exists(base_path):
            team_stats = pd.read_csv(base_path)
            print(f"✅ Loaded {len(team_stats)} Projected Team Ratings.")
        else:
            # Create a "Neutral" baseline if no file exists (prevents App Crash)
            print("⚠️ No projections found. Generating Neutral Baseline (0.0 EPA).")
            teams = nfl.import_team_desc()['team_abbr'].unique()
            team_stats = pd.DataFrame({
                'team': teams,
                'off_epa': 0.0, 'off_success': 0.45, 'pass_rate': 0.55,
                'off_pass_epa': 0.0, 'off_rush_epa': 0.0,
                'def_epa': 0.0, 'def_pass_epa': 0.0, 'def_rush_epa': 0.0
            })
            
    else:
        print(f"📊 Analyzing {len(valid_plays)} Real {TARGET_SEASON} Plays...")
        
        # 3. Aggregate OFFENSE (Real Data)
        off_stats = valid_plays.groupby('posteam').agg({
            'epa': 'mean',
            'success': 'mean',
            'pass': 'mean'
        }).rename(columns={'epa': 'off_epa', 'success': 'off_success', 'pass': 'pass_rate'})

        # 4. Split Offense (Real Data)
        pass_epa = valid_plays[valid_plays['play_type'] == 'pass'].groupby('posteam')['epa'].mean().rename('off_pass_epa')
        rush_epa = valid_plays[valid_plays['play_type'] == 'run'].groupby('posteam')['epa'].mean().rename('off_rush_epa')

        # 5. Aggregate DEFENSE (Real Data)
        def_stats = valid_plays.groupby('defteam')['epa'].mean().rename('def_epa')
        def_pass_epa = valid_plays[valid_plays['play_type'] == 'pass'].groupby('defteam')['epa'].mean().rename('def_pass_epa')
        def_rush_epa = valid_plays[valid_plays['play_type'] == 'run'].groupby('defteam')['epa'].mean().rename('def_rush_epa')

        # 6. Merge
        team_stats = pd.concat([off_stats, pass_epa, rush_epa, def_stats, def_pass_epa, def_rush_epa], axis=1)
        team_stats = team_stats.round(3)
        team_stats.index.name = 'team'
        team_stats = team_stats.reset_index()

    # 7. Save to the "Live" File
    # The App ALWAYS looks for 'team_ratings.csv'. We overwrite it with either Projections OR Real Data.
    output_dir = os.path.join(REPO_ROOT, "global")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "team_ratings.csv")
    team_stats.to_csv(output_path, index=False)
    
    print(f"✅ Saved Master Ratings to {output_path}")

if __name__ == "__main__":
    fetch_and_process_stats()
