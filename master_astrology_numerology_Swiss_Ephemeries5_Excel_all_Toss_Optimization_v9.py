import pandas as pd
import sys
import os
import time
import re

# --- CONFIGURATION ---
EXCEL_FILE = 'match_analysis_data.xlsx'
COLOR_MAGENTA = '\033[95m'
COLOR_BLUE = '\033[94m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_GREEN = '\033[92m'
COLOR_BOLD = '\033[1m'
COLOR_END = '\033[0m'

# Define standard column names for internal use (Target names for resilient matching)
TARGET_TEAM_A = 'Team_A_Name'
TARGET_TEAM_B = 'Team_B_Name'
TARGET_CAPTAIN_A = 'Captain_A_Name'
TARGET_CAPTAIN_B = 'Captain_B_Name'
TARGET_DATE = 'Match_Date'
TARGET_REAL_TOSS = 'Real_Toss_Winner' # Using 'REA TOSS' based on previous successful columns
TARGET_REAL_MATCH = 'Real_Match_Winner' # New tracking column
PRED_COL = 'PREDICTED TOSS WINNER'
STATUS_COL = 'STATUS' 

# --- 0. UTILITY FUNCTIONS ---

def normalize_string(s):
    """Aggressively cleans a string for comparison by removing all non-alphanumeric characters and lowercasing."""
    if pd.isna(s):
        return ""
    # Remove spaces, underscores, and convert to uppercase
    return re.sub(r'[^A-Z0-9]', '', str(s).upper())

# --- 1. HISTORICAL ANALYSIS & PREDICTION CORE LOGIC ---

def map_toss_winner_to_ab(row, col_map):
    """
    Maps the winner's name in Rea_Toss to 'A' (Captain A) or 'B' (Captain B).
    """
    winner_col = col_map[normalize_string(TARGET_REAL_TOSS)]
    captain_a_col = col_map[normalize_string(TARGET_CAPTAIN_A)]
    captain_b_col = col_map[normalize_string(TARGET_CAPTAIN_B)]
    team_a_col = col_map[normalize_string(TARGET_TEAM_A)]
    team_b_col = col_map[normalize_string(TARGET_TEAM_B)]

    winner = str(row[winner_col]).strip().upper()
    captain_a = str(row[captain_a_col]).strip().upper()
    captain_b = str(row[captain_b_col]).strip().upper()
    
    if winner == '' or winner == 'NAN' or pd.isna(row[winner_col]):
        return None 
    
    if winner == captain_a: return 'A'
    if winner == captain_b: return 'B'
    
    # Fallback to Team Names
    team_a = str(row[team_a_col]).strip().upper()
    team_b = str(row[team_b_col]).strip().upper()
    if winner == team_a: return 'A'
    if winner == team_b: return 'B'
        
    # Default return if a result exists but cannot be mapped
    return 'A' 

def perform_h2h_analysis(match_data, history_df, col_map):
    """
    Analyzes Head-to-Head history for the current match's teams 
    to find a dominant toss winner. (Case-Based Logic)
    """
    team_a_col = col_map[normalize_string(TARGET_TEAM_A)]
    team_b_col = col_map[normalize_string(TARGET_TEAM_B)]
    rea_toss_col = col_map[normalize_string(TARGET_REAL_TOSS)]

    # Identify the teams in the match to predict
    team_a_name = str(match_data[team_a_col]).strip().upper()
    team_b_name = str(match_data[team_b_col]).strip().upper()
    
    print(f"{COLOR_BLUE}{COLOR_BOLD}   1. Performing H2H Analysis ({team_a_name} vs {team_b_name})...{COLOR_END}")

    # Step 1: Filter historical matches involving these two teams
    
    # Identify historical matches where Team A was Team A and Team B was Team B (or vice versa)
    matchup_filter = (
        (history_df[team_a_col].str.strip().str.upper() == team_a_name) & 
        (history_df[team_b_col].str.strip().str.upper() == team_b_name)
    ) | (
        (history_df[team_a_col].str.strip().str.upper() == team_b_name) & 
        (history_df[team_b_col].str.strip().str.upper() == team_a_name)
    )
    
    h2h_history = history_df[matchup_filter].copy()
    
    if h2h_history.empty:
        print(f"{COLOR_YELLOW}   No prior Head-to-Head history found for this matchup. Fallback required.{COLOR_END}")
        return None # Fallback to pattern analysis

    print(f"   Found {len(h2h_history)} previous matches between these two teams.")

    # Step 2: Determine toss winner relative to the predicted match's Team A/B
    
    # This function determines if the ACTUAL toss winner (from Rea_Toss) corresponds to 
    # the current match's Team A (A) or Team B (B).
    def get_h2h_winner_label(row):
        toss_winner = str(row[rea_toss_col]).strip().upper()
        
        # Check if winner is Captain/Team A from the *current historical row*
        captain_a_hist = str(row[col_map[normalize_string(TARGET_CAPTAIN_A)]]).strip().upper()
        team_a_hist = str(row[col_map[normalize_string(TARGET_TEAM_A)]]).strip().upper()
        
        # Check if winner is Captain/Team B from the *current historical row*
        captain_b_hist = str(row[col_map[normalize_string(TARGET_CAPTAIN_B)]]).strip().upper()
        team_b_hist = str(row[col_map[normalize_string(TARGET_TEAM_B)]]).strip().upper()

        # Determine which of the two teams (A or B in the current prediction) won the toss
        winner_name = ''
        if toss_winner == captain_a_hist or toss_winner == team_a_hist:
            winner_name = team_a_hist
        elif toss_winner == captain_b_hist or toss_winner == team_b_hist:
            winner_name = team_b_hist
        else:
             return None # Unclear winner

        # Now, map the historical winner's name to the prediction's A or B label
        if winner_name == team_a_name:
            return 'A'
        elif winner_name == team_b_name:
            return 'B'
        return None # Should not happen if data is clean

    h2h_history['WINNER_AB'] = h2h_history.apply(get_h2h_winner_label, axis=1)
    
    valid_h2h = h2h_history.dropna(subset=['WINNER_AB'])
    if valid_h2h.empty:
        print(f"{COLOR_YELLOW}   Historical data is present but all Rea_Toss values are missing for this matchup. Fallback required.{COLOR_END}")
        return None
        
    # Step 3: Calculate the H2H Win Rates
    total_tosses = len(valid_h2h)
    a_wins = len(valid_h2h[valid_h2h['WINNER_AB'] == 'A'])
    b_wins = len(valid_h2h[valid_h2h['WINNER_AB'] == 'B'])

    a_rate = a_wins / total_tosses
    b_rate = b_wins / total_tosses

    print(f"   {team_a_name} (A) H2H Toss Wins: {a_wins}/{total_tosses} ({a_rate:.1%})")
    print(f"   {team_b_name} (B) H2H Toss Wins: {b_wins}/{total_tosses} ({b_rate:.1%})")

    # Step 4: Make the H2H Prediction
    if a_rate > b_rate:
        prediction = 'A'
    elif b_rate > a_rate:
        prediction = 'B'
    else:
        # Tie-breaker (use the winner of the last H2H match, if it exists)
        last_winner = valid_h2h.iloc[-1]['WINNER_AB']
        prediction = last_winner if last_winner in ['A', 'B'] else 'A' # Default to A if last is also None

    print(f"\n{COLOR_GREEN}{COLOR_BOLD}   -> H2H Prediction: {prediction} (High Confidence Case Match){COLOR_END}")
    return prediction

def pattern_fallback_analysis(history_df, col_map):
    """
    Analyzes the full historical sequence for the most successful simple periodic 
    pattern (A/B/A/B or A/A/B/B). (Fallback Logic)
    """
    print(f"{COLOR_BLUE}{COLOR_BOLD}   2. Executing Pattern Fallback Analysis on all history...{COLOR_END}")
    
    # 1. Generate the actual historical sequence (A or B)
    history_df['ACTUAL_AB'] = history_df.apply(lambda row: map_toss_winner_to_ab(row, col_map), axis=1)
    
    # Filter out rows that didn't have a valid result (None)
    valid_results = [res for res in history_df['ACTUAL_AB'].tolist() if res in ['A', 'B']]
    
    if len(valid_results) < 8:
        print(f"{COLOR_YELLOW}   Insufficient history ({len(valid_results)} lines) for pattern analysis. Defaulting to A.{COLOR_END}")
        return 'A', 0 # Default safe return

    # --- 2. Define Patterns to Test (Length 8) ---
    pattern_ab = ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'] 
    pattern_aabb = ['A', 'A', 'B', 'B', 'A', 'A', 'B', 'B'] 
    
    patterns = {
        'A/B/A/B': pattern_ab,
        'A/A/B/B': pattern_aabb
    }
    
    # --- 3. Calculate Success Rates ---
    success_rates = {}
    
    # We only analyze the first 8 matches for pattern success
    for name, pattern in patterns.items():
        matches = 0
        total_predictions = 0
        for i in range(8): 
            total_predictions += 1
            if valid_results[i] == pattern[i]:
                matches += 1
        
        rate = matches / total_predictions if total_predictions > 0 else 0
        success_rates[name] = rate
        print(f"   Pattern '{name}' Success Rate (first 8): {matches}/{total_predictions} ({rate:.1%})")

    # --- 4. Select the Best Pattern ---
    best_pattern_name = max(success_rates, key=success_rates.get)
    
    # --- 5. Generate Prediction for the Next Match ---
    # The next prediction index is the length of valid history (N) % 8
    next_index = len(valid_results) % 8
    
    if best_pattern_name == 'A/B/A/B':
        next_prediction = pattern_ab[next_index]
    else: # A/A/B/B
        next_prediction = pattern_aabb[next_index]
        
    print(f"\n{COLOR_GREEN}{COLOR_BOLD}   -> Fallback Pattern Prediction: {next_prediction}{COLOR_END}")
    return next_prediction

def calculate_toss_prediction(match_data, historical_df, col_map):
    """
    Determines the prediction strategy: H2H (case-based) first, then fallback to pattern analysis.
    """
    
    # 1. Attempt H2H Analysis (Case-Based)
    h2h_prediction = perform_h2h_analysis(match_data, historical_df, col_map)
    
    if h2h_prediction in ['A', 'B']:
        return h2h_prediction
    
    # 2. If H2H fails (no history or missing data), fall back to pattern analysis
    return pattern_fallback_analysis(historical_df, col_map)


# --- 2. DATA HANDLING FUNCTIONS ---

def load_data(file_path):
    """Loads match data, dynamically maps headers, and ensures required columns exist."""
    try:
        df = pd.read_excel(file_path)
        print(f"{COLOR_BLUE}Successfully loaded {len(df)} matches from {COLOR_BOLD}{file_path}{COLOR_END}")
        
        # --- Create Robust Column Mapping ---
        normalized_excel_headers = {normalize_string(col): col for col in df.columns}
        
        required_targets = [
            TARGET_TEAM_A, TARGET_TEAM_B, TARGET_CAPTAIN_A, TARGET_CAPTAIN_B, 
            TARGET_DATE, TARGET_REAL_TOSS, TARGET_REAL_MATCH # Including the new match winner column
        ]
        
        column_map = {}
        missing_targets = []
        
        for target in required_targets:
            normalized_target = normalize_string(target)
            if normalized_target in normalized_excel_headers:
                column_map[normalized_target] = normalized_excel_headers[normalized_target]
            else:
                missing_targets.append(target)

        if missing_targets:
            print(f"\n{COLOR_RED}Fatal Error: Missing expected data columns after resilient check: {missing_targets}{COLOR_END}")
            print(f"{COLOR_RED}Please ensure the following column headers exist in your Excel file (case, space, and underscore insensitive):{COLOR_END}")
            for name in required_targets:
                print(f"{COLOR_RED}  - {name}{COLOR_END}")
            sys.exit(1)

        print(f"{COLOR_GREEN}Successfully mapped Excel columns using resilient naming logic.{COLOR_END}")

        # --- Initialization: Add prediction/status columns if missing ---
        rea_toss_col_name = column_map[normalize_string(TARGET_REAL_TOSS)]
        
        if PRED_COL not in df.columns:
            df[PRED_COL] = ''
        
        if STATUS_COL not in df.columns:
            # Set default status based on whether the real toss winner is present
            df[STATUS_COL] = df[rea_toss_col_name].apply(
                lambda x: 'ARCHIVED' if pd.notna(x) and str(x).strip() != '' else 'FUTURE'
            )
        
        # Ensure the new Real Match Winner column exists, and fill empty strings for future/predicted matches
        target_real_match_col_name = column_map[normalize_string(TARGET_REAL_MATCH)]
        if target_real_match_col_name not in df.columns:
            df[target_real_match_col_name] = ''
        
        # Ensure matches marked 'FUTURE' or 'PREDICTED' have empty values in the real result columns
        future_or_predicted = df[STATUS_COL].isin(['FUTURE', 'PREDICTED'])
        df.loc[future_or_predicted, rea_toss_col_name] = ''
        df.loc[future_or_predicted, target_real_match_col_name] = ''

        return df, column_map
    except FileNotFoundError:
        print(f"{COLOR_RED}Error: Input file {file_path} not found. Please ensure the file exists and is named '{EXCEL_FILE}'.{COLOR_END}")
        sys.exit(1)
    except Exception as e:
        print(f"{COLOR_RED}Error loading Excel file: {e}{COLOR_END}")
        if 'are in use by another program' in str(e):
             print(f"{COLOR_YELLOW}Hint: Your Excel file might be open. Please close '{EXCEL_FILE}' and try again.{COLOR_END}")
        sys.exit(1)


def save_updated_data(df, file_path):
    """Saves the DataFrame back to the Excel file, retrying if locked."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            df.to_excel(file_path, index=False)
            print(f"\n{COLOR_GREEN}{COLOR_BOLD}✅ Successfully wrote results (including the prediction) back to {file_path}{COLOR_END}")
            return
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"{COLOR_YELLOW}Warning: File locked. Retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries}){COLOR_END}")
                time.sleep(2)
            else:
                print(f"{COLOR_RED}Error: Could not save file '{file_path}'. It is likely open or locked by another program (like Excel). Please close it and run the script again.{COLOR_END}")
                return
        except Exception as e:
            print(f"{COLOR_RED}Error writing results to Excel: {e}{COLOR_END}")
            return


# --- 3. MAIN PROCESSING LOGIC ---

def process_matches(df, col_map):
    """Processes the next match based on the historical data."""
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}=== CASE-BASED TOSS PREDICTION STARTING ==={COLOR_END}\n")
    
    # Get the actual column names from the map for easier indexing
    team_a_col = col_map[normalize_string(TARGET_TEAM_A)]
    team_b_col = col_map[normalize_string(TARGET_TEAM_B)]
    captain_a_col = col_map[normalize_string(TARGET_CAPTAIN_A)]
    captain_b_col = col_map[normalize_string(TARGET_CAPTAIN_B)]
    
    processed_matches_count = 0

    # 1. Find the first row that needs prediction (STATUS == 'FUTURE' or 'PREDICTED')
    # We predict the first match that is not 'ARCHIVED'
    predict_index = df[df[STATUS_COL] != 'ARCHIVED'].index
    
    if predict_index.empty:
        print(f"{COLOR_YELLOW}No new match found with status 'FUTURE' or 'PREDICTED'. All rows appear to have been archived.{COLOR_END}")
        return

    predict_index = predict_index[0]
    match_to_predict = df.loc[predict_index]
    
    # The historical data is everything UP TO the match we are predicting
    history_df = df.loc[df[STATUS_COL] == 'ARCHIVED'].copy()
    
    # If there are no ARCHIVED rows, we can't predict anything with history
    if history_df.empty:
         print(f"{COLOR_RED}ERROR: No historical 'ARCHIVED' data found. Cannot execute prediction logic. Skipping.{COLOR_END}")
         return

    # Run the prediction logic
    toss_prediction = calculate_toss_prediction(match_to_predict, history_df, col_map)
    
    # Store prediction back into the DataFrame and update status
    df.loc[predict_index, PRED_COL] = toss_prediction
    df.loc[predict_index, STATUS_COL] = 'PREDICTED' 
    processed_matches_count += 1
    
    print("-" * 60)
    print(f"{COLOR_MAGENTA}{COLOR_BOLD}3. Final Prediction for Match {predict_index + 1}:{COLOR_END} {match_to_predict[team_a_col]} vs {match_to_predict[team_b_col]}")
    print(f"  {COLOR_BOLD}Toss Winner (A/B):{COLOR_END} {toss_prediction}")
    
    # Determine which team/captain 'A' or 'B' refers to for the final printout
    predicted_captain = match_to_predict[captain_a_col] if toss_prediction == 'A' else match_to_predict[captain_b_col]
    
    print(f"  {COLOR_BOLD}Predicted Toss Winner (Captain/Team):{COLOR_END} {predicted_captain}")
    print("-" * 60)

    
    if processed_matches_count > 0:
        # Save the updated DataFrame back to the Excel file
        save_updated_data(df, EXCEL_FILE)
    else:
        print(f"\n{COLOR_YELLOW}❌ No new predictions processed.{COLOR_END}")


if __name__ == "__main__":
    # 1. Load the data from Excel and get the column mapping
    data_df, col_map = load_data(EXCEL_FILE)
    
    # 2. Process the future match based on historical data
    process_matches(data_df, col_map)