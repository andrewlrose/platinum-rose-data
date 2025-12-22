import pandas as pd
import json
import os

# 1. Find the CSV file (we know it's in the 'global' folder from your logs)
csv_path = 'global/team_ratings.csv'

if os.path.exists(csv_path):
    # 2. Read the Spreadsheet
    df = pd.read_csv(csv_path)
    
    # 3. Convert it to JSON (List of Objects)
    # This turns the spreadsheet rows into code blocks your website can read
    json_data = df.to_dict(orient='records')
    
    # 4. Save the new file in the MAIN folder
    with open('weekly_stats.json', 'w') as f:
        json.dump(json_data, f)
        
    print("✅ SUCCESS: Converted CSV to weekly_stats.json!")
else:
    print(f"❌ ERROR: Could not find {csv_path}. Did you run fetch_stats.py first?")