import nfl_data_py as nfl
import pandas as pd
import os
import sys

# --- CONFIGURATION ---
TARGET_SEASON = 2025
REPO_ROOT = "."

def fetch_and_process_stats():
    print(f"🚀 Bot B (The Scout): Fetching LIVE Data for Season {TARGET_SEASON}...")
    
    # 1. Fetch Real-Time Data (No Fallbacks)
    # This pulls directly from the nflverse GitHub repository
    pbp = nfl.import_pbp_data([TARGET_SEASON])
    
    print(f"📥 Downloaded {len(pbp)} rows of data.")

    # 2. Filter for Regular Season & Valid Plays
    # We remove penalties, timeouts, and plays with no EPA
    valid_plays = pbp[
        (pbp['season_type'] == 'REG') & 
        (pbp['play_type'].isin(['pass', 'run'])) & 
        (pbp['epa'].notna())
    ]
    
    if valid_plays.empty:
        print("❌ CRITICAL ERROR: No valid plays found. Check internet connection or library version.")
        sys.exit(1)

    print(f"📊 Analyzing {len(valid_plays)} valid offensive plays...")

    # 3. Aggregate OFFENSE Stats
    # Group by Possession Team
    off_stats = valid_plays.groupby('posteam').agg({
        'epa': 'mean',
        'success': 'mean',
        'pass': 'mean'
    }).rename(columns={'epa': 'off_epa', 'success': 'off_success', 'pass': 'pass_rate'})

    # 4. Split Offense (Pass vs Rush)
    pass_epa = valid_plays[valid_plays['play_type'] == 'pass'].groupby('posteam')['epa'].mean().rename('off_pass_epa')
    rush_epa = valid_plays[valid_plays['play_type'] == 'run'].groupby('posteam')['epa'].mean().rename('off_rush_epa')

    # 5. Aggregate DEFENSE Stats
    # Group by Defensive Team
    def_stats = valid_plays.groupby('defteam')['epa'].mean().rename('def_epa')
    def_pass_epa = valid_plays[valid_plays['play_type'] == 'pass'].groupby('defteam')['epa'].mean().rename('def_pass_epa')
    def_rush_epa = valid_plays[valid_plays['play_type'] == 'run'].groupby('defteam')['epa'].mean().rename('def_rush_epa')

    # 6. Merge Everything
    team_stats = pd.concat([off_stats, pass_epa, rush_epa, def_stats, def_pass_epa, def_rush_epa], axis=1)
    
    # 7. Formatting & Cleanup
    team_stats = team_stats.round(3)
    team_stats.index.name = 'team'
    team_stats = team_stats.reset_index()

    # 8. Save to Global Folder
    output_dir = os.path.join(REPO_ROOT, "global")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "team_ratings.csv")
    team_stats.to_csv(output_path, index=False)
    
    print(f"✅ SUCCESS: Saved Live 2025 Ratings to {output_path}")
    print("Sample Data:")
    print(team_stats.sort_values(by='off_epa', ascending=False).head(5))

if __name__ == "__main__":
    fetch_and_process_stats()
