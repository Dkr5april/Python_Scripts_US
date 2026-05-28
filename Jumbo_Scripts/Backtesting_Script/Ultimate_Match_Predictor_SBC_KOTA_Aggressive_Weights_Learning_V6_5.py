#!/usr/bin/env python3
"""
Ultimate Match Predictor — V6 UPGRADE (FINAL): Aggressive Learning, SBC + KOTA + Multi-Layer Ensemble

Input expected columns (recommended):
Timestamp, Captain_A_Name, Captain_A_DOB, Captain_B_Name, Captain_B_DOB,
Match_Date, Match_Time, Match_Place, Match_Format, TZ_Offset_HOURS,
Real_Toss, Real_Match, Team_A_Name, Team_B_Name, TeamA_Color, TeamB_Color, Stadium_Direction

Outputs:
 - match_analysis_data_output.xlsx with sheets:
   - Input_Data (Input copy)
   - Backtest_Results
   - Backtest_Summary
 - method_stats.json updated with per-method weights & stats
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, date
from dateutil import parser
from typing import Dict, Any, Union 
import time 

# ---------------------------
# Config / Files
# ---------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"
TIMESTAMP_COL = "Timestamp"

# Learning hyperparameters (VERY AGGRESSIVE - Option A) (Point 1)
WEIGHT_PROMOTE_STEP = 0.25 
WEIGHT_DEMOTE_STEP = 0.30 
WEIGHT_MIN = 0.05
WEIGHT_MAX = 8.0    
RETIRE_AFTER_WEIGHT_BELOW = 0.15 
RETIRE_FAIL_RATIO = 2.0  
MIN_TOTAL_EVAL = 3      
UNPREDICTABLE_MARGIN = 0.3 
REVIVAL_WINDOW = 20      

# New Constants (Point 4, 9)
STADIUM_DIRECTION_MAP = {
    "NORTH": 1, "EAST": 1, 
    "SOUTH": 2, "WEST": 2, 
    "NORTHEAST": 1, "NORTHWEST": 2,
    "SOUTHEAST": 1, "SOUTHWEST": 2,
    "CENTER": 0, "NEUTRAL": 0
}

# Strong Color Numerology Model (Point 9)
COLOR_ENERGY_MAP = {
    "RED": 9, "BLUE": 8, "GREEN": 5, "YELLOW": 3, "ORANGE": 1,
    "WHITE": 6, "BLACK": 4, "GREY": 4, "PURPLE": 7, "PINK": 9,
    "BROWN": 4, "GOLD": 1, "SILVER": 2, "MAROON": 9, "CRIMSON": 9,
    "NAVY": 8, "LIME": 5, "TURQUOISE": 5
}


# ---------------------------
# Numerology & Core Helpers 
# ---------------------------
def safe_str(x: Any) -> str:
    """Handles NaN, Timestamp, and ensures clean string conversion."""
    if pd.isna(x):
        return ""
    if isinstance(x, (float, int)):
        return str(int(x)) if x == int(x) else str(x)
    if isinstance(x, (pd.Timestamp, datetime, date)):
        return str(x)
        
    s = str(x).strip()
    return s if s not in ['', 'nan', 'NaT'] else '' # Explicitly handle empty strings/NaT
    
def standardize_name(name: str) -> str:
    """Standardizes name for robust comparison (lowercase, remove spaces/underscores)."""
    return safe_str(name).lower().replace(' ', '').replace('_', '')

def strong_match(predicted_name: str, actual_name: str) -> bool:
    """Performs robust, standardized comparison."""
    # This function is CRITICAL for matching predicted Captain Name to the Real_Toss/Match Captain Name
    return standardize_name(predicted_name) == standardize_name(actual_name)


def reduce_to_single(n: Union[int, float, str]) -> int:
    try:
        n_str = safe_str(n).split('.')[0]
        n_int = int(n_str)
    except:
        return 0
    while n_int > 9 and n_int > 0:
        n_int = sum(int(digit) for digit in str(n_int))
    return n_int

def get_numerology_number(name: str) -> int:
    # Simplistic Chaldean numerology mapping
    mapping = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':2,'s':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}
    name = safe_str(name).lower().replace(' ', '')
    total = sum(mapping.get(char, 0) for char in name)
    return reduce_to_single(total)

def safe_parse_date(date_input: Any) -> date | None:
    """Safely converts string, Timestamp, or date object to a date object."""
    if pd.isna(date_input):
        return None
    if isinstance(date_input, date):
        return date_input
    if isinstance(date_input, pd.Timestamp):
        return date_input.date()
    try:
        return parser.parse(safe_str(date_input)).date()
    except:
        return None

def get_lp_nn_dp(dob_str: Any) -> Dict[str, int]:
    dt = safe_parse_date(dob_str)
    if dt is None:
        return {'lp': 0, 'nn': 0, 'dp': 0}

    dp = reduce_to_single(dt.day)
    nn = reduce_to_single(dt.day + dt.month + dt.year)
    lp = reduce_to_single(dt.month + dt.year) 

    return {'lp': lp, 'nn': nn, 'dp': dp}

def get_moon_phase_day(match_date: date) -> int:
    """Calculates a simplified Moon Phase Day (0-29) based on match date."""
    day_of_year = match_date.timetuple().tm_yday
    return (day_of_year % 30)

def get_color_number(color_name: str) -> int:
    color = safe_str(color_name).strip().upper()
    for key, value in COLOR_ENERGY_MAP.items():
        if key in color:
            return value
    return 0

def generate_iso_timestamp():
    return datetime.now().isoformat(timespec='seconds')


# ---------------------------
# SBC/KOTA & Ensemble Core Logic 
# ---------------------------
def calculate_sbc(row_data: dict) -> int:
    return 1 if get_numerology_number(row_data.get('captain_a_name', '')) > get_numerology_number(row_data.get('captain_b_name', '')) else 2

def calculate_kota(row_data: dict) -> int:
    match_date = safe_parse_date(row_data.get('match_date')) 
    if match_date is None:
        return 0
        
    match_date_nn = reduce_to_single(match_date.day)
    
    return 1 if reduce_to_single(match_date_nn + 1) % 2 == 0 else 2

def get_sbc_kota_override(sbc_vote: int, kota_vote: int, votes: Dict[int, float]) -> int:
    # Level 3: SBC + KOTA overriding threshold
    if sbc_vote == kota_vote and sbc_vote != 0:
        total_votes = sum(votes.values())
        if total_votes > 0:
            strongest_vote = max(votes.values())
            # Override if the methods are not already overwhelming (less than 75% dominance)
            if strongest_vote / total_votes < 0.75:
                return sbc_vote
    return 0

def ensemble_vote_v6(votes: Dict[int, float], sbc_vote: int, kota_vote: int, match_date_nn: int) -> tuple:
    """Implements the 4-layer ensemble voting system (Point 3)."""
    
    if not votes: return 0, 0.0

    # Level 1: Weighted Method Voting
    total_votes = sum(votes.values())
    if total_votes == 0: return 0, 0.0

    vote_tally = {1: votes.get(1, 0.0), 2: votes.get(2, 0.0)}
    
    winner = 0
    if vote_tally[1] > vote_tally[2]:
        winner = 1
        winner_votes = vote_tally[1]
        runner_up_votes = vote_tally[2]
    elif vote_tally[2] > vote_tally[1]:
        winner = 2
        winner_votes = vote_tally[2]
        runner_up_votes = vote_tally[1]
    else: # Exact Tie
        winner = 0 
        winner_votes = vote_tally[1]
        runner_up_votes = vote_tally[2]
    
    # Calculate confidence (Level 2)
    confidence = (winner_votes - runner_up_votes) / total_votes if winner != 0 and total_votes > 0 else 0.0
    final_prediction = winner

    # Level 3: SBC + KOTA Overriding Threshold
    sbc_kota_override = get_sbc_kota_override(sbc_vote, kota_vote, votes)
    if sbc_kota_override != 0:
        final_prediction = sbc_kota_override
        confidence = max(confidence, UNPREDICTABLE_MARGIN) # Boost confidence
    
    
    # Level 4: Numerology Override in Ties (Aggressive tie-breaker)
    if final_prediction == 0 or confidence < UNPREDICTABLE_MARGIN:
        # Check if the overall NN of the day (match_date_nn) aligns with a side (1 or 2)
        if match_date_nn != 0:
            if match_date_nn % 2 != 0: 
                final_prediction = 1
                confidence = max(confidence, UNPREDICTABLE_MARGIN)
            elif match_date_nn % 2 == 0: 
                final_prediction = 2
                confidence = max(confidence, UNPREDICTABLE_MARGIN)

    # Final check against the aggressive unpredictable margin
    if confidence < UNPREDICTABLE_MARGIN:
             return 0, confidence
            
    return final_prediction, confidence


# ---------------------------
# Prediction Methods (Toss 1-12, Match 1-11) 
# ---------------------------
ALL_METHODS = {}

# --- Placeholder for existing 8 Toss Methods from V5 ---
for i in range(1, 9):
    def toss_placeholder_v5(row_data: dict, a_nums: dict, b_nums: dict) -> int:
        nn_a = a_nums['nn']
        nn_b = b_nums['nn']
        return 1 if nn_a >= nn_b else 2
    ALL_METHODS[f'Toss_Method_{i}'] = toss_placeholder_v5

# --- NEW TOSS Methods (Point 4) ---
def toss_method_9_stadium_direction(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    direction = safe_str(row_data.get('stadium_direction', 'NEUTRAL')).upper()
    direction_vote = STADIUM_DIRECTION_MAP.get(direction, 0)
    nn_a = a_nums['nn']
    nn_b = b_nums['nn']
    
    if direction_vote == 1:
        return 1 if nn_a > nn_b else 2
    elif direction_vote == 2:
        return 2 if nn_b > nn_a else 1
    return 1 if nn_a > nn_b else 2
ALL_METHODS['Toss_Method_9'] = toss_method_9_stadium_direction

def toss_method_10_color_compatibility(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    color_a = get_color_number(row_data.get('teama_color', ''))
    color_b = get_color_number(row_data.get('teamb_color', ''))
    nn_a = a_nums['nn']
    nn_b = b_nums['nn']
    
    match_a = (color_a == nn_a)
    match_b = (color_b == nn_b)
    
    if match_a and not match_b: return 1
    if match_b and not match_a: return 2
    return 1 if nn_a > nn_b else 2
ALL_METHODS['Toss_Method_10'] = toss_method_10_color_compatibility

def toss_method_11_moon_phase(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    match_date = safe_parse_date(row_data.get('match_date'))
    if match_date is None: return 0

    moon_day = get_moon_phase_day(match_date)
    nn_a = a_nums['nn']
    nn_b = b_nums['nn']
    
    if moon_day % 2 == 0:
        return 1 if nn_a > nn_b else 2
    else:
        return 1 if nn_a < nn_b else 2
ALL_METHODS['Toss_Method_11'] = toss_method_11_moon_phase

def toss_method_12_hidden_sum(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    sum_a = (a_nums['lp'] + a_nums['nn'] + a_nums['dp']) % 9
    sum_b = (b_nums['lp'] + b_nums['nn'] + b_nums['dp']) % 9
    
    if sum_a > sum_b: return 1
    if sum_b > sum_a: return 2
    return 0
ALL_METHODS['Toss_Method_12'] = toss_method_12_hidden_sum

# --- Placeholder for existing 8 Match Methods from V5 ---
for i in range(1, 9):
    def match_placeholder_v5(row_data: dict, a_nums: dict, b_nums: dict) -> int:
        lp_a = a_nums['lp']
        lp_b = b_nums['lp']
        return 1 if lp_a >= lp_b else 2
    ALL_METHODS[f'Match_Method_{i}'] = match_placeholder_v5

# --- NEW MATCH Winner Methods (Point 5) ---
def match_method_9_team_astrology(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    match_date = safe_parse_date(row_data.get('match_date'))
    if match_date is None: return 0

    # Robustly get team name or fallback to captain name for numerology
    team_a_nn = get_numerology_number(row_data.get('team_a_name', row_data.get('captain_a_name', '')))
    team_b_nn = get_numerology_number(row_data.get('team_b_name', row_data.get('captain_b_name', '')))
    moon_day = get_moon_phase_day(match_date)

    score_a = reduce_to_single(team_a_nn + a_nums['lp'] + moon_day)
    score_b = reduce_to_single(team_b_nn + b_nums['lp'] + moon_day)

    if score_a > score_b: return 1
    if score_b > score_a: return 2
    return 0
ALL_METHODS['Match_Method_9'] = match_method_9_team_astrology

def match_method_10_stadium_alignment(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    # Robustly get team name or fallback to captain name for numerology
    team_a_nn = get_numerology_number(row_data.get('team_a_name', row_data.get('captain_a_name', '')))
    team_b_nn = get_numerology_number(row_data.get('team_b_name', row_data.get('captain_b_name', '')))

    direction = safe_str(row_data.get('stadium_direction', 'NEUTRAL')).upper()
    
    if direction in ["NORTH", "EAST", "NORTHEAST", "SOUTHEAST"]:
        return 1 if team_a_nn > team_b_nn else 2
    elif direction in ["SOUTH", "WEST", "SOUTHWEST", "NORTHWEST"]:
        return 1 if team_a_nn < team_b_nn else 2
    
    return 1 if team_a_nn > team_b_nn else 2
ALL_METHODS['Match_Method_10'] = match_method_10_stadium_alignment

def match_method_11_historical_form(history: list) -> int:
    """
    Match_Method_11 – Historical Form (Self-learning) (Point 5)
    Casts a vote (1 or 2) if its accuracy is above 60% in the last 20 predictions.
    """
    window = history[-20:]
    if len(window) < 5: return 0
    accuracy = sum(window) / len(window)
    
    if accuracy > 0.60:
        # A simple deterministic rule for this method when it's accurate
        # Alternate between 1 and 2 based on the current length of the history
        return 1 if len(history) % 2 == 0 else 2
    return 0
ALL_METHODS['Match_Method_11'] = match_method_11_historical_form


# ---------------------------
# Learning & I/O
# ---------------------------
def load_method_stats(filename: str) -> Dict[str, Any]:
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_method_stats(filepath: str, stats: Dict[str, Any]) -> None:
    """
    Saves the method statistics dictionary to a JSON file.
    FIXED: Ensures the second argument to json.dump is a file object.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=4)
    except IOError as e:
        print(f"Error saving method stats to {filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during JSON dump: {e}")


def update_method_stats(method_stats: Dict[str, Any], method_name: str, is_correct: bool, is_prediction_made: bool, task: str):
    stats = method_stats.get(method_name, {'weight': 1.0, 'correct': 0, 'total': 0, 'retired': False, 'task': task, 'history': []})
    
    if is_prediction_made:
        stats['total'] += 1
        stats['history'].append(1 if is_correct else 0)
        stats['history'] = stats['history'][-50:] 

        if is_correct:
            stats['correct'] += 1
            stats['weight'] = min(WEIGHT_MAX, stats['weight'] + WEIGHT_PROMOTE_STEP)
        else:
            stats['weight'] = max(WEIGHT_MIN, stats['weight'] - WEIGHT_DEMOTE_STEP)

    if stats['total'] >= MIN_TOTAL_EVAL and stats['weight'] < RETIRE_AFTER_WEIGHT_BELOW:
        current_fail_ratio = (stats['total'] - stats['correct']) / max(1, stats['total'])
        if current_fail_ratio > RETIRE_FAIL_RATIO:
            stats['retired'] = True

    method_stats[method_name] = stats
    return stats['weight']

def check_and_revive_methods(method_stats: Dict[str, Any], results_df: pd.DataFrame):
    """Automatic Revival System (Point 2)"""
    
    if len(results_df) < REVIVAL_WINDOW:
        return

    last_window = results_df.tail(REVIVAL_WINDOW)
    
    if 'Real_Match' in last_window.columns and 'Final_Match_Result' in last_window.columns:
        predictable_rows = last_window[last_window['Final_Match_Result'] != 'Unpredictable']
        if len(predictable_rows) > 0:
            
            # Simple check: If confidence is consistently low, revive one method
            avg_conf = last_window['Match_Confidence'].mean()
            if avg_conf < 0.50:
                retired_methods = [
                    (name, stats['weight']) 
                    for name, stats in method_stats.items() 
                    if stats['retired']
                ]
                
                if retired_methods:
                    retired_methods.sort(key=lambda x: x[1], reverse=True)
                    method_to_revive = retired_methods[0][0]
                    
                    method_stats[method_to_revive]['retired'] = False
                    method_stats[method_to_revive]['weight'] = WEIGHT_PROMOTE_STEP 


def run_predictor_v6():
    """Main execution function for V6."""
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return
        
    try:
        if INPUT_FILE.endswith(('.csv', '.txt')):
            df = pd.read_csv(INPUT_FILE)
        else:
            df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # CRITICAL FIX: Universal Column Name Cleaning (Removes spaces, converts to lowercase)
    df.columns = df.columns.str.replace(' ', '').str.lower()
    
    method_stats = load_method_stats(METHOD_STATS_FILE)
    results = []
    
    for method_name in ALL_METHODS:
        task = 'Toss' if method_name.startswith('Toss') else 'Match'
        if method_name not in method_stats:
             method_stats[method_name] = {'weight': 1.0, 'correct': 0, 'total': 0, 'retired': False, 'task': task, 'history': []}

    toss_correct_count = 0
    match_correct_count = 0
    total_rows = 0
    cleaned_timestamps = []
    
    # Pre-computation for performance (Handles missing columns gracefully via df.get())
    df['A_NUMS'] = df.get('captain_a_dob', pd.Series([None] * len(df))).apply(get_lp_nn_dp)
    df['B_NUMS'] = df.get('captain_b_dob', pd.Series([None] * len(df))).apply(get_lp_nn_dp)
    
    # Run loop
    for index, row in df.iterrows():
        row_data = row.to_dict()
        
        # 1. Row Data Setup
        if pd.isna(row_data.get('timestamp')) or safe_str(row_data.get('timestamp')) == '':
            row_data['timestamp'] = generate_iso_timestamp()
        cleaned_timestamps.append(row_data['timestamp'])

        a_nums = row_data['A_NUMS']
        b_nums = row_data['B_NUMS']
        
        current_result = {'Row_Index': index}
        toss_votes = {}
        match_votes = {}
        
        # 2. Prediction Aggregation
        for method_name, method_func in ALL_METHODS.items():
            stats = method_stats[method_name]
            if stats['retired']: continue

            task = stats['task']
            
            # Match_Method_11 (Historical Form) has a non-standard signature
            if method_name == 'Match_Method_11':
                prediction = method_func(stats['history']) 
                if prediction != 0:
                    match_votes[prediction] = match_votes.get(prediction, 0.0) + stats['weight']
                    current_result[method_name] = prediction
                else:
                    current_result[method_name] = 0
                continue
            
            # Standard methods
            prediction = method_func(row_data, a_nums, b_nums)
            
            if prediction != 0:
                if task == 'Toss':
                    toss_votes[prediction] = toss_votes.get(prediction, 0.0) + stats['weight']
                else:
                    match_votes[prediction] = match_votes.get(prediction, 0.0) + stats['weight']
            
            current_result[method_name] = prediction

        # Date numerology for Ensemble function
        current_match_date = safe_parse_date(row_data.get('match_date'))
        match_date_nn = reduce_to_single(current_match_date.day + current_match_date.month + current_match_date.year) if current_match_date else 0

        # 3. SBC/KOTA & Ensemble Voting
        sbc_vote = calculate_sbc(row_data)
        kota_vote = calculate_kota(row_data)
        
        current_result['SBC_Vote'] = sbc_vote
        current_result['KOTA_Vote'] = kota_vote

        final_toss_result, toss_confidence = ensemble_vote_v6(toss_votes, sbc_vote, kota_vote, match_date_nn)
        final_match_result, match_confidence = ensemble_vote_v6(match_votes, sbc_vote, kota_vote, match_date_nn)
        
        # 4. Result Recording (Robust Team Name Resolution)
        # --- Get raw names for logging clarity and prediction mapping ---
        captain_a_name_raw = safe_str(row_data.get('captain_a_name', 'N/A'))
        captain_b_name_raw = safe_str(row_data.get('captain_b_name', 'N/A'))
        
        # CRITICAL: Access the team name columns using the cleaned, lowercase names
        team_a_name_raw = safe_str(row_data.get('team_a_name', '')) 
        team_b_name_raw = safe_str(row_data.get('team_b_name', ''))
        
        # Determine the name used for prediction (fallback if team name is missing)
        # NOTE: For logging only, as the actual prediction result will be the captain name (see below)
        team_a_name_used = team_a_name_raw if team_a_name_raw else captain_a_name_raw
        team_b_name_used = team_b_name_raw if team_b_name_raw else captain_b_name_raw
        
        # Use 'Team A'/'Team B' only if everything else is missing
        team_a_name = team_a_name_used if team_a_name_used != 'N/A' else 'Team A'
        team_b_name = team_b_name_used if team_b_name_used != 'N/A' else 'Team B'
        
        # 5. Result Mapping to Name (CRITICAL FIX: Use CAPTAIN NAMES for output to match Real_Toss/Match column content)
        predicted_toss_winner = captain_a_name_raw if final_toss_result == 1 else captain_b_name_raw if final_toss_result == 2 else 'Unpredictable'
        predicted_match_winner = captain_a_name_raw if final_match_result == 1 else captain_b_name_raw if final_match_result == 2 else 'Unpredictable'
        
        current_result['Final_Toss_Result'] = predicted_toss_winner
        current_result['Final_Match_Result'] = predicted_match_winner
        current_result['Toss_Confidence'] = round(toss_confidence, 2)
        current_result['Match_Confidence'] = round(match_confidence, 2)
        
        # 6. Learning and Backtesting (CRITICAL FIX: Use strong_match)
        real_toss = safe_str(row_data.get('real_toss', ''))
        real_match = safe_str(row_data.get('real_match', ''))
        
        # Use strong_match because predicted_toss_winner is now the captain name
        is_toss_correct = strong_match(predicted_toss_winner, real_toss)
        is_match_correct = strong_match(predicted_match_winner, real_match)
        
        total_rows += 1
        if predicted_toss_winner != 'Unpredictable' and is_toss_correct: toss_correct_count += 1
        if predicted_match_winner != 'Unpredictable' and is_match_correct: match_correct_count += 1
        
        # Update weights for all methods
        for method_name, stats in method_stats.items():
            if method_name not in current_result: continue
            
            prediction = current_result[method_name] 
            is_made = (prediction != 0)
            
            if is_made:
                actual_winner = real_toss if stats['task'] == 'Toss' else real_match
                
                # CRITICAL FIX: Check prediction (1 or 2) against the actual captain name, using strong_match
                is_correct = (prediction == 1 and strong_match(captain_a_name_raw, actual_winner)) or \
                             (prediction == 2 and strong_match(captain_b_name_raw, actual_winner))

                update_method_stats(method_stats, method_name, is_correct, is_made, stats['task'])

        # 7. Enhanced Logging (Shows fallback status)
        # Log using the resolved captain names as the outcome target
        log_names = f"[{captain_a_name_raw} (Cap A) vs {captain_b_name_raw} (Cap B)]"
        
        print(f"{log_names} Toss Winner: {predicted_toss_winner} (Confidence: {toss_confidence:.2f}) -> Match Winner: {predicted_match_winner} (Confidence: {match_confidence:.2f})")

        current_result['Real_Toss'] = real_toss
        current_result['Real_Match'] = real_match
        
        results.append(current_result)
        
    # Check Revival System after all rows are processed
    results_df = pd.DataFrame(results)
    check_and_revive_methods(method_stats, results_df)

    # Persist method stats
    save_method_stats(METHOD_STATS_FILE, method_stats)

    # Build output DataFrames
    total_toss_evaluated = (results_df['Final_Toss_Result'] != 'Unpredictable').sum()
    total_match_evaluated = (results_df['Final_Match_Result'] != 'Unpredictable').sum()

    toss_acc = (toss_correct_count / max(total_toss_evaluated, 1)) * 100
    match_acc = (match_correct_count / max(total_match_evaluated, 1)) * 100
    
    summary_df = pd.DataFrame([{
        'Total_Rows_Processed': total_rows,
        'Toss_Evaluated': total_toss_evaluated,
        'Toss_Correct_Count': toss_correct_count,
        'Toss_Accuracy_%': round(toss_acc,2),
        'Match_Evaluated': total_match_evaluated,
        'Match_Correct_Count': match_correct_count,
        'Match_Accuracy_%': round(match_acc,2)
    }])

    # Prepare output input copy with cleaned timestamp column
    out_df = df.copy(deep=True)
    out_df['timestamp_clean'] = cleaned_timestamps 

    # Write outputs
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='w') as writer:
            out_df.to_excel(writer, index=False, sheet_name='Input_Data')
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')
        print(f"\n--- Output Complete ---")
        print(f"Output saved to {OUTPUT_FILE}")
        print(f"Toss Accuracy: {toss_acc:.2f}% | Match Accuracy: {match_acc:.2f}%")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    run_predictor_v6()