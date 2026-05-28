#!/usr/bin/env python3
"""
MASTER COMPLETE OFFLINE ASTRO–NUMEROLOGY & MATCH TREND SCRIPT
Reads match data from 'match_analysis_data.xlsx', calculates results,
and writes output back to the same file, appending new columns for analysis.
"""

import sys
import pandas as pd
from datetime import datetime, date, time, timedelta

# ---------------------------
# ANSI Color Codes
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
# Numerology Helpers
# ---------------------------
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),
    (9,3),(9,6),(9,9)
])

def reduce_num(n: int) -> int:
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    try:
        dt = datetime.strptime(dob_str, "%d/%m/%Y")
        return reduce_num(dt.day)
    except:
        return reduce_num(sum(int(c) for c in dob_str if c.isdigit()))

def life_path_number(dob_str: str) -> int:
    digits = "".join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def name_number(name: str) -> int:
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in name if ch.isalpha())
    return reduce_num(s)

def date_life_path(date_str: str) -> int:
    digits = "".join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def day_power(match_date: date) -> int:
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday = match_date.weekday()
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1)
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)

def place_power(place_name: str) -> int:
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in str(place_name) if ch.isalpha())
    return min(reduce_num(s), 10)

# ---------------------------
# Toss Prediction Helpers
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

def final_toss_prediction(toss_results):
    a_wins = b_wins = 0
    a_name = b_name = ""
    for result in toss_results.values():
        if result.startswith("Captain A"):
            a_wins += 1
            if not a_name and '(' in result: a_name = result.split('(')[1].split(')')[0].strip()
        elif result.startswith("Captain B"):
            b_wins += 1
            if not b_name and '(' in result: b_name = result.split('(')[1].split(')')[0].strip()
    if a_wins > b_wins:
        return f"Captain A ({a_name}) - Majority ({a_wins}-{b_wins})"
    if b_wins > a_wins:
        return f"Captain B ({b_name}) - Majority ({b_wins}-{a_wins})"
    return "Neutral - Tie/Mixed Results"

# ---------------------------
# Innings Trend Logic
# ---------------------------
def predict_innings_trend(score, lp, nn, dp, pp, is_winner):
    start_score = dp + pp
    start = "Strong start" if start_score >= 14 else "Balanced start"
    middle = "Dominant middle overs" if nn >= 5 else "Moderate middle overs"
    end = "Decisive finish" if is_winner else "Struggles in finish"
    return f"{start} → {middle} → {end}"

# ---------------------------
# Main Function
# ---------------------------
def main():
    input_file = "match_analysis_data.xlsx"
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    results_list = []

    for idx, row in df.iterrows():
        try:
            a_name = row.get('Captain_A_Name', f'TeamA_{idx}')
            b_name = row.get('Captain_B_Name', f'TeamB_{idx}')
            a_dob = row.get('Captain_A_DOB', '01/01/1980')
            b_dob = row.get('Captain_B_DOB', '01/01/1980')
            match_date_str = row.get('Match_Date', '01/01/2025')
            match_date = pd.to_datetime(match_date_str, dayfirst=True).date()
            match_place = row.get('Match_Place', 'Unknown')

            a_bno = birth_number(a_dob)
            b_bno = birth_number(b_dob)
            a_lp = life_path_number(a_dob)
            b_lp = life_path_number(b_dob)
            a_nn = name_number(a_name)
            b_nn = name_number(b_name)
            dp = day_power(match_date)
            pp = place_power(match_place)
            date_lp = date_life_path(match_date_str)

            toss_results = {}
            toss_results['Method1_Numerology'] = toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp)
            toss_results['Method2_HoraryRuler'] = toss_method_2_horary_ruler(a_name, b_name, dp, a_bno, b_bno)
            toss_results['Method3_StarLord'] = toss_method_3_star_lord(a_name, b_name, pp, a_nn, b_nn)
            toss_results['Method4_RulingNo'] = toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno)
            toss_results['Method5_CompoundScore'] = toss_method_5_compound_score(a_name, b_name, a_lp + a_nn, b_lp + b_nn)
            toss_results['Method6_MoonSignLord'] = toss_method_6_moon_sign_lord(a_name, b_name, dp, a_bno, b_bno)
            toss_results['FinalTossPrediction'] = final_toss_prediction(toss_results)

            innings_trend_a = predict_innings_trend(a_lp + a_nn, a_lp, a_nn, dp, pp, True)
            innings_trend_b = predict_innings_trend(b_lp + b_nn, b_lp, b_nn, dp, pp, False)

            results_list.append({
                **toss_results,
                "Innings_Trend_A": innings_trend_a,
                "Innings_Trend_B": innings_trend_b,
                "A_Match_Score": a_lp + a_nn,
                "B_Match_Score": b_lp + b_nn,
                "Overall_Advantage": "Team A" if a_lp + a_nn > b_lp + b_nn else "Team B"
            })

        except Exception as e:
            print(f"Skipping row {idx} due to error: {e}")
            results_list.append({})

    for col in results_list[0].keys():
        df[col] = [res.get(col, "") for res in results_list]

    output_file = "match_analysis_data_output.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Analysis complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()
