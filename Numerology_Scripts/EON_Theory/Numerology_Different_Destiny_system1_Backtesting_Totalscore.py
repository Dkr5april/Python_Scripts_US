#!/usr/bin/env python3
"""
EON Numerology Full Team Match Backtester (ROBUST COMPARISON V2 - CODE FIX)

Reads: match_analysis_data.xlsx 
Writes: match_analysis_data_ROBUST_REPORT.xlsx
Logic: Calculates Team Match Score (TNN + Day Power + Place Power). 
***Team with LOWER score is predicted to win.***
***Features Robust String Matching to fix 0.0% error.***
"""
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
from dateutil import parser 
from typing import Dict, Any, Tuple

# ---------------------------
# Config & Fixed Path (Moved to Global Scope for accessibility)
# ---------------------------
BASE_DIR = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Numerology_Scripts\EON_Theory"
INPUT_FILE = "match_analysis_data.xlsx"

# --- Numerology Mappings ---
PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1, 'B': 2, 'K': 2, 'T': 2, 'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4, 'E': 5, 'N': 5, 'W': 5, 'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7, 'H': 8, 'Q': 8, 'Z': 8, 'I': 9, 'R': 9
}

# ---------------------------
# Core Numerology & Date Helpers
# ---------------------------

def safe_str(x: Any) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_parse_timestamp(value: Any) -> datetime:
    """Robustly parses a date value into a datetime object."""
    s = safe_str(value)
    if s == "":
        raise ValueError("Date value is empty.")

    try:
        dt = parser.parse(s, dayfirst=True)
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        return dt
    except Exception:
        try:
             # Fallback for raw Excel numbers
             if s.isdigit() and int(s) > 30000:
                days_since_1900 = int(s)
                dt_excel_start = datetime(1899, 12, 30)
                return dt_excel_start + timedelta(days=days_since_1900)
        except:
             pass
        raise ValueError(f"Invalid date format: {s}")

def reduce_to_single_digit(n: int) -> int:
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    return n

def calculate_name_number(full_name: str) -> int:
    """Calculates the single-digit Name Number (TNN or PP) using Pythagorean map."""
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    return reduce_to_single_digit(total_sum)

def calculate_day_power(date: datetime) -> int:
    """Calculates the single-digit Day Power (DP) for the match date."""
    return reduce_to_single_digit(date.day + date.month + date.year)

def normalize_name(name: str) -> str:
    """Removes spaces, non-alphabetic chars, and converts to lowercase for comparison."""
    return ''.join(c for c in name if c.isalpha()).lower()


# ---------------------------
# Main Backtest Routine (LOGIC AND COMPARISON FIXED)
# ---------------------------

def run_team_match_backtest():
    
    # Use the globally defined variables
    full_path = os.path.join(BASE_DIR, INPUT_FILE)
    OUTPUT_FILE = os.path.join(BASE_DIR, os.path.splitext(INPUT_FILE)[0] + "_ROBUST_REPORT.xlsx")

    # 1. Read Input File
    if not os.path.exists(full_path):
        print(f"\nFATAL ERROR: Input file '{INPUT_FILE}' not found at path: {full_path}")
        sys.exit(1)

    try:
        df_input = pd.read_excel(full_path) 
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    # 2. Ensure critical columns exist (using the EXACT names you confirmed)
    REQUIRED_COLS = ['Team_A_name', 'Team_B_name', 'Match_Date', 'Match_Place', 'Real_Match']
    for col in REQUIRED_COLS:
        if col not in df_input.columns:
            print(f"FATAL ERROR: Input file is missing required column: '{col}'")
            sys.exit(1)

    print(f"Loaded {len(df_input)} rows for Robust Team Match Score backtesting.")

    # 3. Process Each Match
    results_list = []
    total_matches = 0
    matches_passed = 0
    matches_failed = 0
    matches_neutral = 0

    for index, row in df_input.iterrows():
        total_matches += 1
        
        try:
            # Extract and normalize inputs for comparison
            team_a_name = safe_str(row['Team_A_name'])
            team_b_name = safe_str(row['Team_B_name'])
            real_winner_raw = safe_str(row['Real_Match'])
            real_winner_normalized = normalize_name(real_winner_raw)
            match_place = safe_str(row['Match_Place'])
            
            # Parse Date
            match_dt = safe_parse_timestamp(row['Match_Date'])
            
            # 4. Calculate Numerology Components
            day_power = calculate_day_power(match_dt)
            place_power = calculate_name_number(match_place)
            
            a_tnn = calculate_name_number(team_a_name)
            b_tnn = calculate_name_number(team_b_name)

            # 5. Calculate Team Match Score (TMS)
            a_tms = reduce_to_single_digit(a_tnn + day_power + place_power)
            b_tms = reduce_to_single_digit(b_tnn + day_power + place_power)

            # 6. Apply Prediction Logic: ***LOWER Score is predicted to win.***
            if a_tms < b_tms: 
                predicted_winner = team_a_name
                predicted_winner_normalized = normalize_name(team_a_name)
                prediction_reason = f"{team_a_name} (TMS {a_tms} < TMS {b_tms})"
            elif b_tms < a_tms: 
                predicted_winner = team_b_name
                predicted_winner_normalized = normalize_name(team_b_name)
                prediction_reason = f"{team_b_name} (TMS {b_tms} < TMS {a_tms})"
            else:
                predicted_winner = "Neutral"
                predicted_winner_normalized = ""
                prediction_reason = f"Neutral (TMS {a_tms} = {b_tms})"

            # 7. Robust Backtest (Uses normalized names to solve potential 0.0% failure)
            if predicted_winner == "Neutral":
                backtest_result = "Neutral"
                matches_neutral += 1
            elif predicted_winner_normalized == real_winner_normalized: 
                backtest_result = "PASS"
                matches_passed += 1
            else:
                backtest_result = "FAIL"
                matches_failed += 1

            # 8. Record Result
            results_list.append({
                'Match_Date': match_dt.strftime('%d/%m/%Y'),
                'Day_Power': day_power,
                'Place_Power': place_power,
                'Team_A_Name': team_a_name,
                'Team_A_TMS': a_tms,
                'Team_B_Name': team_b_name,
                'Team_B_TMS': b_tms,
                'Predicted_Winner': predicted_winner,
                'Real_Match_Winner': real_winner_raw,
                'Prediction_Reason': prediction_reason,
                'Backtest_Result': backtest_result,
            })
            
        except Exception as e:
            # Handle row-specific errors gracefully
            results_list.append({
                'Match_Date': safe_str(row.get('Match_Date')),
                'Team_A_Name': safe_str(row.get('Team_A_name')),
                'Team_B_Name': safe_str(row.get('Team_B_name')),
                'Predicted_Winner': 'ERROR',
                'Prediction_Reason': f"ROW SKIPPED DUE TO ERROR: {e}",
                'Real_Match_Winner': safe_str(row.get('Real_Match')),
                'Backtest_Result': 'ERROR'
            })
            print(f"Warning: Skipping row {index+1} due to error: {e}")

    results_df = pd.DataFrame(results_list)

    # 9. Generate Summary Report
    total_rows_predicted = total_matches - matches_neutral
    summary_df = pd.DataFrame([{
        'Total_Matches_Tested': total_matches,
        'Matches_Passed_(Correct)': matches_passed,
        'Matches_Failed_(Incorrect)': matches_failed,
        'Matches_Neutral_(Tie_Prediction)': matches_neutral,
        'Total_Predicted_Matches': total_rows_predicted,
        'Prediction_Accuracy_% (Ignoring Neutrals)': round((matches_passed / total_rows_predicted) * 100, 2) if total_rows_predicted > 0 else 0.00
    }])
    
    # 10. Write Output
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='w') as writer:
            results_df.to_excel(writer, index=False, sheet_name='Team_Score_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        
        print("\n" + "="*70)
        print("✅ Team Match Score Backtest Complete (ROBUST COMPARISON V2).")
        print(f"Report saved to: {OUTPUT_FILE}")
        print("-" * 70)
        print(f"Total Matches: {total_matches}")
        print(f"Passed: {matches_passed}")
        print(f"Failed: {matches_failed}")
        print(f"Neutral: {matches_neutral}")
        print(f"Accuracy (Non-Neutral): {summary_df['Prediction_Accuracy_% (Ignoring Neutrals)'].iloc[0]}%")
        print("="*70)

    except Exception as we:
        print(f"FATAL ERROR: Failed to write output: {we}")
        sys.exit(1)

if __name__ == '__main__':
    print("--- EON Numerology Full Team Match Backtester (ROBUST COMPARISON V2) ---")
    
    # CRITICAL FIX: Ensure these variables are defined before printing
    BASE_DIR = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Numerology_Scripts\EON_Theory"
    INPUT_FILE = "match_analysis_data.xlsx"
    
    print(f"Input: {INPUT_FILE} in {BASE_DIR}")
    print("-" * 70)
        
    run_team_match_backtest()