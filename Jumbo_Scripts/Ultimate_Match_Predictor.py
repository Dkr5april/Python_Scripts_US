#!/usr/bin/env python3
"""
Ultimate Learning Match Predictor (Numerology + Astrology + ML Hybrid)
- Backtestable, persistent learning of method weights
- Ensemble of many heuristic methods (numerology, astrology, venue, element, moon phase)
- Optional ML layer (scikit-learn) trained on historical labeled matches for match prediction
- Persists method_stats.json and ml_model.pkl
- Writes detailed Excel output: Input_with_Predictions, Backtest_Results, Backtest_Summary

Usage:
  - Place match_analysis_data.xlsx in same folder
  - Run: python ultimate_match_predictor.py
  - Optional deps: pandas, openpyxl, pyswisseph, scikit-learn, colorama

Notes:
  - Script auto-detects available libraries and gracefully falls back
  - Tunable constants near top for learning aggressiveness
"""

import sys
import os
import json
import math
import random
from datetime import datetime, date, time, timedelta, timezone
from typing import Dict, Any, Tuple, List

import pandas as pd

# Optional astrology (pyswisseph)
try:
    import swisseph as swe
    SWE_AVAILABLE = True
except Exception:
    swe = None
    SWE_AVAILABLE = False

# Optional ML (scikit-learn)
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKL_AVAILABLE = True
except Exception:
    SKL_AVAILABLE = False

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

# ---------------------
# Config / constants
# ---------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"
ML_MODEL_FILE = "ml_model.pkl"

# Learning hyperparams
WEIGHT_PROMOTE_STEP = 0.10
WEIGHT_DEMOTE_STEP = 0.08
WEIGHT_MIN = 0.05
WEIGHT_MAX = 3.0
RETIRE_AFTER_WEIGHT_BELOW = 0.08
RETIRE_FAIL_RATIO = 2.5
MIN_TOTAL_EVAL = 5
UNPREDICTABLE_MARGIN = 0.5

# ML params
ML_ENABLED = True
ML_MIN_ROWS_TO_TRAIN = 20  # require at least this many labeled rows
ML_MODEL_TYPE = 'rf'  # 'rf' or 'lr'

# Numerology maps
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
GOOD_PAIRS = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

DAY_LORDS = {0:'Moon',1:'Mars',2:'Mercury',3:'Jupiter',4:'Venus',5:'Saturn',6:'Sun'}
PLANET_NUMBERS = {'Sun':1,'Moon':2,'Jupiter':3,'Rahu':4,'Mercury':5,'Venus':6,'Ketu':7,'Saturn':8,'Mars':9}

# ---------------------
# Utility functions
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
    except Exception:
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

# ---------------------
# Astro helpers (swisseph if available)
# ---------------------

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
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
        'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury',
        'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury',
        'Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury'
    ]
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada, "lord": lord}

# ---------------------
# Date parsing helper (no infer_datetime_format)
# ---------------------

def parse_match_date(raw: str) -> Tuple[date,str]:
    s = safe_str(raw)
    formats = ["%d/%m/%Y","%Y-%m-%d","%Y/%m/%d","%d-%m-%Y","%d %b %Y","%d %B %Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date(), dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s, dayfirst=False)
        d = dt.date()
        return d, d.strftime("%d/%m/%Y")
    except Exception:
        d = date.today()
        return d, d.strftime("%d/%m/%Y")

# ---------------------
# New heuristic methods (more coverage)
# Each method returns: (toss_name_or_None, match_name_or_None, meta)
# ---------------------

def method_compound_score(a_name, b_name, score_a, score_b, **kwargs):
    toss = a_name if score_a > score_b else (b_name if score_b > score_a else None)
    predicted_match = toss
    return toss, predicted_match, {'method':'compound_score','score_a':score_a,'score_b':score_b}


def method_ruling_number(a_name,b_name,dp,pp,a_bno,b_bno,**kwargs):
    ruling_no = reduce_num(dp + pp)
    a_diff = abs(a_bno - ruling_no); b_diff = abs(b_bno - ruling_no)
    toss = a_name if a_diff < b_diff else (b_name if b_diff < a_diff else None)
    predicted_match = a_name if a_bno <= b_bno else b_name
    return toss,predicted_match,{'method':'ruling_no','ruling_no':ruling_no}


def method_day_lord(a_name,b_name,day_lord_planet,a_bno,b_bno,**kwargs):
    day_lord_num = PLANET_NUMBERS.get(day_lord_planet,0)
    a_match = (a_bno,day_lord_num) in GOOD_PAIRS
    b_match = (b_bno,day_lord_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_match else (b_name if b_match else (a_name if a_bno>=b_bno else b_name))
    return toss,predicted_match,{'method':'day_lord','planet':day_lord_planet}


def method_star_lord(a_name,b_name,nak_lord,a_nn,b_nn,**kwargs):
    star_num = PLANET_NUMBERS.get(nak_lord,0)
    a_match = (a_nn,star_num) in GOOD_PAIRS
    b_match = (b_nn,star_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_nn >= b_nn else b_name
    return toss,predicted_match,{'method':'star_lord','nak_lord':nak_lord}


def method_moon_sign(a_name,b_name,moon_sign_lord,a_bno,b_bno,**kwargs):
    moon_num = PLANET_NUMBERS.get(moon_sign_lord,0)
    a_match = (a_bno,moon_num) in GOOD_PAIRS
    b_match = (b_bno,moon_num) in GOOD_PAIRS
    toss = a_name if a_match and not b_match else (b_name if b_match and not a_match else None)
    predicted_match = a_name if a_match else (b_name if b_match else (a_name if a_bno>=b_bno else b_name))
    return toss,predicted_match,{'method':'moon_sign','moon_lord':moon_sign_lord}


def method_random(a_name,b_name,**kwargs):
    toss = random.choice([a_name,b_name,None])
    predicted_match = random.choice([a_name,b_name])
    return toss,predicted_match,{'method':'random'}

# New methods: element compatibility, moon_phase, planetary_hour, lagna_compat

def element_of_name(name: str) -> str:
    # simple heuristic mapping by starting letter
    s = safe_str(name).upper()
    if not s: return 'Neutral'
    first = s[0]
    if first in 'ABCG': return 'Fire'
    if first in 'HIJKL': return 'Earth'
    if first in 'MNOPQ': return 'Air'
    if first in 'RSTUVWXYZ': return 'Water'
    return 'Neutral'


def method_element_compat(a_name,b_name,**kwargs):
    a_el = element_of_name(a_name); b_el = element_of_name(b_name)
    # if different elements, toss to more 'flexible' element (Air/Fire)
    score_map = {'Fire':2,'Air':2,'Earth':1,'Water':1}
    a_score = score_map.get(a_el,1); b_score = score_map.get(b_el,1)
    toss = a_name if a_score > b_score else (b_name if b_score > a_score else None)
    predicted_match = a_name if a_score >= b_score else b_name
    return toss,predicted_match,{'method':'element_compat','a_el':a_el,'b_el':b_el}


def moon_phase_on_date(d: date) -> str:
    # approximate moon phase by age: new(0)-full(14)-new(29)
    # Use known new moon reference: 2000-01-06 18:14 UTC JD 2451550.26 (approx)
    # Simpler: use synodic month 29.53058867 days
    ref = datetime(2000,1,6,18,14)
    diff = datetime.combine(d, time()) - ref
    days = diff.total_seconds()/86400.0
    age = days % 29.53058867
    if age < 1.9: return 'New'
    if age < 7.4: return 'Waxing Crescent'
    if age < 10.9: return 'First Quarter'
    if age < 15.2: return 'Waxing Gibbous/Full'
    if age < 22.1: return 'Waning Gibbous/Last Quarter'
    return 'Waning Crescent'


def method_moon_phase(a_name,b_name,match_date,**kwargs):
    phase = moon_phase_on_date(match_date)
    # heuristic: Full/Waxing -> aggressive toss to team with higher name number
    a_nn = kwargs.get('a_nn',0); b_nn = kwargs.get('b_nn',0)
    if 'Full' in phase or 'Waxing' in phase:
        toss = a_name if a_nn >= b_nn else b_name
    else:
        toss = a_name if a_nn <= b_nn else b_name
    predicted_match = toss
    return toss,predicted_match,{'method':'moon_phase','phase':phase}


def method_planetary_hour(a_name,b_name,match_date,match_time_str,tz_offset=0,**kwargs):
    # Very simple planetary hour heuristic: use hour of day modulo 9 mapping
    try:
        t = datetime.strptime(match_time_str, '%H:%M').time()
        hour = t.hour
    except Exception:
        hour = 6
    mapping = {0:a_name,1:b_name,2:a_name,3:b_name,4:a_name,5:b_name,6:a_name,7:b_name,8:a_name}
    toss = mapping.get(hour%9,None)
    predicted_match = toss
    return toss,predicted_match,{'method':'planetary_hour','hour':hour}

# ---------------------
# METHOD IMPLEMENTATION REGISTRY
# ---------------------
METHOD_IMPLEMENTATIONS = {
    'compound_score': method_compound_score,
    'ruling_number': method_ruling_number,
    'day_lord': method_day_lord,
    'star_lord': method_star_lord,
    'moon_sign': method_moon_sign,
    'element_compat': method_element_compat,
    'moon_phase': method_moon_phase,
    'planetary_hour': method_planetary_hour,
    'numerology_random': method_random
}

# ---------------------
# Method stats persistence
# ---------------------
def load_method_stats(path: str) -> Dict[str,Any]:
    default = {}
    for name in METHOD_IMPLEMENTATIONS.keys():
        default[name] = {'weight': 1.0 if name!='numerology_random' else 0.4, 'active': True, 'success':0, 'fail':0, 'last_seen': None}
    if os.path.exists(path):
        try:
            with open(path,'r') as f:
                data = json.load(f)
            for k,v in default.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return default
    return default


def save_method_stats(path: str, stats: Dict[str,Any]):
    with open(path,'w') as f:
        json.dump(stats, f, indent=2, default=str)


def promote_method(stats: Dict[str,Any], method: str, correct: bool):
    if method not in stats:
        stats[method] = {'weight':1.0,'active':True,'success':0,'fail':0,'last_seen':None}
    entry = stats[method]
    entry['last_seen'] = datetime.now(timezone.utc).isoformat()
    if correct:
        entry['success'] = entry.get('success',0) + 1
        entry['weight'] = min(WEIGHT_MAX, entry.get('weight',1.0) + WEIGHT_PROMOTE_STEP)
    else:
        entry['fail'] = entry.get('fail',0) + 1
        entry['weight'] = max(0.0, entry.get('weight',1.0) - WEIGHT_DEMOTE_STEP)
    total = entry.get('success',0) + entry.get('fail',0)
    if entry['weight'] < RETIRE_AFTER_WEIGHT_BELOW and total >= MIN_TOTAL_EVAL:
        entry['active'] = False
    if total >= MIN_TOTAL_EVAL and entry.get('fail',0) > entry.get('success',0)*RETIRE_FAIL_RATIO:
        entry['active'] = False
    if entry['weight'] < WEIGHT_MIN:
        entry['active'] = False
    stats[method] = entry

# ---------------------
# Ensemble voting
# ---------------------
def weighted_vote_for_row(method_stats, ctx) -> Tuple[str,str,Dict[str,Any]]:
    votes = {}
    match_votes = {}
    details = []
    for mname,impl in METHOD_IMPLEMENTATIONS.items():
        mstat = method_stats.get(mname, {'active':True,'weight':1.0})
        if not mstat.get('active',True):
            details.append({'method':mname,'active':False})
            continue
        weight = float(mstat.get('weight',1.0))
        try:
            toss_pred, match_pred, meta = impl(**ctx)
        except Exception as e:
            details.append({'method':mname,'error':str(e),'weight':weight})
            continue
        if toss_pred:
            votes[toss_pred] = votes.get(toss_pred,0.0) + weight
        if match_pred:
            match_votes[match_pred] = match_votes.get(match_pred,0.0) + weight
        details.append({'method':mname,'weight':weight,'toss_pred':toss_pred,'match_pred':match_pred,'meta':meta})
    # compute final toss
    if not votes:
        final_toss = None; toss_conf = 0.0
    else:
        sorted_votes = sorted(votes.items(), key=lambda x:-x[1])
        top_name,top_score = sorted_votes[0]
        runner_up = sorted_votes[1][1] if len(sorted_votes)>1 else 0.0
        toss_conf = top_score - runner_up
        final_toss = "Unpredictable" if toss_conf <= UNPREDICTABLE_MARGIN else top_name
    # compute final match
    if not match_votes:
        final_match = None; match_conf = 0.0
    else:
        sorted_mv = sorted(match_votes.items(), key=lambda x:-x[1])
        final_match = sorted_mv[0][0]
        match_conf = sorted_mv[0][1] - (sorted_mv[1][1] if len(sorted_mv)>1 else 0.0)
    return final_toss, final_match, {'votes':votes,'match_votes':match_votes,'details':details,'toss_confidence':round(toss_conf,3),'match_confidence':round(match_conf,3)}

# ---------------------
# ML helper: create features from row
# ---------------------
def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame,pd.Series]:
    # build numeric features for ML from available columns
    X = pd.DataFrame()
    X['A_birth_no'] = df['Captain_A_DOB'].fillna('').apply(lambda s: birth_number(s))
    X['B_birth_no'] = df['Captain_B_DOB'].fillna('').apply(lambda s: birth_number(s))
    X['A_life'] = df['Captain_A_DOB'].fillna('').apply(lambda s: life_path_number(s))
    X['B_life'] = df['Captain_B_DOB'].fillna('').apply(lambda s: life_path_number(s))
    X['A_name_no'] = df['Captain_A_Name'].fillna('').apply(lambda s: name_number(s))
    X['B_name_no'] = df['Captain_B_Name'].fillna('').apply(lambda s: name_number(s))
    # date features
    X['day'] = pd.to_datetime(df['Match_Date'], errors='coerce').dt.day.fillna(1).astype(int)
    X['month'] = pd.to_datetime(df['Match_Date'], errors='coerce').dt.month.fillna(1).astype(int)
    X['weekday'] = pd.to_datetime(df['Match_Date'], errors='coerce').dt.weekday.fillna(0).astype(int)
    X['dp'] = df['Match_Date'].fillna('').apply(lambda s: day_power(parse_match_date(s)[0]))
    X['pp'] = df['Match_Place'].fillna('').apply(lambda s: place_power(s))
    # score diffs
    X['score_proxy_diff'] = (X['A_life']+X['A_name_no']+X['dp']+X['pp']) - (X['B_life']+X['B_name_no']+X['dp']+X['pp'])
    return X

# train ML model for match winner using available labeled rows
def train_ml_model(df: pd.DataFrame) -> Any:
    if not SKL_AVAILABLE:
        return None
    # require Real_Match present
    labeled = df[df['Real_Match'].notna() & (df['Real_Match']!='')]
    if len(labeled) < ML_MIN_ROWS_TO_TRAIN:
        return None
    X = build_features(labeled)
    # target: 1 if A wins else 0 (assumes Real_Match contains A or B name)
    def target_fn(row):
        rm = safe_str(row['Real_Match']).lower()
        a = safe_str(row['Captain_A_Name']).lower()
        return 1 if a and a in rm else 0
    y = labeled.apply(target_fn, axis=1)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    if ML_MODEL_TYPE == 'rf':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    else:
        model = LogisticRegression(max_iter=1000)
    model.fit(Xs, y)
    joblib.dump({'model':model,'scaler':scaler}, ML_MODEL_FILE)
    return {'model':model,'scaler':scaler}

def load_ml_model():
    if not SKL_AVAILABLE or not os.path.exists(ML_MODEL_FILE):
        return None
    try:
        m = joblib.load(ML_MODEL_FILE)
        return m
    except Exception:
        return None

# ---------------------
# Main backtest runner
# ---------------------
def main():
    # load method stats
    method_stats = load_method_stats(METHOD_STATS_FILE)
    ml_model = load_ml_model()

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(COL_ERR + f"Failed to read '{INPUT_FILE}': {e}")
        sys.exit(1)

    # ensure columns exist
    required = ['Timestamp','Captain_A_Name','Captain_A_DOB','Captain_B_Name','Captain_B_DOB','Match_Date','Match_Time','Match_Place','Match_Format','TZ_Offset_Hours','Real_Toss','Real_Match']
    for c in required:
        if c not in df.columns:
            df[c] = ''

    results = []
    toss_correct = 0
    match_correct = 0
    n = len(df) if len(df)>0 else 1

    # optional: train ML on file if enough labeled rows
    if ML_ENABLED and SKL_AVAILABLE:
        trained = train_ml_model(df)
        if trained:
            ml_model = trained
            print(COL_INFO + "ML model trained from input data and saved.")

    for idx,row in df.iterrows():
        try:
            a_name = safe_str(row['Captain_A_Name'])
            b_name = safe_str(row['Captain_B_Name'])
            a_dob = safe_str(row['Captain_A_DOB'])
            b_dob = safe_str(row['Captain_B_DOB'])
            match_date_raw = safe_str(row['Match_Date'])
            match_time_raw = safe_str(row['Match_Time'])
            match_place = safe_str(row['Match_Place'])
            match_format = safe_str(row['Match_Format']).upper()
            tz_offset = float(row.get('TZ_Offset_Hours',0) or 0.0)

            match_date_obj, match_date_str = parse_match_date(match_date_raw)

            a_bno = birth_number(a_dob); b_bno = birth_number(b_dob)
            a_lp = life_path_number(a_dob); b_lp = life_path_number(b_dob)
            a_nn = name_number(a_name); b_nn = name_number(b_name)
            dp = day_power(match_date_obj)
            pp = place_power(match_place)
            date_lp = date_life_path(match_date_str)
            score_a = a_lp + a_nn + dp + pp
            score_b = b_lp + b_nn + dp + pp

            moon_info = {'nakshatra':None,'lord':None,'pada':None}
            moon_sign_lord = None
            if SWE_AVAILABLE:
                try:
                    dt_local = datetime.combine(match_date_obj, datetime.strptime(match_time_raw if match_time_raw else '06:00','%H:%M').time())
                    jd = to_utc_jd_from_datetime(dt_local, tz_offset)
                    moon_lon = swe.calc_ut(jd, swe.MOON)[0][0] % 360
                    moon_info = moon_nakshatra_pada(moon_lon)
                    moon_sign = sign_from_long(moon_lon)[0]
                    sign_lords = {"Aries":'Mars',"Taurus":'Venus',"Gemini":'Mercury',"Cancer":'Moon',"Leo":'Sun',"Virgo":'Mercury',"Libra":'Venus',"Scorpio":'Mars',"Sagittarius":'Jupiter',"Capricorn":'Saturn',"Aquarius":'Saturn',"Pisces":'Jupiter'}
                    moon_sign_lord = sign_lords.get(moon_sign,'Mars')
                except Exception:
                    moon_info = {'nakshatra':None,'lord':None,'pada':None}

            # build method context
            ctx = {
                'a_name':a_name,'b_name':b_name,'a_bno':a_bno,'b_bno':b_bno,'a_lp':a_lp,'b_lp':b_lp,
                'a_nn':a_nn,'b_nn':b_nn,'dp':dp,'pp':pp,'date_lp':date_lp,'score_a':score_a,'score_b':score_b,
                'match_date':match_date_obj,'match_date_str':match_date_str,'match_time_str':match_time_raw,'match_place':match_place,'match_format':match_format,
                'tz_offset':tz_offset,'nak_info':moon_info,'nak_lord':moon_info.get('lord'),'moon_sign_lord':moon_sign_lord
            }

            final_toss, final_match, agg = weighted_vote_for_row(method_stats, ctx)

            # if ML available and model loaded, use ML to provide match prediction probability
            ml_pred = None
            ml_prob = None
            if ml_model:
                try:
                    single = pd.DataFrame([{
                        'Captain_A_DOB':a_dob,'Captain_B_DOB':b_dob,'Captain_A_Name':a_name,'Captain_B_Name':b_name,'Match_Date':match_date_str,'Match_Place':match_place
                    }])
                    X = build_features(single)
                    scaler = ml_model['scaler']; model = ml_model['model']
                    Xs = scaler.transform(X)
                    p = model.predict_proba(Xs)[0]
                    prob_a = p[1]
                    ml_prob = prob_a
                    ml_pred = a_name if prob_a>=0.5 else b_name
                    # if ensemble confidence low, prefer ML
                    if agg.get('match_confidence',0) <= UNPREDICTABLE_MARGIN:
                        final_match = ml_pred
                except Exception:
                    pass

            predicted_toss_name = final_toss if final_toss and final_toss!='Unpredictable' else ''
            predicted_match_name = final_match if final_match else ''

            actual_toss = safe_str(row.get('Real_Toss',''))
            actual_match = safe_str(row.get('Real_Match',''))
            def normalize(s): return ' '.join(s.split()).lower()
            toss_ok = False; match_ok = False
            if actual_toss and predicted_toss_name:
                toss_ok = normalize(actual_toss) == normalize(predicted_toss_name)
            if actual_match and predicted_match_name:
                match_ok = normalize(actual_match) == normalize(predicted_match_name)
            if toss_ok: toss_correct += 1
            if match_ok: match_correct += 1

            # update method stats based on per-method details
            for det in agg.get('details',[]):
                m = det.get('method')
                if not m: continue
                if m not in method_stats:
                    method_stats[m] = {'weight':1.0,'active':True,'success':0,'fail':0,'last_seen':None}
                method_pred_toss = det.get('toss_pred') or ''
                method_pred_match = det.get('match_pred') or ''
                method_toss_correct = False; method_match_correct = False
                if actual_toss and method_pred_toss:
                    method_toss_correct = normalize(method_pred_toss) == normalize(actual_toss)
                if actual_match and method_pred_match:
                    method_match_correct = normalize(method_pred_match) == normalize(actual_match)
                combined_correct = False
                if actual_match:
                    combined_correct = method_match_correct
                elif actual_toss:
                    combined_correct = method_toss_correct
                promote_method(method_stats, m, combined_correct)

            results.append({
                'Predicted_Toss_Name':predicted_toss_name,
                'Predicted_Match_Name':predicted_match_name,
                'Final_Toss_Ensemble':final_toss,
                'Final_Match_Ensemble':final_match,
                'Toss_Confidence':agg.get('toss_confidence'),
                'Match_Confidence':agg.get('match_confidence'),
                'ML_Predicted_Match': ml_pred,
                'ML_Prob_A': ml_prob,
                'Method_Details': json.dumps(agg.get('details',[]), default=str),
                'Score_A':score_a,'Score_B':score_b,
                'Innings_Trend_A': predict_innings_trend(score_a,a_lp,a_nn,dp,pp,score_a>score_b),
                'Innings_Trend_B': predict_innings_trend(score_b,b_lp,b_nn,dp,pp,score_b>score_a),
                'Actual_Toss': actual_toss,'Actual_Match': actual_match,'Toss_Correct': toss_ok,'Match_Correct': match_ok
            })

        except Exception as e:
            results.append({'Predicted_Toss_Name':'','Predicted_Match_Name':'','Final_Toss_Ensemble':f"ERROR: {e}",'Final_Match_Ensemble':'','Toss_Confidence':0,'Match_Confidence':0,'Method_Details':'[]','Score_A':'','Score_B':'','Innings_Trend_A':'','Innings_Trend_B':'','Actual_Toss':safe_str(row.get('Real_Toss','')),'Actual_Match':safe_str(row.get('Real_Match','')),'Toss_Correct':False,'Match_Correct':False})
            continue

    # persist method stats & ML model
    save_method_stats(METHOD_STATS_FILE, method_stats)

    # append results to df and save Excel
    res_df = pd.DataFrame(results)
    for col in res_df.columns:
        df[col] = res_df[col].values

    total = len(df) if len(df)>0 else 1
    toss_acc = (toss_correct/total)*100
    match_acc = (match_correct/total)*100
    summary = {'Total_Rows':[total],'Toss_Correct_Count':[toss_correct],'Match_Correct_Count':[match_correct],'Toss_Accuracy_%':[round(toss_acc,2)],'Match_Accuracy_%':[round(match_acc,2)]}
    summary_df = pd.DataFrame(summary)

    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Input_with_Predictions')
            res_df.to_excel(writer, index=False, sheet_name='Backtest_Results')
            summary_df.to_excel(writer, index=False, sheet_name='Backtest_Summary')
        print(COL_OK + f"Backtest complete. Output written to: {OUTPUT_FILE}")
        print(f" Toss accuracy: {round(toss_acc,2)}%  Match accuracy: {round(match_acc,2)}%")
        print(COL_INFO + f"Method stats saved to: {METHOD_STATS_FILE}")
        if SKL_AVAILABLE and os.path.exists(ML_MODEL_FILE):
            print(COL_INFO + f"ML model (if trained) saved to: {ML_MODEL_FILE}")
    except Exception as e:
        print(COL_ERR + f"Failed to write output: {e}")

# ---------------------
# condensed innings trend helper
# ---------------------
def predict_innings_trend(score, lp, nn, dp, pp, is_winner):
    start_score = dp + pp
    if start_score >= 14: start = "Strong start"
    elif start_score >= 8: start = "Steady start"
    else: start = "Slow start"
    middle = "Dominant middle" if nn>=5 else "Balanced middle"
    end = "Decisive finish" if is_winner else ("Competitive finish" if lp>=6 else "Below-par finish")
    return f"{start} → {middle} → {end}"

# ---------------------
# Run
# ---------------------
if __name__ == '__main__':
    main()

