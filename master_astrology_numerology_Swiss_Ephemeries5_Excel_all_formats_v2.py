#!/usr/bin/env python3
"""
Master Offline Astro–Numerology & Match Trend Script
Reads match data from 'match_analysis_data.xlsx', calculates results,
and writes output back to the same file, appending new columns for analysis.

Includes three distinct toss prediction methods based on Numerology and Astrology,
and a new heuristic score prediction model for T10, T20, 100-Ball, ODI, and TEST formats.

SETUP REQUIREMENTS: 
You MUST install the necessary Python libraries before running:
pip install pyswisseph python-dateutil pandas openpyxl

USAGE:
1. Ensure the input file 'match_analysis_data.xlsx' is in the same folder.
2. Ensure the Excel file is CLOSED before running the script.
3. Add a column named 'Match_Format' with values like T10, T20, 100-BALL, ODI, or TEST.
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
    if "Red" in common or "Maroon" in common:
        return {"match":"Colour aligned","strength":"Very Strong","winning_colour":"Red"}
    if any("Blue" in c for c in common):
        colours = [c for c in common if "Blue" in c]
        return {"match":"Colour aligned","strength":"Strong","winning_colour":", ".join(colours)}
    return {"match":"Colour aligned","strength":"Medium","winning_colour":", ".join(list(common))}

def day_power(match_date: date) -> int:
    """Calculates a power score for the day (1-10)"""
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday = match_date.weekday()  # 0=Mon..6=Sun
    # Arbitrary weekday bonuses
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1) # Stronger weight on Fri/Sun/Thu
    return min(lp + weekday_bonus, 10)

def place_power(place_name: str) -> int:
    """Calculates a power score for the place (1-10)"""
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
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
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

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
# Toss Prediction Logic
# ---------------------------

def predict_toss_numerology(a_name, b_name, numerology_a, numerology_b):
    """
    Toss Method 1: Numerology compatibility between Captain's numbers and the Match Date (Day 1).
    """
    if numerology_a == "GOOD DAY" and numerology_b == "BAD DAY":
        return f"Team A ({a_name} - Good Day)"
    if numerology_b == "GOOD DAY" and numerology_a == "BAD DAY":
        return f"Team B ({b_name} - Good Day)"
    
    # If both good or both bad, it's a toss-up
    return "Neutral (Numerology Tie)"

def predict_toss_horary(a_name, b_name, a_bno, b_bno, match_date):
    """
    Toss Method 2: Day Ruler's Number Advantage (Day 1).
    The team whose Birth Number matches the Day Ruler's Number wins.
    """
    weekday = match_date.weekday()
    lord_name = DAY_LORDS[weekday]
    lord_number = PLANET_NUMBERS.get(lord_name, 5) 
    
    a_match = a_bno == lord_number
    b_match = b_bno == lord_number

    if a_match and not b_match:
        return f"Team A ({a_name} - Day Ruler {lord_number})"
    if b_match and not a_match:
        return f"Team B ({b_name} - Day Ruler {lord_number})"
    
    # Check for proximity (plus/minus 1)
    if not a_match and not b_match:
        if abs(a_bno - lord_number) == 1 and abs(b_bno - lord_number) != 1:
            return f"Team A ({a_name} - Ruler Proximity)"
        if abs(b_bno - lord_number) == 1 and abs(a_bno - lord_number) != 1:
            return f"Team B ({b_name} - Ruler Proximity)"

    return "Neutral (Horary Tie)"

def predict_toss_star_lord(a_name, b_name, a_bno, b_bno, moon_info):
    """
    Toss Method 3: Nakshatra Lord (Star Lord) Numerology (Day 1).
    The team whose Birth Number matches the Star Lord's Number wins.
    """
    star_lord = moon_info["lord"]
    lord_number = PLANET_NUMBERS.get(star_lord)

    if lord_number is None:
        return "Neutral (Lord Unknown)"

    a_match = a_bno == lord_number
    b_match = b_bno == lord_number

    if a_match and not b_match:
        return f"Team A ({a_name} - Star Lord Match)"
    if b_match and not a_match:
        return f"Team B ({b_name} - Star Lord Match)"

    # Fallback to proximity
    if abs(a_bno - lord_number) == 1 and abs(b_bno - lord_number) != 1:
        return f"Team A ({a_name} - Star Lord Proximity)"
    if abs(b_bno - lord_number) == 1 and abs(a_bno - lord_number) != 1:
        return f"Team B ({b_name} - Star Lord Proximity)"

    return "Neutral (Star Lord Tie)"


# ---------------------------
# Score Prediction Logic
# ---------------------------

def predict_score_range(score_a: int, score_b: int) -> dict:
    """
    Predicts score ranges for T10, T20, 100-Ball, ODI, and TEST based on combined Match Energy Score.
    Max total score is around 76 (38 + 38).
    """
    total_match_energy = score_a + score_b
    
    # Define Tiers based on Total Match Energy (out of ~76)
    if total_match_energy <= 40: # Low/Medium-Low energy day
        label = "Low Scoring Pitch/Day"
        
        t10_range = "70 - 90"
        t20_range = "130 - 160"
        hundred_ball_range = "110 - 135"
        odi_range = "230 - 270"
        test_range = "Slow-paced match. Likely draws or low individual scores."
        
    elif total_match_energy <= 60: # Medium/Medium-High energy day
        label = "Balanced Scoring Pitch/Day"
        
        t10_range = "91 - 110"
        t20_range = "161 - 185"
        hundred_ball_range = "136 - 155"
        odi_range = "271 - 320"
        test_range = "Balanced play. Expect good scores but quick wickets at times."
        
    else: # total_match_energy > 60: # High/Very High energy day
        label = "High Scoring Pitch/Day"
        
        t10_range = "111 - 130+"
        t20_range = "186 - 210+"
        hundred_ball_range = "156 - 175+"
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
        try:
            # --- 1. Parse Input from Row ---
            a_name = row.get('Team_A_Name', f'TeamA_{index}')
            a_dob = str(row.get('Team_A_DOB', '01/01/1980'))
            b_name = row.get('Team_B_Name', f'TeamB_{index}')
            b_dob = str(row.get('Team_B_DOB', '01/01/1980'))
            
            # Match Format - REQUIRED FOR SCORE PREDICTION
            # Convert to uppercase and normalize spaces/hyphens/etc.
            match_format_raw = str(row.get('Match_Format', 'T20')).upper()
            match_format = match_format_raw.replace(" ", "").replace("-", "") 
            
            # Robust Date Parsing
            match_date_raw = str(row.get('Match_Date', '01/01/2025')).split()[0]
            try:
                # Try format from Pandas datetime object (YYYY-MM-DD)
                match_date = datetime.strptime(match_date_raw, "%Y-%m-%d").date()
                match_date_str_fmt = match_date.strftime("%d/%m/%Y")
            except ValueError:
                # Try format from user input (DD/MM/YYYY)
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
            moon_info = moon_nakshatra_pada(moon_lon)
            
            # --- 3. Run Core Calculations (Numerology) ---
            
            a_bno = birth_number(a_dob)
            a_lp = life_path_number(a_dob)
            b_bno = birth_number(b_dob)
            b_lp = life_path_number(b_dob)

            a_name_num = name_number(a_name)
            b_name_num = name_number(b_name)
            
            m_dno = reduce_num(match_date.day)
            m_dlp = date_life_path(match_date_str_fmt)
            
            numerology_a = numerology_compat(a_bno, a_lp, m_dno, m_dlp)
            numerology_b = numerology_compat(b_bno, b_lp, m_dno, m_dlp)
            
            # Power Scores - Adjusted for Test Matches
            if match_format == 'TEST':
                # For TEST matches, calculate Day Power over 5 days (averaged)
                dp, pp = calculate_five_day_power(match_date, match_place)
                match_format_clean = "TEST"
            else:
                # For all other formats, use Day 1 power only
                dp = day_power(match_date)
                pp = place_power(match_place)
                
                # Normalize 100-Ball variations, including the '100DAYS' typo
                if match_format in ['100BALL', '100', '100DAYS']:
                    match_format_clean = '100-BALL'
                elif match_format == 'T10':
                    match_format_clean = 'T10'
                elif match_format == 'T20':
                    match_format_clean = 'T20'
                elif match_format == 'ODI':
                    match_format_clean = 'ODI'
                else:
                    # Fallback for unexpected formats
                    match_format_clean = match_format
            
            # --- 4. Toss and Match Trend Predictions (Toss based on Day 1) ---
            
            toss_num = predict_toss_numerology(a_name, b_name, numerology_a, numerology_b)
            toss_horary = predict_toss_horary(a_name, b_name, a_bno, b_bno, match_date)
            toss_star = predict_toss_star_lord(a_name, b_name, a_bno, b_bno, moon_info)
            
            # Match trend score (Uses 5-day averaged Day Power for TEST matches)
            score_a = sum([a_lp, a_name_num, dp, pp])
            score_b = sum([b_lp, b_name_num, dp, pp])
            
            if score_a > score_b:
                 advantage = f"Team A ({a_name})"
            elif score_b > score_a:
                 advantage = f"Team B ({b_name})"
            else:
                 advantage = "Neutral / Balanced"

            # Score Prediction - retrieves all formats
            score_prediction = predict_score_range(score_a, score_b)
            
            # Select only the relevant predicted range based on input format
            predicted_range = score_prediction.get(match_format_clean, "N/A - Check Format")


            # Colours (remain based on Day 1)
            date_colors = lucky_colors.get(m_dno, [])
            a_color_res = color_fine_tune(lucky_colors.get(a_bno, []), date_colors)
            b_color_res = color_fine_tune(lucky_colors.get(b_bno, []), date_colors)

            # --- 5. Collect Results for THIS ROW ---

            result = {
                # Astro
                'Moon_Nakshatra': moon_info["nakshatra"],
                'Star_Lord': moon_info["lord"], 
                'Sun_Sign': planets["Sun"]["sign"],
                
                # Numerology
                'A_BNO': a_bno, 
                'A_Life_Path': a_lp,
                'B_BNO': b_bno, 
                'B_Life_Path': b_lp,
                'A_Numerology_Compat': numerology_a,
                'B_Numerology_Compat': numerology_b,
                
                # Scores
                # Note: 'Day_Power' now represents the 5-day average for TEST matches
                'Day_Power': dp, 
                'Place_Power': pp,
                'A_Match_Score': score_a,
                'B_Match_Score': score_b,
                'Overall_Advantage': advantage,

                # Toss Predictions
                'Toss_Method_1_Numerology': toss_num,
                'Toss_Method_2_Horary_Ruler': toss_horary,
                'Toss_Method_3_Star_Lord': toss_star,

                # Score Range Prediction (Now specific to the input format)
                'Match_Energy_Label': score_prediction['label'],
                'Predicted_Score_Range': predicted_range,

                # Colors
                'A_Winning_Colour': a_color_res['winning_colour'],
                'B_Winning_Colour': b_color_res['winning_colour'],
                # Report color strength of the winning team based on the Overall_Advantage
                'Color_Match_Strength': a_color_res['strength'] if score_a > score_b else b_color_res['strength'],
            }
            all_results.append(result)

        except Exception as e:
            error_message = f"ROW ERROR: {type(e).__name__}: {str(e)}"
            print(f"Error processing row {index} (Date: {match_date_raw}): {error_message}")
            all_results.append({'Overall_Advantage': error_message})


    # --- 6. Merge results and Write back to the SAME Excel file ---
    
    if all_results:
        df_output = pd.DataFrame(all_results)
        
        # Ensure indices align for horizontal merge
        df_input.reset_index(drop=True, inplace=True)
        df_output.reset_index(drop=True, inplace=True)
        
        # Concatenate the original input columns and the new output columns
        df_final = pd.concat([df_input, df_output], axis=1)
        
        # Write the combined DataFrame back to the same file
        df_final.to_excel(IO_FILE, index=False)
        print(f"\n✅ Analysis complete! Results appended and saved to **{IO_FILE}**")
        print("The file now handles the '100DAYS' typo and calculates Day Power based on the full 5-day period for TEST matches.")
    else:
        print("\n❌ No results to write. The input file may have been empty.")

if __name__ == "__main__":
    main()