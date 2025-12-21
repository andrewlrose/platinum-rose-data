import nfl_data_py as nfl
import pandas as pd
import os
from datetime import datetime

# CONFIG
# ⚠️ Update to 2025 when the season actually starts.
# For testing right now, we use 2024 so you see real data immediately.
CURRENT_SEASON = 2024 

def fetch_and_process_stats():
    print(f"🏈 Fetching Play-by-Play Data for {CURRENT_SEASON}...")
    
    # 1. Download PBP Data (This takes ~15 seconds)
    pbp = nfl.import_pbp_data([CURRENT_SEASON])
    
    # 2. Filter for regular season & relevant plays
    # We only want plays where EPA was calculated (no kneel downs, etc.)
    pbp = pbp[
        (pbp['season_type'] == 'REG') & 
        (pbp['play_type'].isin(['pass', 'run'])) & 
        (pbp['epa'].notna())
    ]
    
    print(f"📊 Analyzing {len(pbp)} plays...")

    # 3. Aggregate OFFENSE Stats
    # Group by Possession Team to see how good they are at scoring
    off_stats = pbp.groupby('posteam').agg({
        'epa': 'mean',              # Total Efficiency
        'success': 'mean',          # Consistency (Success Rate)
        'pass': 'mean'              # Pass Rate
    }).rename(columns={'epa': 'off_epa', 'success': 'off_success', 'pass': 'pass_rate'})

    # 4. Split Offense into Pass vs Rush EPA
    # (Crucial for your "Matchup" logic - e.g. Good Pass Off vs Bad Pass Def)
    pass_epa = pbp[pbp['play_type'] == 'pass'].groupby('posteam')['epa'].mean().rename('off_pass_epa')
    rush_epa = pbp[pbp['play_type'] == 'run'].groupby('posteam')['epa'].mean().rename('off_rush_epa')

    # 5. Aggregate DEFENSE Stats
    # Group by Defensive Team to see how good they are at stopping
    def_stats = pbp.groupby('defteam')['epa'].mean().rename('def_epa')
    def_pass_epa = pbp[pbp['play_type'] == 'pass'].groupby('defteam')['epa'].mean().rename('def_pass_epa')
    def_rush_epa = pbp[pbp['play_type'] == 'run'].groupby('defteam')['epa'].mean().rename('def_rush_epa')

    # 6. Merge Everything into One "Master Ratings" Table
    team_stats = pd.concat([off_stats, pass_epa, rush_epa, def_stats, def_pass_epa, def_rush_epa], axis=1)
    
    # Clean up (Round to 3 decimals)
    team_stats = team_stats.round(3)
    team_stats.index.name = 'team'
    team_stats = team_stats.reset_index()

    # 7. Save to CSV
    output_dir = "global"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "team_ratings.csv")
    
    team_stats.to_csv(output_path, index=False)
    print(f"✅ Saved Team Ratings to {output_path}")
    print(team_stats.head())

if __name__ == "__main__":
    fetch_and_process_stats()
