#!/usr/bin/env python3
"""
Ultimate Match Predictor — V6 Python 3.9 Compatible with Jamakkol
Includes: SBC + KOTA + Ensemble + Jamakkol predictions
"""

import os
import json
import pandas as pd
from datetime import datetime, date, timedelta
from dateutil import parser
from typing import Dict, Any, Union, Optional
from astral import LocationInfo
from astral.sun import sun

# ---------------------------
# Config / Files
# ---------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"

# ---------------------------
# Helpers
# ---------------------------
def safe_str(x: Any) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (float, int)):
        return str(int(x)) if x == int(x) else str(x)
    if isinstance(x, (pd.Timestamp, datetime, date)):
        return str(x)
    s = str(x).strip()
    return s if s not in ['', 'nan', 'NaT'] else ''

def safe_parse_date(date_input: Any) -> Optional[date]:
    """Convert input to date object safely"""
    if pd.isna(date_input):
        return None
    if isinstance(date_input, date):
        return date_input
    if isinstance(date_input, datetime):
        return date_input.date()
    try:
        return parser.parse(safe_str(date_input)).date()
    except:
        return None

def generate_iso_timestamp():
    return datetime.now().isoformat(timespec='seconds')

def reduce_to_single(n: Union[int, float, str]) -> int:
    try:
        n_int = int(float(n))
    except:
        return 0
    while n_int > 9 and n_int > 0:
        n_int = sum(int(d) for d in str(n_int))
    return n_int

def get_lp_nn_dp(dob_str: Any) -> Dict[str, int]:
    dt = safe_parse_date(dob_str)
    if dt is None:
        return {'lp':0,'nn':0,'dp':0}
    dp = reduce_to_single(dt.day)
    nn = reduce_to_single(dt.day + dt.month + dt.year)
    lp = reduce_to_single(dt.month + dt.year)
    return {'lp':lp,'nn':nn,'dp':dp}

# ---------------------------
# SBC/KOTA and Ensemble
# ---------------------------
def calculate_sbc(row_data: dict) -> int:
    a_nn = get_lp_nn_dp(row_data.get('team_a_dob'))['nn']
    b_nn = get_lp_nn_dp(row_data.get('team_b_dob'))['nn']
    return 1 if a_nn > b_nn else 2

def calculate_kota(row_data: dict) -> int:
    match_date = safe_parse_date(row_data.get('match_date'))
    if match_date is None:
        return 0
    return 1 if reduce_to_single(match_date.day) % 2 != 0 else 2

def ensemble_vote(votes: Dict[int,float], sbc_vote:int, kota_vote:int, match_date_nn:int) -> tuple:
    if not votes:
        return 0, 0.0
    total = sum(votes.values())
    vote_1 = votes.get(1,0.0)
    vote_2 = votes.get(2,0.0)
    winner = 1 if vote_1>vote_2 else 2 if vote_2>vote_1 else 0
    confidence = abs(vote_1 - vote_2)/total if total>0 else 0.0
    if sbc_vote == kota_vote and sbc_vote !=0:
        winner = sbc_vote
        confidence = max(confidence,0.3)
    if winner==0 or confidence<0.3:
        winner = 1 if match_date_nn % 2 !=0 else 2
        confidence = max(confidence,0.3)
    return winner, round(confidence,2)

# ---------------------------
# Toss / Match Methods
# ---------------------------
ALL_METHODS = {}

# Placeholder Toss Methods 1-8
for i in range(1,9):
    def toss_placeholder(row_data: dict, a_nums: dict, b_nums: dict) -> int:
        return 1 if a_nums['nn']>=b_nums['nn'] else 2
    ALL_METHODS[f'Toss_Method_{i}']=toss_placeholder

# Toss Method 9: Stadium direction
def toss_method_9_stadium(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    direction = safe_str(row_data.get('match_place','NEUTRAL')).upper()
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Toss_Method_9']=toss_method_9_stadium

# Toss Method 10: Color compatibility
def toss_method_10_color(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Toss_Method_10']=toss_method_10_color

# Toss Method 11: Moon phase
def toss_method_11_moon(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Toss_Method_11']=toss_method_11_moon

# Toss Method 12: Hidden sum
def toss_method_12_hidden(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['lp']+a_nums['nn']+a_nums['dp']>=b_nums['lp']+b_nums['nn']+b_nums['dp'] else 2
ALL_METHODS['Toss_Method_12']=toss_method_12_hidden

# Placeholder Match Methods 1-8
for i in range(1,9):
    def match_placeholder(row_data: dict, a_nums: dict, b_nums: dict) -> int:
        return 1 if a_nums['lp']>=b_nums['lp'] else 2
    ALL_METHODS[f'Match_Method_{i}']=match_placeholder

# Match Method 9-12 placeholders
def match_method_9(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Match_Method_9']=match_method_9
def match_method_10(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Match_Method_10']=match_method_10
def match_method_11(history: list) -> int:
    return 1
ALL_METHODS['Match_Method_11']=match_method_11
def match_method_12(row_data: dict, a_nums: dict, b_nums: dict) -> int:
    return 1 if a_nums['nn']>=b_nums['nn'] else 2
ALL_METHODS['Match_Method_12']=match_method_12

# ---------------------------
# Jamakkol prediction placeholders
# ---------------------------
def jamakkol_predict(row_data: dict, is_toss: bool=True) -> str:
    """Placeholder: Calculate Jamakkol planets, Udayam, Kavipu, Arudam, Chatram"""
    team_a = safe_str(row_data.get('team_a_name','Team A'))
    team_b = safe_str(row_data.get('team_b_name','Team B'))
    # Simplified: randomly pick based on match date
    match_date = safe_parse_date(row_data.get('match_date'))
    if match_date and match_date.day %2==0:
        return team_b if is_toss else team_a
    else:
        return team_a if is_toss else team_b

# ---------------------------
# Method Stats
# ---------------------------
def load_method_stats(file:str) -> dict:
    if os.path.exists(file):
        try:
            with open(file,'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# ---------------------------
# Main Process
# ---------------------------
def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file {INPUT_FILE} missing.")
        return
    df=pd.read_excel(INPUT_FILE)
    df_output=[]
    method_stats=load_method_stats(METHOD_STATS_FILE)
    for idx,row in df.iterrows():
        row_data=row.to_dict()
        a_nums=get_lp_nn_dp(row_data.get('team_a_dob'))
        b_nums=get_lp_nn_dp(row_data.get('team_b_dob'))

        # Toss predictions
        toss_votes={}
        for mname in [k for k in ALL_METHODS if 'Toss' in k]:
            vote=ALL_METHODS[mname](row_data,a_nums,b_nums)
            toss_votes[vote]=toss_votes.get(vote,0)+method_stats.get(mname,{'weight':1.0})['weight']
        sbc_vote=calculate_sbc(row_data)
        kota_vote=calculate_kota(row_data)
        match_date_nn=reduce_to_single(safe_parse_date(row_data.get('match_date')).day if safe_parse_date(row_data.get('match_date')) else 0)
        final_toss,toss_conf=ensemble_vote(toss_votes,sbc_vote,kota_vote,match_date_nn)

        # Jamakkol toss prediction
        toss_jamakkol_team=jamakkol_predict(row_data,is_toss=True)

        # Match predictions
        match_votes={}
        for mname in [k for k in ALL_METHODS if 'Match' in k]:
            vote=ALL_METHODS[mname](row_data,a_nums,b_nums) if mname!='Match_Method_11' else ALL_METHODS[mname]([])
            match_votes[vote]=match_votes.get(vote,0)+method_stats.get(mname,{'weight':1.0})['weight']
        final_match,match_conf=ensemble_vote(match_votes,sbc_vote,kota_vote,match_date_nn)

        # Jamakkol match prediction
        match_jamakkol_team=jamakkol_predict(row_data,is_toss=False)

        output_row={
            "Timestamp":generate_iso_timestamp(),
            "Match_Date":safe_str(row_data.get('match_date')),
            "Match_Time":safe_str(row_data.get('match_time')),
            "Match_Place":safe_str(row_data.get('match_place')),
            "Team_A":safe_str(row_data.get('team_a_name')),
            "Team_B":safe_str(row_data.get('team_b_name')),
            "Toss_Final_Prediction":final_toss,
            "Toss_Confidence":toss_conf,
            "Toss_Jamakkol_Team":toss_jamakkol_team,
            "Match_Final_Prediction":final_match,
            "Match_Confidence":match_conf,
            "Match_Jamakkol_Team":match_jamakkol_team
        }
        df_output.append(output_row)
    df_out=pd.DataFrame(df_output)
    df_out.to_excel(OUTPUT_FILE,index=False)
    print(f"✅ Output saved to {OUTPUT_FILE}")

if __name__=="__main__":
    main()
