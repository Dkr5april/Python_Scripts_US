#!/usr/bin/env python3
"""
Ultimate Match Predictor — Timestamp-safe version
Now with FULL Sarvatobhadra Chakra (SBC) + FULL Kota Chakra integrated.
- SBC and Kota degrade gracefully if optional columns are missing.
- SBC and Kota are added as independent modules and included in toss_results.
- New output fields: SBC_Toss, SBC_Match, SBC_Score_A/B, Kota_Toss, Kota_Match, Kota_Score_A/B, Combined_Prediction
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

def parse_tz_offset(offset_str: str) -> float:
    """Converts offset strings like '+10:30' or '4' to a float like 10.5 or 4.0."""
    s = safe_str(offset_str).strip()
    if not s:
        return 0.0
    if ":" in s:
        try:
            sign = -1 if s.startswith('-') else 1
            parts = s.lstrip('+-').split(':')
            hours = float(parts[0])
            minutes = float(parts[1]) if len(parts) > 1 else 0.0
            return sign * (hours + (minutes / 60.0))
        except:
            return 0.0
    try:
        return float(s)
    except:
        return 0.0

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
    has_time = ("T" in s and ":" in s) or (":" in s)
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        return dt, has_time
    except Exception:
        pass
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return dt, has_time
    except Exception:
        pass
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="raise")
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        return dt, has_time
    except Exception:
        pass
    try:
        dt = parser.parse(s, dayfirst=True)
        return dt, has_time
    except Exception as e:
        print(f"DEBUG: Failed to parse timestamp value '{s}'. Error: {e}")
        return None, False

def format_timestamp(dt, has_time):
    """Format dt based on whether original had time. Return empty string if dt is None."""
    if dt is None:
        return ""
    if has_time:
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
# SARVATOBHADRA CHAKRA (SBC) MODULES
# ---------------------------

def _first_letter_power(name: str) -> int:
    """Return a small power value based on first letter's SBC ring position.
    Vowels typically stronger; consonants distributed.
    1..4 scale returned."""
    s = safe_str(name).upper()
    if not s:
        return 0
    first = next((ch for ch in s if ch.isalpha()), None)
    if not first:
        return 0
    # Simple vowel/consonant grouping with some ring weights
    vowels = "AUEOI"  # treat these as stronger in SBC
    if first in vowels:
        return 4
    if first in "HMNR":  # strong consonants
        return 3
    if first in "BCDFGJKLPSQT":  # medium
        return 2
    return 1  # weaker letter

def _compute_nakshatra_number_from_date(match_date: date) -> int:
    """Deterministic approximate nakshatra index 1..27 from a date.
    This is a simplified, deterministic mapping for offline use."""
    if not isinstance(match_date, date):
        return 1
    # Use an epoch-based ordinal and map to 27 nakshatras
    idx = (match_date.toordinal() % 27) + 1
    return int(idx)

def _tithi_from_date(match_date: date) -> int:
    """Simplified tithi: day-of-month modulo 15 (1..15)"""
    if not isinstance(match_date, date):
        return 1
    return ((match_date.day - 1) % 15) + 1

def _day_lord_number(match_date: date) -> int:
    """Map weekday to a small number for comparisons (Mon=1..Sun=7 -> reduce to 1..9)"""
    if not isinstance(match_date, date):
        return 1
    # Monday=0 in weekday(); we map to 1..7 then reduce
    base = match_date.weekday() + 1
    return reduce_num(base)

def _direction_score(stadium_direction: str, preferred_dirs: list) -> int:
    """Return small score if stadium_direction in preferred_dirs (case-insensitive)."""
    if not stadium_direction:
        return 0
    sd = safe_str(stadium_direction).lower()
    for d in preferred_dirs:
        if d.lower() in sd:
            return 2
    return 0

def sbc_toss_engine(a_name, b_name, capt_a_name, capt_b_name, match_date, row):
    """
    SBC logic tailored for toss (fast-changing elements).
    Returns: ('A'|'B'|'Neutral', score_a, score_b, textual_reason)
    """
    # graceful fallback on missing fields
    a_name = safe_str(a_name)
    b_name = safe_str(b_name)
    capt_a = safe_str(capt_a_name) or a_name
    capt_b = safe_str(capt_b_name) or b_name

    # core SBC components
    first_a = _first_letter_power(capt_a)
    first_b = _first_letter_power(capt_b)

    nak = _compute_nakshatra_number_from_date(match_date)
    # simple nakshatra preference: odd/even tilt (toy heuristic)
    nak_pref = 1 if nak % 2 == 0 else -1

    tithi = _tithi_from_date(match_date)
    tithi_effect = 1 if tithi in (1,3,9,11,15) else -1

    day_lord = _day_lord_number(match_date)
    # if captain birth/life path matches day_lord, small boost (DOB optional)
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp_from_dob = life_path_number(captA_dob) if captA_dob else 0
    b_lp_from_dob = life_path_number(captB_dob) if captB_dob else 0
    a_daymatch = 1 if a_lp_from_dob and (a_lp_from_dob == day_lord) else 0
    b_daymatch = 1 if b_lp_from_dob and (b_lp_from_dob == day_lord) else 0

    # stadium direction optional
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    # prefer NE/ENE for toss in this heuristic
    a_dir = _direction_score(stadium_dir, ['NE','E','N'])  # small boost if stadium favors
    b_dir = _direction_score(stadium_dir, ['SW','W','S'])

    # Team color optional: small friendly boost if captain's name number matches color number
    teamA_color = safe_str(row.get('TeamA_Color',''))
    teamB_color = safe_str(row.get('TeamB_Color',''))
    # map color -> small number (rough)
    color_map = {'red':1,'blue':2,'green':3,'yellow':4,'white':5,'black':6,'orange':7,'purple':8}
    a_color_val = color_map.get(teamA_color.lower(),0)
    b_color_val = color_map.get(teamB_color.lower(),0)
    a_name_num = name_number(capt_a)
    b_name_num = name_number(capt_b)
    a_color_match = 1 if a_color_val and a_color_val == a_name_num else 0
    b_color_match = 1 if b_color_val and b_color_val == b_name_num else 0

    # Compose SBC toss score
    score_a = first_a + (nak_pref * 1) + (1 if tithi_effect>0 else -1) + a_daymatch + a_dir + a_color_match
    score_b = first_b + ( -nak_pref * 1) + (1 if tithi_effect<0 else -1) + b_daymatch + b_dir + b_color_match

    # normalize & clamp
    score_a = max(-5, min(10, int(score_a)))
    score_b = max(-5, min(10, int(score_b)))

    if score_a > score_b:
        return "A", score_a, score_b, f"SBC Toss favours Captain A ({capt_a})"
    if score_b > score_a:
        return "B", score_a, score_b, f"SBC Toss favours Captain B ({capt_b})"
    return "Neutral", score_a, score_b, "SBC Toss neutral"

def sbc_match_engine(teamA, teamB, captA, captB, match_date, stadium, row):
    """
    SBC logic for match winner — deeper components, uses stadium, team names, vedha-like checks.
    Returns ('A'|'B'|'Neutral', score_a, score_b, textual_reason)
    """
    teamA = safe_str(teamA)
    teamB = safe_str(teamB)
    captA = safe_str(captA) or teamA
    captB = safe_str(captB) or teamB

    # Name ring contributions (sum of first 3 letters' pyth numbers reduced)
    def name_ring_value(n):
        s = safe_str(n).upper()
        vals = [PYTH_MAP.get(ch,0) for ch in s if ch.isalpha()]
        if not vals:
            return 1
        return reduce_num(sum(vals[:3]))

    ring_a = name_ring_value(teamA) + name_ring_value(captA)
    ring_b = name_ring_value(teamB) + name_ring_value(captB)

    # Nakshatra influence (1..27)
    nak = _compute_nakshatra_number_from_date(match_date)
    # friendly nakshatras for A if its name_number parity matches nak parity
    a_nn = name_number(teamA)
    b_nn = name_number(teamB)
    nak_factor_a = 2 if (a_nn % 2) == (nak % 2) else 0
    nak_factor_b = 2 if (b_nn % 2) == (nak % 2) else 0

    # Tithi influence
    tithi = _tithi_from_date(match_date)
    tithi_boost = 2 if tithi in (1,5,9,11,15) else 0

    # Stadium direction vedha-like influence
    stadium_dir = safe_str(stadium or row.get('Stadium_Direction',''))
    dir_a = _direction_score(stadium_dir, ['NE','E','N'])  # small heuristic
    dir_b = _direction_score(stadium_dir, ['SW','W','S'])

    # Captain DOB stronger influence on match-level outcome (if DOB present)
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp = life_path_number(captA_dob) if captA_dob else 0
    b_lp = life_path_number(captB_dob) if captB_dob else 0
    a_dob_boost = 2 if a_lp and ((a_lp + nak) % 2 == 0) else 0
    b_dob_boost = 2 if b_lp and ((b_lp + nak) % 2 == 0) else 0

    # Place power (stadium name)
    place_p = place_power(stadium or "")

    # Combine into SBC match score
    score_a = ring_a + nak_factor_a + tithi_boost + dir_a + a_dob_boost + place_p
    score_b = ring_b + nak_factor_b + tithi_boost + dir_b + b_dob_boost + place_p

    # color matching if available
    teamA_color = safe_str(row.get('TeamA_Color',''))
    teamB_color = safe_str(row.get('TeamB_Color',''))
    color_map = {'red':1,'blue':2,'green':3,'yellow':4,'white':2,'black':1,'orange':2,'purple':3}
    score_a += color_map.get(teamA_color.lower(), 0)
    score_b += color_map.get(teamB_color.lower(), 0)

    score_a = max(0, min(100, int(score_a)))
    score_b = max(0, min(100, int(score_b)))

    if score_a > score_b:
        return "A", score_a, score_b, f"SBC Match favours Team A ({teamA})"
    if score_b > score_a:
        return "B", score_a, score_b, f"SBC Match favours Team B ({teamB})"
    return "Neutral", score_a, score_b, "SBC Match neutral"

# ---------------------------
# KOTA CHAKRA MODULES
# ---------------------------

def _kota_zone_from_nak(nak: int) -> str:
    """Simplified mapping of nakshatra index to Kota zone label."""
    # This is a heuristic mapping into a few zone buckets for scoring
    if nak in (1,2,3,4,5,6): return "Durga"
    if nak in (7,8,9,10,11,12): return "Agni"
    if nak in (13,14,15,16,17,18): return "Roga"
    if nak in (19,20,21,22,23,24): return "Mrityu"
    return "Shanti"

def kota_toss_engine(a_name, b_name, capt_a, capt_b, match_date, row):
    """
    Kota logic for toss: defensive/offensive short-term zones.
    Returns ('A'|'B'|'Neutral', score_a, score_b, textual_reason)
    """
    a = safe_str(a_name) or safe_str(capt_a)
    b = safe_str(b_name) or safe_str(capt_b)
    nak = _compute_nakshatra_number_from_date(match_date)
    zone = _kota_zone_from_nak(nak)

    # Captain strength via life path or name_number
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_strength = life_path_number(captA_dob) if captA_dob else name_number(a)
    b_strength = life_path_number(captB_dob) if captB_dob else name_number(b)

    # Short-term Kota effect: certain zones penalize or boost toss
    zone_penalty = {'Durga': 1, 'Agni': -1, 'Roga': -2, 'Mrityu': -3, 'Shanti': 2}
    zscore = zone_penalty.get(zone, 0)

    # Stadium direction optional: some directions protect vs kota
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    protect_a = _direction_score(stadium_dir, ['N','NE'])
    protect_b = _direction_score(stadium_dir, ['S','SW'])

    score_a = a_strength + zscore + protect_a
    score_b = b_strength - zscore + protect_b  # note reversed application

    score_a = max(-10, min(50, int(score_a)))
    score_b = max(-10, min(50, int(score_b)))

    if score_a > score_b:
        return "A", score_a, score_b, f"Kota Toss favours Captain A (zone {zone})"
    if score_b > score_a:
        return "B", score_a, score_b, f"Kota Toss favours Captain B (zone {zone})"
    return "Neutral", score_a, score_b, f"Kota Toss neutral (zone {zone})"

def kota_match_engine(teamA, teamB, captA, captB, match_date, stadium, row):
    """
    Kota logic for match: longer-term defensive/offensive zone influence.
    Returns ('A'|'B'|'Neutral', score_a, score_b, textual_reason)
    """
    nak = _compute_nakshatra_number_from_date(match_date)
    zone = _kota_zone_from_nak(nak)

    # Team resilience via name_number and place power
    resilience_a = name_number(teamA) + place_power(stadium or "")
    resilience_b = name_number(teamB) + place_power(stadium or "")

    # Captain life-path or birth number influences resilience
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp = life_path_number(captA_dob) if captA_dob else 0
    b_lp = life_path_number(captB_dob) if captB_dob else 0

    # Zone effect (positive or negative)
    zone_effects = {'Durga': 5, 'Agni': 3, 'Roga': -3, 'Mrityu': -5, 'Shanti': 4}
    zeff = zone_effects.get(zone, 0)

    # Stadium direction protection
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    prot_a = _direction_score(stadium_dir, ['NE','N'])
    prot_b = _direction_score(stadium_dir, ['SW','S'])

    score_a = resilience_a + a_lp + zeff + prot_a
    score_b = resilience_b + b_lp - zeff + prot_b  # reversed influence

    # Color protective small addition
    teamA_color = safe_str(row.get('TeamA_Color',''))
    teamB_color = safe_str(row.get('TeamB_Color',''))
    color_map = {'white':2,'blue':1,'green':2}
    score_a += color_map.get(teamA_color.lower(), 0)
    score_b += color_map.get(teamB_color.lower(), 0)

    score_a = max(0, min(200, int(score_a)))
    score_b = max(0, min(200, int(score_b)))

    if score_a > score_b:
        return "A", score_a, score_b, f"Kota Match favours Team A ({teamA}) zone {zone}"
    if score_b > score_a:
        return "B", score_a, score_b, f"Kota Match favours Team B ({teamB}) zone {zone}"
    return "Neutral", score_a, score_b, f"Kota Match neutral zone {zone}"

# ---------------------------
# Main routine
# ---------------------------
def main():
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Method stats file: {METHOD_STATS_FILE}")

    full_path = os.path.abspath(INPUT_FILE)
    if not os.path.exists(INPUT_FILE):
        print(f"\nFATAL ERROR: Input file '{INPUT_FILE}' not found at path: {full_path}")
        sys.exit(1)

    print(f"\nDEBUG: Script is reading from the ABSOLUTE path: {full_path}")

    try:
        df = pd.read_excel(INPUT_FILE, dtype={TIMESTAMP_COL: str})
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    total_rows_loaded = len(df)
    print(f"DEBUG: pandas successfully loaded a DataFrame with {total_rows_loaded} rows.")

    # Ensure expected columns exist (don't modify original df content)
    for col in ['Captain_A_Name','Captain_B_Name','Captain_A_DOB','Captain_B_DOB',
                 'Match_Date','Match_Time','Match_Place','Match_Format','Real_Toss','Real_Match','TZ_Offset_Hours',
                 # optional SBC/Kota assistance columns (do not require them)
                 'Stadium_Direction','TeamA_Color','TeamB_Color','Team_A_Name','Team_B_Name']:
        if col not in df.columns:
            df[col] = ''

    # Parse Timestamp safely for each row, but do NOT write back to the input file
    parsed_dt_list = []
    parsed_has_time = []
    for idx, val in df[TIMESTAMP_COL].items():
        dt, has_time = safe_parse_timestamp(val)
        parsed_dt_list.append(dt)
        parsed_has_time.append(has_time)
    cleaned_timestamps = [format_timestamp(dt, has_time) for dt, has_time in zip(parsed_dt_list, parsed_has_time)]

    # Main processing loop (backtest + predictions)
    results = []
    toss_correct_count = 0
    match_correct_count = 0
    total_rows = len(df)

    for idx, row in df.iterrows():
        try:
            a_name = safe_str(row.get('Captain_A_Name',''))
            b_name = safe_str(row.get('Captain_B_Name',''))
            a_dob = safe_str(row.get('Captain_A_DOB',''))
            b_dob = safe_str(row.get('Captain_B_DOB',''))
            # Team name fallbacks
            teamA = safe_str(row.get('Team_A_Name', row.get('TeamA','')))
            teamB = safe_str(row.get('Team_B_Name', row.get('TeamB','')))
            match_date_raw = safe_str(row.get('Match_Date',''))
            match_time_raw = safe_str(row.get('Match_Time',''))
            match_place = safe_str(row.get('Match_Place',''))
            match_format = safe_str(row.get('Match_Format','')).upper()
            tz_offset = parse_tz_offset(row.get('TZ_Offset_Hours'))

            # Determine match_hour and match_date robustly (as before)
            match_hour = 6
            parsed_ts = parsed_dt_list[idx]
            parsed_ts_has_time = parsed_has_time[idx]
            if parsed_ts is not None and parsed_ts_has_time:
                match_hour = parsed_ts.hour
                match_date = parsed_ts.date()
            else:
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
                        match_date = date.today()
                        match_hour = 6
                except:
                    match_date = date.today()
                    match_hour = 6

            # Numerology & base scores
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

            # Existing toss methods
            toss_results = {}
            toss_results['Numerology'] = toss_method_1_numerology(a_name,b_name,a_lp,b_lp,date_lp)
            toss_results['Horary_Ruler'] = toss_method_2_horary_ruler(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Star_Lord'] = toss_method_3_star_lord(a_name,b_name,pp,a_nn,b_nn)
            toss_results['Ruling_No'] = toss_method_4_ruling_no(a_name,b_name,dp,pp,a_bno,b_bno)
            toss_results['Compound_Score'] = toss_method_5_compound_score(a_name,b_name,score_a,score_b)
            toss_results['Moon_Lord'] = toss_method_6_moon_sign_lord(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Planetary_Hour'] = toss_method_7_planetary_hour(a_name,b_name,a_bno,b_bno,match_hour)
            toss_results['Elemental'] = toss_method_8_elemental(a_name,b_name,a_lp,b_lp,dp)

            # --- NEW: SBC Toss & Match ---
            try:
                sbc_toss_res, sbc_toss_a, sbc_toss_b, sbc_toss_text = sbc_toss_engine(teamA, teamB, a_name, b_name, match_date, row)
                # convert into human-readable toss_results entry
                if sbc_toss_res == "A":
                    toss_results['SBC'] = f"Captain A ({a_name}) - SBC Toss"
                elif sbc_toss_res == "B":
                    toss_results['SBC'] = f"Captain B ({b_name}) - SBC Toss"
                else:
                    toss_results['SBC'] = "Neutral - SBC Toss"
            except Exception as e:
                toss_results['SBC'] = f"ERROR SBC Toss: {e}"
                sbc_toss_res, sbc_toss_a, sbc_toss_b = "Neutral", 0, 0
                sbc_toss_text = f"ERROR: {e}"

            try:
                sbc_match_res, sbc_match_a, sbc_match_b, sbc_match_text = sbc_match_engine(teamA, teamB, a_name, b_name, match_date, match_place, row)
            except Exception as e:
                sbc_match_res, sbc_match_a, sbc_match_b = "Neutral", 0, 0
                sbc_match_text = f"ERROR: {e}"

            # --- NEW: Kota Toss & Match ---
            try:
                kota_toss_res, kota_toss_a, kota_toss_b, kota_toss_text = kota_toss_engine(teamA, teamB, a_name, b_name, match_date, row)
                if kota_toss_res == "A":
                    toss_results['Kota'] = f"Captain A ({a_name}) - Kota Toss"
                elif kota_toss_res == "B":
                    toss_results['Kota'] = f"Captain B ({b_name}) - Kota Toss"
                else:
                    toss_results['Kota'] = "Neutral - Kota Toss"
            except Exception as e:
                toss_results['Kota'] = f"ERROR Kota Toss: {e}"
                kota_toss_res, kota_toss_a, kota_toss_b = "Neutral", 0, 0
                kota_toss_text = f"ERROR: {e}"

            try:
                kota_match_res, kota_match_a, kota_match_b, kota_match_text = kota_match_engine(teamA, teamB, a_name, b_name, match_date, match_place, row)
            except Exception as e:
                kota_match_res, kota_match_a, kota_match_b = "Neutral", 0, 0
                kota_match_text = f"ERROR: {e}"

            # final toss aggregator (unchanged behavior)
            final_toss = final_toss_prediction(toss_results)
            predicted_toss_name = extract_name_from_final(final_toss)

            # Match predicted name (leave original logic as primary)
            if score_a > score_b:
                predicted_match_name = a_name
                is_a_winner = True
            else:
                predicted_match_name = b_name
                is_a_winner = False

            # Add SBC/Kota-informed combined prediction (non-destructive: original result retained)
            # We'll use weights: SBC match 40%, Kota match 30%, Numerology match score difference 30%
            # Normalize SBC and Kota to comparable scale (0-100) already for sbc_match_a/b and kota_match_a/b
            try:
                # safe fallbacks for scores
                sbcA = sbc_match_a if isinstance(sbc_match_a, (int,float)) else 0
                sbcB = sbc_match_b if isinstance(sbc_match_b, (int,float)) else 0
                kotaA = kota_match_a if isinstance(kota_match_a, (int,float)) else 0
                kotaB = kota_match_b if isinstance(kota_match_b, (int,float)) else 0
                # numeric match_score advantage (score_a & score_b small scale)
                numer_a = score_a
                numer_b = score_b
                # compute combined value
                combinedA = 0.4 * sbcA + 0.3 * kotaA + 0.3 * numer_a
                combinedB = 0.4 * sbcB + 0.3 * kotaB + 0.3 * numer_b
                if combinedA > combinedB:
                    combined_pred = a_name
                elif combinedB > combinedA:
                    combined_pred = b_name
                else:
                    combined_pred = "Neutral"
            except Exception:
                combined_pred = predicted_match_name

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
                'Combined_Prediction': combined_pred,
                'Innings_Trend_A': innings_trend_a,
                'Innings_Trend_B': innings_trend_b,
                'Score_A': score_a,
                'Score_B': score_b,
                'SBC_Toss': sbc_toss_text,
                'SBC_Match': sbc_match_text,
                'SBC_Score_A': sbc_match_a,
                'SBC_Score_B': sbc_match_b,
                'Kota_Toss': kota_toss_text,
                'Kota_Match': kota_match_text,
                'Kota_Score_A': kota_match_a,
                'Kota_Score_B': kota_match_b,
                'Actual_Toss': actual_toss,
                'Actual_Match': actual_match,
                'Toss_Correct': toss_correct,
                'Match_Correct': match_correct
            })

            # --- DEBUG BLOCK: PRINTING RESULTS FOR THE LAST ROW ---
            if idx == total_rows - 1:
                print("\n--- DEBUG: PROCESSING LAST ROW (INDEX %d) ---" % idx)
                print(f"Input: Captain A: {a_name}, Captain B: {b_name}")
                print(f"Input: Team A: {teamA}, Team B: {teamB}")
                print(f"Input: Match Date: {match_date_raw}, Time: {match_time_raw}")
                print(f"Numerology Scores: Captain A Score: {score_a}, Captain B Score: {score_b}")
                print(f"SBC Match Scores: A={sbc_match_a}, B={sbc_match_b}")
                print(f"Kota Match Scores: A={kota_match_a}, B={kota_match_b}")
                print(f"Combined Prediction: {combined_pred}")
                print(f"Final Toss Prediction: {final_toss}")
                print(f"Predicted Match Winner: {predicted_match_name}")
                print("-------------------------------------------\n")

        except Exception as e:
            results.append({
                'Predicted_Toss_Name':'',
                'Final_Toss_String': f"ROW ERROR: {e}",
                'Predicted_Match_Name':'',
                'Combined_Prediction':'',
                'Innings_Trend_A':'',
                'Innings_Trend_B':'',
                'Score_A':'',
                'Score_B':'',
                'SBC_Toss':'',
                'SBC_Match':'',
                'SBC_Score_A':'',
                'SBC_Score_B':'',
                'Kota_Toss':'',
                'Kota_Match':'',
                'Kota_Score_A':'',
                'Kota_Score_B':'',
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
