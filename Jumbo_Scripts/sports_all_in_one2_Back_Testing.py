#!/usr/bin/env python3
"""
Backtest-enabled Master Astrology & Numerology Script

Reads:  match_analysis_data.xlsx (expects columns provided below)
Writes: match_analysis_data_output.xlsx and also a new sheet "Backtest_Results"
in the same workbook with per-row comparisons and an overall accuracy summary.

Expected input columns (exact names):
Timestamp, Captain_A_Name, Captain_A_DOB, Captain_B_Name, Captain_B_DOB,
Match_Date, Match_Time, Match_Place, Match_Format, TZ_Offset_Hours,
Real_Toss, Real_Match

Real_Toss and Real_Match should contain full names (e.g. "Annabel Sutherland")
corresponding to either Captain A or Captain B (or team names if you prefer).
This script compares predicted captain-name strings to those Actual columns.
"""
import sys
import math
import pandas as pd
from datetime import datetime, date, time, timedelta
from typing import Dict

# ---------------------------
# Simple ANSI color helpers (optional)
# ---------------------------
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# ---------------------------
# Numerology & helper functions
# ---------------------------
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

def safe_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

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

# ---------------------------
# Toss prediction methods (string outputs)
# ---------------------------
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
    """Return the captain name contained in final toss string, or empty if none."""
    s = safe_str(final_toss_str)
    if '(' in s and ')' in s:
        try:
            return s.split('(')[1].split(')')[0].strip()
        except:
            return s
    # Fallback: try "Captain A" / "Captain B"
    if "Captain A" in s:
        return "A"
    if "Captain B" in s:
        return "B"
    return s

# ---------------------------
# Innings trend helper
# ---------------------------
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
# Main (backtest) routine
# ---------------------------
def main():
    input_file = "match_analysis_data.xlsx"
    output_file = "match_analysis_data_output.xlsx"
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"{Colors.FAIL}Failed to read '{input_file}': {e}{Colors.ENDC}")
        sys.exit(1)

    # Ensure required columns exist; fill NaNs for string columns
    string_cols = ['Captain_A_Name','Captain_B_Name','Captain_A_DOB','Captain_B_DOB',
                   'Match_Date','Match_Time','Match_Place','Match_Format','Real_Toss','Real_Match']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)
        else:
            # create missing columns as empty strings to avoid KeyError
            df[col] = ''

    results = []
    toss_correct_count = 0
    match_correct_count = 0
    total_rows = len(df)

    for idx, row in df.iterrows():
        try:
            # Read and sanitize input values
            a_name = safe_str(row.get('Captain_A_Name', '')).strip()
            b_name = safe_str(row.get('Captain_B_Name', '')).strip()
            a_dob = safe_str(row.get('Captain_A_DOB', '01/01/1980'))
            b_dob = safe_str(row.get('Captain_B_DOB', '01/01/1980'))
            match_date_raw = safe_str(row.get('Match_Date', '01/01/2025'))
            match_time_raw = safe_str(row.get('Match_Time', '06:00'))
            match_place = safe_str(row.get('Match_Place', 'Unknown'))
            match_format_raw = safe_str(row.get('Match_Format', 'T20')).upper()
            tz_offset = float(row.get('TZ_Offset_Hours', 0.0) or 0.0)

            # parse date
            try:
                match_dt = pd.to_datetime(match_date_raw, dayfirst=True)
                match_date = match_dt.date()
                match_date_str = match_dt.strftime("%d/%m/%Y")
            except:
                match_date = date.today()
                match_date_str = match_date.strftime("%d/%m/%Y")

            # numerology
            a_bno = birth_number(a_dob)
            b_bno = birth_number(b_dob)
            a_lp = life_path_number(a_dob)
            b_lp = life_path_number(b_dob)
            a_nn = name_number(a_name)
            b_nn = name_number(b_name)

            dp = day_power(match_date)
            pp = place_power(match_place)
            date_lp = date_life_path(match_date_str)

            # score proxies used for match-prediction
            score_a = a_lp + a_nn + dp + pp
            score_b = b_lp + b_nn + dp + pp

            # Toss method outputs
            toss_results = {}
            toss_results['Toss_Method_1_Numerology'] = toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp)
            toss_results['Toss_Method_2_Horary_Ruler'] = toss_method_2_horary_ruler(a_name, b_name, dp, a_bno, b_bno)
            toss_results['Toss_Method_3_Star_Lord'] = toss_method_3_star_lord(a_name, b_name, pp, a_nn, b_nn)
            toss_results['Toss_Method_4_Ruling_No'] = toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno)
            toss_results['Toss_Method_5_Compound_Score'] = toss_method_5_compound_score(a_name, b_name, score_a, score_b)
            toss_results['Toss_Method_6_Moon_Sign_Lord'] = toss_method_6_moon_sign_lord(a_name, b_name, dp, a_bno, b_bno)
            final_toss = final_toss_prediction(toss_results)
            predicted_toss_name = extract_name_from_final(final_toss)

            # Predicted match winner: higher score
            if score_a > score_b:
                predicted_match_name = a_name or "Captain A"
                is_a_winner = True
            elif score_b > score_a:
                predicted_match_name = b_name or "Captain B"
                is_a_winner = False
            else:
                # tie fallback
                predicted_match_name = a_name or b_name or "Tie"
                is_a_winner = None

            # Innings trend
            innings_trend_a = predict_innings_trend(score_a, a_lp, a_nn, dp, pp, is_a_winner is True)
            innings_trend_b = predict_innings_trend(score_b, b_lp, b_nn, dp, pp, is_a_winner is False)

            # Compare with actuals (string match, case-insensitive, trimmed)
            actual_toss = safe_str(row.get('Real_Toss', '')).strip()
            actual_match = safe_str(row.get('Real_Match', '')).strip()

            def normalize_name(s):
                return ' '.join(s.split()).lower()

            toss_correct = False
            match_correct = False
            if actual_toss:
                toss_correct = normalize_name(actual_toss) == normalize_name(predicted_toss_name)
            if actual_match:
                match_correct = normalize_name(actual_match) == normalize_name(predicted_match_name)

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

        except Exception as row_e:
            # keep row-level safety: record the error and continue
            results.append({
                'Predicted_Toss_Name': '',
                'Final_Toss_String': f"ERROR: {row_e}",
                'Predicted_Match_Name': '',
                'Innings_Trend_A': '',
                'Innings_Trend_B': '',
                'Score_A': '',
                'Score_B': '',
                'Actual_Toss': safe_str(row.get('Real_Toss','')),
                'Actual_Match': safe_str(row.get('Real_Match','')),
                'Toss_Correct': False,
                'Match_Correct': False
            })

    # Build results dataframe and summary
    results_df = pd.DataFrame(results)
    total = total_rows if total_rows>0 else 1
    toss_accuracy = (toss_correct_count/total)*100
    match_accuracy = (match_correct_count/total)*100

    summary = {
        'Total_Rows': [total],
        'Toss_Correct_Count': [toss_correct_count],
        'Match_Correct_Count': [match_correct_count],
        'Toss_Accuracy_%': [round(toss_accuracy,2)],
        'Match_Accuracy_%': [round(match_accuracy,2)]
    }
    summary_df = pd.DataFrame(summary)

    # Write outputs:
    # - main output file (input + appended prediction columns)
    # - new sheet Backtest_Results with per-row results and summary
    try:
        # append the results to original df copy (as columns)
        for col in results_df.columns:
            df[col] = results_df[col].values

        with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False, sheet_name='Input_with_Predictions')
            # write backtest results sheet
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')

        print(f"{Colors.OKGREEN}Backtest complete. Output written to: {output_file}{Colors.ENDC}")
        print(f" Toss accuracy: {round(toss_accuracy,2)}%  Match accuracy: {round(match_accuracy,2)}%")
    except Exception as write_e:
        print(f"{Colors.FAIL}Failed to write output: {write_e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
