#!/usr/bin/env python3
"""
Master Offline Astro–Numerology & Match Trend Script
Reads match data from 'match_analysis_data.xlsx', calculates results,
and writes output back to the same file, appending new columns for analysis.

Includes six distinct toss prediction methods and a final consolidated prediction 
based on a majority vote, along with heuristic score prediction for all formats.

SETUP REQUIREMENTS: 
You MUST install the necessary Python libraries before running:
pip install pyswisseph python-dateutil pandas openpyxl

USAGE:
1. Ensure the input file 'match_analysis_data.xlsx' is in the same folder.
2. Ensure the Excel file is CLOSED before running the script.
3. Add required columns to your Excel file:
    - 'Match_Format' (e.g., T10, T20, 100-BALL, ODI, or TEST)
    - 'Team_A_Name' and 'Team_B_Name' (The actual team names for context)
    - 'Captain_A_Name' and 'Captain_B_Name' (The player names for numerology analysis)
    - 'Team_A_DOB' and 'Team_B_DOB' (The Captain's DOBs in DD/MM/YYYY format)
    - 'Match_Date', 'Match_Time' (e.g., 18:00), 'TZ_Offset_Hours' (e.g., 5.5 for India), 'Match_Place'
4. Run the script from your terminal: python astro_numerology_analysis.py
"""
import sys
import random
import pandas as pd
from datetime import datetime, date, time, timedelta

# Attempt to import Swiss Ephemeris library
try:
    import swisseph as swe
except ImportError:
    # If using Windows, try 'pip install pyswisseph' first.
    print("ERROR: 'pyswisseph' module not found. Please install it using: pip install pyswisseph")
    sys.exit(1)

# ---------------------------
# Constants
# ---------------------------

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
    "Sagittarius","Capricorn","Aquarius","Pisces"
]

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashirsha","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]

# Nakshatra Lords (Used for Toss Method 3)
NAKSHATRA_LORDS = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
]

# Sign Lords (Used for Toss Method 6)
SIGN_LORDS = {
    "Aries": 'Mars', "Taurus": 'Venus', "Gemini": 'Mercury', 
    "Cancer": 'Moon', "Leo": 'Sun', "Virgo": 'Mercury', 
    "Libra": 'Venus', "Scorpio": 'Mars', "Sagittarius": 'Jupiter', 
    "Capricorn": 'Saturn', "Aquarius": 'Saturn', "Pisces": 'Jupiter'
}

# Planet/Number mapping (Used for Toss Methods)
PLANET_NUMBERS = {
    'Sun': 1, 'Moon': 2, 'Jupiter': 3, 'Rahu': 4, 'Mercury': 5, 
    'Venus': 6, 'Ketu': 7, 'Saturn': 8, 'Mars': 9, 'Neptune': 7, 'Uranus': 4, 'Pluto': 9
}

# Day of Week Lord (Used for Toss Method 2) - Mon=0, Tue=1, ..., Sun=6
DAY_LORDS = {
    0: 'Moon',    # Monday
    1: 'Mars',    # Tuesday
    2: 'Mercury', # Wednesday
    3: 'Jupiter', # Thursday
    4: 'Venus',   # Friday
    5: 'Saturn',  # Saturday 
    6: 'Sun',     # Sunday
}

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN
}

# Pythagorean letter-to-number map for Numerology
PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

# Lucky colors based on single-digit numerology (1-9)
lucky_colors = {
    1: ["Red", "Orange", "Gold"], 2: ["White", "Light Blue", "Silver"],
    3: ["Yellow", "Purple", "Pink"], 4: ["Grey", "Dark Blue"],
    5: ["Green", "Light Brown"], 6: ["Cream", "Pink", "Light Blue"],
    7: ["Sea Green", "White"], 8: ["Dark Blue", "Black"], 9: ["Red", "Maroon"]
}

# Compatible numerology pairs for date compatibility check
good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

# ---------------------------
# Numerology helpers
# ---------------------------

def reduce_num(n: int) -> int:
    """Reduce to a single digit by iterative digit-sum (1-9)."""
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    """Birth number = reduced day of month."""
    try:
        # Assuming DD/MM/YYYY format from the generator script
        dt = datetime.strptime(dob_str, "%d/%m/%Y")
        return reduce_num(dt.day)
    except:
        # Fallback if DOB is not in expected format
        return reduce_num(sum(int(c) for c in dob_str if c.isdigit()))

def life_path_number(dob_str: str) -> int:
    """Life path number = reduced sum of all digits in DOB."""
    digits = "".join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def name_number(name: str) -> int:
    """Calculates the reduced numerological value of a name."""
    s = 0
    for ch in name.upper():
        if ch.isalpha():
            s += PYTH_MAP.get(ch, 0)
    return reduce_num(s)

def date_life_path(date_str: str) -> int:
    """Life path number of the date itself."""
    # Takes formatted date string like "25/08/2025" or "2025-08-25"
    digits = "".join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def numerology_compat(bno, lp, dno, dlp):
    """Checks captain's numbers against match date numbers."""
    # Check compatibility for Birth Number (BNO) vs Day Number (DNO)
    # Check compatibility for Life Path (LP) vs Date Life Path (DLP)
    if (bno, dno) in good_pairs or (lp, dlp) in good_pairs:
        return "GOOD DAY"
    return "BAD DAY"

# ---------------------------
# Colour and Power helpers
# ---------------------------

def color_fine_tune(captain_colors, date_colors):
    """Finds common colours and assigns a strength rating."""
    cset, dset = set(captain_colors), set(date_colors)
    common = cset.intersection(dset)
    if not common:
        return {"match":"No colour match", "strength":"Neutral","winning_colour":"None"}
    
    # Priority check for strong colours (Red/Maroon/Gold)
    strong_colors = [c for c in common if c in ["Red", "Maroon", "Gold"]]
    if strong_colors:
        return {"match":"Colour aligned","strength":"Very Strong","winning_colour":", ".join(strong_colors)}
    
    # Second priority for impactful colours (Blue/Yellow/Purple)
    impact_colors = [c for c in common if c in ["Dark Blue", "Light Blue", "Yellow", "Purple"]]
    if impact_colors:
        return {"match":"Colour aligned","strength":"Strong","winning_colour":", ".join(impact_colors)}
    
    return {"match":"Colour aligned","strength":"Medium","winning_colour":", ".join(list(common))}

def day_power(match_date: date) -> int:
    """Calculates a power score for the day (1-10)"""
    # Sum of reduced Day Number and reduced Month Number
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    
    weekday = match_date.weekday()  # 0=Mon..6=Sun
    # Arbitrary weekday bonuses based on their ruling planet's strength
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1) # Stronger weight on Fri/Sun/Thu
    
    # Total power is a combination of these elements
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)

def place_power(place_name: str) -> int:
    """Calculates a power score for the place (1-10)"""
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
    # Place power is based on the reduced name number
    return min(reduce_num(s), 10)

def calculate_five_day_power(start_date: date, place_name: str) -> tuple:
    """
    Calculates the averaged Day Power (dp) and the single Place Power (pp)
    for a 5-day Test Match, starting from the given date.
    
    Returns: (avg_day_power, place_power)
    """
    # 1. Place Power (Static based on name)
    place_p = place_power(place_name)
    
    # 2. 5-Day Averaged Day Power
    total_day_power = 0
    num_days = 5
    
    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        # Sum the Day Power for 5 consecutive days
        total_day_power += day_power(current_date)
        
    # Use the average power over the 5 days, rounded to the nearest integer
    # This prevents the final power score from being too diluted/complex
    avg_day_power = round(total_day_power / num_days)
    
    return avg_day_power, place_p


# ---------------------------
# Swiss Ephemeris helpers
# ---------------------------

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    """
    Convert local datetime and tz offset (hours east of UTC) to Julian Day (UT).
    """
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    # The time component must be passed as a fraction of a day
    time_fraction = (dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0) / 24.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, time_fraction)

def sign_from_long(lon_deg):
    """Converts a 360-degree longitude to Zodiac Sign and degree within sign."""
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
    """Determines Nakshatra, Pada, and Lord from Moon's longitude."""
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx] 
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada, "lord": lord}

# ---------------------------
# Toss Prediction Logic (Methods 1-3)
# ---------------------------

def predict_toss_numerology(a_name, b_name, numerology_a, numerology_b):
    """
    Toss Method 1: Numerology compatibility between Captain's numbers and the Match Date (Day 1).
    """
    if numerology_a == "GOOD DAY" and numerology_b == "BAD DAY":
        return f"Captain A ({a_name} - Good Day)"
    if numerology_b == "GOOD DAY" and numerology_a == "BAD DAY":
        return f"Captain B ({b_name} - Good Day)"
    
    # If both good or both bad, it's a toss-up
    return "Neutral (Numerology Tie)"

def predict_toss_horary(a_name, b_name, a_bno, b_bno, match_date):
    """
    Toss Method 2: Day Ruler's Number Advantage (Day 1).
    The Captain whose Birth Number matches the Day Ruler's Number wins.
    """
    weekday = match_date.weekday()
    lord_name = DAY_LORDS[weekday]
    lord_number = PLANET_NUMBERS.get(lord_name, 5) 
    
    a_match = a_bno == lord_number
    b_match = b_bno == lord_number

    if a_match and not b_match:
        return f"Captain A ({a_name} - Day Ruler {lord_number})"
    if b_match and not a_match:
        return f"Captain B ({b_name} - Day Ruler {lord_number})"
    
    # Check for proximity (plus/minus 1)
    if not a_match and not b_match:
        # Check proximity in a circular manner (1 and 9 are 2 apart, not 8)
        a_prox = min(abs(a_bno - lord_number), 9 - abs(a_bno - lord_number))
        b_prox = min(abs(b_bno - lord_number), 9 - abs(b_bno - lord_number))
        
        if a_prox < b_prox:
            return f"Captain A ({a_name} - Ruler Proximity)"
        if b_prox < a_prox:
            return f"Captain B ({b_name} - Ruler Proximity)"


    return "Neutral (Horary Tie)"

def predict_toss_star_lord(a_name, b_name, a_bno, b_bno, moon_info):
    """
    Toss Method 3: Nakshatra Lord (Star Lord) Numerology (Day 1).
    The Captain whose Birth Number matches the Star Lord's Number wins.
    """
    star_lord = moon_info["lord"]
    lord_number = PLANET_NUMBERS.get(star_lord)

    if lord_number is None:
        return "Neutral (Lord Unknown)"

    a_match = a_bno == lord_number
    b_match = b_bno == lord_number

    if a_match and not b_match:
        return f"Captain A ({a_name} - Star Lord Match)"
    if b_match and not a_match:
        return f"Captain B ({b_name} - Star Lord Match)"

    # Fallback to proximity
    if not a_match and not b_match:
        # Check proximity in a circular manner
        a_prox = min(abs(a_bno - lord_number), 9 - abs(a_bno - lord_number))
        b_prox = min(abs(b_bno - lord_number), 9 - abs(b_bno - lord_number))
        
        if a_prox < b_prox:
            return f"Captain A ({a_name} - Star Lord Proximity)"
        if b_prox < a_prox:
            return f"Captain B ({b_name} - Star Lord Proximity)"

    return "Neutral (Star Lord Tie)"

# ---------------------------
# Toss Prediction Logic (Methods 4-6 - Tie Breakers)
# ---------------------------

def predict_toss_ruling_number(a_name, b_name, a_bno, b_bno, m_dno):
    """
    Toss Method 4: Ruling Number (Match Date Day Number).
    The Captain whose Birth Number matches the Match Date's Day Number (m_dno) wins.
    """
    a_match = a_bno == m_dno
    b_match = b_bno == m_dno

    if a_match and not b_match:
        return f"Captain A ({a_name} - Ruling No. Match)"
    if b_match and not a_match:
        return f"Captain B ({b_name} - Ruling No. Match)"
    
    # Fallback to proximity
    if not a_match and not b_match:
        a_prox = min(abs(a_bno - m_dno), 9 - abs(a_bno - m_dno))
        b_prox = min(abs(b_bno - m_dno), 9 - abs(b_bno - m_dno))
        
        if a_prox < b_prox:
            return f"Captain A ({a_name} - Ruling No. Proximity)"
        if b_prox < a_prox:
            return f"Captain B ({b_name} - Ruling No. Proximity)"

    return "Neutral (Ruling No. Tie)"

def predict_toss_compound_score(a_name, b_name, a_bno, b_bno, a_name_num, b_name_num):
    """
    Toss Method 5: Compound Toss Score (BNO + Name Number).
    The captain with the highest reduced combined score wins.
    """
    # Reduce the sum of Birth Number (BNO) and Name Number (NN)
    a_score = reduce_num(a_bno + a_name_num)
    b_score = reduce_num(b_bno + b_name_num)
    
    if a_score > b_score:
        return f"Captain A ({a_name} - Compound Score {a_score} > {b_score})"
    if b_score > a_score:
        return f"Captain B ({b_name} - Compound Score {b_score} > {a_score})"
    
    return "Neutral (Compound Score Tie)"

def predict_toss_moon_sign_lord(a_name, b_name, a_bno, b_bno, moon_sign):
    """
    Toss Method 6: Moon Sign Lord Numerology.
    The Captain whose Birth Number matches the Moon Sign Lord's Number wins.
    """
    lord_name = SIGN_LORDS.get(moon_sign)
    lord_number = PLANET_NUMBERS.get(lord_name)

    if lord_number is None:
        return "Neutral (Sign Lord Unknown)"

    a_match = a_bno == lord_number
    b_match = b_bno == lord_number

    if a_match and not b_match:
        return f"Captain A ({a_name} - Sign Lord Match)"
    if b_match and not a_match:
        return f"Captain B ({b_name} - Sign Lord Match)"

    # Fallback to proximity
    if not a_match and not b_match:
        a_prox = min(abs(a_bno - lord_number), 9 - abs(a_bno - lord_number))
        b_prox = min(abs(b_bno - lord_number), 9 - abs(b_bno - lord_number))
        
        if a_prox < b_prox:
            return f"Captain A ({a_name} - Sign Lord Proximity)"
        if b_prox < a_prox:
            return f"Captain B ({b_name} - Sign Lord Proximity)"

    return "Neutral (Sign Lord Tie)"

# ---------------------------
# Final Prediction Logic
# ---------------------------

def final_toss_prediction(toss_results):
    """
    Analyzes results from all 6 toss methods to determine a final prediction.
    The prediction is based on the majority vote across all six methods.
    """
    a_wins = 0
    b_wins = 0
    a_name = ""
    b_name = ""
    
    # Iterate through all 6 results
    for key, result in toss_results.items():
        if result.startswith("Captain A"):
            a_wins += 1
            # Extract name from the first result that provides it
            if not a_name:
                a_name = result.split('(')[1].split(' -')[0].strip() 
        elif result.startswith("Captain B"):
            b_wins += 1
            if not b_name:
                b_name = result.split('(')[1].split(' -')[0].strip()
        # Neutral results don't count towards A or B win total

    total_predictions = a_wins + b_wins
    
    # If a clear majority (4 or more wins out of 6)
    if a_wins >= 4:
        return f"Captain A ({a_name}) - Strong Majority ({a_wins}-{b_wins} Score)"
    if b_wins >= 4:
        return f"Captain B ({b_name}) - Strong Majority ({b_wins}-{a_wins} Score)"
    
    # Simple majority (3-2) or all 6 resolved (3-3 tie)
    if a_wins > b_wins and total_predictions >= 5: # 3-2, 4-1, 5-0 scenarios where at least 5 results were non-neutral
         return f"Captain A ({a_name}) - Simple Majority ({a_wins}-{b_wins} Score)"
    if b_wins > a_wins and total_predictions >= 5: # 2-3, 1-4, 0-5 scenarios
         return f"Captain B ({b_name}) - Simple Majority ({b_wins}-{a_wins} Score)"

    return f"Neutral - Tie/Mixed Results ({a_wins}-{b_wins} Score)"


# ---------------------------
# Score Prediction Logic
# ---------------------------

def predict_score_range(score_a: int, score_b: int) -> dict:
    """
    Predicts score ranges for T10, T20, 100-Ball, ODI, and TEST based on combined Match Energy Score.
    Max total match energy is around 80.
    """
    total_match_energy = score_a + score_b
    
    # Define Tiers based on Total Match Energy (out of ~80)
    if total_match_energy <= 45: # Low/Medium-Low energy day
        label = "Low Scoring Pitch/Day"
        
        t10_range = "70 - 90"
        t20_range = "130 - 160"
        hundred_ball_range = "110 - 135" 
        odi_range = "230 - 270"
        test_range = "Slow-paced match. Likely draws or low individual scores."
        
    elif total_match_energy <= 65: # Medium/Medium-High energy day
        label = "Balanced Scoring Pitch/Day"
        
        t10_range = "91 - 110"
        t20_range = "161 - 185"
        hundred_ball_range = "136 - 165" 
        odi_range = "271 - 320"
        test_range = "Balanced play. Expect good scores but quick wickets at times."
        
    else: # total_match_energy > 65: # High/Very High energy day
        label = "High Scoring Pitch/Day"
        
        t10_range = "111 - 130+"
        t20_range = "186 - 210+"
        hundred_ball_range = "166 - 190+"
        odi_range = "321 - 360+"
        test_range = "High scoring pitch/day. Expect quick runs and definitive results."
        
    return {
        "label": label,
        "energy_score": total_match_energy,
        "T10": t10_range,
        "T20": t20_range,
        "100-BALL": hundred_ball_range,
        "ODI": odi_range,
        "TEST": test_range
    }


# ---------------------------
# Main function
# ---------------------------

def main():
    print("=== MASTER OFFLINE ASTRO–NUMEROLOGY (IN-PLACE EXCEL I/O) ===\n")
    
    IO_FILE = "match_analysis_data.xlsx"
    
    try:
        df_input = pd.read_excel(IO_FILE)
        print(f"Successfully loaded {len(df_input)} matches from {IO_FILE}")
    except FileNotFoundError:
        print(f"FATAL ERROR: Input file '{IO_FILE}' not found. Please create it or check the file name/location.")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR reading Excel file: {e}")
        sys.exit(1)

    all_results = []

    for index, row in df_input.iterrows():
        match_date_raw = "N/A"
        team_a = "N/A"
        team_b = "N/A"
        a_name = "N/A"
        b_name = "N/A"

        try:
            # --- 1. Parse Input from Row ---
            
            # Read Team Names (for context)
            team_a = row.get('Team_A_Name', f'TeamA_{index}')
            team_b = row.get('Team_B_Name', f'TeamB_{index}')

            # Read Captain Names (used for all numerology calculations)
            a_name = row.get('Captain_A_Name', team_a)
            a_dob = str(row.get('Team_A_DOB', '01/01/1980')).split()[0]
            b_name = row.get('Captain_B_Name', team_b)
            b_dob = str(row.get('Team_B_DOB', '01/01/1980')).split()[0]
            
            # Match Format - REQUIRED FOR SCORE PREDICTION
            match_format_raw = str(row.get('Match_Format', 'T20')).upper()
            match_format = match_format_raw.replace(" ", "").replace("-", "") 
            
            # Robust Date Parsing
            match_date_raw = str(row.get('Match_Date', '01/01/2025')).split()[0]
            try:
                match_date = pd.to_datetime(match_date_raw).date()
                match_date_str_fmt = match_date.strftime("%d/%m/%Y")
            except Exception:
                match_date = datetime.strptime(match_date_raw, "%d/%m/%Y").date()
                match_date_str_fmt = match_date_raw
                
            match_time_str = str(row.get('Match_Time', '06:00'))
            tz_off_hours = float(row.get('TZ_Offset_Hours', 0.0))
            match_place = row.get('Match_Place', 'Unknown')
            
            try:
                hm = datetime.strptime(match_time_str, "%H:%M").time()
            except ValueError:
                hm = time(6, 0)
            
            local_dt = datetime.combine(match_date, hm)
            jd_ut = to_utc_jd_from_datetime(local_dt, tz_offset_hours=tz_off_hours)

            # --- 2. Run Core Calculations (Astro) ---
            
            # Astro calculations (for Moon/Star Lord/Sun Sign) remain based on Day 1 (Toss day)
            ayanamsa = swe.get_ayanamsa_ut(jd_ut)
            planets = {}
            for name, pid in PLANETS.items():
                res = swe.calc_ut(jd_ut, pid)
                lon = float(res[0][0])
                sidereal_lon = (lon - ayanamsa) % 360.0
                sign, deg = sign_from_long(sidereal_lon)
                planets[name] = {"degree_total": round(sidereal_lon, 6), "sign": sign}
            
            moon_lon = planets["Moon"]["degree_total"]
            moon_sign = planets["Moon"]["sign"] # Used for Method 6
            moon_info = moon_nakshatra_pada(moon_lon)
            
            # --- 3. Run Core Calculations (Numerology) ---
            
            # Numerology uses captain's DOB/Name
            a_bno = birth_number(a_dob)
            a_lp = life_path_number(a_dob)
            b_bno = birth_number(b_dob)
            b_lp = life_path_number(b_dob)

            a_name_num = name_number(a_name)
            b_name_num = name_number(b_name)
            
            m_dno = reduce_num(match_date.day) # Used for Method 4
            m_dlp = date_life_path(match_date_str_fmt)
            
            numerology_a = numerology_compat(a_bno, a_lp, m_dno, m_dlp)
            numerology_b = numerology_compat(b_bno, b_lp, m_dno, m_dlp)
            
            # Power Scores - Adjusted for Test Matches
            if match_format == 'TEST':
                dp, pp = calculate_five_day_power(match_date, match_place)
                match_format_clean = "TEST"
            else:
                dp = day_power(match_date)
                pp = place_power(match_place)
                
                # Normalize 100-Ball variations
                if match_format in ['100BALL', '100', '100DAYS']:
                    match_format_clean = '100-BALL'
                elif match_format == 'T10':
                    match_format_clean = 'T10'
                elif match_format == 'T20':
                    match_format_clean = 'T20'
                elif match_format == 'ODI':
                    match_format_clean = 'ODI'
                else:
                    match_format_clean = match_format
            
            # --- 4. Toss and Match Trend Predictions (All 6 Methods + Final) ---
            
            # Methods 1-3
            toss_num = predict_toss_numerology(a_name, b_name, numerology_a, numerology_b)
            toss_horary = predict_toss_horary(a_name, b_name, a_bno, b_bno, match_date)
            toss_star = predict_toss_star_lord(a_name, b_name, a_bno, b_bno, moon_info)

            # New Tie-Breaker Methods 4-6
            toss_ruling = predict_toss_ruling_number(a_name, b_name, a_bno, b_bno, m_dno)
            toss_compound = predict_toss_compound_score(a_name, b_name, a_bno, b_bno, a_name_num, b_name_num)
            toss_sign_lord = predict_toss_moon_sign_lord(a_name, b_name, a_bno, b_bno, moon_sign)
            
            # Consolidate all 6 results for the final prediction
            toss_results = {
                'Method 1': toss_num, 'Method 2': toss_horary, 'Method 3': toss_star,
                'Method 4': toss_ruling, 'Method 5': toss_compound, 'Method 6': toss_sign_lord
            }
            final_toss = final_toss_prediction(toss_results)

            # Match Trend Score (Power Score Calculation)
            # The scores are the sum of: Captain's Life Path, Captain's Name Number, Day Power, Place Power.
            score_a = sum([a_lp, a_name_num, dp, pp])
            score_b = sum([b_lp, b_name_num, dp, pp])
            
            if score_a > score_b:
                advantage = f"Captain A ({a_name})"
            elif score_b > score_a:
                advantage = f"Captain B ({b_name})"
            else:
                advantage = "Neutral / Balanced"

            # Score Prediction - retrieves all formats
            score_prediction = predict_score_range(score_a, score_b)
            predicted_range = score_prediction.get(match_format_clean, "N/A - Check Format")


            # Colours (remain based on Day 1)
            date_colors = lucky_colors.get(m_dno, [])
            a_color_res = color_fine_tune(lucky_colors.get(a_bno, []), date_colors)
            b_color_res = color_fine_tune(lucky_colors.get(b_bno, []), date_colors)

            # --- 5. Collect Results for THIS ROW ---

            result = {
                # New: Team Names (for overall match context)
                'Team_A_Name': team_a,
                'Team_B_Name': team_b,

                # New: Captain Names (used for numerology calculations)
                'Captain_A_Name': a_name,
                'Captain_B_Name': b_name,

                # Astro
                'Moon_Nakshatra': moon_info["nakshatra"],
                'Star_Lord': moon_info["lord"], 
                'Sun_Sign': planets["Sun"]["sign"],
                
                # Numerology (BNO/LP are based on Captains)
                'A_BNO': a_bno, 
                'A_Life_Path': a_lp,
                'B_BNO': b_bno, 
                'B_Life_Path': b_lp,
                'A_Numerology_Compat': numerology_a,
                'B_Numerology_Compat': numerology_b,
                
                # Scores
                'Day_Power': dp, 
                'Place_Power': pp,
                'A_Match_Score': score_a,
                'B_Match_Score': score_b,
                'Overall_Advantage': advantage,

                # Toss Predictions (All 6 methods)
                'Toss_Method_1_Numerology': toss_num,
                'Toss_Method_2_Horary_Ruler': toss_horary,
                'Toss_Method_3_Star_Lord': toss_star,
                'Toss_Method_4_Ruling_No': toss_ruling,
                'Toss_Method_5_Compound_Score': toss_compound,
                'Toss_Method_6_Moon_Sign_Lord': toss_sign_lord,
                'Final_Toss_Prediction': final_toss, # New consolidated result

                # Score Range Prediction (Now specific to the input format)
                'Match_Energy_Label': score_prediction['label'],
                'Predicted_Score_Range': predicted_range,

                # Colors
                'A_Winning_Colour': a_color_res['winning_colour'],
                'B_Winning_Colour': b_color_res['winning_colour'],
                'Color_Match_Strength': a_color_res['strength'] if score_a > score_b else (
                                        b_color_res['strength'] if score_b > score_a else "Neutral"),
            }
            all_results.append(result)

        except Exception as e:
            error_message = f"ROW ERROR: {type(e).__name__}: {str(e)}"
            print(f"Error processing row {index} (Date: {match_date_raw}): {error_message}")
            # If an error occurs, still append a dictionary to maintain row count and context
            all_results.append({
                'Team_A_Name': team_a, 
                'Team_B_Name': team_b, 
                'Captain_A_Name': a_name,
                'Captain_B_Name': b_name,
                'Overall_Advantage': error_message,
                # Fill other columns with error placeholders
                'Moon_Nakshatra': 'ERROR', 'Star_Lord': 'ERROR', 'Sun_Sign': 'ERROR',
                'A_BNO': 0, 'A_Life_Path': 0, 'B_BNO': 0, 'B_Life_Path': 0,
                'A_Numerology_Compat': 'ERROR', 'B_Numerology_Compat': 'ERROR',
                'Day_Power': 0, 'Place_Power': 0, 'A_Match_Score': 0, 'B_Match_Score': 0,
                'Toss_Method_1_Numerology': 'ERROR', 'Toss_Method_2_Horary_Ruler': 'ERROR',
                'Toss_Method_3_Star_Lord': 'ERROR',
                'Toss_Method_4_Ruling_No': 'ERROR',
                'Toss_Method_5_Compound_Score': 'ERROR',
                'Toss_Method_6_Moon_Sign_Lord': 'ERROR',
                'Final_Toss_Prediction': 'ERROR',
                'Match_Energy_Label': 'ERROR', 'Predicted_Score_Range': 'ERROR',
                'A_Winning_Colour': 'None', 'B_Winning_Colour': 'None', 'Color_Match_Strength': 'Neutral',
            })


    # --- 6. Merge results and Write back to the SAME Excel file ---
    
    if all_results:
        df_output = pd.DataFrame(all_results)
        
        # Ensure indices align for horizontal merge
        df_input.reset_index(drop=True, inplace=True)
        df_output.reset_index(drop=True, inplace=True)
        
        # We drop columns that are already present in the input file but might have been included 
        cols_to_drop = ['Team_A_Name', 'Team_B_Name', 'Captain_A_Name', 'Captain_B_Name']
        
        # Merge the input and the new analysis results side-by-side
        df_final = pd.concat([df_input, df_output.drop(columns=cols_to_drop, errors='ignore')], axis=1)

        # Write the combined DataFrame back to the same file
        try:
            df_final.to_excel(IO_FILE, index=False)
            print(f"\n✅ Analysis complete! Results appended and saved to **{IO_FILE}**")
            print("Please check your Excel file. Remember to CLOSE the Excel file before running the script.")
        except Exception as write_error:
            print(f"\nFATAL ERROR WRITING FILE: {write_error}")
            print("Please ensure the Excel file 'match_analysis_data.xlsx' is CLOSED before running the script.")
    else:
        print("\n❌ No results to write. The input file may have been empty.")

if __name__ == "__main__":
    main()