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
    
    # If before season, return Week 1
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
    # import_schedules returns the full season list including scores
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
        # Handle spreads/totals (convert None to 0)
        spread = game.get('spread_line')
        total = game.get('total_line')
        
        # 🔥 NEW: Determine Status & Scores
        h_score = game.get('home_score')
        v_score = game.get('away_score')
        
        # Check if game is finished (score exists and is not NaN)
        is_finished = pd.notnull(h_score) and pd.notnull(v_score)
        
        # Construct the Game Object
        game_obj = {
            "id": f"wk{target_week}-{game['away_team'].lower()}-{game['home_team'].lower()}",
            "home": game['home_team'],
            "visitor": game['away_team'],
            "spread": float(spread) if pd.notnull(spread) else 0,
            "total": float(total) if pd.notnull(total) else 0,
            "home_ml": 0, # Manual or external API for ML if needed
            "visitor_ml": 0,
            
            # Format time as ISO string (e.g., "2025-12-21T13:00:00Z")
            "commence_time": f"{game['gameday']}T{game['gametime']}Z", 
            "conference": "NFL",
            
            # 🔥 Status Logic
            "status": "FINAL" if is_finished else "SCHEDULED",
            "home_score": int(h_score) if is_finished else 0,
            "visitor_score": int(v_score) if is_finished else 0
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
    
    # Read existing status to preserve other fields if needed
    if os.path.exists(status_path):
        with open(status_path, "r") as f:
            status_data = json.load(f)
    else:
        status_data = {}

    status_data["currentWeek"] = int(target_week)
    status_data["season"] = SEASON
    status_data["message"] = f"Week {target_week} Auto-Synced"
    status_data["lastUpdated"] = datetime.datetime.now().isoformat()
    
    with open(status_path, "w") as f:
        json.dump(status_data, f, indent=2)
    print("✅ Updated status.json")

if __name__ == "__main__":
    fetch_and_save_schedule()
