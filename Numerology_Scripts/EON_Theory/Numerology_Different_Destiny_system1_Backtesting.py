#!/usr/bin/env python3
"""
EON Numerology Match Backtester

Reads: match_analysis_data.xlsx (expects specific Captain/Match columns)
Writes: match_analysis_data_REPORT.xlsx (two sheets: Backtest_Results and Summary)
Logic: Predicts Team B win if Captain A Risk > Captain B Risk.
"""
from datetime import datetime, date, timedelta
import pandas as pd
import math
import sys
import os
from dateutil import parser 
from typing import Dict, Any, Tuple

# ---------------------------
# Config & Fixed Path
# ---------------------------
# 🌟 FIXED BASE DIRECTORY 🌟
BASE_DIR = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Numerology_Scripts\EON_Theory"
INPUT_FILE = "match_analysis_data.xlsx"

# --- EON CONFIGURATION & MAPPING (Unchanged) ---
RISK_MAP = {
    0: 'Good (0)', 1: 'Low Risk (1)', 2: 'Medium Risk (2)', 3: 'High Risk (3)'
}
PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1, 'B': 2, 'K': 2, 'T': 2, 'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4, 'E': 5, 'N': 5, 'W': 5, 'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7, 'H': 8, 'Q': 8, 'Z': 8, 'I': 9, 'R': 9
}
CHALDEAN_MAP = {
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1, 'B': 2, 'K': 2, 'R': 2, 'C': 3, 'G': 3, 'L': 3, 'S': 3,
    'D': 4, 'M': 4, 'T': 4, 'E': 5, 'H': 5, 'N': 5, 'X': 5, 'U': 6, 'V': 6, 'W': 6, 'O': 7, 'Z': 7,
    'F': 8, 'P': 8
}
KABBALAH_MAP = PYTHAGOREAN_MAP 

# ---------------------------
# Robust Date Parsing Helpers
# ---------------------------
def safe_str(x: Any) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_parse_timestamp(value: Any) -> Tuple[datetime | None, bool]:
    """Parse a timestamp-like value robustly using dateutil."""
    s = safe_str(value)
    if s == "":
        return None, False

    try:
        dt = parser.parse(s, dayfirst=True)
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        
        # Check if the time component is non-zero
        has_time = dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0
        return dt, has_time
    except Exception:
        # Fallback for raw Excel numbers which dateutil might miss
        try:
             if s.isdigit() and int(s) > 30000:
                days_since_1900 = int(s)
                dt_excel_start = datetime(1899, 12, 30)
                dt = dt_excel_start + timedelta(days=days_since_1900)
                return dt, False
        except:
             pass
        return None, False

# ---------------------------
# EON Numerology Core Functions
# ---------------------------

def reduce_to_single_digit(n: int) -> int:
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    if n in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    return n

def get_dob_dt(dob_value: Any) -> datetime:
    """Uses the robust parser to get the DOB datetime object."""
    dt, _ = safe_parse_timestamp(dob_value)
    if dt is None:
        raise ValueError("Invalid DOB format (cannot parse date).")
    # Return the date part only for numerology
    return dt

def get_3x3_chart(day: int, month: int, year: int) -> Dict[int, int]:
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}

def missing_numbers(chart: Dict[int, int]) -> list[int]:
    return [num for num, count in chart.items() if count == 0]

def get_day_vibe(date: datetime) -> int:
    return reduce_to_single_digit(date.day + date.month + date.year)

def calculate_all_destiny_numbers(full_name: str) -> Tuple[int, int, int]:
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum_p = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    dn_p = reduce_to_single_digit(total_sum_p)
    total_sum_c = sum(CHALDEAN_MAP.get(letter, 0) for letter in name_clean)
    dn_c = reduce_to_single_digit(total_sum_c)
    total_sum_k = sum(KABBALAH_MAP.get(letter, 0) for letter in name_clean)
    dn_k = reduce_to_single_digit(total_sum_k)
    return dn_p, dn_c, dn_k

# --- RISK SCORE CALCULATION ---
def get_overall_risk_for_bar(scores: Dict[str, int]) -> Tuple[int, float]:
    total_score = sum(scores.values())
    average_score = total_score / 8
    
    # Mapping logic from previous EON script
    if average_score < 0.5: return 0, total_score
    if average_score < 1.5: return 1, total_score
    if average_score < 2.5: return 2, total_score
    return 3, total_score

def eon_risk_score(chart: Dict[int, int], birth_root: int, date: datetime) -> int:
    missing = missing_numbers(chart)
    icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month)
    icc_year = reduce_to_single_digit(date.year)
    score = 0
    # Note: birth_root is derived from birth day number
    if icc_day == reduce_to_single_digit(birth_root) and icc_day in missing: score += 2
    if icc_day in missing: score += 1
    if icc_month in missing: score += 1
    if icc_year in missing: score += 1
    
    if score == 0: return 0
    elif score in [1, 2]: return 1
    elif score in [3, 4]: return 2
    else: return 3

def pythagorean_vibe(date: datetime) -> int:
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 9]: return 0
    elif vibe in [2, 6, 7]: return 1
    else: return 3

def chaldean_vibe(date: datetime) -> int:
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 6, 9]: return 0
    elif vibe in [7]: return 1
    else: return 3

def kabbalah_vibe(date: datetime) -> int:
    vibe = get_day_vibe(date)
    if vibe in [3, 6, 9]: return 0
    elif vibe in [1, 5]: return 1
    else: return 3

def destiny_alignment(date: datetime, dn_p: int) -> int:
    return 0 if get_day_vibe(date) == dn_p else 3

def pythagorean_destiny_hybrid(date: datetime, dn_p: int) -> int:
    if get_day_vibe(date) == dn_p: return 0
    return pythagorean_vibe(date)

def chaldean_destiny_hybrid(date: datetime, dn_c: int) -> int:
    if get_day_vibe(date) == dn_c: return 0
    return chaldean_vibe(date)

def kabbalah_destiny_hybrid(date: datetime, dn_k: int) -> int:
    if get_day_vibe(date) == dn_k: return 0
    return kabbalah_vibe(date)

def get_risk_scores(date: datetime, dob_dt: datetime, name: str) -> Tuple[int, Dict[str, int]]:
    """Calculates all 8 risk scores and the final Overall Risk Score."""
    
    day = dob_dt.day
    month = dob_dt.month
    year = dob_dt.year

    birth_root = reduce_to_single_digit(day)
    chart = get_3x3_chart(day, month, year)
    dn_p, dn_c, dn_k = calculate_all_destiny_numbers(name)

    scores = {}
    scores['E'] = eon_risk_score(chart, birth_root, date)
    scores['P'] = pythagorean_vibe(date)
    scores['K'] = kabbalah_vibe(date)
    scores['C'] = chaldean_vibe(date)
    scores['D'] = destiny_alignment(date, dn_p)
    scores['PD'] = pythagorean_destiny_hybrid(date, dn_p)
    scores['KD'] = kabbalah_destiny_hybrid(date, dn_k)
    scores['CD'] = chaldean_destiny_hybrid(date, dn_c)
    
    overall_risk_score, _ = get_overall_risk_for_bar(scores)
    return overall_risk_score, scores

# ---------------------------
# Main Backtest Routine
# ---------------------------

def run_match_backtest():
    
    full_path = os.path.join(BASE_DIR, INPUT_FILE)
    OUTPUT_FILE = os.path.join(BASE_DIR, os.path.splitext(INPUT_FILE)[0] + "_REPORT.xlsx")

    # 1. Read Input File
    if not os.path.exists(full_path):
        print(f"\nFATAL ERROR: Input file '{INPUT_FILE}' not found at path: {full_path}")
        sys.exit(1)

    try:
        # Read the input as Excel, letting pandas determine data types initially
        df_input = pd.read_excel(full_path) 
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    # 2. Ensure critical columns exist
    REQUIRED_COLS = ['Captain_A_Name', 'Captain_B_Name', 'Captain_A_DOB', 'Captain_B_DOB', 'Match_Date', 'Real_Match']
    for col in REQUIRED_COLS:
        if col not in df_input.columns:
            print(f"FATAL ERROR: Input file is missing required column: '{col}'")
            sys.exit(1)

    print(f"Loaded {len(df_input)} rows for backtesting.")

    # 3. Process Each Match
    results_list = []
    total_matches = 0
    matches_passed = 0
    matches_failed = 0
    matches_neutral = 0

    for index, row in df_input.iterrows():
        total_matches += 1
        
        try:
            # Extract inputs
            a_name = safe_str(row['Captain_A_Name'])
            b_name = safe_str(row['Captain_B_Name'])
            a_dob_value = row['Captain_A_DOB']
            b_dob_value = row['Captain_B_DOB']
            match_date_value = row['Match_Date']
            real_winner = safe_str(row['Real_Match'])
            team_a_name = safe_str(row.get('Team_A_Name', a_name)) # Use Captain name as team name if missing
            team_b_name = safe_str(row.get('Team_B_Name', b_name))
            
            # Parse Dates
            a_dob_dt = get_dob_dt(a_dob_value)
            b_dob_dt = get_dob_dt(b_dob_value)
            match_dt = get_dob_dt(match_date_value) # Using DOB parser as it is robust for generic dates
            
            # 4. Calculate Risk Scores
            a_risk, a_scores = get_risk_scores(match_dt, a_dob_dt, a_name)
            b_risk, b_scores = get_risk_scores(match_dt, b_dob_dt, b_name)

            # 5. Apply Prediction Logic
            if a_risk > b_risk:
                # Captain A (Higher Risk) -> Predict Team B Win
                predicted_winner = team_b_name
                prediction_reason = f"{team_b_name} (Captain A Risk {a_risk} > Captain B Risk {b_risk})"
            elif b_risk > a_risk:
                # Captain B (Higher Risk) -> Predict Team A Win
                predicted_winner = team_a_name
                prediction_reason = f"{team_a_name} (Captain B Risk {b_risk} > Captain A Risk {a_risk})"
            else:
                # Scores Equal -> Neutral
                predicted_winner = "Neutral"
                prediction_reason = f"Neutral (Captain A Risk {a_risk} = Captain B Risk {b_risk})"

            # 6. Backtest
            if predicted_winner == "Neutral":
                backtest_result = "Neutral"
                matches_neutral += 1
            elif predicted_winner.lower() == real_winner.lower():
                backtest_result = "PASS"
                matches_passed += 1
            else:
                backtest_result = "FAIL"
                matches_failed += 1

            # 7. Record Result
            results_list.append({
                'Match_Date': match_dt.strftime('%d/%m/%Y'),
                'Team_A': team_a_name,
                'Team_B': team_b_name,
                'Cap_A_Risk_Score': a_risk,
                'Cap_B_Risk_Score': b_risk,
                'Predicted_Winner': predicted_winner,
                'Prediction_Reason': prediction_reason,
                'Real_Match_Winner': real_winner,
                'Backtest_Result': backtest_result,
                # Include the raw scores for deeper analysis
                'A_Scores_Raw': str(a_scores),
                'B_Scores_Raw': str(b_scores)
            })
            
        except Exception as e:
            results_list.append({
                'Match_Date': safe_str(row['Match_Date']),
                'Team_A': safe_str(row.get('Team_A_Name')),
                'Team_B': safe_str(row.get('Team_B_Name')),
                'Cap_A_Risk_Score': 'ERROR',
                'Cap_B_Risk_Score': 'ERROR',
                'Predicted_Winner': 'ERROR',
                'Prediction_Reason': f"ROW SKIPPED DUE TO ERROR: {e}",
                'Real_Match_Winner': safe_str(row['Real_Match']),
                'Backtest_Result': 'ERROR'
            })
            print(f"Warning: Skipping row {index+1} due to error: {e}")

    results_df = pd.DataFrame(results_list)

    # 4. Generate Summary Report
    summary_df = pd.DataFrame([{
        'Total_Matches_Tested': total_matches,
        'Matches_Passed_(Correct)': matches_passed,
        'Matches_Failed_(Incorrect)': matches_failed,
        'Matches_Neutral_(Tie_Prediction)': matches_neutral,
        'Prediction_Accuracy_% (Ignoring Neutrals)': round((matches_passed / (total_matches - matches_neutral)) * 100, 2) if (total_matches - matches_neutral) > 0 else 0.00
    }])
    
    # 5. Write Output
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='w') as writer:
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
        
        print("\n" + "="*60)
        print("✅ Backtest Complete.")
        print(f"Report saved to: {OUTPUT_FILE}")
        print("-" * 60)
        print(f"Total Matches: {total_matches}")
        print(f"Passed: {matches_passed}")
        print(f"Failed: {matches_failed}")
        print(f"Accuracy (Non-Neutral): {summary_df['Prediction_Accuracy_% (Ignoring Neutrals)'].iloc[0]}%")
        print("="*60)

    except Exception as we:
        print(f"FATAL ERROR: Failed to write output: {we}")
        sys.exit(1)

if __name__ == '__main__':
    print("--- EON Numerology Match Backtester ---")
    print(f"Input: {INPUT_FILE} in {BASE_DIR}")
    print("-" * 60)
    
    # Check if pandas is available
    if 'pandas' not in sys.modules:
        print("FATAL ERROR: The 'pandas' library is required. Please run: pip install pandas openpyxl")
        sys.exit(1)
        
    run_match_backtest()