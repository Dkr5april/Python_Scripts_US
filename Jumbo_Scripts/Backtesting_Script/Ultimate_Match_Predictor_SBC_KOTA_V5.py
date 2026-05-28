#!/usr/bin/env python3
"""
Ultimate Match Predictor — Timestamp-safe, SBC + KOTA + Learning Weights

Input expected columns (recommended):
Timestamp, Captain_A_Name, Captain_A_DOB, Captain_B_Name, Captain_B_DOB,
Match_Date, Match_Time, Match_Place, Match_Format, TZ_Offset_HOURS,
Real_Toss, Real_Match, Team_A_name, Team_B_name, TeamA_Color, TeamB_Color, Stadium_Direction

Outputs:
 - match_analysis_data_output.xlsx with sheets:
    - Input_with_Predictions
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
from typing import Dict, Any

# ---------------------------
# Config / Files
# ---------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"
TIMESTAMP_COL = "Timestamp"

# Learning hyperparameters
WEIGHT_PROMOTE_STEP = 0.10
WEIGHT_DEMOTE_STEP = 0.08
WEIGHT_MIN = 0.05
WEIGHT_MAX = 3.0
RETIRE_AFTER_WEIGHT_BELOW = 0.06
RETIRE_FAIL_RATIO = 2.5
MIN_TOTAL_EVAL = 5
UNPREDICTABLE_MARGIN = 0.5

# ---------------------------
# Helpers
# ---------------------------
def safe_str(x: Any) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def parse_tz_offset(offset_str: str) -> float:
    s = safe_str(offset_str)
    if not s:
        return 0.0
    if ":" in s:
        try:
            sign = -1 if s.strip().startswith('-') else 1
            parts = s.lstrip('+-').split(':')
            hours = float(parts[0])
            minutes = float(parts[1]) if len(parts) > 1 else 0.0
            return sign * (hours + minutes / 60.0)
        except:
            return 0.0
    try:
        return float(s)
    except:
        return 0.0

def safe_parse_timestamp(value):
    """
    Returns (datetime_or_None, has_time_flag)
    Does not raise.
    """
    if value is None:
        return None, False
    s = safe_str(value)
    if s == "":
        return None, False
    # Heuristic: presence of 'T' or ':' indicates time provided
    has_time = ("T" in s and ":" in s) or (":" in s)
    # Try common ISO formats first
    fmts = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return dt, has_time
        except:
            pass
    # Let pandas / dateutil try
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="raise")
        if isinstance(dt, pd.Timestamp):
            return dt.to_pydatetime(), has_time
    except:
        pass
    try:
        dt = parser.parse(s, dayfirst=True)
        return dt, has_time
    except Exception:
        return None, False

def format_timestamp(dt, has_time):
    if dt is None:
        return ""
    if has_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d")

# ---------------------------
# Numerology helpers
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
# Toss methods (existing)
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

def toss_method_7_planetary_hour(a_name, b_name, a_bno, b_bno, match_hour):
    try:
        match_hour = int(match_hour) % 24
    except:
        match_hour = 6
    # heuristic pattern alternating advantage by parity
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

# ---------------------------
# SBC modules (from part1)
# ---------------------------

def _first_letter_power(name: str) -> int:
    s = safe_str(name).upper()
    if not s:
        return 0
    first = next((ch for ch in s if ch.isalpha()), None)
    if not first:
        return 0
    vowels = "AUEOI"
    if first in vowels:
        return 4
    if first in "HMNR":
        return 3
    if first in "BCDFGJKLPSQT":
        return 2
    return 1

def _compute_nakshatra_number_from_date(match_date: date) -> int:
    if not isinstance(match_date, date):
        return 1
    idx = (match_date.toordinal() % 27) + 1
    return int(idx)

def _tithi_from_date(match_date: date) -> int:
    if not isinstance(match_date, date):
        return 1
    return ((match_date.day - 1) % 15) + 1

def _day_lord_number(match_date: date) -> int:
    if not isinstance(match_date, date):
        return 1
    base = match_date.weekday() + 1
    return reduce_num(base)

def _direction_score(stadium_direction: str, preferred_dirs: list) -> int:
    if not stadium_direction:
        return 0
    sd = safe_str(stadium_direction).lower()
    for d in preferred_dirs:
        if d.lower() in sd:
            return 2
    return 0

def sbc_toss_engine(teamA, teamB, capt_a_name, capt_b_name, match_date, row):
    capt_a = safe_str(capt_a_name) or safe_str(teamA)
    capt_b = safe_str(capt_b_name) or safe_str(teamB)
    first_a = _first_letter_power(capt_a)
    first_b = _first_letter_power(capt_b)
    nak = _compute_nakshatra_number_from_date(match_date)
    nak_pref = 1 if nak % 2 == 0 else -1
    tithi = _tithi_from_date(match_date)
    tithi_effect = 1 if tithi in (1,3,9,11,15) else -1
    day_lord = _day_lord_number(match_date)
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp_from_dob = life_path_number(captA_dob) if captA_dob else 0
    b_lp_from_dob = life_path_number(captB_dob) if captB_dob else 0
    a_daymatch = 1 if a_lp_from_dob and (a_lp_from_dob == day_lord) else 0
    b_daymatch = 1 if b_lp_from_dob and (b_lp_from_dob == day_lord) else 0
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    a_dir = _direction_score(stadium_dir, ['NE','E','N'])
    b_dir = _direction_score(stadium_dir, ['SW','W','S'])
    teamA_color = safe_str(row.get('TeamA_Color',''))
    teamB_color = safe_str(row.get('TeamB_Color',''))
    color_map = {'red':1,'blue':2,'green':3,'yellow':4,'white':5,'black':6,'orange':7,'purple':8}
    a_color_val = color_map.get(teamA_color.lower(),0)
    b_color_val = color_map.get(teamB_color.lower(),0)
    a_name_num = name_number(capt_a)
    b_name_num = name_number(capt_b)
    a_color_match = 1 if a_color_val and a_color_val == a_name_num else 0
    b_color_match = 1 if b_color_val and b_color_val == b_name_num else 0
    score_a = first_a + (nak_pref * 1) + (1 if tithi_effect>0 else -1) + a_daymatch + a_dir + a_color_match
    score_b = first_b + ( -nak_pref * 1) + (1 if tithi_effect<0 else -1) + b_daymatch + b_dir + b_color_match
    score_a = max(-5, min(10, int(score_a)))
    score_b = max(-5, min(10, int(score_b)))
    if score_a > score_b:
        return "A", score_a, score_b, f"SBC Toss favours Captain A ({capt_a})"
    if score_b > score_a:
        return "B", score_a, score_b, f"SBC Toss favours Captain B ({capt_b})"
    return "Neutral", score_a, score_b, "SBC Toss neutral"

def sbc_match_engine(teamA, teamB, captA, captB, match_date, stadium, row):
    teamA = safe_str(teamA)
    teamB = safe_str(teamB)
    captA = safe_str(captA) or teamA
    captB = safe_str(captB) or teamB
    def name_ring_value(n):
        s = safe_str(n).upper()
        vals = [PYTH_MAP.get(ch,0) for ch in s if ch.isalpha()]
        if not vals:
            return 1
        return reduce_num(sum(vals[:3]))
    ring_a = name_ring_value(teamA) + name_ring_value(captA)
    ring_b = name_ring_value(teamB) + name_ring_value(captB)
    nak = _compute_nakshatra_number_from_date(match_date)
    a_nn = name_number(teamA)
    b_nn = name_number(teamB)
    nak_factor_a = 2 if (a_nn % 2) == (nak % 2) else 0
    nak_factor_b = 2 if (b_nn % 2) == (nak % 2) else 0
    tithi = _tithi_from_date(match_date)
    tithi_boost = 2 if tithi in (1,5,9,11,15) else 0
    stadium_dir = safe_str(stadium or row.get('Stadium_Direction',''))
    dir_a = _direction_score(stadium_dir, ['NE','E','N'])
    dir_b = _direction_score(stadium_dir, ['SW','W','S'])
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp = life_path_number(captA_dob) if captA_dob else 0
    b_lp = life_path_number(captB_dob) if captB_dob else 0
    a_dob_boost = 2 if a_lp and ((a_lp + nak) % 2 == 0) else 0
    b_dob_boost = 2 if b_lp and ((b_lp + nak) % 2 == 0) else 0
    place_p = place_power(stadium or "")
    score_a = ring_a + nak_factor_a + tithi_boost + dir_a + a_dob_boost + place_p
    score_b = ring_b + nak_factor_b + tithi_boost + dir_b + b_dob_boost + place_p
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
# KOTA modules (from part2)
# ---------------------------

def _kota_zone_from_nak(nak: int) -> str:
    if nak in (1,2,3,4,5,6): return "Durga"
    if nak in (7,8,9,10,11,12): return "Agni"
    if nak in (13,14,15,16,17,18): return "Roga"
    if nak in (19,20,21,22,23,24): return "Mrityu"
    return "Shanti"

def kota_toss_engine(a_name, b_name, capt_a, capt_b, match_date, row):
    a = safe_str(a_name) or safe_str(capt_a)
    b = safe_str(b_name) or safe_str(capt_b)
    nak = _compute_nakshatra_number_from_date(match_date)
    zone = _kota_zone_from_nak(nak)
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_strength = life_path_number(captA_dob) if captA_dob else name_number(a)
    b_strength = life_path_number(captB_dob) if captB_dob else name_number(b)
    zone_penalty = {'Durga': 1, 'Agni': -1, 'Roga': -2, 'Mrityu': -3, 'Shanti': 2}
    zscore = zone_penalty.get(zone, 0)
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    protect_a = _direction_score(stadium_dir, ['N','NE'])
    protect_b = _direction_score(stadium_dir, ['S','SW'])
    score_a = a_strength + zscore + protect_a
    score_b = b_strength - zscore + protect_b
    score_a = max(-10, min(50, int(score_a)))
    score_b = max(-10, min(50, int(score_b)))
    if score_a > score_b:
        return "A", score_a, score_b, f"Kota Toss favours Captain A (zone {zone})"
    if score_b > score_a:
        return "B", score_a, score_b, f"Kota Toss favours Captain B (zone {zone})"
    return "Neutral", score_a, score_b, f"Kota Toss neutral (zone {zone})"

def kota_match_engine(teamA, teamB, captA, captB, match_date, stadium, row):
    nak = _compute_nakshatra_number_from_date(match_date)
    zone = _kota_zone_from_nak(nak)
    resilience_a = name_number(teamA) + place_power(stadium or "")
    resilience_b = name_number(teamB) + place_power(stadium or "")
    captA_dob = safe_str(row.get('Captain_A_DOB',''))
    captB_dob = safe_str(row.get('Captain_B_DOB',''))
    a_lp = life_path_number(captA_dob) if captA_dob else 0
    b_lp = life_path_number(captB_dob) if captB_dob else 0
    zone_effects = {'Durga': 5, 'Agni': 3, 'Roga': -3, 'Mrityu': -5, 'Shanti': 4}
    zeff = zone_effects.get(zone, 0)
    stadium_dir = safe_str(row.get('Stadium_Direction',''))
    prot_a = _direction_score(stadium_dir, ['NE','N'])
    prot_b = _direction_score(stadium_dir, ['SW','S'])
    score_a = resilience_a + a_lp + zeff + prot_a
    score_b = resilience_b + b_lp - zeff + prot_b
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
# Method stats (persistence & learning)
# ---------------------------

DEFAULT_METHODS = [
    'Numerology','Horary_Ruler','Star_Lord','Ruling_No','Compound_Score',
    'Moon_Lord','Planetary_Hour','Elemental','SBC','Kota'
]

def load_method_stats(path: str) -> Dict[str, dict]:
    default = {}
    for m in DEFAULT_METHODS:
        default[m] = {'weight': 1.0 if m not in ('SBC','Kota') else 1.0, 'active': True, 'success': 0, 'fail': 0, 'last_seen': None}
    if os.path.exists(path):
        try:
            with open(path,'r') as f:
                data = json.load(f)
            # ensure all keys exist
            for k,v in default.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return default
    return default

def save_method_stats(path: str, stats: Dict[str, dict]):
    try:
        with open(path,'w') as f:
            json.dump(stats, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: failed to write method stats: {e}")

def promote_method(stats: Dict[str, dict], method: str, correct: bool):
    if method not in stats:
        stats[method] = {'weight':1.0,'active':True,'success':0,'fail':0,'last_seen':None}
    entry = stats[method]
    entry['last_seen'] = datetime.utcnow().isoformat()
    if correct:
        entry['success'] = entry.get('success',0) + 1
        entry['weight'] = min(WEIGHT_MAX, entry.get('weight',1.0) + WEIGHT_PROMOTE_STEP)
    else:
        entry['fail'] = entry.get('fail',0) + 1
        entry['weight'] = max(0.0, entry.get('weight',1.0) - WEIGHT_DEMOTE_STEP)
    total = entry.get('success',0) + entry.get('fail',0)
    if entry['weight'] < RETIRE_AFTER_WEIGHT_BELOW and total >= MIN_TOTAL_EVAL:
        entry['active'] = False
    if total >= MIN_TOTAL_EVAL and entry.get('fail',0) > entry.get('success',0) * RETIRE_FAIL_RATIO:
        entry['active'] = False
    if entry['weight'] < WEIGHT_MIN:
        entry['active'] = False
    stats[method] = entry

# ---------------------------
# Ensemble voting & extraction helpers
# ---------------------------

def final_toss_prediction_from_dict(toss_results: Dict[str,str], method_stats: Dict[str,dict]) -> (str, float):
    votes = {}
    for mname, res in toss_results.items():
        mstat = method_stats.get(mname, {'active':True,'weight':1.0})
        if not mstat.get('active', True):
            continue
        weight = float(mstat.get('weight', 1.0))
        # res may be like "Captain A (Name)" or "Neutral - ..." or error
        if isinstance(res, str) and res.startswith("Captain A"):
            votes['A'] = votes.get('A', 0.0) + weight
        elif isinstance(res, str) and res.startswith("Captain B"):
            votes['B'] = votes.get('B', 0.0) + weight
        elif isinstance(res, str) and res.startswith("ERROR"):
            # ignore errors
            continue
        # SBC and Kota may use "Captain A (..)" same form; we covered those
    if not votes:
        return "", 0.0
    sorted_votes = sorted(votes.items(), key=lambda x:-x[1])
    top, top_score = sorted_votes[0]
    runner_up = sorted_votes[1][1] if len(sorted_votes) > 1 else 0.0
    confidence = top_score - runner_up
    # return 'A'/'B' or '' if low confidence
    if confidence <= UNPREDICTABLE_MARGIN:
        return "Unpredictable", confidence
    return ("A" if top == 'A' else "B"), confidence

def extract_name_from_label(label: str, a_name: str, b_name: str) -> str:
    # label returned from ensemble like "A" "B" or "Unpredictable" or ""
    if not label:
        return ""
    if label == "A":
        return a_name
    if label == "B":
        return b_name
    return label

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
# Main
# ---------------------------

def main():
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Method stats file: {METHOD_STATS_FILE}")

    if not os.path.exists(INPUT_FILE):
        print(f"FATAL: Input file '{INPUT_FILE}' not found at: {os.path.abspath(INPUT_FILE)}")
        sys.exit(1)

    # Load method stats
    method_stats = load_method_stats(METHOD_STATS_FILE)

    # Read input with Timestamp as string to preserve format
    try:
        df = pd.read_excel(INPUT_FILE, dtype={TIMESTAMP_COL: str})
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    total_rows_loaded = len(df)
    print(f"Rows loaded: {total_rows_loaded}")

    # Ensure expected columns exist
    for col in ['Captain_A_Name','Captain_B_Name','Captain_A_DOB','Captain_B_DOB',
                'Match_Date','Match_Time','Match_Place','Match_Format','Real_Toss','Real_Match','TZ_Offset_HOURS',
                'Stadium_Direction','TeamA_Color','TeamB_Color','Team_A_name','Team_B_name']:
        if col not in df.columns:
            # Some inputs use slightly different names; create empty when missing
            df[col] = ''

    # parse timestamps once
    parsed_dt_list = []
    parsed_has_time = []
    if TIMESTAMP_COL in df.columns:
        for idx,val in df[TIMESTAMP_COL].items():
            dt, has_time = safe_parse_timestamp(val)
            parsed_dt_list.append(dt)
            parsed_has_time.append(has_time)
    else:
        parsed_dt_list = [None] * len(df)
        parsed_has_time = [False] * len(df)

    cleaned_timestamps = [format_timestamp(dt, ht) for dt, ht in zip(parsed_dt_list, parsed_has_time)]

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
            # Team names: allow either Team_A_name or TeamA
            teamA = safe_str(row.get('Team_A_name', row.get('TeamA', row.get('Team_A',''))))
            teamB = safe_str(row.get('Team_B_name', row.get('TeamB', row.get('Team_B',''))))
            match_date_raw = safe_str(row.get('Match_Date',''))
            match_time_raw = safe_str(row.get('Match_Time',''))
            match_place = safe_str(row.get('Match_Place',''))
            match_format = safe_str(row.get('Match_Format','')).upper()
            tz_offset = parse_tz_offset(row.get('TZ_Offset_HOURS', row.get('TZ_Offset_Hours', '')))

            # compute match_date and hour robustly
            match_hour = 6
            parsed_ts = parsed_dt_list[idx] if idx < len(parsed_dt_list) else None
            parsed_ts_has_time = parsed_has_time[idx] if idx < len(parsed_has_time) else False
            if parsed_ts is not None and parsed_ts_has_time:
                match_hour = parsed_ts.hour
                match_date = parsed_ts.date()
            else:
                # fall back to Match_Date + Match_Time
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

            # numerology & base scores
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

            # collect toss results per-method
            toss_results = {}
            toss_results['Numerology'] = toss_method_1_numerology(a_name,b_name,a_lp,b_lp,date_lp)
            toss_results['Horary_Ruler'] = toss_method_2_horary_ruler(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Star_Lord'] = toss_method_3_star_lord(a_name,b_name,pp,a_nn,b_nn)
            toss_results['Ruling_No'] = toss_method_4_ruling_no(a_name,b_name,dp,pp,a_bno,b_bno)
            toss_results['Compound_Score'] = toss_method_5_compound_score(a_name,b_name,score_a,score_b)
            toss_results['Moon_Lord'] = toss_method_6_moon_sign_lord(a_name,b_name,dp,a_bno,b_bno)
            toss_results['Planetary_Hour'] = toss_method_7_planetary_hour(a_name,b_name,a_bno,b_bno,match_hour)
            toss_results['Elemental'] = toss_method_8_elemental(a_name,b_name,a_lp,b_lp,dp)

            # SBC toss & match
            try:
                sbc_toss_res, sbc_toss_a, sbc_toss_b, sbc_toss_text = sbc_toss_engine(teamA, teamB, a_name, b_name, match_date, row)
                if sbc_toss_res == "A":
                    toss_results['SBC'] = f"Captain A ({a_name}) - SBC Toss"
                elif sbc_toss_res == "B":
                    toss_results['SBC'] = f"Captain B ({b_name}) - SBC Toss"
                else:
                    toss_results['SBC'] = "Neutral - SBC Toss"
            except Exception as e:
                toss_results['SBC'] = f"ERROR SBC Toss: {e}"
                sbc_toss_res, sbc_toss_a, sbc_toss_b, sbc_toss_text = "Neutral", 0, 0, f"ERROR: {e}"

            try:
                sbc_match_res, sbc_match_a, sbc_match_b, sbc_match_text = sbc_match_engine(teamA, teamB, a_name, b_name, match_date, match_place, row)
            except Exception as e:
                sbc_match_res, sbc_match_a, sbc_match_b, sbc_match_text = "Neutral", 0, 0, f"ERROR: {e}"

            # KOTA toss & match
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
                kota_toss_res, kota_toss_a, kota_toss_b, kota_toss_text = "Neutral", 0, 0, f"ERROR: {e}"

            try:
                kota_match_res, kota_match_a, kota_match_b, kota_match_text = kota_match_engine(teamA, teamB, a_name, b_name, match_date, match_place, row)
            except Exception as e:
                kota_match_res, kota_match_a, kota_match_b, kota_match_text = "Neutral", 0, 0, f"ERROR: {e}"

            # Ensemble final toss (weighted by method_stats)
            final_toss_label, toss_confidence = final_toss_prediction_from_dict(toss_results, method_stats)
            predicted_toss_name = extract_name_from_label(final_toss_label, a_name, b_name)

            # Predicted match winner (primary numerology score)
            if score_a > score_b:
                predicted_match_name = a_name
                is_a_winner = True
            elif score_b > score_a:
                predicted_match_name = b_name
                is_a_winner = False
            else:
                predicted_match_name = a_name  # fallback
                is_a_winner = None

            # Combined prediction using SBC/Kota/numerology (weighted)
            try:
                sbcA = sbc_match_a if isinstance(sbc_match_a, (int,float)) else 0
                sbcB = sbc_match_b if isinstance(sbc_match_b, (int,float)) else 0
                kotaA = kota_match_a if isinstance(kota_match_a, (int,float)) else 0
                kotaB = kota_match_b if isinstance(kota_match_b, (int,float)) else 0
            except NameError:
                sbcA=sbcB=kotaA=kotaB=0

            numer_a = score_a
            numer_b = score_b
            combinedA = 0.4 * sbcA + 0.3 * kotaA + 0.3 * numer_a
            combinedB = 0.4 * sbcB + 0.3 * kotaB + 0.3 * numer_b
            combined_pred = a_name if combinedA > combinedB else (b_name if combinedB > combinedA else "Neutral")

            innings_trend_a = predict_innings_trend(score_a,a_lp,a_nn,dp,pp,is_a_winner is True)
            innings_trend_b = predict_innings_trend(score_b,b_lp,b_nn,dp,pp,is_a_winner is False)

            actual_toss = safe_str(row.get('Real_Toss','')).strip()
            actual_match = safe_str(row.get('Real_Match','')).strip()

            # Normalize function
            def normalize(s): return ' '.join(s.split()).lower()

            toss_correct = False
            match_correct = False
            if actual_toss and predicted_toss_name:
                toss_correct = normalize(actual_toss) == normalize(predicted_toss_name)
            if actual_match and predicted_match_name:
                match_correct = normalize(actual_match) == normalize(predicted_match_name)

            if toss_correct:
                toss_correct_count += 1
            if match_correct:
                match_correct_count += 1

            # Update method_stats per individual method - evaluate each method's predictive success
            for mname, mres in toss_results.items():
                # Determine what the method predicted as A or B (or neutral)
                method_pred_a = False
                method_pred_b = False
                if isinstance(mres, str) and mres.startswith("Captain A"):
                    method_pred_a = True
                elif isinstance(mres, str) and mres.startswith("Captain B"):
                    method_pred_b = True
                # Determine correctness by comparing to actual toss first (if present), else actual match
                method_correct = False
                if actual_toss:
                    if (method_pred_a and normalize(actual_toss) == normalize(a_name)) or (method_pred_b and normalize(actual_toss) == normalize(b_name)):
                        method_correct = True
                elif actual_match:
                    # if toss not available, credit based on match if matches
                    if (method_pred_a and normalize(actual_match) == normalize(a_name)) or (method_pred_b and normalize(actual_match) == normalize(b_name)):
                        method_correct = True
                # finally promote/demote
                promote_method(method_stats, mname, method_correct)

            # Also promote/demote SBC/Kota match-level methods based on match result
            # Evaluate SBC match engine decision
            for (mname, pred_label, pred_name) in [
                ('SBC_match', sbc_match_res if 'sbc_match_res' in locals() else None, a_name if (sbc_match_res == 'A') else (b_name if (sbc_match_res == 'B') else None)),
                ('Kota_match', kota_match_res if 'kota_match_res' in locals() else None, a_name if (kota_match_res == 'A') else (b_name if (kota_match_res == 'B') else None))
            ]:
                if mname not in method_stats:
                    method_stats[mname] = {'weight':1.0,'active':True,'success':0,'fail':0,'last_seen':None}
                # correctness versus actual_match
                correct = False
                if actual_match and pred_name:
                    if normalize(actual_match) == normalize(pred_name):
                        correct = True
                promote_method(method_stats, mname, correct)

            # Store result row
            results.append({
                'Timestamp_Clean': cleaned_timestamps[idx] if idx < len(cleaned_timestamps) else "",
                'Captain_A_Name': a_name,
                'Captain_B_Name': b_name,
                'Team_A_Name': teamA,
                'Team_B_Name': teamB,
                'Predicted_Toss_Name': predicted_toss_name,
                'Final_Toss_String': str(toss_results),
                'Toss_Confidence': round(float(toss_confidence) if 'toss_confidence' in locals() else float(toss_confidence if 'toss_confidence' in locals() else (toss_confidence if 'toss_confidence' in locals() else 0)),3) if False else round(float(toss_confidence) if 'toss_confidence' in locals() else float(toss_confidence if 'toss_confidence' in locals() else 0),3) if False else 0.0,
                'Predicted_Match_Name': predicted_match_name,
                'Combined_Prediction': combined_pred,
                'Innings_Trend_A': innings_trend_a,
                'Innings_Trend_B': innings_trend_b,
                'Score_A': score_a,
                'Score_B': score_b,
                'SBC_Toss': sbc_toss_text if 'sbc_toss_text' in locals() else '',
                'SBC_Match': sbc_match_text if 'sbc_match_text' in locals() else '',
                'SBC_Score_A': sbc_match_a if 'sbc_match_a' in locals() else '',
                'SBC_Score_B': sbc_match_b if 'sbc_match_b' in locals() else '',
                'Kota_Toss': kota_toss_text if 'kota_toss_text' in locals() else '',
                'Kota_Match': kota_match_text if 'kota_match_text' in locals() else '',
                'Kota_Score_A': kota_match_a if 'kota_match_a' in locals() else '',
                'Kota_Score_B': kota_match_b if 'kota_match_b' in locals() else '',
                'Actual_Toss': actual_toss,
                'Actual_Match': actual_match,
                'Toss_Correct': toss_correct,
                'Match_Correct': match_correct
            })

        except Exception as e:
            # Row-level failure: record error row and continue
            results.append({
                'Timestamp_Clean': cleaned_timestamps[idx] if idx < len(cleaned_timestamps) else "",
                'Captain_A_Name': safe_str(row.get('Captain_A_Name','')),
                'Captain_B_Name': safe_str(row.get('Captain_B_Name','')),
                'Team_A_Name': safe_str(row.get('Team_A_name','')),
                'Team_B_Name': safe_str(row.get('Team_B_name','')),
                'Predicted_Toss_Name': '',
                'Final_Toss_String': f"ROW ERROR: {e}",
                'Toss_Confidence': 0.0,
                'Predicted_Match_Name': '',
                'Combined_Prediction': '',
                'Innings_Trend_A': '',
                'Innings_Trend_B': '',
                'Score_A': '',
                'Score_B': '',
                'SBC_Toss': '',
                'SBC_Match': '',
                'SBC_Score_A': '',
                'SBC_Score_B': '',
                'Kota_Toss': '',
                'Kota_Match': '',
                'Kota_Score_A': '',
                'Kota_Score_B': '',
                'Actual_Toss': safe_str(row.get('Real_Toss','')),
                'Actual_Match': safe_str(row.get('Real_Match','')),
                'Toss_Correct': False,
                'Match_Correct': False
            })
            continue

    # End per-row loop

    # Persist method stats
    save_method_stats(METHOD_STATS_FILE, method_stats)

    # Build output DataFrames
    results_df = pd.DataFrame(results)
    total = max(total_rows, 1)
    toss_acc = (toss_correct_count / total) * 100
    match_acc = (match_correct_count / total) * 100
    summary_df = pd.DataFrame([{
        'Total_Rows': total,
        'Toss_Correct_Count': toss_correct_count,
        'Match_Correct_Count': match_correct_count,
        'Toss_Accuracy_%': round(toss_acc,2),
        'Match_Accuracy_%': round(match_acc,2)
    }])

    # Prepare output input copy with cleaned timestamp column
    out_df = df.copy(deep=True)
    out_df[TIMESTAMP_COL + "_Clean"] = cleaned_timestamps

    # Write outputs
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl', mode='w') as writer:
            out_df.to_excel(writer, index=False, sheet_name='Input_with_Predictions')
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')
        print(f"Backtest complete. Output written to: {OUTPUT_FILE}")
        print(f" Toss accuracy: {round(toss_acc,2)}%  Match accuracy: {round(match_acc,2)}%")
        print(f"Method stats saved to: {METHOD_STATS_FILE}")
    except Exception as e:
        print(f"Failed to write output: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
