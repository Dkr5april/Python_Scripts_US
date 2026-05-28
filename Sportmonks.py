import requests
import json
import csv
from datetime import datetime, timedelta

# --- 1. CONFIGURATION: REPLACE YOUR TOKEN HERE ---
# NOTE: The script is set up to pull fixtures for TODAY and TOMORROW.
API_KEY = "VxVgbmAz28U9uXbJPVObOdq7HRnx50MYX9tWSPOPIpYQ9InBthrrDk60Jnwq" 

# Sportmonks Base URL for Cricket v2.0
BASE_URL = "https://cricket.sportmonks.com/api/v2.0/fixtures"

# Calculate today and tomorrow's date for the API filter format (YYYY-MM-DD)
TODAY_DATE = datetime.now().strftime("%Y-%m-%d")
TOMORROW_DATE = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Define the parameters as a dictionary (This fixes the 400 Bad Request error)
PAYLOAD = {
    'api_token': API_KEY,
    'filter[starts_between]': f"{TODAY_DATE},{TOMORROW_DATE}",
    # Include squad for captain names. 'squad' is nested under team data.
    'include': 'localteam.squad,visitorteam.squad' 
}

# The endpoint is just the base URL, as params carries the rest
SCHEDULE_URL = BASE_URL 

def fetch_schedule_data(url, params):
    """Fetches upcoming match data from the API and provides debug output."""
    
    # Simple check to ensure the user has replaced the placeholder
    if "PASTE_YOUR_SPORTMONKS_TOKEN_HERE" in params.get('api_token'):
        print("\n❌ CRITICAL ERROR: API Key is not set! Please replace the placeholder.")
        return None
        
    print(f"\n[DEBUG] Attempting to connect to Base URL: {url}")
    print(f"[DEBUG] With Parameters: {params}") 
    
    try:
        # Pass the dictionary to 'params' for correct URL encoding
        response = requests.get(url, params=params, timeout=10) 
        
        # --- ESSENTIAL DEBUG OUTPUT ---
        print(f"[DEBUG] API Request Status Code: {response.status_code}")
        # -----------------------------
        
        response.raise_for_status() # Check for 4xx or 5xx errors
        print("[DEBUG] Connection successful. Data received.")
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        print(f"\n🚨 API ERROR: HTTP error occurred (Status {response.status_code}). Check your API token or rate limit.")
        print(f"   Details: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n🚨 NETWORK ERROR: Could not connect to the API. Check your internet connection or URL.")
        print(f"   Details: {e}")
        return None

def get_captain_name(squad_data):
    """Safely finds the captain's name from the squad data."""
    if squad_data and 'data' in squad_data:
        for player in squad_data['data']:
            # Sportmonks uses the 'captain' property set to 1 for the captain
            if player.get('captain') == 1: 
                return player.get('fullname') or player.get('name') or 'Captain Not Listed'
    return "TBC (Squad Data Unavailable)"

def process_schedule(data):
    """Parses the JSON response and formats the schedule."""
    if not data or 'data' not in data:
        print("\n❌ PROCESSING ERROR: No match data found or API response structure is unexpected.")
        return []

    matches_list = []
    
    for match in data['data']:
        try:
            # 1. Extract basic details
            match_date_str = match.get('starting_at') 
            match_dt = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')) 
            match_date = match_dt.strftime("%b %d, %Y")
            match_time = match_dt.strftime("%I:%M %p UTC")
            
            # 2. Extract Team Names
            local_team_data = match.get('localteam', {}).get('data', {})
            visitor_team_data = match.get('visitorteam', {}).get('data', {})
            
            local_team = local_team_data.get('name', 'N/A')
            visitor_team = visitor_team_data.get('name', 'N/A')
            
            # 3. Extract Captains using the helper function on the 'squad' data
            local_squad = local_team_data.get('squad')
            visitor_squad = visitor_team_data.get('squad')
            
            local_captain = get_captain_name(local_squad)
            visitor_captain = get_captain_name(visitor_squad)

            # 4. Append to list
            matches_list.append({
                "Date": match_date,
                "Time": match_time,
                "Series": match.get('name', 'N/A'), 
                "Team 1": local_team,
                "Team 1 Captain": local_captain,
                "Team 2": visitor_team,
                "Team 2 Captain": visitor_captain
            })
        except Exception as e:
            print(f"[DEBUG] Skipping match due to processing error: {e}") 
            continue
            
    return matches_list

def export_to_csv(matches):
    """Exports the processed match list to a CSV file."""
    if not matches:
        print("\n⚠️ EXPORT WARNING: No matches to export.")
        return
        
    filename = f"cricket_schedule_{datetime.now().strftime('%Y%m%d')}.csv"
    
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)
            
        print(f"\n✅ SUCCESS: Schedule exported successfully to: **{filename}**")
        print(f"Total matches found and exported: {len(matches)}")
        
    except Exception as e:
        print(f"\n🚨 EXPORT ERROR: Could not write CSV file: {e}")


# --- 2. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    
    print("\n--- Starting Cricket Schedule Script ---")
    
    # 1. Fetch data - PASS THE PAYLOAD DICT HERE
    raw_data = fetch_schedule_data(SCHEDULE_URL, PAYLOAD)
    
    # 2. Process data
    schedule = process_schedule(raw_data)
    
    # 3. Export data
    export_to_csv(schedule)
    
    print("\n--- Script Finished ---")