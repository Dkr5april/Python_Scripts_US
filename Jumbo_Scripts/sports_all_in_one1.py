#!/usr/bin/env python3
"""
Multi-Mode Match Predictor (Numerology + Swiss Ephemeris)
Updated: smart input history + input logging + multi-match menu
"""

import sys
import os
import math
import json
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

# --- Numerology & Astrology Constants (unchanged) ---
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
DAY_LORDS = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
GOOD_PAIRS = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])
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
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    try:
        dt = datetime.strptime(dob_str, "%d/%m/%Y")
        return reduce_num(dt.day)
    except Exception:
        digits = ''.join(ch for ch in dob_str if ch.isdigit())
        return reduce_num(sum(int(c) for c in digits) if digits else 1)

def life_path_number(dob_str: str) -> int:
    digits = ''.join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def name_number(name: str) -> int:
    s = 0
    for ch in (name or "").upper():
        if ch.isalpha():
            s += PYTH_MAP.get(ch, 0)
    return reduce_num(s)

def date_life_path(date_str: str) -> int:
    digits = ''.join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def day_power(match_date: date) -> int:
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday = match_date.weekday()
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1)
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)

def place_power(place_name: str) -> int:
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in (place_name or "") if ch.isalpha())
    return min(reduce_num(s), 10)

def calculate_five_day_power(start_date: date, place_name: str) -> tuple:
    place_p = place_power(place_name)
    total_day_power = 0
    for i in range(5):
        total_day_power += day_power(start_date + timedelta(days=i))
    return round(total_day_power / 5), place_p

# -----------------------
# Astronomy Helpers (Swiss Ephemeris)
# -----------------------
def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    time_fraction = (dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0) / 24.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, time_fraction)

def sign_from_long(lon_deg):
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada, "lord": lord}

# -----------------------
# Toss Methods (unchanged)
# -----------------------
def toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp):
    a_good = (a_lp, date_lp) in GOOD_PAIRS
    b_good = (b_lp, date_lp) in GOOD_PAIRS
    if a_good and not b_good:
        return f"Captain A ({a_name}) - Good Numerology Pair"
    if b_good and not a_good:
        return f"Captain B ({b_name}) - Good Numerology Pair"
    return "Neutral - Balanced Numerology"

def toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno):
    day_lord_num = PLANET_NUMBERS.get(day_lord_planet, 0)
    a_match = (a_bno, day_lord_num) in GOOD_PAIRS
    b_match = (b_bno, day_lord_num) in GOOD_PAIRS
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Day Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Day Lord Match"
    return "Neutral - Day Lord Tie"

def toss_method_3_star_lord(a_name, b_name, nak_lord_planet, a_nn, b_nn):
    nak_lord_num = PLANET_NUMBERS.get(nak_lord_planet, 0)
    a_match = (a_nn, nak_lord_num) in GOOD_PAIRS
    b_match = (b_nn, nak_lord_num) in GOOD_PAIRS
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

def toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno):
    moon_lord_num = PLANET_NUMBERS.get(moon_sign_lord_planet, 0)
    a_match = (a_bno, moon_lord_num) in GOOD_PAIRS
    b_match = (b_bno, moon_lord_num) in GOOD_PAIRS
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Moon Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Moon Lord Match"
    return "Neutral - Moon Lord Tie"

# -----------------------
# Weighted Final Toss & Scoring Helpers (unchanged)
# -----------------------
def _method_winner_label(result_str):
    if result_str.startswith("Captain A"):
        return 'A'
    if result_str.startswith("Captain B"):
        return 'B'
    return None

def final_toss_prediction_weighted(toss_results: dict, a_name: str, b_name: str):
    a_weight = 0.0
    b_weight = 0.0
    details = []
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
    detail_str = "; ".join([f"{m}:{lab}({w})" for (m, lab, w) in details])
    explanation = explanation + " Methods: " + detail_str
    return final_label, confidence, explanation

def predict_innings_trend(match_score: int, lp: int, nn: int, dp: int, pp: int, is_winner: bool) -> str:
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
    if diff >= 6:
        return "180 - 200+"
    if diff > 0:
        return "165 - 185"
    return "155 - 175"

# -----------------------
# Smart Input Cache System (improved)
# -----------------------
CACHE_FILE = "predictor_cache.json"
INPUT_LOG_CSV = "input_log.csv"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {"names": [], "dobs": [], "places": [], "formats": []}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"names": [], "dobs": [], "places": [], "formats": []}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

CACHE = load_cache()

def cache_add(key, value):
    value = (value or "").strip()
    if not value:
        return
    lst = CACHE.get(key, [])
    # avoid duplicates case-insensitive
    if not any(x.lower() == value.lower() for x in lst):
        lst.append(value)
        CACHE[key] = lst
        save_cache(CACHE)

def smart_input(prompt, key=None, default=None):
    """
    Enhanced input with history suggestions.
    - key: one of 'names','dobs','places','formats' to access cache.
    - default: fallback value when user presses Enter.
    """
    try:
        raw = input(prompt).strip()
    except EOFError:
        raw = ''

    # If user pressed enter and default provided use it
    if raw == '' and default is not None:
        raw = default

    # If cache key provided and a prefix typed, show suggestions
    if key and raw:
        matches = [x for x in CACHE.get(key, []) if x.lower().startswith(raw.lower())]
        if matches:
            print("Suggestions:")
            for i, m in enumerate(matches, 1):
                print(f"  {i}) {m}")
            sel = input("Select number or press Enter to keep your input: ").strip()
            if sel.isdigit():
                idx = int(sel) - 1
                if 0 <= idx < len(matches):
                    raw = matches[idx]

    # If key provided but the user typed nothing, optionally show all suggestions
    if key and raw == '' and CACHE.get(key):
        print("Previous entries:")
        for i, m in enumerate(CACHE.get(key, []), 1):
            print(f"  {i}) {m}")
        sel = input("Select number or press Enter to skip: ").strip()
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(CACHE[key]):
                raw = CACHE[key][idx]

    # Save to cache
    if key and raw:
        cache_add(key, raw)

    return raw

def append_input_log(entry: dict):
    """
    Append input entry to CSV input log. Creates file with header if missing.
    Stored columns: Timestamp, Captain_A_Name, Captain_A_DOB, Captain_B_Name, Captain_B_DOB,
    Match_Date, Match_Time, Match_Place, Match_Format, TZ_Offset_Hours
    """
    df_entry = pd.DataFrame([entry])
    header = not os.path.exists(INPUT_LOG_CSV)
    try:
        df_entry.to_csv(INPUT_LOG_CSV, mode='a', header=header, index=False, encoding='utf-8')
    except Exception as e:
        print(COL_WARN + f"Failed to append to input log: {e}")

# -----------------------
# Input Validation Helpers (unchanged)
# -----------------------
def safe_input(prompt, default=None):
    try:
        val = input(prompt)
        if val.strip() == '' and default is not None:
            return default
        return val.strip()
    except EOFError:
        return default

def parse_date_str(s:str) -> date:
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        raise ValueError("Date must be DD/MM/YYYY")

def parse_time_str(s:str) -> time:
    try:
        if ':' in s:
            fmt = "%H:%M:%S" if s.count(':')==2 else "%H:%M"
            return datetime.strptime(s, fmt).time()
        else:
            raise ValueError
    except Exception:
        raise ValueError("Time must be HH:MM or HH:MM:SS (24-hour)")

# -----------------------
# Core Analysis (unchanged aside from signature)
# -----------------------
def perform_match_analysis(a_name: str, a_dob: str, b_name: str, b_dob: str, 
                          m_date: str, m_time: str, m_place: str, m_format: str, 
                          tz_offset: float, use_astrology: bool):
    match_date = parse_date_str(m_date)
    match_time = parse_time_str(m_time)
    match_date_str = match_date.strftime("%d/%m/%Y")
    date_lp = date_life_path(match_date_str)
    a_bno = birth_number(a_dob); a_lp = life_path_number(a_dob); a_nn = name_number(a_name)
    b_bno = birth_number(b_dob); b_lp = life_path_number(b_dob); b_nn = name_number(b_name)
    if m_format == 'TEST':
        dp, pp = calculate_five_day_power(match_date, m_place)
    else:
        dp = day_power(match_date)
        pp = place_power(m_place)
    score_a = sum([a_lp, a_nn, dp, pp])
    score_b = sum([b_lp, b_nn, dp, pp])
    moon_lon = 0.0
    nak_info = {"nakshatra": "N/A", "lord": "Ketu", "pada": "N/A"}
    moon_sign = SIGNS[0]
    moon_sign_lord_planet = SIGN_LORDS.get(moon_sign, 'Mars')
    day_lord_planet = DAY_LORDS.get(match_date.weekday(), 'Sun')
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
            print(COL_WARN + f"Astro calc failed, falling back to defaults: {e}")
    toss_results = {}
    toss_results['Toss_Method_1_Numerology'] = toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp)
    toss_results['Toss_Method_2_Horary_Ruler'] = toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno)
    toss_results['Toss_Method_3_Star_Lord'] = toss_method_3_star_lord(a_name, b_name, nak_info.get('lord','Ketu'), a_nn, b_nn)
    toss_results['Toss_Method_4_Ruling_No'] = toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno)
    toss_results['Toss_Method_5_Compound_Score'] = toss_method_5_compound_score(a_name, b_name, score_a, score_b)
    toss_results['Toss_Method_6_Moon_Sign_Lord'] = toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno)
    final_toss_label, toss_confidence, toss_explanation = final_toss_prediction_weighted(toss_results, a_name, b_name)
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
    is_a_winner = score_a >= score_b
    is_b_winner = score_b >= score_a
    trend_a = predict_innings_trend(score_a, a_lp, a_nn, dp, pp, is_a_winner)
    trend_b = predict_innings_trend(score_b, b_lp, b_nn, dp, pp, is_b_winner)
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
# Interactive Routines
# -----------------------
def collect_single_match_interactive():
    """Collects input using smart_input where appropriate and returns the collected dict."""
    print(COL_BOLD + COL_INFO + "\n=== MATCH PREDICTOR: Single Match Interactive Mode ===\n")
    print("Choose input style:")
    print("1) Simple Prompt Mode")
    print("2) Console UI Mode (colored)")
    print("3) Menu-Driven Multi-Match (quick entry)")
    # keep compatibility but ignore selection for now
    _ = safe_input("Select 1/2/3 (default 1): ", "1")
    ast_opt = smart_input("Enable real astrology (swisseph)? (y/n) [y]: ", None, "y").lower()
    use_astrology = ast_opt != 'n'
    if use_astrology and not SWE_AVAILABLE:
        print(COL_WARN + "swisseph not available; falling back to numerology.")
        use_astrology = False
    # Use smart_input for cached fields
    a_name = smart_input("Captain A name: ", "names")
    a_dob = smart_input("Captain A DOB (DD/MM/YYYY): ", "dobs")
    b_name = smart_input("Captain B name: ", "names")
    b_dob = smart_input("Captain B DOB (DD/MM/YYYY): ", "dobs")
    m_date = smart_input("Match Date (DD/MM/YYYY): ", None)
    m_time = smart_input("Match Time (HH:MM, 24h): ", None, "10:00")
    m_place = smart_input("Match Place: ", "places")
    m_format = smart_input("Match Format (T20/ODI/TEST): ", "formats", "T20").upper()
    tz_offset_str = smart_input("Local timezone offset from UTC (hours, e.g. 10 for AEDT or -7): ", None, "0")
    # Validate
    try:
        tz_offset = float(tz_offset_str)
        match_date = parse_date_str(m_date)
        match_time = parse_time_str(m_time)
    except ValueError as e:
        print(COL_ERR + f"Input error: {e}")
        return None
    # Append input to persistent log
    entry = {
        "Timestamp": datetime.now().isoformat(),
        "Captain_A_Name": a_name, "Captain_A_DOB": a_dob,
        "Captain_B_Name": b_name, "Captain_B_DOB": b_dob,
        "Match_Date": m_date, "Match_Time": m_time,
        "Match_Place": m_place, "Match_Format": m_format,
        "TZ_Offset_Hours": tz_offset
    }
    append_input_log(entry)
    # Also cache the items
    cache_add("names", a_name); cache_add("dobs", a_dob)
    cache_add("names", b_name); cache_add("dobs", b_dob)
    cache_add("places", m_place); cache_add("formats", m_format)
    return {
        "a_name": a_name, "a_dob": a_dob, "b_name": b_name, "b_dob": b_dob,
        "m_date": m_date, "m_time": m_time, "m_place": m_place, "m_format": m_format,
        "tz_offset": tz_offset, "use_astrology": use_astrology
    }

def run_single_match_interactive():
    collected = collect_single_match_interactive()
    if not collected:
        return
    try:
        out, toss_results, concise_lines = perform_match_analysis(
            collected["a_name"], collected["a_dob"], collected["b_name"], collected["b_dob"],
            collected["m_date"], collected["m_time"], collected["m_place"], collected["m_format"],
            collected["tz_offset"], collected["use_astrology"]
        )
    except Exception as e:
        print(COL_ERR + f"An error occurred during analysis: {e}")
        return
    print(COL_BOLD + COL_INFO + "\nChoose output style:")
    print("1) Short Console Report")
    print("2) Detailed Console Report")
    print("3) Excel Export Only")
    print("4) Both Console + Excel")
    out_choice = safe_input("Select 1/2/3/4 (default 4): ", "4")
    save_excel = out_choice in ['3','4']
    show_detailed = out_choice in ['2','4']
    show_short = out_choice in ['1','4']
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
    if save_excel:
        safe_name = f"Report_{collected['a_name'].replace(' ','')}_vs_{collected['b_name'].replace(' ','')}_{datetime.strptime(collected['m_date'] , '%d/%m/%Y').strftime('%d-%m-%Y')}.xlsx"
        try:
            df_out = pd.DataFrame([out])
            with pd.ExcelWriter(safe_name, engine='openpyxl') as writer:
                inp_df = pd.DataFrame([{
                    'Captain_A_Name': collected['a_name'], 'Captain_A_DOB': collected['a_dob'],
                    'Captain_B_Name': collected['b_name'], 'Captain_B_DOB': collected['b_dob'],
                    'Match_Date': collected['m_date'], 'Match_Time': collected['m_time'],
                    'Match_Place': collected['m_place'], 'Match_Format': collected['m_format'],
                    'TZ_Offset_Hours': collected['tz_offset']
                }])
                inp_df.to_excel(writer, sheet_name='Input_Data_Original', index=False)
                df_out.to_excel(writer, sheet_name='Analysis_Output', index=False)
            print(COL_OK + f"\nReport saved to: {safe_name}")
        except Exception as e:
            print(COL_ERR + f"Failed to write Excel: {e}")
    print(COL_INFO + "\nDone.\n")

# -----------------------
# Multi-match (menu-driven) implementation
# -----------------------
def multi_match_menu():
    matches = []  # list of dicts collected
    while True:
        print(COL_BOLD + COL_INFO + "\n--- MULTI-MATCH MENU ---")
        print("1) Add new match")
        print("2) View collected matches")
        print("3) Run analysis for all collected matches")
        print("4) Export all collected matches to single Excel")
        print("5) Clear collected matches")
        print("6) Back to main menu")
        sel = safe_input("Choose 1-6: ", None)
        if sel == '1':
            collected = collect_single_match_interactive()
            if collected:
                matches.append(collected)
                print(COL_OK + "Match added.")
        elif sel == '2':
            if not matches:
                print("No matches collected yet.")
            else:
                for i, m in enumerate(matches, 1):
                    print(f"{i}) {m['a_name']} vs {m['b_name']} on {m['m_date']} at {m['m_place']}")
        elif sel == '3':
            if not matches:
                print("No matches to run.")
            else:
                results = []
                for m in matches:
                    try:
                        out, toss_results, concise_lines = perform_match_analysis(
                            m["a_name"], m["a_dob"], m["b_name"], m["b_dob"],
                            m["m_date"], m["m_time"], m["m_place"], m["m_format"],
                            m["tz_offset"], m["use_astrology"]
                        )
                        results.append(out)
                        print(COL_OK + f"Ran: {m['a_name']} vs {m['b_name']} on {m['m_date']}")
                    except Exception as e:
                        print(COL_ERR + f"Failed analysis for {m['a_name']} vs {m['b_name']}: {e}")
                # Optionally show brief summary
                print(COL_OK + f"\nCompleted analyses for {len(results)} matches.")
        elif sel == '4':
            if not matches:
                print("No matches to export.")
            else:
                # Run all analyses and export combined excel
                combined = []
                for m in matches:
                    try:
                        out, _, _ = perform_match_analysis(
                            m["a_name"], m["a_dob"], m["b_name"], m["b_dob"],
                            m["m_date"], m["m_time"], m["m_place"], m["m_format"],
                            m["tz_offset"], m["use_astrology"]
                        )
                        # include original inputs for audit
                        out['Input_Captain_A_Name'] = m['a_name']
                        out['Input_Captain_B_Name'] = m['b_name']
                        out['Input_Match_Place'] = m['m_place']
                        combined.append(out)
                    except Exception as e:
                        print(COL_WARN + f"Skipping {m['a_name']} vs {m['b_name']} due to error: {e}")
                if combined:
                    fname = f"MultiMatch_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    try:
                        df_comb = pd.DataFrame(combined)
                        df_comb.to_excel(fname, index=False)
                        print(COL_OK + f"Exported combined Excel: {fname}")
                    except Exception as e:
                        print(COL_ERR + f"Failed to write combined Excel: {e}")
        elif sel == '5':
            matches.clear()
            print(COL_OK + "Collected matches cleared.")
        elif sel == '6':
            break
        else:
            print("Invalid selection. Please choose 1-6.")

# -----------------------
# Main entry point
# -----------------------
def main():
    print(COL_BOLD + COL_INFO + "Multi-Mode Match Predictor (Numerology + Astrology)")
    print("1) Run single interactive session")
    print("2) Run multiple entries (menu-driven)")
    print("3) Exit")
    choice = safe_input("Choose 1/2/3 (default 1): ", "1")
    if choice == '1':
        run_single_match_interactive()
    elif choice == '2':
        multi_match_menu()
    else:
        print("Exiting.")

if __name__ == '__main__':
    main()
