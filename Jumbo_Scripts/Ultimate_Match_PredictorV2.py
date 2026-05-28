#!/usr/bin/env python3
"""
Ultimate Match Predictor — Timestamp-safe version

Reads: match_analysis_data.xlsx (expects a "Timestamp" column among others)
Writes: match_analysis_data_output.xlsx (three sheets: Input_with_Predictions, Backtest_Results, Backtest_Summary)
Behavior:
 - Does NOT modify the input file.
 - Robustly parses mixed Timestamp formats (ISO, DD/MM/YYYY, YYYY-MM-DD, date-only, date+time).
 - Preserves time only if the original text contains time markers (':' or 'T').
 - Never skips rows even if Timestamp is missing/invalid.
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime, date
from dateutil import parser
from typing import Dict

# ---------------------------
# Config
# ---------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"
TIMESTAMP_COL = "Timestamp"    # exact column name to process

# ---------------------------
# Helpers
# ---------------------------
def safe_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def safe_parse_timestamp(value):
    """
    Parse a timestamp-like value robustly.
    Returns (dt_or_None, has_time_flag)
    - has_time_flag is True when parsed string contains 'T' or ':' (heuristic)
    - never raises; on failure returns (None, False)
    """
    if value is None:
        return None, False
    s = safe_str(value)
    if s == "":
        return None, False

    # Heuristic: if the raw string has 'T' or ':' treat as having time
    has_time = ("T" in s and ":" in s) or (":" in s)

    # Try common cases quickly (fast)
    # ISO with fractional seconds
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        return dt, has_time
    except Exception:
        pass

    # ISO without fraction
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return dt, has_time
    except Exception:
        pass

    # Try common date/time and date formats with pandas (dayfirst True to handle DD/MM/YYYY)
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="raise")
        # pd.to_datetime may return a pandas Timestamp; convert to python datetime
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        return dt, has_time
    except Exception:
        pass

    # Last resort - dateutil parser (very flexible)
    try:
        dt = parser.parse(s, dayfirst=True)
        return dt, has_time
    except Exception as e:
        # This line is for general timestamp parsing errors, which your data currently avoids.
        print(f"DEBUG: Failed to parse timestamp value '{s}'. Error: {e}")
        return None, False

def format_timestamp(dt, has_time):
    """Format dt based on whether original had time. Return empty string if dt is None."""
    if dt is None:
        return ""
    if has_time:
        # normalize to seconds
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d")

# Numerology helpers (unchanged logic)
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

def reduce_num(n: int) -> int:
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    s = safe_str(dob_str)
    try:
        dt = datetime.strptime(s, "%d/%m/%Y")
        return reduce_num(dt.day)
    except:
        digits = "".join(ch for ch in s if ch.isdigit())
        return reduce_num(sum(int(d) for d in digits)) if digits else 1

def life_path_number(dob_str: str) -> int:
    s = safe_str(dob_str)
    digits = "".join(ch for ch in s if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits)) if digits else 1

def name_number(name: str) -> int:
    s = safe_str(name).upper()
    return reduce_num(sum(PYTH_MAP.get(ch,0) for ch in s if ch.isalpha()))

def date_life_path(date_str: str) -> int:
    s = safe_str(date_str)
    digits = "".join(ch for ch in s if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits)) if digits else 1

def day_power(match_date: date) -> int:
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(match_date.weekday(),1)
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)

def place_power(place_name: str) -> int:
    s = safe_str(place_name)
    if not s:
        return 1
    total = sum(PYTH_MAP.get(ch.upper(),0) for ch in s if ch.isalpha())
    return min(reduce_num(total), 10)

# Toss methods (unchanged)
def toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp):
    a_good = (a_lp, date_lp) in good_pairs
    b_good = (b_lp, date_lp) in good_pairs
    if a_good and not b_good:
        return f"Captain A ({a_name}) - Good Numerology Pair"
    if b_good and not a_good:
        return f"Captain B ({b_name}) - Good Numerology Pair"
    return "Neutral - Balanced Numerology"

def toss_method_2_horary_ruler(a_name, b_name, day_lord_num, a_bno, b_bno):
    a_match = (a_bno, day_lord_num) in good_pairs
    b_match = (b_bno, day_lord_num) in good_pairs
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Day Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Day Lord Match"
    return "Neutral - Day Lord Tie"

def toss_method_3_star_lord(a_name, b_name, star_lord_num, a_nn, b_nn):
    a_match = (a_nn, star_lord_num) in good_pairs
    b_match = (b_nn, star_lord_num) in good_pairs
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Star Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Star Lord Match"
    return "Neutral - Star Lord Tie"

def toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno):
    ruling_no = reduce_num(dp + pp)
    a_diff = abs(a_bno - ruling_no)
    b_diff = abs(b_bno - ruling_no)
    if a_diff < b_diff:
        return f"Captain A ({a_name}) - Closer to Ruling No. ({ruling_no})"
    if b_diff < a_diff:
        return f"Captain B ({b_name}) - Closer to Ruling No. ({ruling_no})"
    return "Neutral - Ruling No. Proximity Tie"

def toss_method_5_compound_score(a_name, b_name, a_score, b_score):
    if a_score > b_score:
        return f"Captain A ({a_name}) - Match Score Advantage ({a_score} > {b_score})"
    if b_score > a_score:
        return f"Captain B ({b_name}) - Match Score Advantage ({b_score} > {a_score})"
    return "Neutral - Compound Score Tie"

def toss_method_6_moon_sign_lord(a_name, b_name, moon_lord_num, a_bno, b_bno):
    a_match = (a_bno, moon_lord_num) in good_pairs
    b_match = (b_bno, moon_lord_num) in good_pairs
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Moon Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Moon Lord Match"
    return "Neutral - Moon Lord Tie"

def toss_method_7_planetary_hour(a_name, b_name, a_bno, b_bno, match_hour):
    try:
        match_hour = int(match_hour) % 24
    except:
        match_hour = 6
    if match_hour % 2 == 0:
        if a_bno > b_bno:
            return f"Captain A ({a_name}) - PHI Advantage"
        if b_bno > a_bno:
            return f"Captain B ({b_name}) - PHI Advantage"
    else:
        if a_bno < b_bno:
            return f"Captain A ({a_name}) - PHI Advantage"
        if b_bno < a_bno:
            return f"Captain B ({b_name}) - PHI Advantage"
    return "Neutral - PHI Tie"

def toss_method_8_elemental(a_name, b_name, a_lp, b_lp, match_day_no):
    elements = ['Fire','Earth','Air','Water']
    a_elem = elements[a_lp % 4]
    b_elem = elements[b_lp % 4]
    match_elem = elements[match_day_no % 4]
    if a_elem == match_elem and b_elem != match_elem:
        return f"Captain A ({a_name}) - Elemental Match"
    if b_elem == match_elem and a_elem != match_elem:
        return f"Captain B ({b_name}) - Elemental Match"
    return "Neutral - Elemental Tie"

def final_toss_prediction(toss_results: Dict[str,str]) -> str:
    a_wins = b_wins = 0
    a_name = b_name = ""
    for result in toss_results.values():
        if isinstance(result, str) and result.startswith("Captain A"):
            a_wins += 1
            if not a_name and '(' in result:
                a_name = result.split('(')[1].split(')')[0].strip()
        elif isinstance(result, str) and result.startswith("Captain B"):
            b_wins += 1
            if not b_name and '(' in result:
                b_name = result.split('(')[1].split(')')[0].strip()
    if a_wins > b_wins:
        return f"Captain A ({a_name}) - Majority ({a_wins}-{b_wins})"
    if b_wins > a_wins:
        return f"Captain B ({b_name}) - Majority ({b_wins}-{a_wins})"
    return f"Neutral ({a_wins}-{b_wins})"

def extract_name_from_final(final_toss_str: str) -> str:
    s = safe_str(final_toss_str)
    if '(' in s and ')' in s:
        try:
            return s.split('(')[1].split(')')[0].strip()
        except:
            return s
    if "Captain A" in s:
        return "A"
    if "Captain B" in s:
        return "B"
    return s

def predict_innings_trend(score, lp, nn, dp, pp, is_winner):
    start_score = dp + pp
    if start_score >= 14:
        start = "Strong start"
    elif start_score >= 8:
        start = "Steady start"
    else:
        start = "Slow start"
    middle = "Dominant middle" if nn >= 5 else "Balanced middle"
    end = "Decisive finish" if is_winner else "Below-par finish"
    return f"{start} → {middle} → {end}"

# ---------------------------
# Main routine
# ---------------------------
def main():
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Method stats file: {METHOD_STATS_FILE}")

    # --- NEW DEBUG: ABSOLUTE PATH CHECK ---
    full_path = os.path.abspath(INPUT_FILE)
    if not os.path.exists(INPUT_FILE):
        print(f"\nFATAL ERROR: Input file '{INPUT_FILE}' not found at path: {full_path}")
        sys.exit(1)
    
    print(f"\nDEBUG: Script is reading from the ABSOLUTE path: {full_path}")
    # --- END NEW DEBUG ---

    # Read the input workbook, preserving Timestamp as text where possible
    try:
        # Use converters to coerce Timestamp into string form (keeps blanks as NaN)
        df = pd.read_excel(INPUT_FILE, dtype={TIMESTAMP_COL: str})
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    # --- NEW DEBUG: DATAFRAME SIZE CHECK ---
    total_rows_loaded = len(df)
    print(f"DEBUG: pandas successfully loaded a DataFrame with {total_rows_loaded} rows.")
    # --- END NEW DEBUG ---


    # Ensure expected columns exist (don't modify original df content)
    for col in ['Captain_A_Name','Captain_B_Name','Captain_A_DOB','Captain_B_DOB',
                 'Match_Date','Match_Time','Match_Place','Match_Format','Real_Toss','Real_Match','TZ_Offset_Hours']:
        if col not in df.columns:
            df[col] = ''

    # Parse Timestamp safely for each row, but do NOT write back to the input file
    parsed_dt_list = []
    parsed_has_time = []

    # We'll iterate row-wise to keep behavior consistent
    for idx, val in df[TIMESTAMP_COL].items():
        dt, has_time = safe_parse_timestamp(val)
        parsed_dt_list.append(dt)
        parsed_has_time.append(has_time)

    # Build a cleaned Timestamp column for the output (but we will not overwrite the original input file)
    cleaned_timestamps = [format_timestamp(dt, has_time) for dt, has_time in zip(parsed_dt_list, parsed_has_time)]

    # Main processing loop (backtest + predictions) — same logic but using parsed dt for match hour if needed
    results = []
    toss_correct_count = 0
    match_correct_count = 0
    total_rows = len(df) # This is 6 in your current output

    for idx, row in df.iterrows():
        try:
            a_name = safe_str(row['Captain_A_Name'])
            b_name = safe_str(row['Captain_B_Name'])
            a_dob = safe_str(row['Captain_A_DOB'])
            b_dob = safe_str(row['Captain_B_DOB'])
            match_date_raw = safe_str(row['Match_Date'])
            match_time_raw = safe_str(row.get('Match_Time',''))
            match_place = safe_str(row['Match_Place'])
            match_format = safe_str(row['Match_Format']).upper()
            tz_offset = float(row.get('TZ_Offset_Hours',0.0) or 0.0)

            # For toss methods that need a match hour, prefer:
            # - If Timestamp was present and had time, use it
            # - Else try Match_Date/Match_Time parsing
            match_hour = 6
            parsed_ts = parsed_dt_list[idx]
            parsed_ts_has_time = parsed_has_time[idx]
            if parsed_ts is not None and parsed_ts_has_time:
                match_hour = parsed_ts.hour
                match_date = parsed_ts.date()
            else:
                # Fallback: try to parse Match_Date / Match_Time (simple attempts)
                # Try a few common formats, but never raise
                try:
                    if match_date_raw and match_time_raw:
                        tmp = pd.to_datetime(match_date_raw + " " + match_time_raw, dayfirst=True, errors='coerce')
                    else:
                        tmp = pd.to_datetime(match_date_raw, dayfirst=True, errors='coerce')
                    if pd.notna(tmp):
                        tmp = tmp.to_pydatetime()
                        match_date = tmp.date()
                        match_hour = tmp.hour
                    else:
                        # ultimate fallback: today's date and default hour
                        match_date = date.today()
                        match_hour = 6
                except:
                    match_date = date.today()
                    match_hour = 6

            a_bno = birth_number(a_dob)
            b_bno = birth_number(b_dob)
            a_lp = life_path_number(a_dob)
            b_lp = life_path_number(b_dob)
            a_nn = name_number(a_name)
            b_nn = name_number(b_name)
            dp = day_power(match_date)
            pp = place_power(match_place)
            date_lp = date_life_path(match_date_raw)

            score_a = a_lp + a_nn + dp + pp
            score_b = b_lp + b_nn + dp + pp

            toss_results = {}
            toss_results['Numerology'] = toss_method_1_numerology(a_name,b_name,a_lp,b_lp,date_lp)
            toss_results['Horary_Ruler'] = toss_method_2_horary_ruler(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Star_Lord'] = toss_method_3_star_lord(a_name,b_name,pp,a_nn,b_nn)
            toss_results['Ruling_No'] = toss_method_4_ruling_no(a_name,b_name,dp,pp,a_bno,b_bno)
            toss_results['Compound_Score'] = toss_method_5_compound_score(a_name,b_name,score_a,score_b)
            toss_results['Moon_Lord'] = toss_method_6_moon_sign_lord(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Planetary_Hour'] = toss_method_7_planetary_hour(a_name,b_name,a_bno,b_bno,match_hour)
            toss_results['Elemental'] = toss_method_8_elemental(a_name,b_name,a_lp,b_lp,dp)

            final_toss = final_toss_prediction(toss_results)
            predicted_toss_name = extract_name_from_final(final_toss)

            if score_a > score_b:
                predicted_match_name = a_name
                is_a_winner = True
            else:
                predicted_match_name = b_name
                is_a_winner = False

            innings_trend_a = predict_innings_trend(score_a,a_lp,a_nn,dp,pp,is_a_winner)
            innings_trend_b = predict_innings_trend(score_b,b_lp,b_nn,dp,pp,not is_a_winner)

            actual_toss = safe_str(row.get('Real_Toss','')).strip()
            actual_match = safe_str(row.get('Real_Match','')).strip()
            toss_correct = actual_toss.lower() == predicted_toss_name.lower() if actual_toss else False
            match_correct = actual_match.lower() == predicted_match_name.lower() if actual_match else False
            if toss_correct:
                toss_correct_count += 1
            if match_correct:
                match_correct_count += 1

            results.append({
                'Predicted_Toss_Name': predicted_toss_name,
                'Final_Toss_String': final_toss,
                'Predicted_Match_Name': predicted_match_name,
                'Innings_Trend_A': innings_trend_a,
                'Innings_Trend_B': innings_trend_b,
                'Score_A': score_a,
                'Score_B': score_b,
                'Actual_Toss': actual_toss,
                'Actual_Match': actual_match,
                'Toss_Correct': toss_correct,
                'Match_Correct': match_correct
            })
            
            # --- DEBUG BLOCK: PRINTING RESULTS FOR THE LAST ROW ---
            if idx == total_rows - 1: # Check if this is the last row loaded
                print("\n--- DEBUG: PROCESSING LAST ROW (INDEX %d) ---" % idx)
                print(f"Input: Captain A: {a_name}, Captain B: {b_name}")
                print(f"Input: Match Date: {match_date_raw}, Time: {match_time_raw}")
                print(f"Numerology Scores: Captain A Score: {score_a}, Captain B Score: {score_b}")
                print(f"Match Params: Day Power (dp): {dp}, Place Power (pp): {pp}, Match Hour: {match_hour}")
                print(f"Final Toss Prediction: {final_toss}")
                print(f"Predicted Match Winner: {predicted_match_name}")
                print("-------------------------------------------\n")
            # --- END DEBUG BLOCK ---
            
        except Exception as e:
            # On error for a row, record blank/ERROR in results but never skip
            results.append({
                'Predicted_Toss_Name':'',
                'Final_Toss_String': f"ROW ERROR: {e}",
                'Predicted_Match_Name':'',
                'Innings_Trend_A':'',
                'Innings_Trend_B':'',
                'Score_A':'',
                'Score_B':'',
                'Actual_Toss':safe_str(row.get('Real_Toss','')),
                'Actual_Match':safe_str(row.get('Real_Match','')),
                'Toss_Correct':False,
                'Match_Correct':False
            })

    # Create DataFrames for output
    results_df = pd.DataFrame(results)
    total = max(total_rows,1)
    toss_acc = (toss_correct_count/total)*100
    match_acc = (match_correct_count/total)*100
    summary_df = pd.DataFrame([{
        'Total_Rows':total,
        'Toss_Correct_Count':toss_correct_count,
        'Match_Correct_Count':match_correct_count,
        'Toss_Accuracy_%':round(toss_acc,2),
        'Match_Accuracy_%':round(match_acc,2)
    }])

    # Prepare an output copy of the input with a cleaned Timestamp column added (but do NOT write input file)
    out_df = df.copy(deep=True)
    out_df[TIMESTAMP_COL + "_Clean"] = cleaned_timestamps

    # Write output workbook (separate file)
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='w') as writer:
            out_df.to_excel(writer, index=False, sheet_name='Input_with_Predictions')
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')

        print(f"Backtest complete. Output written to: {OUTPUT_FILE}")
        print(f" Toss accuracy: {round(toss_acc,2)}%  Match accuracy: {round(match_acc,2)}%")
    except Exception as we:
        print(f"Failed to write output: {we}")
        sys.exit(1)

if __name__ == '__main__':
    main()