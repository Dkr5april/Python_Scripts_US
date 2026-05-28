#!/usr/bin/env python3
"""
EON Numerology Group Analysis - Robust Version
Reads: <FILENAME>.xlsx from BASE_DIR (expects 'Name' and 'DOB' columns)
Writes: <FILENAME>_RISK_REPORT.xlsx to BASE_DIR
Behavior: Uses robust date parsing logic to handle mixed date formats in the DOB column.
"""
from datetime import datetime, date, timedelta
import pandas as pd
import math
import sys
import os
from dateutil import parser # Required for robust parsing

# ---------------------------
# Config & Fixed Path
# ---------------------------
# 🌟 Fixed Base Directory - Matches your previous setting
BASE_DIR = r"C:\backup\US_word_files\Interview_learnings\python_scripts\Numerology_Scripts\EON_Theory"

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
# Robust Date Parsing Helpers (From Match Predictor)
# ---------------------------
def safe_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_parse_timestamp(value):
    """
    Parse a timestamp-like value robustly (dateutil parser).
    Returns (dt_or_None, has_time_flag)
    - never raises; on failure returns (None, False)
    """
    if value is None:
        return None, False
    s = safe_str(value)
    if s == "":
        return None, False

    # Heuristic: assume 'DOB' usually doesn't have time, but let the parser decide
    has_time = (":" in s)

    # Try dateutil parser (very flexible, dayfirst=True for DD/MM/YYYY preference)
    try:
        dt = parser.parse(s, dayfirst=True)
        # pd.to_datetime may return a pandas Timestamp; convert to python datetime
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        
        # Check if the parsed date has a time component that isn't midnight
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0:
             has_time = True
        
        return dt, has_time
    except Exception as e:
        # Fallback for raw Excel numbers which dateutil might miss if the column wasn't read as a number
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
# EON Numerology Functions (Adjusted Date Parsing)
# ---------------------------

def reduce_to_single_digit(n):
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    if n in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    return n

def parse_target_date(date_str):
    """Parses a target date string, strictly expecting DD/MM/YYYY."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Invalid target date format. Use DD/MM/YYYY.")

def get_dob_dt(dob_value):
    """Uses the robust parser to get the DOB datetime object."""
    dt, _ = safe_parse_timestamp(dob_value)
    if dt is None:
        raise ValueError("Invalid DOB format.")
    # For numerology, we only need the date part
    return dt

def get_3x3_chart(day, month, year):
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}

def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]

def get_day_vibe(date):
    return reduce_to_single_digit(date.day + date.month + date.year)

def calculate_all_destiny_numbers(full_name):
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum_p = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    dn_p = reduce_to_single_digit(total_sum_p)
    total_sum_c = sum(CHALDEAN_MAP.get(letter, 0) for letter in name_clean)
    dn_c = reduce_to_single_digit(total_sum_c)
    total_sum_k = sum(KABBALAH_MAP.get(letter, 0) for letter in name_clean)
    dn_k = reduce_to_single_digit(total_sum_k)
    return dn_p, dn_c, dn_k

# --- RISK SCORE FUNCTIONS (Unchanged) ---
def get_overall_risk_for_bar(scores):
    total_score = sum(scores.values())
    average_score = total_score / 8
    if average_score < 0.5: return 0, total_score
    if average_score < 1.5: return 1, total_score
    if average_score < 2.5: return 2, total_score
    return 3, total_score

def eon_risk_score(chart, birth_root, date):
    missing = missing_numbers(chart)
    icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month)
    icc_year = reduce_to_single_digit(date.year)
    score = 0
    if icc_day == reduce_to_single_digit(birth_root) and icc_day in missing: score += 2
    if icc_day in missing: score += 1
    if icc_month in missing: score += 1
    if icc_year in missing: score += 1
    if score == 0: return 0
    elif score in [1, 2]: return 1
    elif score in [3, 4]: return 2
    else: return 3

def pythagorean_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 9]: return 0
    elif vibe in [2, 6, 7]: return 1
    else: return 3

def chaldean_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 6, 9]: return 0
    elif vibe in [7]: return 1
    else: return 3

def kabbalah_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [3, 6, 9]: return 0
    elif vibe in [1, 5]: return 1
    else: return 3

def destiny_alignment(date, dn_p):
    day_vibe = get_day_vibe(date)
    return 0 if day_vibe == dn_p else 3

def pythagorean_destiny_hybrid(date, dn_p):
    if get_day_vibe(date) == dn_p: return 0
    return pythagorean_vibe(date)

def chaldean_destiny_hybrid(date, dn_c):
    if get_day_vibe(date) == dn_c: return 0
    return chaldean_vibe(date)

def kabbalah_destiny_hybrid(date, dn_k):
    if get_day_vibe(date) == dn_k: return 0
    return kabbalah_vibe(date)


# ---------------------------
# Main Calculation Routine
# ---------------------------

def calculate_group_risk(input_excel_path, target_dates_str):
    
    try:
        # Read the input as Excel, letting pandas determine data types initially
        df_input = pd.read_excel(input_excel_path) 
    except FileNotFoundError:
        print(f"ERROR: Input file not found at {input_excel_path}")
        sys.exit()
    except Exception as e:
        print(f"ERROR: Could not read Excel file. Ensure file exists and 'openpyxl' is installed: {e}")
        sys.exit()

    # 1. Prepare Target Dates (strict DD/MM/YYYY)
    target_dates = []
    for dstr in target_dates_str.split(','):
        dstr = dstr.strip()
        try:
            target_dates.append(parse_target_date(dstr))
        except ValueError:
            print(f"Skipping invalid target date format: {dstr}. Please use DD/MM/YYYY.")

    if not target_dates:
        print("ERROR: No valid target dates provided.")
        sys.exit()

    print(f"Analyzing {len(df_input)} individuals against {len(target_dates)} target date(s)...")
    results_list = []

    # 2. Process Each Individual using robust DOB parser
    for index, row in df_input.iterrows():
        try:
            # Name and DOB column are critical
            name = safe_str(row['Name'])
            dob_value = row['DOB'] # Pass the raw value to the robust parser
            
            dob_dt = get_dob_dt(dob_value)
            
            day = dob_dt.day
            month = dob_dt.month
            year = dob_dt.year
            dob_str_clean = dob_dt.strftime('%d/%m/%Y') # Use a clean string for output

            birth_root = reduce_to_single_digit(day)
            chart = get_3x3_chart(day, month, year)
            dn_p, dn_c, dn_k = calculate_all_destiny_numbers(name)

        except Exception as e:
            print(f"Skipping row {index+1} ({safe_str(row.get('Name', 'Unknown'))}) due to error: {e}")
            continue

        # 3. Process Each Target Date
        for date in target_dates:
            
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
            alignment_score = scores['D'] + scores['PD'] + scores['KD'] + scores['CD']
            
            result = {
                'Name': name,
                'DOB': dob_str_clean,
                'DN_P': dn_p, 'DN_C': dn_c, 'DN_K': dn_k,
                'Target_Date': date.strftime('%d/%m/%Y'),
                'Day_Vibe': get_day_vibe(date),
                
                'Score_EON_E': scores['E'], 'Score_Pyth_P': scores['P'], 
                'Score_Kaba_K': scores['K'], 'Score_Chald_C': scores['C'], 
                'Score_Dest_D': scores['D'], 'Score_PD': scores['PD'], 
                'Score_KD': scores['KD'], 'Score_CD': scores['CD'],
                
                'Total_Alignment_T': alignment_score,
                'Overall_Risk_Score': overall_risk_score,
                'Risk_Level': RISK_MAP[overall_risk_score]
            }
            results_list.append(result)

    return pd.DataFrame(results_list)

# ---------------------------
# Execution (Fixed Path Logic)
# ---------------------------

if __name__ == "__main__":
    print("--- EON Group Numerology Risk Analysis (ULTRA ROBUST) ---")
    print(f"Base Directory Fixed To: {BASE_DIR}")
    print("----------------------------------------------------------")

    # 1. Input XLSX Path - Ask for file name only
    while True:
        file_name = input("Enter the INPUT XLSX file name (e.g., players.xlsx): ").strip()
        
        # Build the full path
        input_file = os.path.join(BASE_DIR, file_name) 

        if os.path.exists(input_file):
             break
        print(f"File not found at: {input_file}. Please check the file name and try again.")

    # 2. Target Dates Input
    while True:
        target_dates_input = input("Enter target date(s) (DD/MM/YYYY, comma-separated): ")
        if target_dates_input.strip():
            break
        print("Please enter at least one target date.")

    # 3. Calculate
    try:
        results_df = calculate_group_risk(input_file, target_dates_input)
    except Exception as e:
        print(f"A critical error occurred during calculation: {e}")
        sys.exit()

    # 4. Output XLSX Path - Save to the same base directory
    if not results_df.empty:
        base_name = os.path.splitext(file_name)[0]
        output_file_name = f"{base_name}_RISK_REPORT.xlsx"
        output_file = os.path.join(BASE_DIR, output_file_name)
        
        # Write output workbook (separate file)
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
                results_df.to_excel(writer, index=False, sheet_name='Numerology_Report')
            
            print("\n" + "="*50)
            print(f"✅ Analysis Complete.")
            print(f"Output saved to: {output_file}")
            print("="*50)
        except Exception as we:
            print(f"Failed to write output: {we}")
            sys.exit(1)
            
    else:
        print("\nNo results generated. Please check your input file and required headers ('Name' and 'DOB').")