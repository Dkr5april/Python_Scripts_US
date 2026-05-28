import math
import datetime
from geopy.geocoders import Nominatim

# ============================================================
# EPM MODI v38.0: FULL NUMEROLOGY DEBUG + PRECISION LAGNA
# ============================================================

CHALDEAN = {'A':1,'I':1,'J':1,'Q':1,'Y':1,'B':2,'K':2,'R':2,'C':3,'G':3,'L':3,'S':3,
            'D':4,'M':4,'T':4,'E':5,'H':5,'N':5,'X':5,'U':6,'V':6,'W':6,'O':7,'Z':7,'F':8,'P':8}

ZODIAC_LORDS = {
    0: ("ARIES", "MARS"), 1: ("TAURUS", "VENUS"), 2: ("GEMINI", "MERCURY"), 
    3: ("CANCER", "MOON"), 4: ("LEO", "SUN"), 5: ("VIRGO", "MERCURY"), 
    6: ("LIBRA", "VENUS"), 7: ("SCORPIO", "MARS"), 8: ("SAGITTARIUS", "JUPITER"), 
    9: ("CAPRICORN", "SATURN"), 10: ("AQUARIUS", "SATURN"), 11: ("PISCES", "JUPITER")
}

def reduce(n):
    num = sum(int(d) for d in str(n) if d.isdigit())
    while num > 9: num = sum(int(d) for d in str(num))
    return num

def vib(name):
    return sum(CHALDEAN.get(c, 0) for c in name.upper() if c in CHALDEAN)

def calculate_accurate_lagna(day, month, year, hh, mm, lon, lat):
    # Standard Vedic Sidereal Time Calculation
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + (A // 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    ut = (hh + mm/60.0) - 5.5
    t = (jd + ut/24.0 - 2451545.0) / 36525.0
    gmst = (6.697374558 + 2400.051336 * t + 0.000025862 * t**2) % 24
    lst_hours = (gmst + ut * 1.002737909 + lon/15.0) % 24
    ramc_rad = math.radians(lst_hours * 15.0)
    eps = math.radians(23.439)
    phi = math.radians(lat)
    y = math.cos(ramc_rad)
    x = -(math.sin(ramc_rad) * math.cos(eps) + math.tan(phi) * math.sin(eps))
    tropical_asc = math.degrees(math.atan2(y, x)) % 360
    ayanamsa = 24.22
    sidereal_deg = (tropical_asc - ayanamsa) % 360
    return int(sidereal_deg / 30), sidereal_deg

def run_epm_modi_v38():
    print("\n--- [ENTER ALL DATA POINTS] ---")
    tA = input("Team A Name: "); cA = input("Captain A Name: "); dba = input("Captain A DOB: ")
    tB = input("Team B Name: "); cB = input("Captain B Name: "); dbb = input("Captain B DOB: ")
    m_date = input("Match Date (DDMMYYYY): "); m_time = input("Match Time: "); m_place = input("Match City: ")
    hora = input("Ruling Match Hora: ").upper()
    q_date = input("Query Date (DDMMYYYY): "); q_time = input("Query Time (HH:MM): "); q_place = input("Query City Name: ")

    # Fixed Coordinates for Vijayawada (Matches your verified table)
    lat = 16.5167; lon = 80.6167 
    qd, qm, qy = int(q_date[:2]), int(q_date[2:4]), int(q_date[4:])
    hh, mm = map(int, q_time.split(':'))

    print("\n" + "="*100)
    print(f"      EPM MODI v38.0 MASTER AUDIT: {tA} vs {tB}")
    print(f"      COORDINATES: {lat}N, {lon}E")
    print("="*100)

    # --- [PHASE 2: NUMEROLOGY DEBUG 01-26] ---
    p1 = reduce(m_date); print(f"Pt [01] Match Date Reduction: {p1}")
    p2 = reduce(q_date); print(f"Pt [02] Query Date Reduction: {p2}")
    p3 = reduce(vib(hora)); print(f"Pt [03] Match Hora ({hora}) Vibration: {p3}")
    
    v_ta = reduce(vib(tA)); print(f"Pt [11] {tA} Team Vibration: {v_ta}")
    v_ca = reduce(vib(cA)); print(f"Pt [12] {cA} Captain Vibration: {v_ca}")
    v_da = reduce(dba); print(f"Pt [13] Captain DOB Reduction: {v_da}")
    scoreA = reduce(p1 + p2 + p3 + v_ta + v_ca + v_da)
    print(f"Pt [20] {tA} Composite Score: {scoreA}")

    v_tb = reduce(vib(tB)); print(f"Pt [21] {tB} Team Vibration: {v_tb}")
    v_cb = reduce(vib(cB)); print(f"Pt [22] {cB} Captain Vibration: {v_cb}")
    v_db = reduce(dbb); print(f"Pt [23] Captain DOB Reduction: {v_db}")
    scoreB = reduce(p1 + p2 + p3 + v_tb + v_cb + v_db)
    print(f"Pt [25] {tB} Composite Score: {scoreB}")

    # --- [PHASE 3: ASSIGNMENT DEBUG 27-31] ---
    lead = tA if scoreA >= scoreB else tB
    fA = (scoreA + 3) if lead == tA else scoreA
    fB = (scoreB + 3) if lead == tB else scoreB
    l_team, s_team = (tA, tB) if fA >= fB else (tB, tA)
    print(f"Pt [31] DIRECT ASSIGNMENT: Lagna = {l_team} | 7th House = {s_team}")

    # --- [PHASE 4: PRECISION LAGNA 32-34] ---
    lagna_idx, lagna_deg = calculate_accurate_lagna(qd, qm, qy, hh, mm, lon, lat)
    l_sign, l_lord = ZODIAC_LORDS[lagna_idx]
    s_sign, s_lord = ZODIAC_LORDS[(lagna_idx + 6) % 12]

    print(f"Pt [32a] Sidereal Degree: {lagna_deg:.2f}°")
    print(f"Pt [32c] FINAL SIDEREAL LAGNA: {l_sign} (Lord: {l_lord})")
    print(f"Pt [33]  FINAL SIDEREAL 7th HOUSE: {s_sign} (Lord: {s_lord})")

    l_shad = reduce(vib(l_lord) + p2 + int(lat))
    s_shad = reduce(vib(s_lord) + p2 + int(lon))
    l_dig = 2 if (l_lord in ["JUPITER", "MERCURY"]) else 0
    s_dig = 2 if (s_lord == "SATURN") else 0
    
    print(f"Pt [34a] Lagna Lord ({l_lord}) Power: {l_shad} + Digbala: {l_dig}")
    print(f"Pt [34b] 7th Lord ({s_lord}) Power: {s_shad} + Digbala: {s_dig}")

    # --- [PHASE 5: FINAL VERDICT] ---
    l_final = l_shad + l_dig
    s_final = s_shad + s_dig
    winner = l_team if l_final >= s_final else s_team

    print("\n" + "#"*100)
    print(f"Pt [35] FINAL PREDICTION: {winner.upper()} WINS")
    print(f"Pt [36] JUSTIFICATION: {l_lord} strength vs {s_lord}.")
    print("#"*100)

if __name__ == "__main__":
    run_epm_modi_v38()