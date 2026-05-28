# kota_chakra.py
from astro_utils import *
from dateutil import parser
from datetime import timezone
import pytz

NATURAL_BENEFICS = {'Venus', 'Jupiter', 'Mercury', 'Moon', 'Sun'}
NATURAL_MALEFICS = {'Mars', 'Saturn', 'Rahu', 'Ketu'}

REGION_OFFSETS = {
    'Stambha': [4, 11, 18, 25],
    'Madhya': [3, 5, 10, 12, 17, 19, 24, 26],
    'Prakaara': [2, 6, 9, 13, 16, 20, 23, 27],
    'Bahya': [1, 7, 8, 14, 15, 21, 22, 28],
}

def offsets_to_indices(janma_index):
    regs = {}
    for name, offs in REGION_OFFSETS.items():
        regs[name] = [ (janma_index + (o-1)) % NAK_N for o in offs ]
    return regs

def score_for_natal(janma_index, transits):
    regions = offsets_to_indices(janma_index)
    janma_central_long = (janma_index + 0.5) * NAK_WIDTH
    kota_swami = RASHI_LORD[rashi_from_long(janma_central_long)]
    natal_pada = pada_of_long(janma_central_long)
    kota_paala = avakhada_pada_lord_from_nak_and_pada(janma_index, natal_pada)
    score = 0
    for reg in ('Stambha','Madhya'):
        for nak_idx in regions[reg]:
            if kota_swami in transits:
                if nakshatra_index_from_long(transits[kota_swami]) == nak_idx:
                    score += 3
    if kota_paala and kota_paala in transits:
        if nakshatra_index_from_long(transits[kota_paala]) in regions['Bahya']:
            score += 2
    entry_indices = [ (janma_index + o) % NAK_N for o in (0,7,14,21) ]
    exit_indices  = [ (janma_index + o) % NAK_N for o in (3,10,17,24) ]
    for m in NATURAL_MALEFICS:
        if m in transits:
            if nakshatra_index_from_long(transits[m]) in entry_indices:
                score -= 3
    for b in NATURAL_BENEFICS:
        if b in transits:
            if nakshatra_index_from_long(transits[b]) in exit_indices:
                score += 1
    return {'score': score, 'kota_swami': kota_swami, 'kota_paala': kota_paala, 'regions': regions}

def calculate_kota(row_data):
    tz_name = row_data.get('timezone','UTC')
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.UTC
    match_date = row_data.get('match_date')
    match_time = row_data.get('match_time','12:00')
    if not match_date:
        return 0
    try:
        if 'T' in match_date:
            md = parser.isoparse(match_date)
            if md.tzinfo is None:
                md = tz.localize(md)
            match_dt_utc = md.astimezone(timezone.utc)
        else:
            dt_str = f"{match_date}T{match_time}"
            naive = parser.isoparse(dt_str)
            if naive.tzinfo is None:
                naive = tz.localize(naive)
            match_dt_utc = naive.astimezone(timezone.utc)
    except Exception:
        try:
            naive = parser.parse(f"{match_date} {match_time}")
            naive = tz.localize(naive)
            match_dt_utc = naive.astimezone(timezone.utc)
        except Exception:
            return 0
    jd_ut = julian_day_from_datetime(match_dt_utc)
    transits = planetary_longitudes(jd_ut)
    a_dob = row_data.get('captain_a_dob')
    b_dob = row_data.get('captain_b_dob')
    if not a_dob or not b_dob:
        return 0
    janma_a = natal_moon_nakshatra_index(a_dob)
    janma_b = natal_moon_nakshatra_index(b_dob)
    info_a = score_for_natal(janma_a, transits)
    info_b = score_for_natal(janma_b, transits)
    sa = info_a['score']; sb = info_b['score']
    if sa > sb + 0.5:
        return 1
    elif sb > sa + 0.5:
        return 2
    else:
        return 0

# Example test when run directly
if __name__ == "__main__":
    row = {
        'match_date': '2025-11-24',
        'match_time': '18:00',
        'timezone': 'Asia/Kolkata',
        'captain_a_dob': '1988-03-10T06:30:00+05:30',
        'captain_b_dob': '1990-07-22T14:10:00+05:30'
    }
    print("KOTA vote:", calculate_kota(row))
