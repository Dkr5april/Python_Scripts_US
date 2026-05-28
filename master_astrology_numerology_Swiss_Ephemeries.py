#!/usr/bin/env python3
"""
Master Offline Astro–Numerology Script
KP Ayanamsa | Moon Nakshatra/Pada | Planetary Energy | Numerology | Colour Fine-tuning
Requirements: pip install pyswisseph python-dateutil
Run: py master_offline_astro_kp.py
Author: ChatGPT (GPT-5 mini)
"""

import sys, math, json
from datetime import datetime, date, time, timedelta
from dateutil import tz
from dateutil.parser import parse as parse_date

# ---------------------------
# Swiss Ephemeris import
# ---------------------------
try:
    import swisseph as swe
except Exception as e:
    print("ERROR: 'swisseph' module not found.", e)
    print("Install: py -m pip install pyswisseph")
    sys.exit(1)

# ---------------------------
# Constants
# ---------------------------
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
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
NODE_TRUE = swe.TRUE_NODE  # Rahu (Ketu = opposite)

# ---------------------------
# Numerology helpers
# ---------------------------
def reduce_num(n: int) -> int:
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    dt = datetime.strptime(dob_str, "%d/%m/%Y")
    return reduce_num(dt.day)

def life_path_number(dob_str: str) -> int:
    digits = "".join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

PYTH_MAP = {c: ((ord(c)-65) % 9) + 1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
def name_number(name: str) -> int:
    s = 0
    for ch in name.upper():
        if ch.isalpha():
            s += PYTH_MAP[ch]
    return reduce_num(s)

def day_number(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%d/%m/%Y")
    return reduce_num(dt.day)

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
        return {"match":"No colour match", "strength":"Neutral", "winning_colour":None}
    if "Red" in common or "Maroon" in common:
        return {"match":"Colour aligned","strength":"Very Strong","winning_colour":"Red"}
    if any("Blue" in c for c in common):
        colours = [c for c in common if "Blue" in c]
        return {"match":"Colour aligned","strength":"Strong","winning_colour":", ".join(colours)}
    if "Gold" in common or "White" in common:
        return {"match":"Colour aligned","strength":"Strong","winning_colour":list(common)[0]}
    return {"match":"Colour aligned","strength":"Medium","winning_colour":list(common)[0]}

# ---------------------------
# Swiss Ephemeris helpers
# ---------------------------
def to_utc_jd(year, month, day, hour=0, minute=0, second=0):
    return swe.julday(year, month, day, hour + minute/60.0 + second/3600.0)

def planet_longitude(jd_ut, planet):
    res = swe.calc_ut(jd_ut, planet)
    if isinstance(res[0], (list, tuple)):
        lon = res[0][0]
    else:
        lon = res[0]
    return lon % 360

def sign_from_long(lon_deg):
    idx = int(lon_deg // 30) % 12
    return SIGNS[idx], lon_deg % 30

def moon_nakshatra_pada(moon_lon):
    nak_size = 360.0 / 27.0
    idx = int(moon_lon // nak_size) % 27
    nak = NAKSHATRAS[idx]
    within = moon_lon - idx*nak_size
    pada = int((within / nak_size) * 4) + 1
    return {"nakshatra": nak, "nak_index": idx, "pada": pada}

def node_longitudes(jd_ut):
    rahu = planet_longitude(jd_ut, NODE_TRUE)
    ketu = (rahu + 180) % 360
    return rahu, ketu

def jd_to_utc_datetime(jd):
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour)*60 - minute)*60)
    return datetime(y, m, int(d), hour, minute, second)

# ---------------------------
# Moon transitions within a day
# ---------------------------
def find_moon_transitions(date_obj, tz_offset_hours=0.0, step_minutes=15):
    local_midnight = datetime.combine(date_obj, time(0,0))
    utc_midnight = local_midnight - timedelta(hours=tz_offset_hours)
    jd_start = to_utc_jd(utc_midnight.year, utc_midnight.month, utc_midnight.day)
    last_jd = jd_start
    last_moon_lon = planet_longitude(last_jd, swe.MOON)
    last_info = moon_nakshatra_pada(last_moon_lon)
    last_nak, last_pada = last_info["nak_index"], last_info["pada"]

    transitions = []
    for i in range(1, int(24*60/step_minutes)+1):
        jd = jd_start + i*step_minutes/(24*60)
        moon_lon = planet_longitude(jd, swe.MOON)
        info = moon_nakshatra_pada(moon_lon)
        if info["nak_index"] != last_nak or info["pada"] != last_pada:
            trans_jd = (last_jd + jd)/2
            trans_dt = jd_to_utc_datetime(trans_jd)
            transitions.append({
                "transition_time_utc": trans_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "transition_time_local": (trans_dt + timedelta(hours=tz_offset_hours)).strftime("%Y-%m-%d %H:%M:%S"),
                "from_nakshatra": NAKSHATRAS[last_nak],
                "to_nakshatra": NAKSHATRAS[info["nak_index"]],
                "from_pada": last_pada, "to_pada": info["pada"]
            })
            last_nak, last_pada = info["nak_index"], info["pada"]
        last_jd = jd
    return transitions

# ---------------------------
# Numerology Compatibility
# ---------------------------
good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),(2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),(4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),(6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),(8,1),(8,2),(8,4),(8,8),(9,3),(9,6),(9,9)
])

def numerology_compat(bno, lp, dno, dlp):
    if (bno,dno) in good_pairs or (lp,dlp) in good_pairs:
        return "GOOD DAY"
    return "BAD DAY"

# ---------------------------
# Main
# ---------------------------
def main():
    print("=== MASTER OFFLINE ASTRO–NUMEROLOGY ===\n")
    a_name = input("Enter Team A captain name: ").strip()
    a_dob = input("Enter Team A captain DOB (DD/MM/YYYY): ").strip()
    b_name = input("Enter Team B captain name: ").strip()
    b_dob = input("Enter Team B captain DOB (DD/MM/YYYY): ").strip()
    match_date_str = input("Enter match date (DD/MM/YYYY): ").strip()
    match_time_str = input("Enter match time (HH:MM, optional): ").strip()
    tz_off_str = input("Enter local timezone offset from UTC (e.g., +10): ").strip()

    match_date = datetime.strptime(match_date_str,"%d/%m/%Y").date()
    hm = datetime.strptime(match_time_str,"%H:%M").time() if match_time_str else time(6,0)
    tz_off_hours = float(tz_off_str) if tz_off_str else 0.0
    local_dt = datetime.combine(match_date, hm)
    jd_ut = to_utc_jd(local_dt.year, local_dt.month, local_dt.day, local_dt.hour, local_dt.minute)

    # planetary snapshot
    planets = {}
    for name,pid in PLANETS.items():
        lon = planet_longitude(jd_ut, pid)
        sign, deg = sign_from_long(lon)
        planets[name] = {"degree_total": lon, "sign": sign, "deg_in_sign": round(deg,2)}
    rahu_lon, ketu_lon = node_longitudes(jd_ut)
    planets["Rahu"] = {"degree_total": rahu_lon}
    planets["Ketu"] = {"degree_total": ketu_lon}
    moon_info = moon_nakshatra_pada(planets["Moon"]["degree_total"])
    planets["Moon"]["nakshatra"] = moon_info["nakshatra"]
    planets["Moon"]["pada"] = moon_info["pada"]

    # numerology
    a_bno, a_lp, a_name_num = birth_number(a_dob), life_path_number(a_dob), name_number(a_name)
    b_bno, b_lp, b_name_num = birth_number(b_dob), life_path_number(b_dob), name_number(b_name)
    m_dno, m_dlp = day_number(match_date_str), date_life_path(match_date_str)
    numerology_a = numerology_compat(a_bno, a_lp, m_dno, m_dlp)
    numerology_b = numerology_compat(b_bno, b_lp, m_dno, m_dlp)

    # colours
    a_colors = lucky_colors.get(a_bno,[])
    b_colors = lucky_colors.get(b_bno,[])
    date_colors = lucky_colors.get(m_dno,[])
    a_color_res = color_fine_tune(a_colors,date_colors)
    b_color_res = color_fine_tune(b_colors,date_colors)

    # moon transitions
    transitions = find_moon_transitions(match_date, tz_offset_hours=tz_off_hours)

    # output summary
    print("\n=== PLANETARY SNAPSHOT ===")
    print(json.dumps(planets, indent=2))
    print("\n=== NUMEROLOGY ===")
    print(f"Team A {a_name}: birth {a_bno}, life_path {a_lp}, name {a_name_num}, numerology: {numerology_a}")
    print(f"Team B {b_name}: birth {b_bno}, life_path {b_lp}, name {b_name_num}, numerology: {numerology_b}")
    print("\n=== COLOURS ===")
    print(f"Team A colours: {a_colors} | fine-tune: {a_color_res}")
    print(f"Team B colours: {b_colors} | fine-tune: {b_color_res}")
    print("\n=== MOON TRANSITIONS DURING THE DAY ===")
    if transitions:
        for t in transitions:
            print(f"{t['transition_time_local']}: {t['from_nakshatra']} p{t['from_pada']} -> {t['to_nakshatra']} p{t['to_pada']}")
    else:
        print("Moon remains in same nakshatra/pada for the day.")

if __name__=="__main__":
    main()
