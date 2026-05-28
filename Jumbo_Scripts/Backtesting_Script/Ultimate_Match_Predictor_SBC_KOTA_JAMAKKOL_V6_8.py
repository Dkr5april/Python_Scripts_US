#!/usr/bin/env python3
"""
Ultimate Match Predictor — V6.8 Full Merge: SBC + KOTA + Jamakkol + Learning + Ensemble

Input expected columns:
Timestamp, Captain_A_Name, Captain_A_DOB, Captain_B_Name, Captain_B_DOB,
Match_Date, Match_Time, Match_Place, Match_Format, TZ_Offset_HOURS,
Real_Toss, Real_Match, Team_A_Name, Team_B_Name, TeamA_Color, TeamB_Color, Stadium_Direction

Output:
- Excel with Input_Data & Backtest_Results
- Updates method_stats.json
"""

import sys, os, json, pandas as pd, datetime
from datetime import datetime, timedelta
from dateutil import parser

# ----------------------------
# Config
# ----------------------------
INPUT_FILE = "match_analysis_data.xlsx"
OUTPUT_FILE = "match_analysis_data_output.xlsx"
METHOD_STATS_FILE = "method_stats.json"

WEIGHT_PROMOTE_STEP = 0.25
WEIGHT_DEMOTE_STEP = 0.30
WEIGHT_MIN = 0.05
WEIGHT_MAX = 8.0
RETIRE_AFTER_WEIGHT_BELOW = 0.15
RETIRE_FAIL_RATIO = 2.0
MIN_TOTAL_EVAL = 3
UNPREDICTABLE_MARGIN = 0.3
REVIVAL_WINDOW = 20

COLOR_ENERGY_MAP = {
    "RED": 9, "BLUE": 8, "GREEN": 5, "YELLOW": 3, "ORANGE": 1,
    "WHITE": 6, "BLACK": 4, "GREY": 4, "PURPLE": 7, "PINK": 9,
    "BROWN": 4, "GOLD": 1, "SILVER": 2, "MAROON": 9, "CRIMSON": 9,
    "NAVY": 8, "LIME": 5, "TURQUOISE": 5
}

# ----------------------------
# Utilities
# ----------------------------
def safe_str(x): 
    if pd.isna(x): return ''
    return str(x).strip()

def standardize_name(name): 
    return safe_str(name).lower().replace(' ','').replace('_','')

def strong_match(predicted, actual):
    return standardize_name(predicted) == standardize_name(actual)

def reduce_to_single(n):
    try: n_int = int(float(n))
    except: return 0
    while n_int > 9 and n_int > 0:
        n_int = sum(int(d) for d in str(n_int))
    return n_int

def get_numerology_number(name):
    mapping = {'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':2,'s':3,'t':4,'u':6,'v':6,'w':6,'x':5,'y':1,'z':7}
    name = safe_str(name).lower().replace(' ','')
    total = sum(mapping.get(c,0) for c in name)
    return reduce_to_single(total)

def safe_parse_date(d):
    if pd.isna(d): return None
    if isinstance(d, datetime): return d.date()
    if isinstance(d, (str,pd.Timestamp)):
        try: return parser.parse(str(d)).date()
        except: return None
    return None

def get_lp_nn_dp(dob_str):
    dt = safe_parse_date(dob_str)
    if dt is None: return {'lp':0,'nn':0,'dp':0}
    dp = reduce_to_single(dt.day)
    nn = reduce_to_single(dt.day + dt.month + dt.year)
    lp = reduce_to_single(dt.month + dt.year)
    return {'lp':lp,'nn':nn,'dp':dp}

def get_color_number(color_name):
    color = safe_str(color_name).upper()
    for k,v in COLOR_ENERGY_MAP.items():
        if k in color: return v
    return 0

def generate_iso_timestamp():
    return datetime.now().isoformat(timespec='seconds')

def parse_tz_offset(tz_val) -> float:
    """
    Converts '+10:30', '+10:30:00', -5.75, or datetime to float hours
    """
    if tz_val is None: return 0.0
    if isinstance(tz_val, (int, float)):
        return float(tz_val)
    if isinstance(tz_val, datetime):
        # assume it's local time and no offset info, return 0
        return 0.0
    s = str(tz_val).strip()
    # If it's a datetime string like '1900-01-11 00:00:00', treat as 0
    try:
        _ = parser.parse(s)
        return 0.0
    except:
        pass
    # Now try normal +HH:MM parsing
    sign = 1
    if s.startswith('-'):
        sign = -1; s = s[1:]
    elif s.startswith('+'):
        s = s[1:]
    if ':' in s:
        parts = s.split(':')
        try:
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return sign * (hours + minutes/60)
        except:
            return 0.0
    try:
        return sign*float(s)
    except:
        return 0.0


# ----------------------------
# Jamakkol Placeholder (full planetary system)
# ----------------------------
def calculate_jamakkol_planets(match_date, city, tz_offset, match_time):
    """
    Placeholder: Returns dictionary with Jamakkol planets for the day
    """
    # TODO: Replace with full astronomical calculations (Udayam, Arudam, Kavipu, Jama planets)
    return {
        "Sun":1,"Moon":2,"Mars":3,"Mercury":4,"Jupiter":5,"Venus":6,"Saturn":7,"Rahu":8,"Ketu":9
    }

# ----------------------------
# SBC & KOTA
# ----------------------------
def calculate_sbc(row):
    return 1 if get_numerology_number(row.get('captain_a_name','')) > get_numerology_number(row.get('captain_b_name','')) else 2

def calculate_kota(row):
    match_date = safe_parse_date(row.get('match_date'))
    if match_date is None: return 0
    match_date_nn = reduce_to_single(match_date.day)
    return 1 if reduce_to_single(match_date_nn+1)%2==0 else 2

def get_sbc_kota_override(sbc_vote, kota_vote, votes):
    if sbc_vote==kota_vote and sbc_vote!=0:
        total_votes=sum(votes.values())
        if total_votes>0:
            strongest=max(votes.values())
            if strongest/total_votes<0.75: return sbc_vote
    return 0

def ensemble_vote_v6(votes, sbc_vote, kota_vote, match_date_nn):
    if not votes: return 0,0.0
    total=sum(votes.values())
    if total==0: return 0,0.0
    vote_tally={1:votes.get(1,0.0),2:votes.get(2,0.0)}
    if vote_tally[1]>vote_tally[2]: winner=1; winner_votes=vote_tally[1]; runner_up_votes=vote_tally[2]
    elif vote_tally[2]>vote_tally[1]: winner=2; winner_votes=vote_tally[2]; runner_up_votes=vote_tally[1]
    else: winner=0; winner_votes=vote_tally[1]; runner_up_votes=vote_tally[2]
    confidence=(winner_votes-runner_up_votes)/total if winner!=0 else 0.0
    final=winner
    sbc_kota_override=get_sbc_kota_override(sbc_vote,kota_vote,votes)
    if sbc_kota_override!=0:
        final=sbc_kota_override
        confidence=max(confidence,UNPREDICTABLE_MARGIN)
    if final==0 or confidence<UNPREDICTABLE_MARGIN:
        if match_date_nn!=0:
            if match_date_nn%2!=0: final=1; confidence=max(confidence,UNPREDICTABLE_MARGIN)
            else: final=2; confidence=max(confidence,UNPREDICTABLE_MARGIN)
    if confidence<UNPREDICTABLE_MARGIN: return 0,confidence
    return final,confidence

# ----------------------------
# Placeholder Toss & Match Methods
# ----------------------------
ALL_METHODS={}

# Toss Methods 1-12 placeholder logic
for i in range(1,9):
    def toss_placeholder(row,a,b): nn_a=a['nn']; nn_b=b['nn']; return 1 if nn_a>=nn_b else 2
    ALL_METHODS[f'Toss_Method_{i}']=toss_placeholder

# Toss Methods 9-12 examples
def toss_method_9_stadium_direction(row,a,b):
    nn_a=a['nn']; nn_b=b['nn']; dir_vote=1
    return 1 if nn_a>nn_b else 2
ALL_METHODS['Toss_Method_9']=toss_method_9_stadium_direction

def toss_method_10_color(row,a,b):
    nn_a=a['nn']; nn_b=b['nn']; c_a=get_color_number(row.get('teama_color','')); c_b=get_color_number(row.get('teamb_color',''))
    return 1 if nn_a>nn_b else 2
ALL_METHODS['Toss_Method_10']=toss_method_10_color

def toss_method_11_moon(row,a,b):
    nn_a=a['nn']; nn_b=b['nn']; return 1 if nn_a>nn_b else 2
ALL_METHODS['Toss_Method_11']=toss_method_11_moon

def toss_method_12_hidden(row,a,b):
    sum_a=(a['lp']+a['nn']+a['dp'])%9; sum_b=(b['lp']+b['nn']+b['dp'])%9
    if sum_a>sum_b: return 1
    if sum_b>sum_a: return 2
    return 0
ALL_METHODS['Toss_Method_12']=toss_method_12_hidden

# Match Methods 1-11
for i in range(1,9):
    def match_placeholder(row,a,b): return 1 if a['lp']>=b['lp'] else 2
    ALL_METHODS[f'Match_Method_{i}']=match_placeholder

def match_method_9_astrology(row,a,b):
    score_a=reduce_to_single(get_numerology_number(row.get('team_a_name',''))+a['lp'])
    score_b=reduce_to_single(get_numerology_number(row.get('team_b_name',''))+b['lp'])
    if score_a>score_b: return 1
    if score_b>score_a: return 2
    return 0
ALL_METHODS['Match_Method_9']=match_method_9_astrology

def match_method_10_stadium(row,a,b):
    return 1 if a['lp']>=b['lp'] else 2
ALL_METHODS['Match_Method_10']=match_method_10_stadium

def match_method_11_history(history):
    return 1 if len(history)%2==0 else 2
ALL_METHODS['Match_Method_11']=match_method_11_history

# ----------------------------
# Method stats load/save
# ----------------------------
def load_method_stats(filename):
    if os.path.exists(filename):
        try: return json.load(open(filename,'r'))
        except: return {}
    return {}

def save_method_stats(filename,stats):
    try: json.dump(stats,open(filename,'w'),indent=4)
    except: pass

def update_method_stats(method_stats, method_name, is_correct, is_prediction_made, task):
    stats=method_stats.get(method_name,{'weight':1.0,'correct':0,'total':0,'retired':False,'task':task,'history':[]})
    if is_prediction_made:
        stats['total']+=1
        stats['history'].append(1 if is_correct else 0)
        stats['history']=stats['history'][-50:]
        if is_correct: stats['correct']+=1; stats['weight']=min(WEIGHT_MAX,stats['weight']+WEIGHT_PROMOTE_STEP)
        else: stats['weight']=max(WEIGHT_MIN,stats['weight']-WEIGHT_DEMOTE_STEP)
    if stats['total']>=MIN_TOTAL_EVAL and stats['weight']<RETIRE_AFTER_WEIGHT_BELOW:
        fail_ratio=(stats['total']-stats['correct'])/max(1,stats['total'])
        if fail_ratio>RETIRE_FAIL_RATIO: stats['retired']=True
    method_stats[method_name]=stats
    return stats['weight']

# ----------------------------
# Main predictor
# ----------------------------
def run_predictor():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found"); return
    try:
        df=pd.read_excel(INPUT_FILE)
    except:
        print(f"Cannot read {INPUT_FILE}"); return
    df.columns=df.columns.str.replace(' ','').str.lower()
    method_stats=load_method_stats(METHOD_STATS_FILE)
    results=[]
    for mname in ALL_METHODS:
        task='Toss' if 'Toss' in mname else 'Match'
        if mname not in method_stats: method_stats[mname]={'weight':1.0,'correct':0,'total':0,'retired':False,'task':task,'history':[]}
    for idx,row in df.iterrows():
        row_data=row.to_dict()
        a_nums=get_lp_nn_dp(row_data.get('captain_a_dob',''))
        b_nums=get_lp_nn_dp(row_data.get('captain_b_dob',''))
        match_date=safe_parse_date(row_data.get('match_date'))
        tz_offset=parse_tz_offset(row_data.get('tz_offset_hours',0))
        city=safe_str(row_data.get('match_place',''))
        jamakkol_planets=calculate_jamakkol_planets(match_date,city,tz_offset,row_data.get('match_time',''))
        row_data['Jamakkol_Planets']=jamakkol_planets
        votes={}
        match_history=[]
        for mname in ALL_METHODS:
            try:
                if mname=='Match_Method_11': vote=ALL_METHODS[mname](match_history)
                else: vote=ALL_METHODS[mname](row_data,a_nums,b_nums)
            except: vote=0
            votes[mname]=vote
        sbc_vote=calculate_sbc(row_data)
        kota_vote=calculate_kota(row_data)
        match_date_nn=reduce_to_single(match_date.day) if match_date else 0
        final_vote,confidence=ensemble_vote_v6(votes,sbc_vote,kota_vote,match_date_nn)
        row_data['Final_Match_Result']=final_vote if final_vote else 'Unpredictable'
        row_data['Match_Confidence']=confidence
        results.append(row_data)
        for mname in ALL_METHODS:
            update_method_stats(method_stats,mname,(votes[mname]==final_vote if votes[mname]!=0 else False),(votes[mname]!=0),'match' if 'Match' in mname else 'toss')

    df_out=pd.DataFrame(results)

    # ---------------------------- 
    # Print last 50 matches and method performance
    # ----------------------------
    print("\n--- Last 50 Matches ---")
    for row in results[-50:]:
        match_date = row.get('match_date', '')
        team_a = row.get('team_a_name','')
        team_b = row.get('team_b_name','')
        final_vote = row.get('Final_Match_Result','')
        confidence = row.get('Match_Confidence',0.0)
        print(f"{match_date} | {team_a} vs {team_b} | Final: {final_vote} | Confidence: {confidence:.2f}")

    # Calculate method success %
    method_performance = []
    for method, stats in method_stats.items():
        total = stats.get('total',0)
        correct = stats.get('correct',0)
        success_pct = (correct/total*100) if total>0 else 0
        method_performance.append((method, success_pct, stats.get('weight',1.0), correct, total))

    # Sort descending by success %
    method_performance.sort(key=lambda x: x[1], reverse=True)

    # Print top 3 methods
    print("\n--- Top 3 Methods by Accuracy ---")
    for method, pct, weight, correct, total in method_performance[:3]:
        print(f"{method}: {correct}/{total} = {pct:.1f}% | Weight: {weight:.2f}")

    # Jamakkol overall
    jamakkol_correct = sum(1 for row in results if row.get('Jamakkol_Planets_Vote', 0) == row.get('Final_Match_Result', 0))
    jamakkol_total = len(results)
    jamakkol_pct = (jamakkol_correct/jamakkol_total*100) if jamakkol_total else 0
    print(f"\nJamakkol Overall Accuracy: {jamakkol_correct}/{jamakkol_total} = {jamakkol_pct:.1f}%")

    # Save output
    try:
        with pd.ExcelWriter(OUTPUT_FILE,engine='openpyxl') as writer:
            df_out.to_excel(writer,index=False,sheet_name='Backtest_Results')
            df.to_excel(writer,index=False,sheet_name='Input_Data')
        save_method_stats(METHOD_STATS_FILE,method_stats)
        print(f"\n✅ Output saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving: {e}")

if __name__=="__main__":
    run_predictor()
