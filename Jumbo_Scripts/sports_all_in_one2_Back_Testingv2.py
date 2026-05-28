#!/usr/bin/env python3
"""
Learning-based Backtestable Astrology & Numerology Predictor

Features:
- Reads: match_analysis_data.xlsx (input)
- Writes: match_analysis_data_output.xlsx (predictions/backtest)
- Persists: method_stats.json (weights/success/fail history)
- Ensemble of prediction methods with weighted voting
- Automatic promotion/demotion and retirement of methods
- Optional Swiss Ephemeris (pyswisseph) support
"""

import sys
import os
import json
import math
import time as _time
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Tuple, List

import pandas as pd

# Optional dependencies
try:
    import swisseph as swe
    SWE_AVAILABLE = True
except Exception:
    swe = None
    SWE_AVAILABLE = False

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

# ---------------------
# Configuration / Tunables
# ---------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"

# promotion/demotion steps (per correct/incorrect prediction)
WEIGHT_PROMOTE_STEP = 0.10
WEIGHT_DEMOTE_STEP = 0.08

# weight caps and retirement thresholds
WEIGHT_MIN = 0.05
WEIGHT_MAX = 3.0
RETIRE_AFTER_WEIGHT_BELOW = 0.08  # if weight goes below this -> deactivate
RETIRE_FAIL_RATIO = 2.5  # if fails > success * this and total >= MIN_TOTAL_EVAL -> retire
MIN_TOTAL_EVAL = 5  # minimum number of evaluations before aggressive retirement

# Confidence margin for calling "Unpredictable"
UNPREDICTABLE_MARGIN = 0.5

# Good pairs and constants (same as prior)
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
GOOD_PAIRS = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

DAY_LORDS = {
    0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun',
}

# ---------------------
# Utilities: numerology & astro helpers
# ---------------------
def reduce_num(n: int) -> int:
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def safe_str(x) -> str:
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

# swiss ephemeris helpers (if available)
def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    if not SWE_AVAILABLE:
        raise RuntimeError("swisseph not available")
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    time_fraction = (dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0) / 24.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, time_fraction)

def sign_from_long(lon_deg):
    signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    idx = int(lon_deg // 30) % 12
    return signs[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
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
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada, "lord": lord}

# ---------------------
# Date parsing helper that tries multiple formats intelligently
# ---------------------
def parse_match_date(raw: str) -> Tuple[date, str]:
    """
    Try multiple common date formats and return (date_obj, formatted_ddmmyyyy)
    """
    s = safe_str(raw)
    formats = ["%d/%m/%Y","%Y-%m-%d","%Y/%m/%d","%d-%m-%Y","%d %b %Y","%d %B %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date(), dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    # fallback to pandas (infer)
    try:
        dt = pd.to_datetime(s, dayfirst=False, infer_datetime_format=True)
        d = dt.date()
        return d, d.strftime("%d/%m/%Y")
    except Exception:
        # last fallback: today
        d = date.today()
        return d, d.strftime("%d/%m/%Y")

# ---------------------
# Method registry & implementations
# ---------------------
# Each method returns a tuple (predicted_toss_name, predicted_match_name, meta)
# meta is a dict with details (useful for backtest logging)

def method_toss_numerology(a_name, b_name, a_lp, b_lp, date_lp, **kwargs):
    res = toss_method_1_numerology_impl(a_name, b_name, a_lp, b_lp, date_lp)
    # For match prediction, use score proxies (higher life_path->match)
    predicted_match = a_name if a_lp + kwargs.get('a_nn',0) >= b_lp + kwargs.get('b_nn',0) else b_name
    return res.get('toss_name'), predicted_match, {'method':'toss_numerology', 'details':res}

def toss_method_1_numerology_impl(a_name, b_name, a_lp, b_lp, date_lp):
    a_good = (a_lp, date_lp) in GOOD_PAIRS
    b_good = (b_lp, date_lp) in GOOD_PAIRS
    if a_good and not b_good:
        return {'toss_name': a_name, 'toss_string': f"Captain A ({a_name}) - Good Numerology Pair"}
    if b_good and not a_good:
        return {'toss_name': b_name, 'toss_string': f"Captain B ({b_name}) - Good Numerology Pair"}
    return {'toss_name': None, 'toss_string': "Neutral - Balanced Numerology"}

def method_day_lord(a_name, b_name, day_lord_planet, a_bno, b_bno, **kwargs):
    day_lord_num = PLANET_NUMBERS.get(day_lord_planet, 0)
    a_match = (a_bno, day_lord_num) in GOOD_PAIRS
    b_match = (b_bno, day_lord_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_bno >= b_bno else b_name
    return toss, predicted_match, {'method':'day_lord', 'planet': day_lord_planet, 'a_match':a_match,'b_match':b_match}

def method_star_lord(a_name, b_name, nak_lord_planet, a_nn, b_nn, **kwargs):
    star_lord_num = PLANET_NUMBERS.get(nak_lord_planet, 0)
    a_match = (a_nn, star_lord_num) in GOOD_PAIRS
    b_match = (b_nn, star_lord_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_nn >= b_nn else b_name
    return toss, predicted_match, {'method':'star_lord','nak_lord':nak_lord_planet,'a_match':a_match,'b_match':b_match}

def method_ruling_number(a_name, b_name, dp, pp, a_bno, b_bno, **kwargs):
    ruling_no = reduce_num(dp + pp)
    a_diff = abs(a_bno - ruling_no)
    b_diff = abs(b_bno - ruling_no)
    toss = a_name if a_diff < b_diff else (b_name if b_diff < a_diff else None)
    predicted_match = a_name if a_bno <= b_bno else b_name
    return toss, predicted_match, {'method':'ruling_no','ruling_no':ruling_no,'a_diff':a_diff,'b_diff':b_diff}

def method_compound_score(a_name, b_name, score_a, score_b, **kwargs):
    toss = a_name if score_a > score_b else (b_name if score_b > score_a else None)
    predicted_match = toss  # compound score assumes toss correlates to match in this method
    return toss, predicted_match, {'method':'compound_score','score_a':score_a,'score_b':score_b}

def method_moon_sign(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno, **kwargs):
    moon_lord_num = PLANET_NUMBERS.get(moon_sign_lord_planet, 0)
    a_match = (a_bno, moon_lord_num) in GOOD_PAIRS
    b_match = (b_bno, moon_lord_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_match else (b_name if b_match else (a_name if a_bno>=b_bno else b_name))
    return toss, predicted_match, {'method':'moon_sign','moon_sign_lord':moon_sign_lord_planet,'a_match':a_match,'b_match':b_match}

# Simple random baseline method (useful for calibration)
import random
def method_random(a_name, b_name, **kwargs):
    toss = random.choice([a_name, b_name, None])
    predicted_match = random.choice([a_name, b_name])
    return toss, predicted_match, {'method':'random'}

# A method list that references the function objects and labels
# Note: PLANET_NUMBERS is re-used from earlier code or define here:
PLANET_NUMBERS = {
    'Sun': 1, 'Moon': 2, 'Jupiter': 3, 'Rahu': 4, 'Mercury': 5,
    'Venus': 6, 'Ketu': 7, 'Saturn': 8, 'Mars': 9, 'Neptune': 7, 'Uranus': 4, 'Pluto': 9
}

METHOD_IMPLEMENTATIONS = {
    'compound_score': method_compound_score,
    'ruling_number': method_ruling_number,
    'day_lord': method_day_lord,
    'star_lord': method_star_lord,
    'moon_sign': method_moon_sign,
    'numerology_toss': method_toss_numerology,
    'random_baseline': method_random,
}

# ---------------------
# Method stats persistence & helpers
# ---------------------
def load_method_stats(path: str) -> Dict[str, Any]:
    # Default initialization
    default = {}
    for name in METHOD_IMPLEMENTATIONS.keys():
        default[name] = {
            'weight': 1.0 if name != 'random_baseline' else 0.5,
            'active': True,
            'success': 0,
            'fail': 0,
            'last_seen': None
        }
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            # ensure keys present
            for k,v in default.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return default
    return default

def save_method_stats(path: str, stats: Dict[str, Any]):
    with open(path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)

def promote_method(stats: Dict[str, Any], method: str, correct: bool):
    entry = stats.get(method)
    if not entry:
        return
    entry['last_seen'] = datetime.utcnow().isoformat()
    if correct:
        entry['success'] = entry.get('success',0) + 1
        entry['weight'] = min(WEIGHT_MAX, entry.get('weight',1.0) + WEIGHT_PROMOTE_STEP)
    else:
        entry['fail'] = entry.get('fail',0) + 1
        entry['weight'] = max(0.0, entry.get('weight',1.0) - WEIGHT_DEMOTE_STEP)
    # retirement logic
    total = entry.get('success',0) + entry.get('fail',0)
    if entry['weight'] < RETIRE_AFTER_WEIGHT_BELOW and total >= MIN_TOTAL_EVAL:
        entry['active'] = False
    # aggressive retirement on very poor performance
    if total >= MIN_TOTAL_EVAL and entry.get('fail',0) > entry.get('success',0) * RETIRE_FAIL_RATIO:
        entry['active'] = False
    # ensure weight floor
    if entry['weight'] < WEIGHT_MIN:
        entry['active'] = False
    stats[method] = entry

# ---------------------
# Ensemble & scoring engine
# ---------------------
def weighted_vote_for_row(method_stats, row_ctx) -> Tuple[str, float, Dict[str,Any]]:
    """
    For a single input row (context), run active methods and get weighted votes.
    Returns:
      - final_toss_name (or 'Unpredictable')
      - toss_confidence (weighted diff)
      - details: per-method contributions
    """
    votes = {}
    match_votes = {}
    details = []

    # run each active method
    for mname, impl in METHOD_IMPLEMENTATIONS.items():
        mstat = method_stats.get(mname, {'active': True, 'weight':1.0})
        if not mstat.get('active', True):
            details.append({'method': mname, 'active': False})
            continue
        weight = float(mstat.get('weight',1.0))
        try:
            toss_pred, match_pred, meta = impl(**row_ctx)
        except Exception as e:
            # method failed at runtime — mark as neutral
            details.append({'method': mname, 'error': str(e), 'weight': weight})
            continue
        # accumulate toss votes (None means neutral)
        if toss_pred:
            votes[toss_pred] = votes.get(toss_pred, 0.0) + weight
        # accumulate match votes
        if match_pred:
            match_votes[match_pred] = match_votes.get(match_pred, 0.0) + weight
        details.append({'method':mname, 'weight': weight, 'toss_pred': toss_pred, 'match_pred': match_pred, 'meta': meta})

    # choose top toss
    if not votes:
        final_toss = None
        toss_confidence = 0.0
    else:
        sorted_votes = sorted(votes.items(), key=lambda x: -x[1])
        top_name, top_score = sorted_votes[0]
        runner_up_score = sorted_votes[1][1] if len(sorted_votes)>1 else 0.0
        toss_confidence = top_score - runner_up_score
        # call unpredictable if margin small
        if toss_confidence <= UNPREDICTABLE_MARGIN:
            final_toss = "Unpredictable"
        else:
            final_toss = top_name

    # choose top match
    if not match_votes:
        final_match = None
        match_conf = 0.0
    else:
        sorted_mv = sorted(match_votes.items(), key=lambda x: -x[1])
        final_match = sorted_mv[0][0]
        match_conf = sorted_mv[0][1] - (sorted_mv[1][1] if len(sorted_mv)>1 else 0.0)

    aggregated = {
        'votes': votes,
        'match_votes': match_votes,
        'details': details,
        'toss_confidence': round(toss_confidence,3),
        'match_confidence': round(match_conf,3)
    }
    return final_toss, final_match, aggregated

# ---------------------
# Runner / Backtest main
# ---------------------
def main():
    # load method stats
    method_stats = load_method_stats(METHOD_STATS_FILE)

    # read input
    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(COL_ERR + f"Failed to read '{INPUT_FILE}': {e}" + COL_ERR)
        sys.exit(1)

    # ensure required columns present
    required_cols = ['Timestamp','Captain_A_Name','Captain_A_DOB','Captain_B_Name','Captain_B_DOB',
                     'Match_Date','Match_Time','Match_Place','Match_Format','TZ_Offset_Hours',
                     'Real_Toss','Real_Match']
    for c in required_cols:
        if c not in df.columns:
            df[c] = ''

    results_rows = []
    toss_correct = 0
    match_correct = 0
    n_rows = len(df) if len(df)>0 else 1

    for idx, row in df.iterrows():
        try:
            a_name = safe_str(row.get('Captain_A_Name',''))
            b_name = safe_str(row.get('Captain_B_Name',''))
            a_dob = safe_str(row.get('Captain_A_DOB','01/01/1980'))
            b_dob = safe_str(row.get('Captain_B_DOB','01/01/1980'))
            match_date_raw = safe_str(row.get('Match_Date','01/01/2025'))
            match_time_raw = safe_str(row.get('Match_Time','06:00'))
            match_place = safe_str(row.get('Match_Place','Unknown'))
            match_format = safe_str(row.get('Match_Format','T20')).upper()
            tz_offset = float(row.get('TZ_Offset_Hours', 0.0) or 0.0)

            # parse date - using robust helper
            match_date_obj, match_date_str = parse_match_date(match_date_raw)

            # numerology features
            a_bno = birth_number(a_dob)
            b_bno = birth_number(b_dob)
            a_lp = life_path_number(a_dob)
            b_lp = life_path_number(b_dob)
            a_nn = name_number(a_name)
            b_nn = name_number(b_name)
            dp = day_power(match_date_obj)
            pp = place_power(match_place)
            date_lp = date_life_path(match_date_str)
            score_a = a_lp + a_nn + dp + pp
            score_b = b_lp + b_nn + dp + pp

            # astro (moon/nakshatra) if available
            moon_lon = None
            moon_info = {'nakshatra':None,'lord':None,'pada':None}
            moon_sign = None
            moon_sign_lord = None
            if SWE_AVAILABLE:
                try:
                    dt_local = datetime.combine(match_date_obj, datetime.strptime(match_time_raw if match_time_raw else "06:00", "%H:%M").time())
                    jd = to_utc_jd_from_datetime(dt_local, tz_offset)
                    moon_lon = swe.calc_ut(jd, swe.MOON)[0][0] % 360
                    moon_info = moon_nakshatra_pada(moon_lon)
                    moon_sign = sign_from_long(moon_lon)[0]
                    # map moon sign to lord; simple mapping:
                    sign_lords = {"Aries":'Mars',"Taurus":'Venus',"Gemini":'Mercury',"Cancer":'Moon',"Leo":'Sun',"Virgo":'Mercury',
                                  "Libra":'Venus',"Scorpio":'Mars',"Sagittarius":'Jupiter',"Capricorn":'Saturn',"Aquarius":'Saturn',"Pisces":'Jupiter'}
                    moon_sign_lord = sign_lords.get(moon_sign,'Mars')
                except Exception:
                    moon_lon = None

            # prepare common row context passed to methods
            row_ctx = {
                'a_name': a_name, 'b_name': b_name,
                'a_bno': a_bno, 'b_bno': b_bno,
                'a_lp': a_lp, 'b_lp': b_lp,
                'a_nn': a_nn, 'b_nn': b_nn,
                'dp': dp, 'pp': pp,
                'date_lp': date_lp,
                'score_a': score_a, 'score_b': score_b,
                'match_date': match_date_obj, 'match_date_str': match_date_str,
                'match_time_raw': match_time_raw,
                'match_place': match_place, 'match_format': match_format,
                'tz_offset': tz_offset,
                'nak_info': moon_info,
                'nak_lord_planet': moon_info.get('lord'),
                'moon_sign_lord': moon_sign_lord
            }

            # Run ensemble weighted voting
            # adapt row_ctx keys to method signatures
            method_ctx = {
                'a_name': a_name, 'b_name': b_name,
                'a_bno': a_bno, 'b_bno': b_bno,
                'a_lp': a_lp, 'b_lp': b_lp,
                'a_nn': a_nn, 'b_nn': b_nn,
                'dp': dp, 'pp': pp,
                'date_lp': date_lp, 'score_a': score_a, 'score_b': score_b,
                'nak_lord_planet': moon_info.get('lord'), 'moon_sign_lord_planet': moon_sign_lord
            }

            final_toss, final_match, aggregated = weighted_vote_for_row(method_stats=method_stats_wrapper(method_stats:=load_method_stats(METHOD_STATS_FILE)), row_ctx=method_ctx) if False else weighted_vote_for_row(method_stats=method_stats, row_ctx=method_ctx)  # run normally

            # if final_toss is "Unpredictable", set predicted toss name to blank
            predicted_toss_name = final_toss if final_toss and final_toss != "Unpredictable" else ""

            # predicted match name (already a string or None)
            predicted_match_name = final_match if final_match else ""

            # Determine correctness vs actuals
            actual_toss = safe_str(row.get('Real_Toss',''))
            actual_match = safe_str(row.get('Real_Match',''))

            def normalize(s): return ' '.join(s.split()).lower()

            toss_ok = False
            match_ok = False
            if actual_toss:
                toss_ok = (predicted_toss_name and normalize(predicted_toss_name) == normalize(actual_toss))
            if actual_match:
                match_ok = (predicted_match_name and normalize(predicted_match_name) == normalize(actual_match))

            if toss_ok:
                toss_correct += 1
            if match_ok:
                match_correct += 1

            # Update method stats based on per-method contribution and actual results
            # For each method in aggregated['details'] that participated, check whether its toss/match prediction matched actuals
            for det in aggregated.get('details', []):
                m = det.get('method')
                if not m:
                    continue
                if not method_stats.get(m):
                    # add new method to stats with default
                    method_stats[m] = {'weight':1.0,'active':True,'success':0,'fail':0,'last_seen':None}
                # determine whether this method predicted toss/match in the way that matched actuals
                method_pred_toss = det.get('toss_pred') if det.get('toss_pred') else ""
                method_pred_match = det.get('match_pred') if det.get('match_pred') else ""
                # Evaluate toss correctness for method (only if it predicted a toss explicitly)
                method_toss_correct = False
                method_match_correct = False
                if actual_toss and method_pred_toss:
                    method_toss_correct = normalize(method_pred_toss) == normalize(actual_toss)
                if actual_match and method_pred_match:
                    method_match_correct = normalize(method_pred_match) == normalize(actual_match)
                # Combine results: we treat match correctness as higher priority; promote/demote by combined correctness metric
                combined_correct = False
                if actual_match:
                    combined_correct = method_match_correct
                elif actual_toss:
                    combined_correct = method_toss_correct
                # promote/demote
                promote_method(method_stats, m, combined_correct)

            # store row-level output for writing
            results_rows.append({
                'Predicted_Toss_Name': predicted_toss_name,
                'Predicted_Match_Name': predicted_match_name,
                'Final_Toss_Ensemble': final_toss,
                'Final_Match_Ensemble': final_match,
                'Toss_Confidence': aggregated.get('toss_confidence'),
                'Match_Confidence': aggregated.get('match_confidence'),
                'Method_Details': json.dumps(aggregated.get('details',[]), default=str),
                'Score_A': score_a,
                'Score_B': score_b,
                'Innings_Trend_A': predict_innings_trend(score_a, a_lp, a_nn, dp, pp, score_a > score_b),
                'Innings_Trend_B': predict_innings_trend(score_b, b_lp, b_nn, dp, pp, score_b > score_a),
                'Actual_Toss': actual_toss,
                'Actual_Match': actual_match,
                'Toss_Correct': toss_ok,
                'Match_Correct': match_ok
            })

        except Exception as e_row:
            # keep going, but record error in results
            results_rows.append({
                'Predicted_Toss_Name': '',
                'Predicted_Match_Name': '',
                'Final_Toss_Ensemble': f"ERROR: {e_row}",
                'Final_Match_Ensemble': '',
                'Toss_Confidence': 0,
                'Match_Confidence': 0,
                'Method_Details': '[]',
                'Score_A': '',
                'Score_B': '',
                'Innings_Trend_A': '',
                'Innings_Trend_B': '',
                'Actual_Toss': safe_str(row.get('Real_Toss','')),
                'Actual_Match': safe_str(row.get('Real_Match','')),
                'Toss_Correct': False,
                'Match_Correct': False
            })
            continue

    # After processing all rows, persist updated method stats
    save_method_stats(METHOD_STATS_FILE, method_stats)

    # Build summary and write Excel outputs
    results_df = pd.DataFrame(results_rows)
    # append results as new columns to original df
    for col in results_df.columns:
        df[col] = results_df[col].values

    total = len(df) if len(df)>0 else 1
    toss_accuracy = (toss_correct/total)*100
    match_accuracy = (match_correct/total)*100

    summary = {
        'Total_Rows':[total],
        'Toss_Correct_Count':[toss_correct],
        'Match_Correct_Count':[match_correct],
        'Toss_Accuracy_%':[round(toss_accuracy,2)],
        'Match_Accuracy_%':[round(match_accuracy,2)]
    }
    summary_df = pd.DataFrame(summary)

    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Input_with_Predictions')
            results_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')
        print(COL_OK + f"Backtest complete. Output written to: {OUTPUT_FILE}")
        print(f" Toss accuracy: {round(toss_accuracy,2)}%  Match accuracy: {round(match_accuracy,2)}%")
        print(COL_INFO + f"Method stats saved to: {METHOD_STATS_FILE}")
    except Exception as e_write:
        print(COL_ERR + f"Failed to write output: {e_write}")

# ---------------------
# Small helper used above (predict_innings_trend)
# ---------------------
def predict_innings_trend(score, lp, nn, dp, pp, is_winner):
    # condensed / crisp phrasing for Excel-friendly output
    start_score = dp + pp
    if start_score >= 14:
        start = "Strong start"
    elif start_score >= 8:
        start = "Steady start"
    else:
        start = "Slow start"
    if nn >= 5:
        middle = "Dominant middle"
    else:
        middle = "Balanced middle"
    end = "Decisive finish" if is_winner else ("Competitive finish" if lp >= 6 else "Below-par finish")
    return f"{start} → {middle} → {end}"

# ---------------------
# Run
# ---------------------
if __name__ == '__main__':
    main()
