#!/usr/bin/env python3
"""
MASTER COMPLETE OFFLINE ASTRO–NUMEROLOGY & MATCH TREND SCRIPT
Reads match data from 'match_analysis_data.xlsx', calculates results,
and writes output back to the same file, appending new columns for analysis.

This version includes:
1. Core Numerology/Astrology Helpers.
2. The complete logic for all six Toss Prediction Methods.
3. Final Toss Consolidation Logic.
4. Innings Trend Analysis (Start, Middle, End).
"""
import sys
import random
import pandas as pd
from datetime import datetime, date, time, timedelta

# Attempt to import Swiss Ephemeris library
try:
    import swisseph as swe
    # Set the path to the ephemeris files (essential for swe functions)
    # NOTE: You may need to adjust this path on your local machine
    # swe.set_ephe_path("/path/to/ephe_files") 
except ImportError:
    print("ERROR: 'pyswisseph' module not found. Please install it using: pip install pyswisseph")
    # Set a flag to use mock data if swisseph fails
    swe = None

# ---------------------------
# Constants & Helpers
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

NAKSHATRA_LORDS = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
]

SIGN_LORDS = {
    "Aries": 'Mars', "Taurus": 'Venus', "Gemini": 'Mercury', 
    "Cancer": 'Moon', "Leo": 'Sun', "Virgo": 'Mercury', 
    "Libra": 'Venus', "Scorpio": 'Mars', "Sagittarius": 'Jupiter', 
    "Capricorn": 'Saturn', "Aquarius": 'Saturn', "Pisces": 'Jupiter'
}

PLANET_NUMBERS = {
    'Sun': 1, 'Moon': 2, 'Jupiter': 3, 'Rahu': 4, 'Mercury': 5, 
    'Venus': 6, 'Ketu': 7, 'Saturn': 8, 'Mars': 9, 'Neptune': 7, 'Uranus': 4, 'Pluto': 9
}

DAY_LORDS = {
    0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun',
}

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN
}

PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])


def reduce_num(n: int) -> int:
    """Reduce to a single digit by iterative digit-sum (1-9)."""
    n = int(n)
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    """Birth number = reduced day of month. Expects DD/MM/YYYY string."""
    try:
        dt = datetime.strptime(dob_str, "%d/%m/%Y")
        return reduce_num(dt.day)
    except:
        # Fallback for unexpected formats, sums all digits
        return reduce_num(sum(int(c) for c in dob_str if c.isdigit()))

def life_path_number(dob_str: str) -> int:
    """Life path number = reduced sum of all digits in DOB. Expects DD/MM/YYYY string."""
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
    """Life path number of the date itself. Expects DD/MM/YYYY string."""
    digits = "".join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

def day_power(match_date: date) -> int:
    """Calculates a power score for the day (1-10)"""
    dno = reduce_num(match_date.day)
    mno = reduce_num(match_date.month)
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday = match_date.weekday()
    weekday_bonus = {0:2,1:1,2:3,3:4,4:5,5:1,6:6}.get(weekday, 1)
    return min(reduce_num(dno + mno + lp + weekday_bonus), 10)

def place_power(place_name: str) -> int:
    """Calculates a power score for the place (1-10)"""
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
    return min(reduce_num(s), 10)

def calculate_five_day_power(start_date: date, place_name: str) -> tuple:
    """Calculates the averaged Day Power (dp) and the single Place Power (pp) for a 5-day Test Match."""
    place_p = place_power(place_name)
    total_day_power = 0
    for i in range(5):
        total_day_power += day_power(start_date + timedelta(days=i))
    return round(total_day_power / 5), place_p

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    """Convert local datetime and tz offset to Julian Day (UT)."""
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
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
# 6 TOSS PREDICTION METHODS (Full Logic Implemented)
# ---------------------------

def toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp):
    """Method 1: Numerological Match between Captain's LP and Match Date LP."""
    a_good = (a_lp, date_lp) in good_pairs
    b_good = (b_lp, date_lp) in good_pairs

    if a_good and not b_good:
        return f"Captain A ({a_name}) - Good Numerology Pair"
    if b_good and not a_good:
        return f"Captain B ({b_name}) - Good Numerology Pair"
    return "Neutral - Balanced Numerology"

def toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno):
    """Method 2: Horary Ruler (Day Lord) compatibility with Captain's Birth Numbers."""
    day_lord_num = PLANET_NUMBERS.get(day_lord_planet, 0)
    
    a_match = (a_bno, day_lord_num) in good_pairs
    b_match = (b_bno, day_lord_num) in good_pairs
    
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Day Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Day Lord Match"
    return "Neutral - Day Lord Tie"

def toss_method_3_star_lord(a_name, b_name, nak_lord_planet, a_nn, b_nn):
    """Method 3: Nakshatra (Star) Lord compatibility with Captain's Name Numbers."""
    nak_lord_num = PLANET_NUMBERS.get(nak_lord_planet, 0)
    
    a_match = (a_nn, nak_lord_num) in good_pairs
    b_match = (b_nn, nak_lord_num) in good_pairs
    
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Star Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Star Lord Match"
    return "Neutral - Star Lord Tie"

def toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno):
    """Method 4: Ruling Number (Day/Place Power) proximity to Captain's Birth Numbers."""
    ruling_no = reduce_num(dp + pp) # Simple ruling number
    
    a_diff = abs(a_bno - ruling_no)
    b_diff = abs(b_bno - ruling_no)

    if a_diff < b_diff:
        return f"Captain A ({a_name}) - Closer to Ruling No. ({ruling_no})"
    if b_diff < a_diff:
        return f"Captain B ({b_name}) - Closer to Ruling No. ({ruling_no})"
    return "Neutral - Ruling No. Proximity Tie"

def toss_method_5_compound_score(a_name, b_name, a_score, b_score):
    """Method 5: Compound Score, based on the overall match prediction scores."""
    if a_score > b_score:
        return f"Captain A ({a_name}) - Match Score Advantage ({a_score} > {b_score})"
    if b_score > a_score:
        return f"Captain B ({b_name}) - Match Score Advantage ({b_score} > {a_score})"
    return "Neutral - Compound Score Tie"

def toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno):
    """Method 6: Moon Sign Lord compatibility with Captain's Birth Numbers."""
    moon_lord_num = PLANET_NUMBERS.get(moon_sign_lord_planet, 0)
    
    a_match = (a_bno, moon_lord_num) in good_pairs
    b_match = (b_bno, moon_lord_num) in good_pairs
    
    if a_match and not b_match:
        return f"Captain A ({a_name}) - Moon Lord Match"
    if b_match and not a_match:
        return f"Captain B ({b_name}) - Moon Lord Match"
    return "Neutral - Moon Lord Tie"


def final_toss_prediction(toss_results):
    """
    Analyzes results from all 6 toss methods to determine a final prediction.
    """
    a_wins = 0
    b_wins = 0
    a_name = ""
    b_name = ""
    
    # We only count wins for decisive methods, ignoring "Neutral" or "Tie"
    for result in toss_results.values():
        if result.startswith("Captain A"):
            a_wins += 1
            # Extract captain name from the first match
            if not a_name and '(' in result: a_name = result.split('(')[1].split(' -')[0].strip()
        elif result.startswith("Captain B"):
            b_wins += 1
            if not b_name and '(' in result: b_name = result.split('(')[1].split(' -')[0].strip()

    total_predictions = a_wins + b_wins
    
    # Determine the majority winner
    if a_wins >= 4:
        return f"Captain A ({a_name}) - Strong Majority ({a_wins}-{b_wins} Score)"
    if b_wins >= 4:
        return f"Captain B ({b_name}) - Strong Majority ({b_wins}-{a_wins} Score)"
    
    if a_wins > b_wins and total_predictions >= 5:
         return f"Captain A ({a_name}) - Simple Majority ({a_wins}-{b_wins} Score)"
    if b_wins > a_wins and total_predictions >= 5:
         return f"Captain B ({b_name}) - Simple Majority ({b_wins}-{a_wins} Score)"

    return f"Neutral - Tie/Mixed Results ({a_wins}-{b_wins} Score)"

# ---------------------------
# Innings Trend Logic (Inclused in full)
# ---------------------------

def predict_innings_trend(match_score: int, lp: int, nn: int, dp: int, pp: int, is_winner: bool) -> str:
    """
    Generates a narrative for the innings trend based on Captain's numbers and environment scores.
    """
    # Sum of DP and PP (Max 20)
    start_score = dp + pp
    
    # 1. Start of Innings (DP + PP)
    if start_score >= 14:
        start = "Strong, aggressive start"
    elif start_score >= 8:
        start = "Steady, watchful start"
    else:
        start = "Slow, cautious start"
        
    # 2. Middle Overs (Name Number + Match Score)
    # Using nn and a simple check on score influence for T20/ODI formats
    score_influence = 1 if match_score > 35 else 0 # Simple way to judge a dominant score environment
    if nn + score_influence >= 8:
        middle = "consistent, dominant middle overs"
    elif nn >= 4:
        middle = "balanced flow with periodic power hitting"
    else:
        middle = "slowdown with potential wicket clusters"

    # 3. Finish/End Result (Life Path + Win Probability)
    if is_winner:
        end = "culminating in a decisive, good finish"
    else:
        # If not the overall match winner, their finish is weaker.
        if lp >= 6:
            end = "struggles in the final few overs but reaches a competitive total"
        else:
            # Using a threshold of score_bno being low to indicate failure to reach target
            end = "fail to reach the target" if match_score < 40 else "fizzle out towards a below-par total"

    # Assemble the final narrative
    return f"{start} → {middle} → {end}"


# ---------------------------
# Main function (Now calculating all required fields)
# ---------------------------

def main():
    print("=== MASTER COMPLETE ASTRO–NUMEROLOGY ANALYSIS (IN-PLACE EXCEL I/O) ===\n")
    IO_FILE = "match_analysis_data.xlsx"
    
    # ------------------ Initialization & Input ------------------
    try:
        # Pandas reads all date columns as datetime objects internally
        df_input = pd.read_excel(IO_FILE)
        print(f"Successfully loaded {len(df_input)} matches from {IO_FILE}")
    except FileNotFoundError:
        print(f"FATAL ERROR: Input file '{IO_FILE}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR reading Excel file: {e}")
        sys.exit(1)

    all_results = []
    
    # ------------------ Main Processing Loop ------------------
    for index, row in df_input.iterrows():
        try:
            # --- 1. Parse Input & Date/Time Setup ---
            
            # Use the consistent, full name for the variable: tz_offset_hours
            tz_offset_hours = float(row.get('TZ_Offset_Hours', 0.0))
            
            # Match Date Handling
            match_dt_obj = pd.to_datetime(row.get('Match_Date', '01/01/2025'))
            match_date = match_dt_obj.date() # Date object for weekday/day_power calculation
            # Use this clean string for numerology calculations ONLY
            match_date_str = match_dt_obj.strftime("%d/%m/%Y") 
            
            # Captain DOB Handling (cleans up any time component from input)
            a_dob_dt = pd.to_datetime(row.get('Captain_A_DOB', '01/01/1980'))
            a_dob = a_dob_dt.strftime("%d/%m/%Y") 

            b_dob_dt = pd.to_datetime(row.get('Captain_B_DOB', '01/01/1980'))
            b_dob = b_dob_dt.strftime("%d/%m/%Y") 

            # Match Time Handling (uses specific time string, with robust parsing)
            match_time_str = str(row.get('Match_Time', '06:00'))
            match_place = row.get('Match_Place', 'Unknown')
            
            team_a = row.get('Team_A_Name', f'TeamA_{index}')
            team_b = row.get('Team_B_Name', f'TeamB_{index}')
            a_name = row.get('Captain_A_Name', team_a)
            b_name = row.get('Captain_B_Name', team_b)
            
            # Robust time parsing (FIXED from previous run error)
            try:
                hm = datetime.strptime(match_time_str, "%H:%M:%S").time()
            except ValueError:
                hm = datetime.strptime(match_time_str, "%H:%M").time()

            local_dt = datetime.combine(match_date, hm)
            
            date_lp = date_life_path(match_date_str)
            # Use the now-consistent variable name
            jd_utc = to_utc_jd_from_datetime(local_dt, tz_offset_hours)
            
            day_lord_planet = DAY_LORDS.get(match_date.weekday(), 'Sun')
            
            # Astro Calculations (Requires swisseph)
            moon_lon = 0.0 # Default/Mock if no swisseph
            if swe:
                # Use MOON for general astro calculations at the time of the toss
                moon_lon = swe.calc_ut(jd_utc, swe.MOON)[0][0]
            
            moon_info = moon_nakshatra_pada(moon_lon)
            nak_lord_planet = moon_info.get('lord', 'Ketu')
            moon_sign = sign_from_long(moon_lon)[0]
            moon_sign_lord_planet = SIGN_LORDS.get(moon_sign, 'Mars')
            
            # --- 2. Numerology & Power Scores ---
            
            # Power Scores
            match_format_raw = str(row.get('Match_Format', 'T20')).upper()
            if match_format_raw == 'TEST':
                dp, pp = calculate_five_day_power(match_date, match_place)
            else:
                dp = day_power(match_date)
                pp = place_power(match_place)

            # Numerology using clean date strings
            a_bno = birth_number(a_dob); a_lp = life_path_number(a_dob); a_nn = name_number(a_name)
            b_bno = birth_number(b_dob); b_lp = life_path_number(b_dob); b_nn = name_number(b_name)
            
            # Overall Match Scores
            score_a = sum([a_lp, a_nn, dp, pp])
            score_b = sum([b_lp, b_nn, dp, pp])
            
            # --- 3. Overall Advantage & Score Range ---
            if score_a > score_b + 5:
                advantage = f"Captain A ({a_name}) - Strong Advantage"
                score_range = "180 - 200+"
            elif score_a > score_b:
                advantage = f"Captain A ({a_name})"
                score_range = "165 - 185"
            elif score_b > score_a + 5:
                advantage = f"Captain B ({b_name}) - Strong Advantage"
                score_range = "180 - 200+"
            elif score_b > score_a:
                advantage = f"Captain B ({b_name})"
                score_range = "165 - 185"
            else:
                advantage = "Neutral / Balanced"
                score_range = "155 - 175"

            # --- 4. Toss Predictions (6 Methods) ---
            toss_results = {}
            toss_results['Toss_Method_1_Numerology'] = toss_method_1_numerology(a_name, b_name, a_lp, b_lp, date_lp)
            toss_results['Toss_Method_2_Horary_Ruler'] = toss_method_2_horary_ruler(a_name, b_name, day_lord_planet, a_bno, b_bno)
            toss_results['Toss_Method_3_Star_Lord'] = toss_method_3_star_lord(a_name, b_name, nak_lord_planet, a_nn, b_nn)
            toss_results['Toss_Method_4_Ruling_No'] = toss_method_4_ruling_no(a_name, b_name, dp, pp, a_bno, b_bno)
            toss_results['Toss_Method_5_Compound_Score'] = toss_method_5_compound_score(a_name, b_name, score_a, score_b)
            toss_results['Toss_Method_6_Moon_Sign_Lord'] = toss_method_6_moon_sign_lord(a_name, b_name, moon_sign_lord_planet, a_bno, b_bno)
            
            final_toss = final_toss_prediction(toss_results)
            
            # --- 5. Innings Trend Calculation ---
            is_a_winner = score_a > score_b
            is_b_winner = score_b > score_a
            
            trend_a = predict_innings_trend(score_a, a_lp, a_nn, dp, pp, is_a_winner)
            trend_b = predict_innings_trend(score_b, b_lp, b_nn, dp, pp, is_b_winner)
            
            # --- 6. Collect Final Results for THIS ROW ---

            result = {
                'Overall_Advantage': advantage,
                'Predicted_Score_Range': score_range,
                **toss_results, # Unpack the 6 toss methods
                'Final_Toss_Prediction': final_toss,
                'Innings_Trend_A': trend_a,
                'Innings_Trend_B': trend_b,
                'A_Match_Score': score_a,
                'B_Match_Score': score_b,
            }
            all_results.append(result)

        except Exception as e:
            print(f"Error processing match at index {index}: {e}")
            continue

    # ------------------ Output & File Write ------------------
    if all_results:
        df_output = pd.DataFrame(all_results)
        df_input.reset_index(drop=True, inplace=True)
        df_output.reset_index(drop=True, inplace=True)
        
        # Merge input and output data 
        cols_to_drop = [col for col in df_output.columns if col in df_input.columns and col not in ['A_Match_Score', 'B_Match_Score']]
        df_final = pd.concat([df_input, df_output.drop(columns=cols_to_drop, errors='ignore')], axis=1)

        # === CRITICAL FIX: Explicitly convert all date columns back to DD/MM/YYYY string before writing ===
        date_cols_to_reformat = ['Captain_A_DOB', 'Captain_B_DOB', 'Match_Date']
        for col in date_cols_to_reformat:
            if col in df_final.columns:
                # Ensure the column is treated as datetime before converting to string
                try:
                    df_final[col] = pd.to_datetime(df_final[col]).dt.strftime('%d/%m/%Y')
                except Exception as format_e:
                    # Print a warning but continue processing
                    print(f"Warning: Could not reformat column {col} to string: {format_e}")
        # =================================================================================================

        try:
            # Overwrite the file with the new complete data
            df_final.to_excel(IO_FILE, index=False)
            print(f"\n✅ Analysis complete! All columns (including 6 toss methods and trends) saved to **{IO_FILE}**")
        except Exception as write_error:
            print(f"\nFATAL ERROR WRITING FILE: {write_error}")
            print("Please ensure the Excel file 'match_analysis_data.xlsx' is CLOSED before running the script.")
    else:
        print("\n❌ No results to write. Please check input file content.")
    
    # Check for Swiss Ephemeris import issue again
    if not swe:
         print("\nNOTE: Swiss Ephemeris (`pyswisseph`) was not found. Astrological calculations (e.g., Moon Sign, Nakshatra) are using mock/default values. Install the module for full functionality.")


if __name__ == "__main__":
    main()