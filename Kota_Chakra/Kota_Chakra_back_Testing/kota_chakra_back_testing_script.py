#!/usr/bin/env python3
"""
Batch Kota Chakra Script
Processes CSV file of matches (300+) and outputs:
- Detailed JSON with planetary positions, scores, weights, recommendations
- Summary CSV with KOTA votes per method and agreement
"""

import csv
import json
import sys
from datetime import datetime, timezone
from dateutil import parser
import pytz
import swisseph as swe

# ---------------- Constants ----------------
NAK_N = 28
NAK_WIDTH = 360.0 / NAK_N
DEFAULT_CALC_MODE = 'sidereal'

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Rahu': swe.MEAN_NODE,
}

NATURAL_BENEFICS = {'Venus', 'Jupiter', 'Mercury', 'Moon', 'Sun'}
NATURAL_MALEFICS = {'Mars', 'Saturn', 'Rahu', 'Ketu'}

RASHI_LORD = {
    0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
    4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
    8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
}

REGION_OFFSETS = {
    'Stambha': [4, 11, 18, 25],
    'Madhya': [3, 5, 10, 12, 17, 19, 24, 26],
    'Prakaara': [2, 6, 9, 13, 16, 20, 23, 27],
    'Bahya': [1, 7, 8, 14, 15, 21, 22, 28],
}

# ---------------- Helper Functions ----------------
def set_swe_mode(calc_mode: str):
    if calc_mode.lower() == 'sidereal':
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    else:
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)

def julian_day_from_datetime(dt: datetime) -> float:
    frac_hours = dt.hour + dt.minute/60.0 + dt.second/3600.0 + dt.microsecond/(3600*1e6)
    return swe.julday(dt.year, dt.month, dt.day, frac_hours)

def planetary_longitudes(jd_ut: float) -> dict:
    longs = {}
    for name, pid in PLANETS.items():
        arr = swe.calc_ut(jd_ut, pid)
        lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
        if name == 'Rahu':
            longs['Rahu'] = lon % 360
            longs['Ketu'] = (lon + 180) % 360
        else:
            longs[name] = lon % 360
    return longs

def nakshatra_index_from_long(lon: float) -> int:
    return int((lon % 360) // NAK_WIDTH)

def rashi_from_long(lon: float) -> int:
    return int((lon % 360) // 30)

def offsets_to_indices(janma_index: int) -> dict:
    regs = {}
    for name, offs in REGION_OFFSETS.items():
        regs[name] = [(janma_index + (o-1)) % NAK_N for o in offs]
    return regs

def calculate_kota_score(janma_index: int, transits: dict) -> dict:
    regions = offsets_to_indices(janma_index)
    janma_central_long = (janma_index + 0.5) * NAK_WIDTH
    kota_swami = RASHI_LORD[rashi_from_long(janma_central_long)]
    score = 0
    breakdown = {}
    # Swami in Stambha/Madhya
    st_m_score = 0
    for reg in ['Stambha','Madhya']:
        for nak_idx in regions[reg]:
            if kota_swami in transits and nakshatra_index_from_long(transits[kota_swami]) == nak_idx:
                st_m_score += 3
    score += st_m_score
    breakdown['Swami_Stambha_Madhya'] = st_m_score
    # Paala and others (simplified, can extend)
    breakdown['Total'] = score
    return {'score': score, 'kota_swami': kota_swami, 'regions': regions, 'breakdown': breakdown}

def process_match(row: dict, calc_mode: str):
    """
    row: dictionary from CSV
    Returns: dict with detailed info for JSON
    """
    set_swe_mode(calc_mode)
    
    # Parse match date/time
    dt_str = f"{row.get('Match_Date')}T{row.get('Match_Time','12:00')}"
    tz_str = row.get('TZ_Offset_Hours', '0')
    try:
        tz_offset = float(tz_str)
    except:
        tz_offset = 0
    tz = timezone.utc
    try:
        naive = parser.isoparse(dt_str)
        match_dt_utc = naive.replace(tzinfo=timezone.utc)
    except:
        match_dt_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    
    jd_ut = julian_day_from_datetime(match_dt_utc)
    transits = planetary_longitudes(jd_ut)
    
    # Method 1: Match Date only
    a_index = 0  # placeholder
    b_index = 7  # placeholder
    md_score_a = calculate_kota_score(a_index, transits)
    md_score_b = calculate_kota_score(b_index, transits)
    md_vote = 1 if md_score_a['score'] > md_score_b['score'] else 2
    md_weight = min(1.0, abs(md_score_a['score'] - md_score_b['score']) / 5.0)
    
    # Method 2: Captain DOBs
    try:
        a_dob = parser.isoparse(row.get('Captain_A_DOB','1970-01-01T12:00'))
        b_dob = parser.isoparse(row.get('Captain_B_DOB','1970-01-01T12:00'))
        jd_a = julian_day_from_datetime(a_dob)
        jd_b = julian_day_from_datetime(b_dob)
        # Here simplification: natal moon nakshatra index
        janma_a = nakshatra_index_from_long(transits['Moon'])
        janma_b = nakshatra_index_from_long((transits['Moon']+180)%360)
    except:
        janma_a = 0
        janma_b = 7
    
    dob_score_a = calculate_kota_score(janma_a, transits)
    dob_score_b = calculate_kota_score(janma_b, transits)
    dob_vote = 1 if dob_score_a['score'] > dob_score_b['score'] else 2
    dob_weight = min(1.0, abs(dob_score_a['score'] - dob_score_b['score']) / 5.0)
    
    agreement_flag = md_vote == dob_vote
    
    # Recommendation logic (simplified)
    recommendation = 'promote' if md_weight >= 0.5 else 'retire'
    
    result = {
        "series": row.get('Series'),
        "match_date": row.get('Match_Date'),
        "match_time": row.get('Match_Time'),
        "match_place": row.get('Match_Place'),
        "timezone": row.get('TZ_Offset_Hours'),
        "team_a": row.get('Team_A_Name'),
        "team_b": row.get('Team_B_Name'),
        "captain_a_name": row.get('Captain_A_Name'),
        "captain_b_name": row.get('Captain_B_Name'),
        "match_date_method": {
            "scores": {"team_a": md_score_a['score'], "team_b": md_score_b['score']},
            "kota_vote": md_vote,
            "weight": md_weight
        },
        "dob_method": {
            "scores": {"team_a": dob_score_a['score'], "team_b": dob_score_b['score']},
            "kota_vote": dob_vote,
            "weight": dob_weight
        },
        "agreement_flag": agreement_flag,
        "recommendation": recommendation,
        "planetary_longitudes": transits,
        "kota_swami": md_score_a['kota_swami'],
        "regions": md_score_a['regions']
    }
    return result

def main():
    input_file = 'matches_input.csv'
    detailed_json_file = 'matches_detailed.json'
    summary_csv_file = 'matches_summary.csv'
    
    calc_mode = DEFAULT_CALC_MODE
    # Optionally pass via command-line
    if len(sys.argv) > 1:
        calc_mode = sys.argv[1]
    
    all_results = []
    
    with open(input_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            result = process_match(row, calc_mode)
            all_results.append(result)
    
    # Write JSON detailed
    with open(detailed_json_file,'w',encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    # Write summary CSV
    with open(summary_csv_file,'w',newline='',encoding='utf-8') as f:
        fieldnames = ['Series','Match_Date','Team_A','Team_B','Vote_Method_Date','Vote_Method_DOB','Agreement_Flag','Recommendation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in all_results:
            writer.writerow({
                'Series': res['series'],
                'Match_Date': res['match_date'],
                'Team_A': res['team_a'],
                'Team_B': res['team_b'],
                'Vote_Method_Date': res['match_date_method']['kota_vote'],
                'Vote_Method_DOB': res['dob_method']['kota_vote'],
                'Agreement_Flag': res['agreement_flag'],
                'Recommendation': res['recommendation']
            })
    
    print(f"Processed {len(all_results)} matches. Detailed JSON: {detailed_json_file}, Summary CSV: {summary_csv_file}")

if __name__=="__main__":
    main()
