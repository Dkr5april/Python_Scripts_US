#!/usr/bin/env python3
"""
Master Offline Astro–Numerology & Match Trend Script
Reads data from 'match_analysis_data.xlsx', calculates results,
and writes output back to the same file, appending new columns.

Requirements: pip install pyswisseph python-dateutil pandas openpyxl
"""
import sys
import random
import pandas as pd
from datetime import datetime, date, time, timedelta

# Attempt to import Swiss Ephemeris library
try:
    import swisseph as swe
except ImportError:
    print("ERROR: 'swisseph' module not found. Install: pip install pyswisseph")
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
    dt = datetime.strptime(dob_str, "%d/%m/%Y")
    return reduce_num(dt.day)

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
        return {"match":"No colour match", "strength":"Neutral","winning_colour":None}
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
    weekday_bonus = {0:1,1:2,2:1,3:2,4:3,5:1,6:3}.get(weekday, 1)
    return min(lp + weekday_bonus, 10)

def place_power(place_name: str) -> int:
    """Calculates a power score for the place (1-10)"""
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
    return min(reduce_num(s), 10)

# ---------------------------
# Swiss Ephemeris helpers
# ---------------------------

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    """
    Convert local datetime and tz offset (hours east of UTC) to Julian Day (UT).
    """
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    # julday expects fractional hours (UT)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def sign_from_long(lon_deg):
    """Converts a 360-degree longitude to Zodiac Sign and degree within sign."""
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
    """Determines Nakshatra and Pada from Moon's longitude."""
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada}

# ---------------------------
# Main function - MODIFIED FOR IN-PLACE EXCEL I/O
# ---------------------------

def main():
    print("=== MASTER OFFLINE ASTRO–NUMEROLOGY (IN-PLACE EXCEL I/O) ===\n")
    
    # Define the single file name for both input and output
    IO_FILE = "match_analysis_data.xlsx"
    
    try:
        # Read the input Excel file
        df_input = pd.read_excel(IO_FILE)
        print(f"Successfully loaded {len(df_input)} matches from {IO_FILE}")
    except FileNotFoundError:
        print(f"ERROR: Input file '{IO_FILE}' not found. Ensure it is in the same directory.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR reading Excel file: {e}")
        sys.exit(1)

    all_results = []

    # Loop through each row (match) in the input file
    for index, row in df_input.iterrows():
        try:
            # --- 1. Parse and Validate Input from Row ---
            a_name = row['Team_A_Name']
            a_dob = str(row['Team_A_DOB'])
            b_name = row['Team_B_Name']
            b_dob = str(row['Team_B_DOB'])
            
            # Date Parsing: Handles both datetime objects (from pandas) or strings
            match_date_raw = str(row['Match_Date']).split()[0]
            try:
                # Try parsing standard Excel datetime format (YYYY-MM-DD)
                match_date = datetime.strptime(match_date_raw, "%Y-%m-%d").date()
                match_date_str_fmt = match_date.strftime("%d/%m/%Y")
            except ValueError:
                # Fallback to direct DD/MM/YYYY string format
                match_date = datetime.strptime(match_date_raw, "%d/%m/%Y").date()
                match_date_str_fmt = match_date_raw
                
            match_time_str = str(row.get('Match_Time', '06:00'))
            tz_off_hours = float(row.get('TZ_Offset_Hours', 0.0))
            match_place = row.get('Match_Place', 'Unknown')
            
            # Time setup
            try:
                hm = datetime.strptime(match_time_str, "%H:%M").time()
            except ValueError:
                 hm = time(6, 0)
            
            local_dt = datetime.combine(match_date, hm)
            jd_ut = to_utc_jd_from_datetime(local_dt, tz_offset_hours=tz_off_hours)

            # --- 2. Run Calculations ---
            
            # Planetary snapshot
            planets = {}
            ayanamsa = swe.get_ayanamsa_ut(jd_ut)
            for name, pid in PLANETS.items():
                res = swe.calc_ut(jd_ut, pid)
                lon = float(res[0][0])
                sidereal_lon = (lon - ayanamsa) % 360.0
                sign, deg = sign_from_long(sidereal_lon)
                planets[name] = {"degree_total": round(sidereal_lon, 6), "sign": sign, "deg_in_sign": round(deg, 2)}
            
            moon_lon = planets["Moon"]["degree_total"]
            moon_info = moon_nakshatra_pada(moon_lon)
            
            # Numerology
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
            
            # Colours
            date_colors = lucky_colors.get(m_dno, [])
            a_color_res = color_fine_tune(lucky_colors.get(a_bno, []), date_colors)
            b_color_res = color_fine_tune(lucky_colors.get(b_bno, []), date_colors)
            
            # Day & Place power
            dp = day_power(match_date)
            pp = place_power(match_place)
            
            # Toss prediction (Random for demonstration)
            toss_winner = random.choice([a_name, b_name])

            # Match trend score
            score_a = sum([a_lp, a_name_num, dp, pp])
            score_b = sum([b_lp, b_name_num, dp, pp])
            
            if score_a > score_b:
                 advantage = f"Team A ({a_name})"
            elif score_b > score_a:
                 advantage = f"Team B ({b_name})"
            else:
                 advantage = "Neutral / Balanced"

            # --- 3. Collect Results for THIS ROW ---

            result = {
                # Astro
                'Moon_Nakshatra': moon_info["nakshatra"],
                'Moon_Pada': moon_info["pada"],
                'Sun_Sign': planets["Sun"]["sign"],
                'Jupiter_Sign': planets["Jupiter"]["sign"],
                
                # Numerology
                'A_Life_Path': a_lp,
                'A_Name_Num': a_name_num,
                'A_Numerology_Compat': numerology_a,
                'B_Life_Path': b_lp,
                'B_Name_Num': b_name_num,
                'B_Numerology_Compat': numerology_b,
                
                # Scores
                'Day_Power': dp,
                'Place_Power': pp,
                'A_Match_Score': score_a,
                'B_Match_Score': score_b,
                'Overall_Advantage': advantage,
                'Toss_Prediction': toss_winner,
                
                # Colors
                'A_Winning_Colour': a_color_res['winning_colour'],
                'B_Winning_Colour': b_color_res['winning_colour'],
                'Color_Match_Strength': a_color_res['strength'] if score_a > score_b else b_color_res['strength'],
            }
            all_results.append(result)

        except Exception as e:
            # Handle errors for specific rows
            print(f"Error processing row {index} (Match Date: {match_date_raw}): {e}")
            all_results.append({'Overall_Advantage': f"ROW ERROR: {e}"})


    # --- 4. Merge results and Write back to the SAME Excel file ---
    
    if all_results:
        # Create a DataFrame from the calculated results
        df_output = pd.DataFrame(all_results)
        
        # Reset index to ensure clean concatenation
        df_input.reset_index(drop=True, inplace=True)
        df_output.reset_index(drop=True, inplace=True)
        
        # Concatenate the original input columns and the new output columns horizontally
        df_final = pd.concat([df_input, df_output], axis=1)
        
        # Write the combined DataFrame back to the same file
        df_final.to_excel(IO_FILE, index=False)
        print(f"\n✅ Analysis complete! Results appended and saved to **{IO_FILE}**")
        print("You can now open the Excel file to view the new columns.")
    else:
        print("\n❌ No results to write. The input file may have been empty.")

if __name__ == "__main__":
    main()