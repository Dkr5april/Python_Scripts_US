#!/usr/bin/env python3
"""
Ultimate Match Predictor — V7 UPGRADE: Aggressive Learning + Jamakkol Astrology

Features:
- V6 SBC + KOTA + Ensemble retained
- Jamakkol Astrology added for Toss & Match predictions
- Toss Time = Match Time - 30 minutes
- City-based Sunrise/Sunset/Next Sunrise calculation
- Udayam, Kavipu, Arudam, Jama planets, Chatram
- Confidence-gated Jamakkol voting
"""

import sys, os, json, pandas as pd
from datetime import datetime, date, timedelta
from dateutil import parser
from typing import Dict, Any, Union
from astral import LocationInfo
from astral.sun import sun
import pytz
import time

# ---------------------------
# Config / Files
# ---------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"
TIMESTAMP_COL = "Timestamp"

# Hyperparameters
WEIGHT_PROMOTE_STEP = 0.25
WEIGHT_DEMOTE_STEP = 0.30
WEIGHT_MIN = 0.05
WEIGHT_MAX = 8.0
RETIRE_AFTER_WEIGHT_BELOW = 0.15
RETIRE_FAIL_RATIO = 2.0
MIN_TOTAL_EVAL = 3
UNPREDICTABLE_MARGIN = 0.3
REVIVAL_WINDOW = 20

# Stadium direction mapping
STADIUM_DIRECTION_MAP = {
    "NORTH": 1, "EAST": 1, "SOUTH": 2, "WEST": 2,
    "NORTHEAST": 1, "NORTHWEST": 2,
    "SOUTHEAST": 1, "SOUTHWEST": 2,
    "CENTER": 0, "NEUTRAL": 0
}

# Color energy mapping
COLOR_ENERGY_MAP = {
    "RED": 9, "BLUE": 8, "GREEN": 5, "YELLOW": 3, "ORANGE": 1,
    "WHITE": 6, "BLACK": 4, "GREY": 4, "PURPLE": 7, "PINK": 9,
    "BROWN": 4, "GOLD": 1, "SILVER": 2, "MAROON": 9, "CRIMSON": 9,
    "NAVY": 8, "LIME": 5, "TURQUOISE": 5
}

# Australia City Coordinates
CITY_COORDS = {
    "Perth": (-31.9523, 115.8613),
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Brisbane": (-27.4698, 153.0251),
    "Adelaide": (-34.9285, 138.6007),
    "Hobart": (-42.8821, 147.3272),
    "Canberra": (-35.2809, 149.1300),
    "Geelong": (-38.1499, 144.3617),
    "Coffs Harbour": (-30.2963, 153.1157)
}

# Jamakkol planet sequences
DAY_JAMA_PLANETS = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars", "Rahu"]
NIGHT_JAMA_PLANETS = ["Moon", "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Ketu"]
PLANET_STRENGTH = {"Sun":1,"Moon":2,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":6,"Saturn":8,"Rahu":4,"Ketu":7}

# ---------------------------
# Helper functions
# ---------------------------
def safe_str(x: Any) -> str:
    if pd.isna(x): return ""
    if isinstance(x,(float,int)): return str(int(x)) if x==int(x) else str(x)
    if isinstance(x,(pd.Timestamp,datetime,date)): return str(x)
    s=str(x).strip()
    return s if s not in ['','nan','NaT'] else ''

def standardize_name(name: str) -> str:
    return safe_str(name).lower().replace(' ','').replace('_','')

def strong_match(predicted_name: str, actual_name: str) -> bool:
    return standardize_name(predicted_name) == standardize_name(actual_name)

def reduce_to_single(n: Union[int,float,str]) -> int:
    try: n_int=int(str(n).split('.')[0])
    except: return 0
    while n_int>9: n_int=sum(int(d) for d in str(n_int))
    return n_int

def get_numerology_number(name: str) -> int:
    mapping={'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':2,'s':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}
    name=safe_str(name).lower().replace(' ','')
    total=sum(mapping.get(char,0) for char in name)
    return reduce_to_single(total)

def safe_parse_date(date_input: Any) -> date | None:
    if pd.isna(date_input): return None
    if isinstance(date_input,date): return date_input
    if isinstance(date_input,pd.Timestamp): return date_input.date()
    try: return parser.parse(safe_str(date_input)).date()
    except: return None

def get_lp_nn_dp(dob_str: Any) -> Dict[str,int]:
    dt=safe_parse_date(dob_str)
    if dt is None: return {'lp':0,'nn':0,'dp':0}
    dp=reduce_to_single(dt.day)
    nn=reduce_to_single(dt.day+dt.month+dt.year)
    lp=reduce_to_single(dt.month+dt.year)
    return {'lp':lp,'nn':nn,'dp':dp}

def get_moon_phase_day(match_date: date) -> int:
    day_of_year = match_date.timetuple().tm_yday
    return day_of_year % 30

def get_color_number(color_name: str) -> int:
    color=safe_str(color_name).strip().upper()
    for k,v in COLOR_ENERGY_MAP.items():
        if k in color: return v
    return 0

def generate_iso_timestamp(): return datetime.now().isoformat(timespec='seconds')

# ---------------------------
# Jamakkol / Astrology
# ---------------------------
def normalize_city(match_place: str) -> str | None:
    place=safe_str(match_place).lower()
    for city in CITY_COORDS:
        if city.lower() in place: return city
    return None

def get_sun_times_from_place(match_place: str, match_date: date):
    city=normalize_city(match_place)
    if not city: return None
    lat, lon=CITY_COORDS[city]
    tz="Australia/Sydney"
    if city=="Perth": tz="Australia/Perth"
    elif city=="Brisbane": tz="Australia/Brisbane"
    elif city=="Adelaide": tz="Australia/Adelaide"
    elif city=="Hobart": tz="Australia/Hobart"
    loc=LocationInfo(city,"",tz,lat,lon)
    s_today=sun(loc.observer,date=match_date,tzinfo=pytz.timezone(tz))
    s_next=sun(loc.observer,date=match_date+timedelta(days=1),tzinfo=pytz.timezone(tz))
    return {"city":city,"sunrise":s_today["sunrise"],"sunset":s_today["sunset"],"next_sunrise":s_next["sunrise"]}

def get_toss_time(match_time: datetime) -> datetime:
    return match_time - timedelta(minutes=30)

def get_kalam_index(event_time: datetime, sunrise: datetime, sunset: datetime, next_sunrise: datetime):
    if sunrise <= event_time < sunset:
        total=(sunset-sunrise).total_seconds()
        slot=total/8
        index=int((event_time-sunrise).total_seconds()/slot)
        return ("DAY", min(index,7))
    else:
        total=(next_sunrise-sunset).total_seconds()
        slot=total/8
        index=int((event_time-sunset).total_seconds()/slot)
        return ("NIGHT", min(index,7))

def get_jama_planet(day_or_night: str, kalam_index: int) -> str:
    return DAY_JAMA_PLANETS[kalam_index] if day_or_night=="DAY" else NIGHT_JAMA_PLANETS[kalam_index]

# ---------------------------
# Core methods: SBC, KOTA, Ensemble
# ---------------------------
def calculate_sbc(row_data: dict) -> int:
    return 1 if get_numerology_number(row_data.get('captain_a_name',''))>get_numerology_number(row_data.get('captain_b_name','')) else 2

def calculate_kota(row_data: dict) -> int:
    match_date=safe_parse_date(row_data.get('match_date'))
    if not match_date: return 0
    match_date_nn=reduce_to_single(match_date.day)
    return 1 if reduce_to_single(match_date_nn+1)%2==0 else 2

def get_sbc_kota_override(sbc_vote:int,kota_vote:int,votes:Dict[int,float])->int:
    if sbc_vote==kota_vote and sbc_vote!=0:
        total_votes=sum(votes.values())
        if total_votes>0:
            strongest_vote=max(votes.values())
            if strongest_vote/total_votes<0.75: return sbc_vote
    return 0

def ensemble_vote_v7(votes:Dict[int,float],sbc_vote:int,kota_vote:int,match_date_nn:int)->tuple:
    if not votes: return 0,0.0
    total_votes=sum(votes.values())
    if total_votes==0: return 0,0.0
    vote_tally={1:votes.get(1,0.0),2:votes.get(2,0.0)}
    if vote_tally[1]>vote_tally[2]: winner=1;winner_votes=vote_tally[1];runner_up_votes=vote_tally[2]
    elif vote_tally[2]>vote_tally[1]: winner=2;winner_votes=vote_tally[2];runner_up_votes=vote_tally[1]
    else: winner=0;winner_votes=vote_tally[1];runner_up_votes=vote_tally[2]
    confidence=(winner_votes-runner_up_votes)/total_votes if winner!=0 else 0.0
    final_prediction=winner
    sbc_kota_override=get_sbc_kota_override(sbc_vote,kota_vote,votes)
    if sbc_kota_override!=0:
        final_prediction=sbc_kota_override
        confidence=max(confidence,UNPREDICTABLE_MARGIN)
    if final_prediction==0 or confidence<UNPREDICTABLE_MARGIN:
        if match_date_nn!=0:
            final_prediction=1 if match_date_nn%2!=0 else 2
            confidence=max(confidence,UNPREDICTABLE_MARGIN)
    if confidence<UNPREDICTABLE_MARGIN: return 0,confidence
    return final_prediction,confidence

# ---------------------------
# Define ALL methods
# ---------------------------
ALL_METHODS={}

# V5 placeholder Toss & Match
for i in range(1,9):
    def toss_placeholder_v5(row_data,a_nums,b_nums): return 1 if a_nums['nn']>=b_nums['nn'] else 2
    ALL_METHODS[f'Toss_Method_{i}']=toss_placeholder_v5
    def match_placeholder_v5(row_data,a_nums,b_nums): return 1 if a_nums['lp']>=b_nums['lp'] else 2
    ALL_METHODS[f'Match_Method_{i}']=match_placeholder_v5

# New Toss Methods 9-12
def toss_method_9_stadium_direction(row_data,a_nums,b_nums):
    direction=safe_str(row_data.get('stadium_direction','NEUTRAL')).upper()
    nn_a=a_nums['nn']; nn_b=b_nums['nn']
    dir_vote=STADIUM_DIRECTION_MAP.get(direction,0)
    if dir_vote==1: return 1 if nn_a>nn_b else 2
    elif dir_vote==2: return 2 if nn_b>nn_a else 1
    return 1 if nn_a>nn_b else 2
ALL_METHODS['Toss_Method_9']=toss_method_9_stadium_direction

def toss_method_10_color_compatibility(row_data,a_nums,b_nums):
    color_a=get_color_number(row_data.get('teama_color',''))
    color_b=get_color_number(row_data.get('teamb_color',''))
    nn_a=a_nums['nn']; nn_b=b_nums['nn']
    match_a=(color_a==nn_a); match_b=(color_b==nn_b)
    if match_a and not match_b: return 1
    if match_b and not match_a: return 2
    return 1 if nn_a>nn_b else 2
ALL_METHODS['Toss_Method_10']=toss_method_10_color_compatibility

def toss_method_11_moon_phase(row_data,a_nums,b_nums):
    match_date=safe_parse_date(row_data.get('match_date'))
    if not match_date: return 0
    moon_day=get_moon_phase_day(match_date)
    nn_a=a_nums['nn']; nn_b=b_nums['nn']
    return 1 if (moon_day%2==0 and nn_a>nn_b) else 2
ALL_METHODS['Toss_Method_11']=toss_method_11_moon_phase

def toss_method_12_hidden_sum(row_data,a_nums,b_nums):
    sum_a=(a_nums['lp']+a_nums['nn']+a_nums['dp'])%9
    sum_b=(b_nums['lp']+b_nums['nn']+b_nums['dp'])%9
    if sum_a>sum_b: return 1
    if sum_b>sum_a: return 2
    return 0
ALL_METHODS['Toss_Method_12']=toss_method_12_hidden_sum

# Jamakkol Toss Method
def toss_method_13_jamakkol(row_data,a_nums,b_nums):
    match_date=safe_parse_date(row_data.get('match_date'))
    try: match_time=parser.parse(row_data.get('match_time'))
    except: return 0
    toss_time=get_toss_time(match_time)
    sun_times=get_sun_times_from_place(row_data.get('match_place'),match_date)
    if not sun_times: return 0
    day_type,kalam_index=get_kalam_index(toss_time,sun_times['sunrise'],sun_times['sunset'],sun_times['next_sunrise'])
    jama=get_jama_planet(day_type,kalam_index)
    strength=PLANET_STRENGTH[jama]
    score_a=reduce_to_single(a_nums['nn']+strength)
    score_b=reduce_to_single(b_nums['nn']+strength)
    if score_a>score_b: return 1
    if score_b>score_a: return 2
    return 0
ALL_METHODS['Toss_Method_13']=toss_method_13_jamakkol

# New Match Methods 9-12
def match_method_9_team_astrology(row_data,a_nums,b_nums):
    match_date=safe_parse_date(row_data.get('match_date'))
    if not match_date: return 0
    team_a_nn=get_numerology_number(row_data.get('team_a_name',row_data.get('captain_a_name','')))
    team_b_nn=get_numerology_number(row_data.get('team_b_name',row_data.get('captain_b_name','')))
    moon_day=get_moon_phase_day(match_date)
    score_a=reduce_to_single(team_a_nn+a_nums['lp']+moon_day)
    score_b=reduce_to_single(team_b_nn+b_nums['lp']+moon_day)
    if score_a>score_b: return 1
    if score_b>score_a: return 2
    return 0
ALL_METHODS['Match_Method_9']=match_method_9_team_astrology

def match_method_10_stadium_alignment(row_data,a_nums,b_nums):
    team_a_nn=get_numerology_number(row_data.get('team_a_name',row_data.get('captain_a_name','')))
    team_b_nn=get_numerology_number(row_data.get('team_b_name',row_data.get('captain_b_name','')))
    direction=safe_str(row_data.get('stadium_direction','NEUTRAL')).upper()
    if direction in ["NORTH","EAST","NORTHEAST","SOUTHEAST"]: return 1 if team_a_nn>team_b_nn else 2
    if direction in ["SOUTH","WEST","SOUTHWEST","NORTHWEST"]: return 1 if team_a_nn<team_b_nn else 2
    return 1 if team_a_nn>team_b_nn else 2
ALL_METHODS['Match_Method_10']=match_method_10_stadium_alignment

def match_method_11_historical_form(history: list) -> int:
    window=history[-20:]
    if len(window)<5: return 0
    accuracy=sum(window)/len(window)
    return 1 if accuracy>0.6 and len(history)%2==0 else 2 if accuracy>0.6 else 0
ALL_METHODS['Match_Method_11']=match_method_11_historical_form

# Jamakkol Match Method
def match_method_12_jamakkol(row_data,a_nums,b_nums):
    match_date=safe_parse_date(row_data.get('match_date'))
    try: match_time=parser.parse(row_data.get('match_time'))
    except: return 0
    toss_time=get_toss_time(match_time)
    sun_times=get_sun_times_from_place(row_data.get('match_place'),match_date)
    if not sun_times: return 0
    day_type,kalam_index=get_kalam_index(toss_time,sun_times['sunrise'],sun_times['sunset'],sun_times['next_sunrise'])
    jama=get_jama_planet(day_type,kalam_index)
    strength=PLANET_STRENGTH[jama]
    score_a=reduce_to_single(a_nums['nn']+a_nums['lp']+strength)
    score_b=reduce_to_single(b_nums['nn']+b_nums['lp']+strength)
    if score_a>score_b: return 1
    if score_b>score_a: return 2
    return 0
ALL_METHODS['Match_Method_12']=match_method_12_jamakkol

# ---------------------------
# Main Runner
# ---------------------------
def process_matches(df: pd.DataFrame) -> pd.DataFrame:
    output=[]
    for idx,row in df.iterrows():
        row_data=row.to_dict()
        a_nums=get_lp_nn_dp(row_data.get('captain_a_dob'))
        b_nums=get_lp_nn_dp(row_data.get('captain_b_dob'))
        sbc_vote=calculate_sbc(row_data)
        kota_vote=calculate_kota(row_data)
        votes={}
        for method_name,func in ALL_METHODS.items():
            try:
                vote=func(row_data,a_nums,b_nums)
            except:
                vote=0
            votes[vote]=votes.get(vote,0)+1.0
        match_date=safe_parse_date(row_data.get('match_date'))
        match_date_nn=reduce_to_single(match_date.day) if match_date else 0
        final_pred,confidence=ensemble_vote_v7(votes,sbc_vote,kota_vote,match_date_nn)
        row_data['Final_Prediction']=final_pred
        row_data['Confidence']=confidence
        row_data['Votes']=json.dumps(votes)
        output.append(row_data)
    return pd.DataFrame(output)

# ---------------------------
# Entry point
# ---------------------------
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} missing!")
        sys.exit(1)
    df=pd.read_excel(INPUT_FILE)
    df_result=process_matches(df)
    df_result.to_excel(OUTPUT_FILE,index=False)
    print(f"✅ Output saved to {OUTPUT_FILE}")

if __name__=="__main__":
    main()
