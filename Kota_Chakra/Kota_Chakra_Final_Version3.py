#!/usr/bin/env python3
"""
Kota Chakra Interactive & Batch Script (FINAL VERSION with Comparison Logic Implemented)

Features:
- Option 1 (Compare): Compares two specific people (DOBs) using their Natal Moon Nakshatra. (IMPLMENTED)
    * **New Feature:** Defaults to 12:00 +05:30 if only DOB is provided for practical use.
- Option 2 (Toss Check): Calculates dynamic transit strength at location and time duration.
    * **FIXED:** All output times are now correctly converted and displayed in the LOCAL timezone.
- Supports both Vimshottari (Dasa) and Avakhada (Rashi) Pada Lord systems for dynamic tracking.
"""

import swisseph as swe
from datetime import datetime, timezone, timedelta
from dateutil import parser
import logging
import json
import os
import time
import pandas as pd

# NEW: Import for geocoding
try:
    from geopy.geocoders import Nominatim
    GEOLOCATOR_AVAILABLE = True
except ImportError:
    GEOLOCATOR_AVAILABLE = False
    class Nominatim:
        def geocode(self, location, timeout=5):
            return None 

# ---------------- Constants ----------------
NAK_N = 27
NAK_WIDTH = 360.0 / NAK_N

PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS,
    'Mars': swe.MARS, 'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE,
}

NATURAL_BENEFICS = {'Venus', 'Jupiter', 'Moon', 'Sun'} 
NATURAL_MALEFICS = {'Mars', 'Saturn', 'Rahu', 'Ketu'}

RASHI_LORD = {
    0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury', 
    6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter' 
}

VIMSHOTTARI_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']

REGION_OFFSETS = {
    'Stambha': [5, 11, 18, 25],
    'Madhya': [4, 6, 11, 13, 18, 20, 25, 27],
    'Prakaara': [3, 7, 10, 14, 17, 21, 24, 28],
    'Bahya': [1, 2, 8, 9, 15, 16, 22, 23],
}

DEFAULT_CALC_MODE = 'sidereal'
AFFLICTION_ORB = 3.0

# ---------------- Logging Setup ----------------
logger = logging.getLogger("kota_debug")
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------- Helper (trace collector) ----------------
def make_tracer(verbose=False):
    trace = []
    def tlog(step_name, **kwargs):
        entry = {"step": step_name, "time": time.time()}
        entry.update(kwargs)
        trace.append(entry)
        if verbose:
            print(f"--- {step_name} ---")
            for k, v in kwargs.items():
                print(f"  {k}: {v}")
            print()
    return tlog, trace

# ---------------- Timezone parser ----------------
def parse_hhmm_timezone(tz_input: str):
    tz_input = str(tz_input).strip()
    sign = 1
    if tz_input.startswith('+'):
        tz_input = tz_input[1:]
    elif tz_input.startswith('-'):
        tz_input = tz_input[1:]
        sign = -1
    try:
        hours, minutes = map(int, tz_input.split(":"))
        offset = timedelta(hours=hours*sign, minutes=minutes*sign)
        return timezone(offset)
    except:
        try:
            hours = int(tz_input)
            offset = timedelta(hours=hours)
            return timezone(offset)
        except:
            return timezone.utc

# ---------------- Geocoding Function (Required for Option 2 Lagna) ----------------
def lookup_coordinates(location_name: str, tlog=None) -> tuple[float, float] | None:
    if not GEOLOCATOR_AVAILABLE:
        if tlog: tlog("geocoding_unavailable", note="Using default Lat 28.7, Lon 77.2")
        return 28.7, 77.2 

    try:
        geolocator = Nominatim(user_agent="kota_chakra_script", timeout=10)
        location = geolocator.geocode(location_name)
        
        if location:
            if tlog: tlog("geocoding_success", location=location_name, latitude=location.latitude, longitude=location.longitude)
            return location.latitude, location.longitude
        else:
            if tlog: tlog("geocoding_failure", location=location_name, note="Location not found by geocoder.")
            return None
            
    except Exception as e:
        if tlog: tlog("geocoding_error", location=location_name, error=str(e))
        return None

# ---------------- Geometry / Astrology helpers ----------------
def set_swe_mode(calc_mode: str, tlog=None):
    if calc_mode.lower() == 'sidereal':
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    else:
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY, 0, 0)

def rashi_from_long(lon: float) -> int:
    return int((lon % 360.0) // 30)

def nakshatra_index_from_long(lon: float) -> int:
    return int((lon % 360.0) // NAK_WIDTH)

def julian_day_from_datetime(dt: datetime) -> float:
    frac_hours = dt.hour + dt.minute/60.0 + dt.second/3600.0 + dt.microsecond/(3600.0*1e6)
    return swe.julday(dt.year, dt.month, dt.day, frac_hours)
    
def datetime_from_julian_day(jd_ut: float) -> datetime:
    unix_ts = (jd_ut - 2440587.5) * 86400.0
    # Returns datetime object aware of UTC timezone
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc)

def planetary_longitudes(jd_ut: float, tlog=None):
    longs = {}
    CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    
    for name, pid in PLANETS.items():
        arr = swe.calc_ut(jd_ut, pid, CALC_FLAGS)
        lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
        
        if name == 'Rahu':
            longs['Rahu'] = lon % 360.0
            longs['Ketu'] = (lon + 180.0) % 360.0
        else:
            longs[name] = lon % 360.0
            
    return longs

def get_ascendant_nakshatra_and_pada(jd_ut: float, lat: float, lon: float, tlog=None) -> tuple[int, int, float]:
    cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P') 
    lagna_lon = cusps[1]
    lagna_nak_idx = nakshatra_index_from_long(lagna_lon)
    lagna_pada = pada_of_long(lagna_lon)
    return lagna_nak_idx, lagna_pada, lagna_lon

def offsets_to_indices(janma_index: int, tlog=None):
    regs = {name:[(janma_index + (o-1)) % NAK_N for o in offs] for name, offs in REGION_OFFSETS.items()}
    return regs

def pada_of_long(lon: float) -> int:
    nak_index = nakshatra_index_from_long(lon)
    nak_start_long = nak_index * NAK_WIDTH
    long_in_nak = (lon - nak_start_long) % NAK_WIDTH
    return int(long_in_nak // (NAK_WIDTH/4.0)) + 1

def avakhada_pada_lord_from_nak_and_pada(nak_index: int, pada: int, tlog=None):
    nak_start = nak_index * NAK_WIDTH
    width = NAK_WIDTH / 4.0
    mid = (nak_start + (pada - 1)*width + (nak_start + pada*width))/2 % 360.0
    lord = RASHI_LORD[rashi_from_long(mid)]
    return lord

def vimshottari_pada_lord_from_nak_and_pada(nak_index: int, pada: int, tlog=None):
    total_pada_index = (nak_index * 4) + (pada - 1)
    lord_index = total_pada_index % 9 
    pada_lord = VIMSHOTTARI_SEQUENCE[lord_index]
    return pada_lord

def natal_moon_nakshatra_index(dob_input: str, tlog=None):
    # --- UPDATED LOGIC FOR PRACTICAL USE ---
    dob_parts = dob_input.strip().split()
    if len(dob_parts) < 3:
        # Default to 12:00 +05:30 (Noon, Indian Standard Time)
        default_time_tz = "12:00 +05:30"
        dob_input_with_default = f"{dob_input} {default_time_tz}"
        if tlog: tlog("natal_dob_default", input=dob_input, defaulted_to=default_time_tz)
        dob_input = dob_input_with_default

    try:
        dt = datetime.strptime(dob_input, '%d/%m/%Y %H:%M %z')
        dt_utc = dt.astimezone(timezone.utc)
        
    except Exception as e:
        if tlog: tlog("natal_dob_parse_error", input=dob_input, error=str(e))
        return None 
        
    if tlog: tlog("natal_dob_parsed", dob_input=dob_input, dt_utc=str(dt_utc))
    
    jd = julian_day_from_datetime(dt_utc)
    CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    arr = swe.calc_ut(jd, swe.MOON, CALC_FLAGS) 
    lon = arr[0][0] if isinstance(arr[0], (list, tuple)) else arr[0]
    nak_idx = nakshatra_index_from_long(lon % 360.0)
    
    if tlog: tlog("natal_moon_nakshatra", nakshatra_index=nak_idx, moon_long=lon % 360.0)
    return nak_idx

# ---------------- Scoring ----------------
def check_affliction(p_lon: float, m_lon: float, tlog, planet_name: str, malefic_name: str, orb=AFFLICTION_ORB) -> bool:
    if p_lon == -1 or m_lon is None: return False
    diff = abs(p_lon - m_lon)
    if diff < orb or (360.0 - diff) < orb:
        if tlog: tlog("affliction_check_hit", planet=planet_name, malefic=malefic_name, difference=min(diff, 360.0 - diff), orb=orb)
        return True
    return False

def get_mercury_status(transits: dict, tlog=None):
    mercury_is_afflicted = False
    mercury_lon = transits.get('Mercury', -1)
    
    if mercury_lon != -1:
        for m in NATURAL_MALEFICS:
            malefic_lon = transits.get(m)
            if check_affliction(mercury_lon, malefic_lon, tlog, 'Mercury', m):
                mercury_is_afflicted = True
                break
    return mercury_is_afflicted, mercury_lon

def score_for_natal(janma_index: int, transits: dict, tlog=None):
    regions = offsets_to_indices(janma_index, tlog)
    janma_central_long = (janma_index + 0.5) * NAK_WIDTH
    kota_swami = RASHI_LORD[rashi_from_long(janma_central_long)]
    natal_pada = pada_of_long(janma_central_long)
    kota_paala = avakhada_pada_lord_from_nak_and_pada(janma_index, natal_pada, tlog) 
    score = 0
    details = {'added': [], 'subtracted': []}

    entry_indices = [(janma_index + o)%NAK_N for o in (0,7,14,21)]
    exit_indices = [(janma_index + o)%NAK_N for o in (3,10,17,24)]

    mercury_is_afflicted, mercury_lon = get_mercury_status(transits, tlog)

    # 1. Kota Swami in Stambha/Madhya (+3)
    for reg in ('Stambha','Madhya'):
        for nak_idx in regions[reg]:
            if kota_swami in transits:
                if nakshatra_index_from_long(transits[kota_swami]) == nak_idx:
                    score += 3
                    details['added'].append({'reason': f'{reg} match for kota_swami','planet':kota_swami,'value':3})
                    break 

    # 2. Kota Paala (Rashi Lord of Moon's Pada) in Bahya (+2)
    if kota_paala and kota_paala in transits:
        paala_nak = nakshatra_index_from_long(transits[kota_paala])
        if paala_nak in regions['Bahya']:
            score += 2
            details['added'].append({'reason':'bahya kota_paala','planet':kota_paala,'value':2})

    # 3. Malefics (Mars, Saturn, Rahu, Ketu) in Entry Gates (-3)
    for m in NATURAL_MALEFICS:
        if m in transits:
            m_nak = nakshatra_index_from_long(transits[m])
            if m_nak in entry_indices:
                score -= 3
                details['subtracted'].append({'reason':'malefic_entry','planet':m,'value':-3})

    # 4. Afflicted Mercury in Entry Gates (-3)
    if mercury_is_afflicted and mercury_lon != -1:
        mercury_nak = nakshatra_index_from_long(mercury_lon)
        if mercury_nak in entry_indices:
            score -= 3
            details['subtracted'].append({'reason':'afflicted_mercury_entry','planet':'Mercury','value':-3})

    # 5 & 6. Benefics (and Unafflicted Mercury) in Exit Gates (+1)
    planets_to_check = NATURAL_BENEFICS.copy()
    if not mercury_is_afflicted:
        planets_to_check.add('Mercury')
        
    for p in planets_to_check:
        if p in transits:
            p_nak = nakshatra_index_from_long(transits[p])
            if p_nak in exit_indices:
                score += 1
                details['added'].append({'reason':'benefic_exit','planet':p,'value':1})

    return {'score':score,'kota_swami':kota_swami,'kota_paala':kota_paala,'details':details}

def score_pada_lord_transit(pada_lord: str, lagna_nak_index: int, transits: dict, tlog=None):
    regions = offsets_to_indices(lagna_nak_index, tlog)
    score = 0
    
    if pada_lord not in transits: return 0
        
    p_nak = nakshatra_index_from_long(transits[pada_lord])

    for reg in ('Stambha','Madhya'):
        if p_nak in regions[reg]:
            score += 2
            return score 

    for reg in ('Bahya','Prakaara'):
        if p_nak in regions[reg]:
            score -= 1
            return score 
            
    return score

def score_transit_strength(transits: dict, lagna_nak_index: int, current_pada_lord: str | None = None, tlog=None) -> int:
    REFERENCE_NAK_INDEX = lagna_nak_index
    janma_central_long = (REFERENCE_NAK_INDEX + 0.5) * NAK_WIDTH
    kota_swami = RASHI_LORD[rashi_from_long(janma_central_long)]
    score = 0
    regions = offsets_to_indices(REFERENCE_NAK_INDEX, tlog)
    entry_indices = [(REFERENCE_NAK_INDEX + o)%NAK_N for o in (0,7,14,21)]
    mercury_is_afflicted, mercury_lon = get_mercury_status(transits, tlog)

    # Simplified scoring for Option 2 (Transit Check)
    # 1. Kota Swami in Stambha/Madhya (+3)
    for reg in ('Stambha','Madhya'):
        for nak_idx in regions[reg]:
            if kota_swami in transits and nakshatra_index_from_long(transits[kota_swami]) == nak_idx:
                score += 3
                break

    # 2. Dynamic Pada Lord Check
    if current_pada_lord:
        score += score_pada_lord_transit(current_pada_lord, REFERENCE_NAK_INDEX, transits, tlog)

    # 3/4. Malefics & Afflicted Mercury in Entry Gates (-3)
    for m in NATURAL_MALEFICS:
        if m in transits and nakshatra_index_from_long(transits[m]) in entry_indices:
            score -= 3
    if mercury_is_afflicted and mercury_lon != -1 and nakshatra_index_from_long(mercury_lon) in entry_indices:
        score -= 3

    # 5/6. Benefics & Unafflicted Mercury in Exit Gates (+1) (Exit indices are 4, 11, 18, 25)
    exit_indices = [(REFERENCE_NAK_INDEX + o)%NAK_N for o in (3,10,17,24)]
    planets_to_check = NATURAL_BENEFICS.copy()
    if not mercury_is_afflicted: planets_to_check.add('Mercury')

    for p in planets_to_check:
        if p in transits and nakshatra_index_from_long(transits[p]) in exit_indices:
            score += 1
            
    return score

# --- CRITICAL FIX FOR OPTION 2 TIMELINE DISPLAY ---
def calculate_dynamic_strength_timeline(start_dt_utc: datetime, tz: timezone, lat: float, lon: float, tlog=None, duration_hours: int = 8, pada_lord_system: str = 'vimshottari'):
    # The 'tz' (timezone) argument is now required to correctly format the output times.
    if pada_lord_system.lower() == 'avakhada':
        get_lord_func = avakhada_pada_lord_from_nak_and_pada
    else: 
        get_lord_func = vimshottari_pada_lord_from_nak_and_pada

    timeline = []
    current_dt_utc = start_dt_utc
    end_dt_utc = start_dt_utc + timedelta(hours=duration_hours)
    
    jd_ut_start = julian_day_from_datetime(current_dt_utc)
    lagna_nak_idx, lagna_pada, _ = get_ascendant_nakshatra_and_pada(jd_ut_start, lat, lon, tlog)
    start_pada_lord = get_lord_func(lagna_nak_idx, lagna_pada, tlog)
    transits = planetary_longitudes(jd_ut_start, tlog)
    initial_score = score_transit_strength(transits, lagna_nak_idx, start_pada_lord, tlog)

    # 1. Convert initial UTC time to Local time for display
    dt_local_start = start_dt_utc.astimezone(tz)
    
    timeline.append({
        'time': dt_local_start.strftime("%H:%M"),
        'jd_ut': jd_ut_start,
        'lagna_nak': lagna_nak_idx,
        'lagna_pada': lagna_pada,
        'pada_lord': start_pada_lord,
        'score': initial_score,
        'change': 'Start'
    })
    
    time_step = timedelta(minutes=15) 
    current_dt_utc += time_step

    while current_dt_utc <= end_dt_utc:
        jd_ut_current = julian_day_from_datetime(current_dt_utc)
        new_lagna_nak_idx, new_lagna_pada, _ = get_ascendant_nakshatra_and_pada(jd_ut_current, lat, lon, tlog)
        
        # Check for change in Lagna Pada
        if new_lagna_nak_idx != lagna_nak_idx or new_lagna_pada != lagna_pada:
            transits = planetary_longitudes(jd_ut_current, tlog)
            new_pada_lord = get_lord_func(new_lagna_nak_idx, new_lagna_pada, tlog)
            new_score = score_transit_strength(transits, new_lagna_nak_idx, new_pada_lord, tlog)
            
            # 2. Convert current UTC time to Local time for display
            dt_utc_current = datetime_from_julian_day(jd_ut_current)
            dt_local_current = dt_utc_current.astimezone(tz)
            
            timeline.append({
                'time': dt_local_current.strftime("%H:%M"),
                'jd_ut': jd_ut_current,
                'lagna_nak': new_lagna_nak_idx,
                'lagna_pada': new_lagna_pada,
                'pada_lord': new_pada_lord,
                'score': new_score,
                'change': f'Pada Change: {lagna_nak_idx}.{lagna_pada} -> {new_lagna_nak_idx}.{new_lagna_pada}'
            })
            
            lagna_nak_idx = new_lagna_nak_idx
            lagna_pada = new_lagna_pada
            
        current_dt_utc += time_step
        
    return timeline
# --- END CRITICAL FIX ---


# ---------------- Interactive CLI ----------------
if __name__=="__main__":
    if not GEOLOCATOR_AVAILABLE:
        print("\n*** WARNING: Geocoding library 'geopy' not found. Location lookup is disabled. ***")
        print("*** Please run 'pip install geopy' for Option 2 to work correctly. ***\n")
        
    logger.setLevel(logging.INFO)
    print("=== KOTA Chakra Interactive (debuggable) ===")
    print("Choose mode:")
    print("1) Compare two people (DOBs)")
    print("2) Toss advantage check (transit strength at location & time duration)") 
    print("3) Batch CSV processing")
    choice = input("Enter 1, 2, or 3 [default 2]: ").strip()
    if choice not in ('1','2','3'): choice='2'

    calc_mode_input = input("Calculation mode ('sidereal' or 'tropical') [default: sidereal]: ").strip().lower()
    if calc_mode_input not in ('sidereal','tropical'): calc_mode_input=DEFAULT_CALC_MODE
    verbose_input = input("Verbose debug trace? (y/N): ").strip().lower()
    verbose = verbose_input=='y'
    
    # --- Universal Time Inputs ---
    current_date = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    match_date = input(f"Enter match date (DD/MM/YYYY or YYYY-MM-DD) [default: {current_date}]: ").strip() or current_date
    match_time = input("Enter match time (HH:MM) [default: 12:00]: ").strip() or '12:00'
    timezone_input = input("Enter timezone (HH:MM or +HH:MM) [default: 00:00]: ").strip() or '00:00'

    # --- Processing ---
    tlog, trace = make_tracer(verbose=verbose) 
    set_swe_mode(calc_mode_input, tlog) 
    
    # Calculate MATCH UTC Time for Transits
    tz = parse_hhmm_timezone(timezone_input)
    dt_str = f"{match_date} {match_time}"
    date_format = "%d/%m/%Y %H:%M"
    try:
        naive = datetime.strptime(dt_str, date_format)
        # Apply the input timezone to the naive datetime object
        match_dt_local = naive.replace(tzinfo=tz) 
        match_dt_utc = match_dt_local.astimezone(timezone.utc)
        match_jd_ut = julian_day_from_datetime(match_dt_utc)
        match_transits = planetary_longitudes(match_jd_ut, tlog)
        
    except Exception as e:
        print(f"Error processing match date/time: {e}")
        exit()

    if choice=='3':
        print("\nNote: Option 3 (Batch processing) logic is currently a placeholder.")
        
    elif choice=='1':
        # Option 1: Comparison (Now Fully Implemented with practical defaults)
        
        # Simplified prompt for DOB, using the new default logic
        captain_a_dob_input = input("Captain A DOB (DD/MM/YYYY only, e.g., 31/12/1997) [demo if blank]: ").strip() or '31/12/1997'
        captain_b_dob_input = input("Captain B DOB (DD/MM/YYYY only, e.g., 12/10/2001) [demo if blank]: ").strip() or '12/10/2001'

        # 1. Get Natal Moon Nakshatra Index
        # The function handles adding the default time/timezone if missing
        nak_a = natal_moon_nakshatra_index(captain_a_dob_input, tlog)
        nak_b = natal_moon_nakshatra_index(captain_b_dob_input, tlog)
        
        if nak_a is None or nak_b is None:
            print("\nError: Could not determine Natal Moon Nakshatra for one or both captains. Please ensure the DD/MM/YYYY format is correct.")
            exit()
            
        # 2. Calculate Score
        score_a_result = score_for_natal(nak_a, match_transits, tlog)
        score_b_result = score_for_natal(nak_b, match_transits, tlog)
        
        score_a = score_a_result['score']
        score_b = score_b_result['score']
        
        print("\n=== KOTA CHAKRA COMPARISON (Option 1) ===")
        print(f"Match Time (Local): **{match_dt_local.strftime('%d/%m/%Y %H:%M %z')}**")
        print("---")
        print(f"Captain A (DOB: {captain_a_dob_input})")
        print(f"  Natal Moon Nakshatra Index: **{nak_a}**")
        print(f"  Score: **{score_a}**")
        print("---")
        print(f"Captain B (DOB: {captain_b_dob_input})")
        print(f"  Natal Moon Nakshatra Index: **{nak_b}**")
        print(f"  Score: **{score_b}**")
        print("---")
        
        if score_a > score_b:
            print(f"Final Prediction: **Captain A is favored to win!** (Score {score_a} > {score_b}) ✅")
        elif score_b > score_a:
            print(f"Final Prediction: **Captain B is favored to win!** (Score {score_b} > {score_a}) ✅")
        else:
            print(f"Final Prediction: **Tie/Even Match!** (Score {score_a} = {score_b}) ⚖️")


    elif choice=='2':
        # Option 2: Dynamic Toss Advantage Check 
        
        match_place = input("Enter Match Place (City/Ground Name) [default: Delhi]: ").strip() or 'Delhi'
        duration_input = input("Enter Match Duration (in hours) [default: 8]: ").strip() or '8'
        try:
            match_duration_hours = int(duration_input)
        except ValueError:
            print("Error: Match duration must be an integer.")
            exit()

        pada_system_input = input("Choose Pada Lord System: (1) Vimshottari (Dasa Lords) or (2) Avakhada (Rashi Lords) [default: 1]: ").strip()
        pada_lord_system = 'avakhada' if pada_system_input == '2' else 'vimshottari'
        print(f"-> Using {pada_lord_system.capitalize()} (Pada Lord) system for dynamic scoring.")
            
        coords = lookup_coordinates(match_place, tlog)
        if coords:
            match_lat, match_lon = coords
            print(f"-> Coordinates used: Lat {match_lat}, Lon {match_lon}")
        else:
            match_lat, match_lon = 28.7, 77.2
            print(f"-> Could not resolve location. Using Fallback coordinates: Lat {match_lat}, Lon {match_lon}")
            
        try:
            # --- CRITICAL CHANGE: Pass the 'tz' object ---
            strength_timeline = calculate_dynamic_strength_timeline(
                match_dt_utc, tz, match_lat, match_lon, tlog, 
                duration_hours=match_duration_hours,
                pada_lord_system=pada_lord_system 
            )
            # ---------------------------------------------
            
        except Exception as e:
            print(f"Error processing dynamic calculation for Option 2: {e}")
            strength_timeline = None
            
        print("\n=== DYNAMIC TOSS ADVANTAGE CHECK ===")
        if strength_timeline:
            print(f"Match Location: **{match_place}** (Duration: {match_duration_hours} hrs)")
            print(f"Pada Lord System: **{pada_lord_system.capitalize()}**")
            
            initial_state = strength_timeline[0]
            
            # Use the correctly calculated Local Match Start Time for display
            offset_seconds = tz.utcoffset(None).total_seconds()
            offset_hours = int(offset_seconds // 3600)
            offset_minutes = int((offset_seconds % 3600) // 60)
            offset_sign = '+' if offset_hours >= 0 else '-'
            tz_display = f"{offset_sign}{abs(offset_hours):02}:{abs(offset_minutes):02}"
            
            print(f"\nLocal Match Start Time: **{match_dt_local.strftime('%d/%m/%Y %H:%M')} {tz_display}**")

            print(f"Time {initial_state['time']} (Toss): Score **{initial_state['score']}**")
            print(f"  (Lagna Nak: {initial_state['lagna_nak']}, Pada: {initial_state['lagna_pada']}, Lord: {initial_state['pada_lord']})")

            print("\n--- Subsequent Strength Changes (Lagna Pada Shifts, Local Time) ---")
            has_change = len(strength_timeline) > 1
            if has_change:
                for i in range(1, len(strength_timeline)):
                    entry = strength_timeline[i]
                    prev_score = strength_timeline[i-1]['score']
                    
                    change_indicator = ""
                    if entry['score'] < prev_score:
                        change_indicator = "(-)"
                    elif entry['score'] > prev_score:
                        change_indicator = "(+)"
                    else:
                        change_indicator = "(~)" # Stable
                    
                    # Display the local time which is now correctly stored in 'entry['time']'
                    print(f"Time {entry['time']}: Score **{entry['score']}** (Lord: {entry['pada_lord']}) {change_indicator}")
            
            if not has_change:
                print(f"No Lagna Pada changes detected within the {match_duration_hours}-hour window.")
                
        # --- Save Trace for Option 2 ---
        if verbose and strength_timeline is not None:
            ts = int(time.time())
            tmp_dir = os.path.join(os.getcwd(), "tmp_traces")
            os.makedirs(tmp_dir, exist_ok=True)
            fname_base = f"kota_trace_transit_strength_{match_date.replace('/', '_')}_{match_time.replace(':', '_')}"
            fname = os.path.join(tmp_dir, f"{fname_base}.json")
            
            counter = 0
            while os.path.exists(fname):
                counter += 1
                fname = os.path.join(tmp_dir, f"{fname_base}_{counter}.json")
                
            with open(fname,"w",encoding="utf-8") as fh: json.dump(trace, fh, indent=2, default=str)
            print(f"Trace saved at {fname}")