#!/usr/bin/env python3
"""
Master Offline Astro–Numerology & Match Trend Script
Multiple Ayanamsas | Planetary Energy | Moon Nakshatra | Numerology | Colour | Day & Place Power
Requirements: pip install pyswisseph python-dateutil
Author: ChatGPT (GPT-5 Thinking mini) — corrected version
"""
import sys
import json
import random
from datetime import datetime, date, time, timedelta

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

PYTH_MAP = {c: ((ord(c) - 65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}

def name_number(name: str) -> int:
    s = 0
    for ch in name.upper():
        if ch.isalpha():
            s += PYTH_MAP.get(ch, 0)
    return reduce_num(s)

def date_life_path(date_str: str) -> int:
    digits = "".join(ch for ch in date_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

# ---------------------------
# Lucky colours
# ---------------------------

lucky_colors = {
    1: ["Red", "Orange", "Gold"], 2: ["White", "Light Blue", "Silver"],
    3: ["Yellow", "Purple", "Pink"], 4: ["Grey", "Dark Blue"],
    5: ["Green", "Light Brown"], 6: ["Cream", "Pink", "Light Blue"],
    7: ["Sea Green", "White"], 8: ["Dark Blue", "Black"], 9: ["Red", "Maroon"]
}

def color_fine_tune(captain_colors, date_colors):
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

# ---------------------------
# Swiss Ephemeris helpers
# ---------------------------

def to_utc_jd_from_datetime(dt_local: datetime, tz_offset_hours: float = 0.0):
    """
    Convert a naive local datetime and tz offset (hours east of UTC, e.g. +5.5 -> 5.5)
    to a Swiss Ephemeris Julian Day (UT).
    """
    dt_utc = dt_local - timedelta(hours=tz_offset_hours)
    # julday expects fractional hours (UT)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute/60.0 + dt_utc.second/3600.0)

def planet_longitude(jd_ut, planet):
    """
    Return sidereal longitude (degrees) for a planet at given Julian Day UT.
    Handles different return styles of pyswisseph by being defensive.
    """
    res = swe.calc_ut(jd_ut, planet)
    # res often is (pos_array, flags) where pos_array[0] is ecliptic longitude
    if isinstance(res, tuple) and len(res) >= 1 and isinstance(res[0], (list, tuple)):
        pos = res[0]
    else:
        pos = res  # fallback if API is different
    lon = float(pos[0])
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)  # Lahiri sidereal default (degrees)
    sidereal_lon = (lon - ayanamsa) % 360.0
    return sidereal_lon

def sign_from_long(lon_deg):
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    within = (moon_lon - idx * nak_size) % nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada}

# ---------------------------
# Day & Place power
# ---------------------------

def day_power(match_date: date) -> int:
    lp = reduce_num(match_date.day + match_date.month + match_date.year)
    weekday = match_date.weekday()  # 0=Mon..6=Sun
    weekday_bonus = {0:1,1:2,2:1,3:2,4:3,5:1,6:3}.get(weekday, 1)
    return min(lp + weekday_bonus, 10)

def place_power(place_name: str) -> int:
    s = sum(PYTH_MAP.get(ch.upper(), 0) for ch in place_name if ch.isalpha())
    return min(s, 10)

# ---------------------------
# Numerology compatibility
# ---------------------------

good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

def numerology_compat(bno, lp, dno, dlp):
    if (bno, dno) in good_pairs or (lp, dlp) in good_pairs:
        return "GOOD DAY"
    return "BAD DAY"

# ---------------------------
# Main function
# ---------------------------

def main():
    print("=== MASTER OFFLINE ASTRO–NUMEROLOGY ===\n")
    try:
        a_name = input("Enter Team A captain name: ").strip() or "TeamA_Captain"
        a_dob = input("Enter Team A captain DOB (DD/MM/YYYY): ").strip()
        b_name = input("Enter Team B captain name: ").strip() or "TeamB_Captain"
        b_dob = input("Enter Team B captain DOB (DD/MM/YYYY): ").strip()
        match_date_str = input("Enter match date (DD/MM/YYYY): ").strip()
        match_time_str = input("Enter match time (HH:MM, optional, default 06:00): ").strip()
        tz_off_str = input("Enter local timezone offset from UTC (hours, e.g., +5.5 or -4) [default 0]: ").strip()
        match_place = input("Enter match location/city name: ").strip() or "Unknown"

        # Validate and parse
        try:
            match_date = datetime.strptime(match_date_str, "%d/%m/%Y").date()
        except Exception:
            print("Invalid match date format. Use DD/MM/YYYY.")
            return

        if match_time_str:
            try:
                hm = datetime.strptime(match_time_str, "%H:%M").time()
            except Exception:
                print("Invalid time format. Use HH:MM (24-hour).")
                return
        else:
            hm = time(6, 0)

        try:
            tz_off_hours = float(tz_off_str) if tz_off_str else 0.0
        except Exception:
            print("Invalid timezone offset. Enter numeric hours (e.g. +5.5 or -4).")
            return

        local_dt = datetime.combine(match_date, hm)
        # convert local datetime -> JD UT
        jd_ut = to_utc_jd_from_datetime(local_dt, tz_offset_hours=tz_off_hours)

        # Planetary snapshot
        planets = {}
        for name, pid in PLANETS.items():
            try:
                lon = planet_longitude(jd_ut, pid)
            except Exception as e:
                lon = None
            if lon is not None:
                sign, deg = sign_from_long(lon)
                planets[name] = {"degree_total": round(lon, 6), "sign": sign, "deg_in_sign": round(deg, 2)}
            else:
                planets[name] = {"degree_total": None, "sign": None, "deg_in_sign": None}

        if planets.get("Moon", {}).get("degree_total") is not None:
            moon_info = moon_nakshatra_pada(planets["Moon"]["degree_total"])
            planets["Moon"]["nakshatra"] = moon_info["nakshatra"]
            planets["Moon"]["pada"] = moon_info["pada"]

        # Numerology
        try:
            a_bno = birth_number(a_dob)
            a_lp = life_path_number(a_dob)
        except Exception:
            print("Invalid Team A DOB format. Use DD/MM/YYYY.")
            return

        try:
            b_bno = birth_number(b_dob)
            b_lp = life_path_number(b_dob)
        except Exception:
            print("Invalid Team B DOB format. Use DD/MM/YYYY.")
            return

        a_name_num = name_number(a_name)
        b_name_num = name_number(b_name)

        m_dno = reduce_num(match_date.day)
        m_dlp = date_life_path(match_date_str)
        numerology_a = numerology_compat(a_bno, a_lp, m_dno, m_dlp)
        numerology_b = numerology_compat(b_bno, b_lp, m_dno, m_dlp)

        # Colours
        a_colors = lucky_colors.get(a_bno, [])
        b_colors = lucky_colors.get(b_bno, [])
        date_colors = lucky_colors.get(m_dno, [])
        a_color_res = color_fine_tune(a_colors, date_colors)
        b_color_res = color_fine_tune(b_colors, date_colors)

        # Day & Place power
        dp = day_power(match_date)
        pp = place_power(match_place)

        # Toss prediction
        toss_winner = random.choice([a_name, b_name])

        # Match trend score (simple sum). dp and pp are already 1..10, so use directly.
        score_a = sum([a_lp, a_name_num, dp, pp])
        score_b = sum([b_lp, b_name_num, dp, pp])

        # Output summary
        print("\n=== PLANETARY SNAPSHOT ===")
        print(json.dumps(planets, indent=2, ensure_ascii=False))
        print("\n=== NUMEROLOGY ===")
        print(f"Team A {a_name}: birth {a_bno}, life_path {a_lp}, name {a_name_num}, numerology: {numerology_a}")
        print(f"Team B {b_name}: birth {b_bno}, life_path {b_lp}, name {b_name_num}, numerology: {numerology_b}")
        print("\n=== COLOURS ===")
        print(f"Team A colours: {a_colors} | fine-tune: {a_color_res}")
        print(f"Team B colours: {b_colors} | fine-tune: {b_color_res}")
        print("\n=== DAY & PLACE POWER ===")
        print(f"Day Power: {dp}/10 | Place Power: {pp}/10")
        print("\n=== TOSS PREDICTION ===")
        print(f"Toss Likely Winner: {toss_winner}")
        print("\n=== MATCH TREND SCORE ===")
        print(f"Team A {a_name}: {score_a}")
        print(f"Team B {b_name}: {score_b}")
        if score_a > score_b:
            print(f"Overall Advantage: Team A ({a_name})")
        elif score_b > score_a:
            print(f"Overall Advantage: Team B ({b_name})")
        else:
            print("Overall Advantage: Neutral / Balanced")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
    except Exception as exc:
        print("An unexpected error occurred:", repr(exc))

# ---------------------------
# Run script
# ---------------------------

if __name__ == "__main__":
    main()