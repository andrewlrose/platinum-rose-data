import nfl_data_py as nfl
import pandas as pd
import json
import os
import datetime
from dateutil import parser

# --- CONFIGURATION ---
SEASON = 2025
REPO_ROOT = "."  # Root of your git repo

# Define Season Start Date (approximate for 2025 logic)
SEASON_START = datetime.datetime(2025, 9, 4)

def get_current_nfl_week():
    """Calculates the NFL week number based on today's date."""
    today = datetime.datetime.now()
    if today < SEASON_START:
        return 1
    
    # Calculate days since start
    delta = today - SEASON_START
    week_num = (delta.days // 7) + 1
    
    # Cap at week 18 for regular season
    return max(1, min(18, week_num))

def fetch_and_save_schedule():
    print(f"🏈 Fetching schedule for {SEASON}...")
    
    # 1. Fetch Data
    df = nfl.import_schedules([SEASON])
    
    # 2. Determine Week
    target_week = get_current_nfl_week()
    print(f"📅 Calculated Current Week: {target_week}")
    
    # 3. Filter for this week
    weekly_games = df[df['week'] == target_week].copy()
    
    if weekly_games.empty:
        print("❌ No games found for this week. Is the season over?")
        return

    # 4. Transform to Platinum Rose Format
    formatted_games = []
    
    for _, game in weekly_games.iterrows():
        # Handle spreads (convert None to 0 or null)
        spread = game.get('spread_line', 0)
        total = game.get('total_line', 0)
        
        # Convert Moneyline odds if available (nflverse usually has decimal/probability, 
        # so we might need to approximate or leave blank if standard US odds aren't in this specific feed.
        # For now, we will default to 0 if missing, or you can use a betting-specific library).
        
        game_obj = {
            "id": f"wk{target_week}-{game['away_team'].lower()}-{game['home_team'].lower()}",
            "home": game['home_team'],
            "visitor": game['away_team'],
            "spread": float(spread) if pd.notnull(spread) else 0,
            "total": float(total) if pd.notnull(total) else 0,
            "home_ml": 0, # Difficult to get free live MLs consistently, set to manual or 0
            "visitor_ml": 0,
            "commence_time": game['gameday'] + "T" + str(game['gametime']) + "Z", # Formatting ISO
            "conference": "NFL" # Generic or calculate from team list
        }
        formatted_games.append(game_obj)

    # 5. Save games.json
    folder_path = os.path.join(REPO_ROOT, "weeks", f"week{target_week}")
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, "games.json")
    with open(file_path, "w") as f:
        json.dump(formatted_games, f, indent=2)
    
    print(f"✅ Saved {len(formatted_games)} games to {file_path}")

    # 6. Update status.json
    status_path = os.path.join(REPO_ROOT, "status.json")
    status_data = {
        "currentWeek": int(target_week),
        "season": SEASON,
        "message": f"Week {target_week} Auto-Synced",
        "lastUpdated": datetime.datetime.now().isoformat()
    }
    with open(status_path, "w") as f:
        json.dump(status_data, f, indent=2)
    print("✅ Updated status.json")

if __name__ == "__main__":
    fetch_and_save_schedule()
