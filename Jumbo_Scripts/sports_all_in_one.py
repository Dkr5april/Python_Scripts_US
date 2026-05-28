#!/usr/bin/env python3
"""
Multi-Mode Match Predictor (Numerology + Swiss Ephemeris)

This refactored script maintains the original calculation logic but separates 
the core analytical process from the interactive user input and output display, 
improving code organization and readability.

- Writes a detailed Excel file (pandas + openpyxl) and concise console reports.
- Requires: pandas, openpyxl, pyswisseph (swisseph), colorama

Usage: run `python match_predictor.py` and follow prompts.
"""

import sys
import os
import math
from datetime import datetime, date, time, timedelta
import pandas as pd

# --- Library Setup ---
try:
    import swisseph as swe
    SWE_AVAILABLE = True
except Exception:
    SWE_AVAILABLE = False

# Optional colored console output
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COL_OK = Fore.GREEN
    COL_WARN = Fore.YELLOW
    COL_ERR = Fore.RED
    COL_INFO = Fore.CYAN
    COL_BOLD = Style.BRIGHT
except Exception:
    COL_OK = COL_WARN = COL_ERR = COL_INFO = COL_BOLD = ''

# --- Numerology & Astrology Constants ---
SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashirsha","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

NAKSHATRA_LORDS = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
]

SIGN_LORDS = {
    "Aries": 'Mars', "Taurus": 'Venus', "Gemini": 'Mercury', 
    "Cancer": 'Moon', "Leo": 'Sun', "Virgo": 'Mercury', 
    "Libra": 'Venus', "Scorpio": 'Mars', "Sagittarius": 'Jupiter', 
    "Capricorn": 'Saturn', "Aquarius": 'Saturn', "Pisces": 'Jupiter'
}

PLANET_NUMBERS = {
    'Sun': 1, 'Moon': 2, 'Jupiter': 3, 'Rahu': 4, 'Mercury': 5, 
    'Venus': 6, 'Ketu': 7, 'Saturn': 8, 'Mars': 9, 'Neptune': 7, 'Uranus': 4, 'Pluto': 9
}

DAY_LORDS = {
    0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun',
}

PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

GOOD_PAIRS = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

# Weighted toss settings
TOSS_METHOD_WEIGHTS = {
    'Toss_Method_1_Numerology': 1.0,
    'Toss_Method_2_Horary_Ruler': 0.8,
    'Toss_Method_3_Star_Lord': 1.0,
    'Toss_Method_4_Ruling_No': 0.9,
    'Toss_Method_5_Compound_Score': 1.2,
    'Toss_Method_6_Moon_Sign_Lord': 0.8,
}
STRONG_CONFIDENCE_THRESHOLD = 3.0
MODERATE_CONFIDENCE_THRESHOLD = 1.0
UNPREDICTABLE_MARGIN = 1.0

# -----------------------
# Core Numerology Helpers
# -----------------------

def reduce_num(n: int) -> int:
    """Reduces a number to a single digit (1-9)."""
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n


def birth_number(dob_str: str) -> int:
    """Calculates Birth Number from DOB day."""
    try:
        dt = datetime.strptime(dob_str, "%d/%m/%Y")
        return reduce_num(dt.day)
    except Exception:
        # Fallback if parsing fails
        digits = ''.join(ch for ch in dob_str if ch.isdigit())
        return reduce_num(sum(int(c) for c in digits) if digits else 1)


def life_path_number(dob_str: str) -> int:
    """Calculates Life Path Number from full DOB."""
    digits = ''.join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))


def name_number(name: str) -> int:
    """Calculates Name Number (Pythagorean method)."""
    s = 0
    for ch in name.upper():
        if ch.isalpha():
            s += PYTH_MAP.get(ch, 0)
    return reduce_num(s)


def date_life_path(date_str: str) -> int:
    """Calculates the Life Path Number of a given date."""
    digits = ''.join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))


def day_power(match_date: date) -> int:
    """Calculates the single-day power score."""
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    # The original logic used match_date.year directly here, keeping that.
    lp = reduce_num(match_date.day + match_date.month + match_date.year) 
    weekday = match_date.weekday()
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1)
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)


def place_power(place_name: str) -> int:
    """Calculates the numerological power of the venue name."""
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
    return min(reduce_num(s), 10)


def calculate_five_day_power(start_date: date, place_name: str) -> tuple:
    """Calculates average day power over 5 days for test matches."""
    place_p = place_power(place_name)
    total_day_power = 0
    for i in range(5):
        total_day_power += day_power(start_date + timedelta(days=i))
    # Return average day power and place power
    return round(total_day_power / 5), place_p

# -----------------------
# Astronomy Helpers (Swiss Ephemeris)
# -----------------------

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    """Converts local datetime and TZ offset to Julian Day (JD) UTC."""
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    time_fraction = (dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0) / 24.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, time_fraction)


def sign_from_long(lon_deg):
    """Determines zodiac sign and degree within sign from longitude."""
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30


def moon_nakshatra_pada(moon_lon):
    """Determines Nakshatra, its lord, and the Pada from Moon's longitude."""
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada, "lord": lord}

# -----------------------
# Toss Methods (The core prediction logic)
# -----------------------

def toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp):
    """Compares captain's Life Path (LP) to the Match Date LP."""
    a_good = (a_lp, date_lp) in GOOD_PAIRS
    b_good = (b_lp, date_lp) in GOOD_PAIRS
    if a_good and not b_good:
        return f"Captain A ({a_name}) - Good Numerology Pair"
    if b_good and not a_good:
        return f"Captain B ({b_name}) - Good Numerology Pair"
    return "Neutral - Balanced Numerology"


def toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno):
    """Compares captain's Birth Number (BNO) to the Day Lord."""
    day_lord_num = PLANET_NUMBERS.get(day_lord_planet, 0)
    a_match = (a_bno, day_lord_num) in GOOD_PAIRS
    b_match = (b_bno, day_lord_num) in GOOD_PAIRS
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Day Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Day Lord Match"
    return "Neutral - Day Lord Tie"


def toss_method_3_star_lord(a_name, b_name, nak_lord_planet, a_nn, b_nn):
    """Compares captain's Name Number (NN) to the Nakshatra Star Lord."""
    nak_lord_num = PLANET_NUMBERS.get(nak_lord_planet, 0)
    a_match = (a_nn, nak_lord_num) in GOOD_PAIRS
    b_match = (b_nn, nak_lord_num) in GOOD_PAIRS
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Star Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Star Lord Match"
    return "Neutral - Star Lord Tie"


def toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno):
    """Compares captain's Birth Number (BNO) to the Ruling Number (DP+PP)."""
    ruling_no = reduce_num(dp + pp)
    a_diff = abs(a_bno - ruling_no)
    b_diff = abs(b_bno - ruling_no)
    if a_diff < b_diff:
        return f"Captain A ({a_name}) - Closer to Ruling No. ({ruling_no})"
    if b_diff < a_diff:
        return f"Captain B ({b_name}) - Closer to Ruling No. ({ruling_no})"
    return "Neutral - Ruling No. Proximity Tie"


def toss_method_5_compound_score(a_name, b_name, a_score, b_score):
    """Determines winner based on overall compound score advantage."""
    if a_score > b_score:
        return f"Captain A ({a_name}) - Match Score Advantage ({a_score} > {b_score})"
    if b_score > a_score:
        return f"Captain B ({b_name}) - Match Score Advantage ({b_score} > {a_score})"
    return "Neutral - Compound Score Tie"


def toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno):
    """Compares captain's Birth Number (BNO) to the Moon Sign Lord."""
    moon_lord_num = PLANET_NUMBERS.get(moon_sign_lord_planet, 0)
    a_match = (a_bno, moon_lord_num) in GOOD_PAIRS
    b_match = (b_bno, moon_lord_num) in GOOD_PAIRS
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Moon Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Moon Lord Match"
    return "Neutral - Moon Lord Tie"

# -----------------------
# Weighted Final Toss & Scoring Helpers
# -----------------------

def _method_winner_label(result_str):
    """Parses a toss result string to return 'A', 'B', or None."""
    if result_str.startswith("Captain A"):
        return 'A'
    if result_str.startswith("Captain B"):
        return 'B'
    return None


def final_toss_prediction_weighted(toss_results: dict, a_name: str, b_name: str):
    """Calculates final toss winner based on weighted method scores."""
    a_weight = 0.0
    b_weight = 0.0
    details = []
    
    # Sum weights for each team
    for method, res in toss_results.items():
        w = TOSS_METHOD_WEIGHTS.get(method, 1.0)
        winner = _method_winner_label(res)
        if winner == 'A':
            a_weight += w
            details.append((method, 'A', w))
        elif winner == 'B':
            b_weight += w
            details.append((method, 'B', w))
        else:
            details.append((method, 'Neutral', w))

    weighted_diff = a_weight - b_weight
    abs_diff = abs(weighted_diff)
    
    final_label, confidence, explanation = "", round(abs_diff, 2), ""
    
    if abs_diff <= UNPREDICTABLE_MARGIN:
        final_label = "Unpredictable"
        explanation = f"Weighted difference is small ({a_weight:.2f} vs {b_weight:.2f}); toss effectively random/low-confidence."
    else:
        winner_label = f"Captain A ({a_name})" if weighted_diff > 0 else f"Captain B ({b_name})"
        
        if abs_diff >= STRONG_CONFIDENCE_THRESHOLD:
            final_label = f"{winner_label} — Strong"
            explanation = f"Weighted difference high ({a_weight:.2f} vs {b_weight:.2f})."
        elif abs_diff >= MODERATE_CONFIDENCE_THRESHOLD:
            final_label = f"{winner_label} — Moderate"
            explanation = f"Weighted difference moderate ({a_weight:.2f} vs {b_weight:.2f})."
        else:
            final_label = "Unpredictable"
            explanation = f"Weighted difference small ({a_weight:.2f} vs {b_weight:.2f})."

    # Combine method details into the explanation
    detail_str = "; ".join([f"{m}:{lab}({w})" for (m, lab, w) in details])
    explanation = explanation + " Methods: " + detail_str
    
    return final_label, confidence, explanation


def predict_innings_trend(match_score: int, lp: int, nn: int, dp: int, pp: int, is_winner: bool) -> str:
    """Predicts the match flow (start, middle, end) based on scores."""
    start_score = dp + pp
    
    if start_score >= 14:
        start = "Strong start"
    elif start_score >= 8:
        start = "Steady start"
    else:
        start = "Slow start"
        
    score_influence = 1 if match_score > 35 else 0
    if nn + score_influence >= 8:
        middle = "Dominant middle"
    elif nn >= 4:
        middle = "Balanced middle"
    else:
        middle = "Wicket clusters"
        
    if is_winner:
        end = "Decisive finish"
    else:
        end = "Competitive finish" if lp >= 6 else "Below-par finish"
        
    return f"{start} → {middle} → {end}"


def score_range_from_advantage(diff:int) -> str:
    """Estimates the typical T20 score range based on the score difference."""
    # diff = score_a - score_b
    if diff >= 6:
        return "180 - 200+"
    if diff > 0:
        return "165 - 185"
    return "155 - 175"
# -----------------------
# Smart Input Cache System
# -----------------------
import json

CACHE_FILE = "predictor_cache.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"names": [], "dobs": [], "places": [], "formats": []}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"names": [], "dobs": [], "places": [], "formats": []}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

CACHE = load_cache()

def cache_add(key, value):
    """Adds a value to cache list without duplicates."""
    value = value.strip()
    if value and value not in CACHE[key]:
        CACHE[key].append(value)
        save_cache(CACHE)

def smart_input(prompt, key=None):
    """Enhanced input with history suggestions."""
    raw = input(prompt).strip()

    # If cache list available, show suggestions
    if key and raw:
        matches = [x for x in CACHE[key] if x.lower().startswith(raw.lower())]
        if matches:
            print("Suggestions:")
            for i, m in enumerate(matches, 1):
                print(f"  {i}) {m}")

            sel = input("Select number or press Enter to keep your input: ").strip()
            if sel.isdigit():
                num = int(sel)
                if 1 <= num <= len(matches):
                    raw = matches[num-1]

    # Save to cache
    if key and raw:
        cache_add(key, raw)

    return raw


# -----------------------
# Input Validation Helpers
# -----------------------

def safe_input(prompt, default=None):
    """Handles user input safely, returning default on empty input or EOF."""
    try:
        val = input(prompt)
        if val.strip() == '' and default is not None:
            return default
        return val.strip()
    except EOFError:
        return default


def parse_date_str(s:str) -> date:
    """Parses DD/MM/YYYY string to a date object."""
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        raise ValueError("Date must be DD/MM/YYYY")


def parse_time_str(s:str) -> time:
    """Parses HH:MM or HH:MM:SS string to a time object."""
    try:
        if ':' in s:
            fmt = "%H:%M:%S" if s.count(':')==2 else "%H:%M"
            return datetime.strptime(s, fmt).time()
        else:
            raise ValueError
    except Exception:
        raise ValueError("Time must be HH:MM or HH:MM:SS (24-hour)")

# -----------------------
# Core Analysis Function (Refactored Logic)
# -----------------------

def perform_match_analysis(a_name: str, a_dob: str, b_name: str, b_dob: str, 
                          m_date: str, m_time: str, m_place: str, m_format: str, 
                          tz_offset: float, use_astrology: bool):
    """
    Performs all numerology, astrology, and prediction calculations.
    Returns the comprehensive analysis data.
    """
    match_date = parse_date_str(m_date)
    match_time = parse_time_str(m_time)
    match_date_str = match_date.strftime("%d/%m/%Y")
    
    # 1. Numerology Calculations
    date_lp = date_life_path(match_date_str)
    a_bno = birth_number(a_dob); a_lp = life_path_number(a_dob); a_nn = name_number(a_name)
    b_bno = birth_number(b_dob); b_lp = life_path_number(b_dob); b_nn = name_number(b_name)

    # Day/Place Power (DP, PP)
    if m_format == 'TEST':
        dp, pp = calculate_five_day_power(match_date, m_place)
    else:
        dp = day_power(match_date)
        pp = place_power(m_place)

    # Compound Match Score
    score_a = sum([a_lp, a_nn, dp, pp])
    score_b = sum([b_lp, b_nn, dp, pp])

    # 2. Astrology Setup
    moon_lon = 0.0
    nak_info = {"nakshatra": "N/A", "lord": "Ketu", "pada": "N/A"}
    moon_sign = SIGNS[0]
    moon_sign_lord_planet = SIGN_LORDS.get(moon_sign, 'Mars')
    day_lord_planet = DAY_LORDS.get(match_date.weekday(), 'Sun')

    # 3. Astrology Computations (Only if enabled and library available)
    if use_astrology and SWE_AVAILABLE:
        try:
            local_dt = datetime.combine(match_date, match_time)
            jd_utc = to_utc_jd_from_datetime(local_dt, tz_offset)
            moon_pos = swe.calc_ut(jd_utc, swe.MOON)[0][0]
            moon_lon = moon_pos % 360
            nak_info = moon_nakshatra_pada(moon_lon)
            moon_sign = sign_from_long(moon_lon)[0]
            moon_sign_lord_planet = SIGN_LORDS.get(moon_sign, 'Mars')
        except Exception as e:
            # Error during calculation, use defaults but warn
            print(COL_WARN + f"Astro calc failed, falling back to defaults: {e}")

    # 4. Toss Predictions (6 Methods)
    toss_results = {}
    toss_results['Toss_Method_1_Numerology'] = toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp)
    toss_results['Toss_Method_2_Horary_Ruler'] = toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno)
    toss_results['Toss_Method_3_Star_Lord'] = toss_method_3_star_lord(a_name, b_name, nak_info.get('lord','Ketu'), a_nn, b_nn)
    toss_results['Toss_Method_4_Ruling_No'] = toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno)
    toss_results['Toss_Method_5_Compound_Score'] = toss_method_5_compound_score(a_name, b_name, score_a, score_b)
    toss_results['Toss_Method_6_Moon_Sign_Lord'] = toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno)

    # 5. Final Toss Prediction
    final_toss_label, toss_confidence, toss_explanation = final_toss_prediction_weighted(toss_results, a_name, b_name)

    # 6. Match Advantage & Score Range
    if score_a > score_b + 5:
        advantage = f"Captain A ({a_name}) - Strong Advantage"
    elif score_a > score_b:
        advantage = f"Captain A ({a_name}) - Advantage"
    elif score_b > score_a + 5:
        advantage = f"Captain B ({b_name}) - Strong Advantage"
    elif score_b > score_a:
        advantage = f"Captain B ({b_name}) - Advantage"
    else:
        advantage = "Neutral / Balanced"

    score_range = score_range_from_advantage(score_a - score_b)

    # 7. Innings Trend Prediction
    is_a_winner = score_a >= score_b
    is_b_winner = score_b >= score_a
    trend_a = predict_innings_trend(score_a, a_lp, a_nn, dp, pp, is_a_winner)
    trend_b = predict_innings_trend(score_b, b_lp, b_nn, dp, pp, is_b_winner)

    # 8. Build Output Structures
    concise_lines = [
        f"Toss Prediction: {final_toss_label} (Confidence: {toss_confidence})",
        f"Match Advantage: {advantage}",
        f"Predicted Score Range: {score_range}",
        f"Match Pattern A ({a_name}): {trend_a}",
        f"Match Pattern B ({b_name}): {trend_b}",
    ]

    out = {
        'Match_Date': match_date_str,
        'Match_Time': match_time.strftime("%H:%M"),
        'Match_Place': m_place,
        'Match_Format': m_format,
        'Captain_A_Name': a_name,
        'Captain_A_DOB': a_dob,
        'A_Birth_No': a_bno,
        'A_LifePath': a_lp,
        'A_Name_No': a_nn,
        'Captain_B_Name': b_name,
        'Captain_B_DOB': b_dob,
        'B_Birth_No': b_bno,
        'B_LifePath': b_lp,
        'B_Name_No': b_nn,
        'Day_Power': dp,
        'Place_Power': pp,
        'Moon_Long': round(moon_lon, 2),
        'Moon_Nakshatra': nak_info.get('nakshatra'),
        'Moon_Nak_Lord': nak_info.get('lord'),
        'Moon_Sign': moon_sign,
        'Moon_Sign_Lord': moon_sign_lord_planet,
        'Date_LifePath': date_lp,
        'Score_A': score_a,
        'Score_B': score_b,
        'Advantage': advantage,
        'Score_Range': score_range,
        'Toss_Confidence': toss_confidence,
        'Toss_Prediction_Final': final_toss_label,
        'Toss_Explanation': toss_explanation,
        'Innings_Trend_A': trend_a,
        'Innings_Trend_B': trend_b,
    }

    return out, toss_results, concise_lines


# -----------------------
# Main Runnable Flow (Refactored I/O)
# -----------------------

def run_single_match_interactive():
    """Handles user interaction, input collection, and output display/export."""
    print(COL_BOLD + COL_INFO +
          "\n=== MATCH PREDICTOR: Single Match Interactive Mode ===\n")

    # --- Input Collection ---
    print("Choose input style:")
    print("1) Simple Prompt Mode")
    print("2) Console UI Mode (colored)")
    print("3) Menu-Driven Multi-Match (quick entry)")
    safe_input("Select 1/2/3 (default 1): ", "1") # Retained for compatibility but unused below

    ast_opt = safe_input("Enable real astrology (swisseph)? (y/n) [y]: ", "y").lower()
    use_astrology = ast_opt != 'n'
    if use_astrology and not SWE_AVAILABLE:
        print(COL_WARN + "swisseph not available; falling back to numerology.")
        use_astrology = False

    # Get basic inputs
    a_name = safe_input("Captain A name: ")
    a_dob = safe_input("Captain A DOB (DD/MM/YYYY): ")
    b_name = safe_input("Captain B name: ")
    b_dob = safe_input("Captain B DOB (DD/MM/YYYY): ")
    m_date = safe_input("Match Date (DD/MM/YYYY): ")
    m_time = safe_input("Match Time (HH:MM, 24h): ", "10:00")
    m_place = safe_input("Match Place: ")
    m_format = safe_input("Match Format (T20/ODI/TEST): ", "T20").upper()
    tz_offset_str = safe_input("Local timezone offset from UTC (hours, e.g. 10 for AEDT or -7): ", "0")

    # Parse and Validate
    try:
        tz_offset = float(tz_offset_str)
        match_date = parse_date_str(m_date) # Check date validity early
        match_time = parse_time_str(m_time) # Check time validity early
    except ValueError as e:
        print(COL_ERR + f"Input error: {e}")
        return

    # --- Core Analysis ---
    try:
        out, toss_results, concise_lines = perform_match_analysis(
            a_name, a_dob, b_name, b_dob, m_date, m_time, m_place, m_format, tz_offset, use_astrology
        )
    except Exception as e:
        print(COL_ERR + f"An error occurred during analysis: {e}")
        return
        
    # --- Output Selection ---
    print(COL_BOLD + COL_INFO + "\nChoose output style:")
    print("1) Short Console Report")
    print("2) Detailed Console Report")
    print("3) Excel Export Only")
    print("4) Both Console + Excel")
    
    out_choice = safe_input("Select 1/2/3/4 (default 4): ", "4")

    save_excel = out_choice in ['3','4']
    show_detailed = out_choice in ['2','4']
    show_short = out_choice in ['1','4']

    # --- Output Generation ---
    if show_short:
        print(COL_BOLD + "\n--- SHORT REPORT ---")
        for line in concise_lines:
            print(line)

    if show_detailed:
        print(COL_BOLD + "\n--- DETAILED REPORT ---")
        for k,v in out.items():
            print(f"{k}: {v}")
        print("\nToss Methods Breakdown:")
        for k,v in toss_results.items():
            print(f" {k}: {v}")

    # Save Excel
    if save_excel:
        safe_name = f"Report_{a_name.replace(' ','')}_vs_{b_name.replace(' ','')}_{match_date.strftime('%d-%m-%Y')}.xlsx"
        try:
            df_out = pd.DataFrame([out])
            
            with pd.ExcelWriter(safe_name, engine='openpyxl') as writer:
                # Input sheet (for completeness/audit)
                inp_df = pd.DataFrame([{ 
                    'Captain_A_Name': a_name, 'Captain_A_DOB': a_dob,
                    'Captain_B_Name': b_name, 'Captain_B_DOB': b_dob,
                    'Match_Date': m_date, 'Match_Time': m_time,
                    'Match_Place': m_place, 'Match_Format': m_format,
                    'TZ_Offset_Hours': tz_offset
                }])
                inp_df.to_excel(writer, sheet_name='Input_Data_Original', index=False)
                df_out.to_excel(writer, sheet_name='Analysis_Output', index=False)
                
            print(COL_OK + f"\nReport saved to: {safe_name}")
        except Exception as e:
            print(COL_ERR + f"Failed to write Excel: {e}")

    print(COL_INFO + "\nDone.\n")

# -----------------------
# Entry point
# -----------------------

def main():
    """Initial menu for selecting the operation mode."""
    print(COL_BOLD + COL_INFO + "Multi-Mode Match Predictor (Numerology + Astrology)")
    print("1) Run single interactive session")
    print("2) Run multiple entries (menu-driven)")
    print("3) Exit")
    choice = safe_input("Choose 1/2/3 (default 1): ", "1")
    if choice == '1':
        run_single_match_interactive()
    elif choice == '2':
        print("Multi-match mode not implemented in this release — running single mode.")
        run_single_match_interactive()
    else:
        print("Exiting.")

if __name__ == '__main__':
    main()