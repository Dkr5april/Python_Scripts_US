# ============================================================
# PRS-3 / EPM MODI v38.0 — VERIFIED INPUT FRAMEWORK
# Author: Sanjeev Kumar (Locked Logic)
# ============================================================

import math
import datetime
import random

# ============================================================
# CHALDEAN NUMEROLOGY
# ============================================================

CHALDEAN = {
    'A':1,'I':1,'J':1,'Q':1,'Y':1,
    'B':2,'K':2,'R':2,
    'C':3,'G':3,'L':3,'S':3,
    'D':4,'M':4,'T':4,
    'E':5,'H':5,'N':5,'X':5,
    'U':6,'V':6,'W':6,
    'O':7,'Z':7,
    'F':8,'P':8
}

# ============================================================
# BASIC NUMEROLOGY
# ============================================================

def reduce_num(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    while s > 9:
        s = sum(int(d) for d in str(s))
    return s

def vib(name):
    return reduce_num(sum(CHALDEAN.get(c, 0) for c in name.upper()))

# ============================================================
# SIDEREAL LAGNA (ASTRO CORE)
# ============================================================

def calculate_sidereal_lagna(day, month, year, hh, mm, lon, lat):
    if month <= 2:
        year -= 1
        month += 12

    A = year // 100
    B = 2 - A + (A // 4)

    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    ut = (hh + mm / 60.0) - 5.5
    t = (jd + ut / 24.0 - 2451545.0) / 36525.0

    gmst = (6.697374558 + 2400.051336 * t) % 24
    lst = (gmst + ut * 1.002737909 + lon / 15.0) % 24

    ramc = math.radians(lst * 15)
    eps = math.radians(23.439)
    phi = math.radians(lat)

    y = math.cos(ramc)
    x = -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps))
    tropical = math.degrees(math.atan2(y, x)) % 360

    ayanamsa = 24.22
    sidereal = (tropical - ayanamsa) % 360

    return int(sidereal / 30), sidereal

# ============================================================
# HORA SYSTEM
# ============================================================

HORA_SEQUENCE = {
    "SUN": ["SUN","VENUS","MERCURY","MOON","SATURN","JUPITER","MARS"],
    "MON": ["MOON","SATURN","JUPITER","MARS","SUN","VENUS","MERCURY"],
    "TUE": ["MARS","SUN","VENUS","MERCURY","MOON","SATURN","JUPITER"],
    "WED": ["MERCURY","MOON","SATURN","JUPITER","MARS","SUN","VENUS"],
    "THU": ["JUPITER","MARS","SUN","VENUS","MERCURY","MOON","SATURN"],
    "FRI": ["VENUS","MERCURY","MOON","SATURN","JUPITER","MARS","SUN"],
    "SAT": ["SATURN","JUPITER","MARS","SUN","VENUS","MERCURY","MOON"]
}

def get_hora_lord(weekday, hour):
    return HORA_SEQUENCE[weekday][hour % 7]

# ============================================================
# LO SHU GRID
# ============================================================

def loshu_from_dob(dob):
    grid = {i:0 for i in range(1,10)}
    for d in dob:
        if d.isdigit() and d != '0':
            grid[int(d)] += 1
    return grid

def loshu_strength(grid):
    filled = sum(1 for v in grid.values() if v > 0)
    repeats = sum(v for v in grid.values() if v > 1)
    return filled + repeats

# ============================================================
# TAROT (DETERMINISTIC)
# ============================================================

MAJOR_ARCANA = [
    "FOOL","MAGICIAN","HIGH PRIESTESS","EMPRESS","EMPEROR",
    "HIEROPHANT","LOVERS","CHARIOT","STRENGTH","HERMIT",
    "WHEEL","JUSTICE","HANGED MAN","DEATH","TEMPERANCE",
    "DEVIL","TOWER","STAR","MOON","SUN","JUDGEMENT","WORLD"
]

def tarot_draw(seed):
    random.seed(seed)
    return random.choice(MAJOR_ARCANA), random.choice(["UPRIGHT","REVERSED"])

# ============================================================
# REVERSE MANIFESTATION (LAW)
# ============================================================

def reverse_manifestation(internal, teamA, teamB):
    return teamB if internal == teamA else teamA

# ============================================================
# PRS-3 ENGINE
# ============================================================

def run_prs3(teamA, teamB, dobA, dobB, weekday, hour, seed):
    internal_winner = teamA  # base assumption

    card, orient = tarot_draw(seed)
    if orient == "REVERSED":
        internal_winner = teamB

    loshuA = loshu_strength(loshu_from_dob(dobA))
    loshuB = loshu_strength(loshu_from_dob(dobB))

    final_winner = reverse_manifestation(internal_winner, teamA, teamB)
    hora_lord = get_hora_lord(weekday, hour)

    return {
        "Tarot": f"{card} ({orient})",
        "LoShu A": loshuA,
        "LoShu B": loshuB,
        "Hora Lord": hora_lord,
        "Final Winner": final_winner
    }

# ============================================================
# USER INPUT
# ============================================================

if __name__ == "__main__":

    print("\n=== PRS-3 / EPM MODI INPUT ===\n")

    teamA = input("Team A Name: ").strip()
    dobA = input("Team A Captain DOB (YYYYMMDD): ").strip()

    teamB = input("\nTeam B Name: ").strip()
    dobB = input("Team B Captain DOB (YYYYMMDD): ").strip()

    date_str = input("\nMatch Date (YYYY-MM-DD): ").strip()
    hour = int(input("Match Hour (0-23): ").strip())

    weekday = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%a").upper()[:3]
    seed = int(date_str.replace("-", ""))

    report = run_prs3(teamA, teamB, dobA, dobB, weekday, hour, seed)

    print("\n=== PRS-3 FINAL REPORT ===\n")
    for k, v in report.items():
        print(f"{k}: {v}")
