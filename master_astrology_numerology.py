"""
master_astrology_numerology.py
Single-file master script:
 - accepts two captains' names + DOBs, match date, optional time, venue
 - queries online astrology APIs for planetary positions (if API key present)
 - computes numerology, lucky colours, color fine-tuning, moon nakshatra/pada shifts,
   Rahu/Ketu flags, Jupiter/Saturn transit flags, venue energy
 - produces combined energy score and recommendation
Requirements:
 - requests
 - python-dateutil
 - optionally: pyswisseph (pyswisseph/swe) for local fallback
Environment variables (one of):
 - ASTRO_USER & ASTRO_PASS  (for json.astrologyapi.com Basic Auth)
 - DIVINEAPI_KEY            (for Divine API)
 - PROKERALA_KEY            (for Prokerala API)
If no API keys present, the script will attempt local Swiss Ephemeris (if installed).
"""

import os, sys, json
import requests
from datetime import datetime, date, time, timedelta
from dateutil import tz, parser as dateparser
import getpass

# ---------------------------
# NUMEROLOGY HELPERS
# ---------------------------

def reduce_num(n:int) -> int:
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob_str: str) -> int:
    dt = datetime.strptime(dob_str, "%d/%m/%Y")
    return reduce_num(dt.day)

def life_path_number(dob_str: str) -> int:
    digits = "".join(ch for ch in dob_str if ch.isdigit())
    return reduce_num(sum(int(d) for d in digits))

# Pythagorean name number (A=1..I=9, J=1..R=9, S=1..Z=8)
PYTH_MAP = {c: ((ord(c)-65) % 9)+1 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
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
# LUCKY COLOURS & STRENGTH RULES
# ---------------------------

lucky_colors = {
    1: ["Red", "Orange", "Gold"],
    2: ["White", "Light Blue", "Silver"],
    3: ["Yellow", "Purple", "Pink"],
    4: ["Grey", "Dark Blue"],
    5: ["Green", "Light Brown"],
    6: ["Cream", "Pink", "Light Blue"],
    7: ["Sea Green", "White"],
    8: ["Dark Blue", "Black"],
    9: ["Red", "Maroon"]
}

color_strength_rank = {"Very Strong":3, "Strong":2, "Medium":1, "Neutral":0}

def color_fine_tune(captain_colors, date_colors):
    cset, dset = set(captain_colors), set(date_colors)
    common = cset.intersection(dset)
    if not common:
        return {"match":"No colour match", "strength":"Neutral", "winning_colour":None}
    # ranking heuristic: prefer Red > Dark Blue/Blue > Gold/White > others
    if "Red" in common or "Maroon" in common:
        return {"match":"Colour aligned", "strength":"Very Strong", "winning_colour":"Red"}
    if "Dark Blue" in common or "Blue" in common:
        return {"match":"Colour aligned", "strength":"Strong", "winning_colour":"Blue/Dark Blue"}
    if "Gold" in common or "White" in common:
        return {"match":"Colour aligned", "strength":"Strong", "winning_colour":list(common)[0]}
    return {"match":"Colour aligned", "strength":"Medium", "winning_colour":list(common)[0]}

# ---------------------------
# NUMEROLOGY COMPATIBILITY
# ---------------------------

good_pairs = set([
    (1,1),(1,3),(1,5),(1,6),
    (2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),
    (4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),
    (6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),
    (8,1),(8,2),(8,4),(8,8),
    (9,3),(9,6),(9,9)
])

def numerology_compat(bno, lp, dno, dlp):
    if (bno,dno) in good_pairs or (lp,dlp) in good_pairs:
        return "GOOD DAY"
    return "BAD DAY"

# ---------------------------
# VENUE GEOCODING (optional)
# ---------------------------

def geocode_place(place):
    """
    Try simple OpenStreetMap Nominatim free geocoding (no API key).
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format":"json", "limit":1}
        headers = {"User-Agent":"master-astro-script/1.0 (+contact)"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "display_name": data[0]["display_name"]}
    except Exception as e:
        return None

# ---------------------------
# ASTRO API ABSTRACTION
# - Uses whichever provider key is available:
#   1) AstrologyAPI (json.astrologyapi.com)  -> planet_panchang or planets
#   2) DivineAPI (divineapi/astroapi)       -> planetary positions / find-nakshatra
#   3) Prokerala / Vedic Rishi / FreeAstrology (if keys set)
# If none present, script will try local Swiss Ephemeris (pyswisseph) if installed.
# ---------------------------

def call_astrologyapi_planet_panchang(dt_utc, lat, lon, tz_off):
    """
    Example call to AstrologyAPI planet_panchang
    Docs: https://json.astrologyapi.com/v1/planet_panchang
    Requires ASTRO_USER, ASTRO_PASS environment variables (Basic Auth).
    """
    user = os.getenv("ASTRO_USER")
    passwd = os.getenv("ASTRO_PASS")
    if not user or not passwd:
        return None
    url = "https://json.astrologyapi.com/v1/planet_panchang"
    payload = {
        "day": dt_utc.day,
        "month": dt_utc.month,
        "year": dt_utc.year,
        "hour": dt_utc.hour,
        "min": dt_utc.minute,
        "lat": lat,
        "lon": lon,
        "tzone": tz_off
    }
    try:
        r = requests.post(url, json=payload, auth=(user, passwd), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("AstrologyAPI call failed:", e)
        return None

def call_divineapi_planetary_positions(dt_local, lat, lon, tz_off):
    """
    Example call to Divine API (astroapi-1.divineapi.com) planetary positions endpoint.
    Requires DIVINEAPI_KEY environment var (Bearer token or api_key param depending on provider).
    Docs: https://developers.divineapi.com/divine-api/indian-api/kundli-api/planetary-positions
    """
    key = os.getenv("DIVINEAPI_KEY")
    if not key:
        return None
    url = "https://astroapi-1.divineapi.com/indian-api/v2/planetary_positions"
    payload = {
        "day": dt_local.day,
        "month": dt_local.month,
        "year": dt_local.year,
        "hour": dt_local.hour,
        "min": dt_local.minute,
        "lat": lat,
        "lon": lon,
        "tzone": tz_off
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("DivineAPI call failed:", e)
        return None

def call_prokerala_planet_positions(dt_local, lat, lon, tz_off):
    key = os.getenv("PROKERALA_KEY")
    if not key:
        return None
    # Prokerala endpoint and payload pattern (example). If you have keys, tailor as needed.
    url = "https://api.prokerala.com/v1/planets"  # placeholder - consult Prokerala docs
    payload = {
        "date": dt_local.strftime("%Y-%m-%d"),
        "time": dt_local.strftime("%H:%M"),
        "longitude": lon,
        "latitude": lat,
        "timezone": tz_off
    }
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Prokerala call failed:", e)
        return None

# ---------------------------
# SIMPLE LOGIC TO EXTRACT MOON NAKSHATRA/PADA & PLANET DATA
# Each provider returns different JSON — we pick common fields:
# - moon: sign, degree, nakshatra, nakshatra_pada
# - each planet: sign, degree
# ---------------------------

def extract_from_provider(raw_json):
    """
    A thin normalizer. Each API returns different shapes — we attempt to read common fields.
    The returned structure:
    {
      "moon": {"sign":"Taurus","degree":xx.xx,"nakshatra":"Rohini","pada":2},
      "planets": {"Sun":{"sign":...,"degree":...}, "Moon":{...}, ...}
    }
    """
    if not raw_json:
        return None

    # AstrologyAPI often returns a 'data' object or direct keys.
    try:
        # AstrologyAPI 'planet_panchang' often has 'data' list with planet entries
        pts = {}
        moon_info = {}
        if isinstance(raw_json, dict):
            # look for 'moon' or 'planets' keys common to DivineAPI / others
            if "moon" in raw_json and "planets" in raw_json:
                moon_info = raw_json["moon"]
                pts = raw_json["planets"]
            elif "data" in raw_json:
                # try to parse 'data' for planets/nakshatra
                for ent in raw_json["data"]:
                    name = ent.get("name") or ent.get("planet")
                    if not name:
                        continue
                    if name.lower().startswith("moon"):
                        moon_info = {
                            "sign": ent.get("sign"),
                            "degree": ent.get("degree"),
                            "nakshatra": ent.get("nakshatra") or ent.get("birth_nakshatra"),
                            "pada": ent.get("nakshatra_pada") or ent.get("pada")
                        }
                    pts[name] = {"sign": ent.get("sign"), "degree": ent.get("degree")}
        return {"moon": moon_info, "planets": pts}
    except Exception as e:
        print("Normalization failed:", e)
        return None

# ---------------------------
# VENUE ENERGY (simple heuristic)
# ---------------------------

def venue_energy(venue_name):
    # heuristic: stadium/city name letters -> numeric sum -> reduced number -> map to strength
    s = 0
    for ch in venue_name.upper():
        if ch.isalpha():
            s += ord(ch) - 64
    r = reduce_num(s)
    # map to energy (example)
    mapping = {1:2,2:1,3:2,4:1,5:2,6:2,7:1,8:3,9:2}
    return {"venue_reduced": r, "venue_energy": mapping.get(r,1)}

# ---------------------------
# TRANSIT & RAHU/KETU FLAGS
# ---------------------------

def transit_flags(planets):
    """
    Very simple heuristics:
     - Jupiter or Saturn in angular sign (Aries, Cancer, Libra, Capricorn) considered stronger
     - Rahu/Ketu presence near Moon sign flagged
    planets: dict of planet -> {"sign": "Taurus", "degree": xx}
    """
    angular = {"Aries","Cancer","Libra","Capricorn"}
    flags = {"jupiter_angular": False, "saturn_angular": False, "rahu_near_moon": False}
    moon_sign = planets.get("Moon",{}).get("sign")
    jup = planets.get("Jupiter") or planets.get("Guru")
    sat = planets.get("Saturn") or planets.get("Shani")
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    if jup and jup.get("sign") in angular:
        flags["jupiter_angular"] = True
    if sat and sat.get("sign") in angular:
        flags["saturn_angular"] = True
    if rahu and moon_sign and rahu.get("sign") == moon_sign:
        flags["rahu_near_moon"] = True
    return flags

# ---------------------------
# COMBINED SCORE / OUTCOME
# ---------------------------

def compute_combined_score(numerology_result, color_res, moon_info, venue_en, transit_flags):
    score = 0
    if numerology_result == "GOOD DAY":
        score += 2
    score += color_strength_rank.get(color_res.get("strength","Neutral"), 0)
    if moon_info and moon_info.get("nakshatra"):
        # boost for auspicious nakshatra (naive list)
        auspicious = {"Rohini","Pushya","Anuradha","Uttara Phalguni"}
        if moon_info["nakshatra"] in auspicious:
            score += 2
        else:
            score += 1
    score += venue_en.get("venue_energy",1)

    if transit_flags.get("jupiter_angular"):
        score += 2
    if transit_flags.get("saturn_angular"):
        score += 1
    if transit_flags.get("rahu_near_moon"):
        score -= 1

    outcome = "Very Favourable" if score >= 7 else ("Balanced" if score >= 4 else "Weak")
    return {"score": score, "outcome": outcome}

# ---------------------------
# MAIN FLOW
# ---------------------------

def main():
    print("MASTER ASTRO-NUMEROLOGY PREDICTION")
    # Inputs
    a_name = input("Enter Team A captain name: ").strip()
    a_dob = input("Enter Team A captain DOB (DD/MM/YYYY): ").strip()
    b_name = input("Enter Team B captain name: ").strip()
    b_dob = input("Enter Team B captain DOB (DD/MM/YYYY): ").strip()
    match_date = input("Enter match date (DD/MM/YYYY): ").strip()
    match_time = input("Enter match time (HH:MM) or leave blank (will use sunrise): ").strip()
    venue = input("Enter venue (city name or 'lat,lon'): ").strip()

    # parse match datetime & venue location
    if "," in venue and all(part.strip().replace(".","").replace("-","").isdigit() for part in venue.split(",")):
        lat, lon = map(float, venue.split(","))
        venue_name = f"{lat},{lon}"
    else:
        geo = geocode_place(venue)
        if geo:
            lat, lon = geo["lat"], geo["lon"]
            venue_name = geo["display_name"]
            print("Resolved venue ->", venue_name)
        else:
            print("Could not geocode venue; defaulting to lat=0,lon=0")
            lat, lon = 0.0, 0.0
            venue_name = venue

    # timezone offset approximate from UTC by using dateutil (we assume local system zone for calculations)
    local_tz = tz.tzlocal()
    # build match datetime
    dt_local = datetime.strptime(match_date, "%d/%m/%Y")
    if match_time:
        hhmm = datetime.strptime(match_time, "%H:%M").time()
        dt_local = datetime.combine(dt_local.date(), hhmm)
    else:
        # get sunrise approx: use 6:00 local as a safe "date-level" time OR you can call sunrise API to accurate sunrise
        dt_local = datetime.combine(dt_local.date(), time(6,0))

    # compute tz offset in hours
    offset_seconds = datetime.now(local_tz).utcoffset().total_seconds() if datetime.now(local_tz).utcoffset() else 0
    tz_off_hours = offset_seconds / 3600.0

    # Try providers in order
    provider_data = None
    provider_used = None
    print("Attempting AstrologyAPI provider...")
    try:
        a_response = call_astrologyapi_planet_panchang(dt_local, lat, lon, tz_off_hours)
        if a_response:
            provider_data = extract_from_provider(a_response)
            provider_used = "AstrologyAPI"
    except Exception:
        pass

    if not provider_data:
        print("AstrologyAPI failed or not configured. Trying DivineAPI...")
        try:
            d_response = call_divineapi_planetary_positions(dt_local, lat, lon, tz_off_hours)
            if d_response:
                provider_data = extract_from_provider(d_response)
                provider_used = "DivineAPI"
        except Exception:
            pass

    if not provider_data:
        print("No online provider available or calls failed. Attempting local Swiss Ephemeris (pyswisseph) if installed...")
        try:
            import swisseph as swe
            # local computation: compute ecliptic longitude for planets and moon, compute nakshatra/pada roughly
            # (left as minimal fallback - for production add full logic)
            jd = swe.julday(dt_local.year, dt_local.month, dt_local.day, dt_local.hour + dt_local.minute/60.0)
            planet_names = {0:"Sun",1:"Moon",2:"Mercury",3:"Venus",4:"Mars",5:"Jupiter",6:"Saturn",7:"Uranus",8:"Neptune",9:"Pluto"}
            pdat = {"planets":{}}
            for pid, pname in planet_names.items():
                lon = swe.calc_ut(jd, pid)[0][0]
                sign_index = int(lon // 30)
                signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
                pdat["planets"][pname] = {"degree": lon % 30, "sign": signs[sign_index], "degree_total": lon}
            # basic moon natshatra approximate: (moon longitude / 13.3333)
            moon_lon = pdat["planets"]["Moon"]["degree_total"]
            nak_idx = int(moon_lon // (13 + 1/3))
            nakashatras = ["Ashwini","Bharani","Krittika","Rohini","Mrigashirsha","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
            pada = int(((moon_lon % (13+1/3)) / (13+1/3)) * 4) + 1
            pdat["moon"] = {"sign": pdat["planets"]["Moon"]["sign"], "degree": pdat["planets"]["Moon"]["degree"], "nakshatra": nakashatras[nak_idx%27], "pada": pada}
            provider_data = {"moon": pdat["moon"], "planets": pdat["planets"]}
            provider_used = "SwissEphemeris(local)"
        except Exception as e:
            print("Local ephemeris not available:", e)
            provider_data = None
            provider_used = None

    if not provider_data:
        print("ERROR: No planetary data available (no API key and no local ephemeris). Exiting.")
        sys.exit(1)

    print("Provider used:", provider_used)
    # Numerical calculations for both captains
    a_bno = birth_number(a_dob)
    a_lp = life_path_number(a_dob)
    a_name_num = name_number(a_name)

    b_bno = birth_number(b_dob)
    b_lp = life_path_number(b_dob)
    b_name_num = name_number(b_name)

    m_dno = day_number(match_date)
    m_dlp = date_life_path(match_date)

    numerology_result_a = numerology_compat(a_bno, a_lp, m_dno, m_dlp)
    numerology_result_b = numerology_compat(b_bno, b_lp, m_dno, m_dlp)

    # colours
    a_colors = lucky_colors.get(a_bno, [])
    b_colors = lucky_colors.get(b_bno, [])
    date_colors = lucky_colors.get(m_dno, [])

    a_color_res = color_fine_tune(a_colors, date_colors)
    b_color_res = color_fine_tune(b_colors, date_colors)

    # venue energy
    v_energy = venue_energy(venue_name)

    # transits & flags
    flags = transit_flags(provider_data.get("planets", {}))

    # combined scoring (per team)
    a_comb = compute_combined_score(numerology_result_a, a_color_res, provider_data.get("moon",{}), v_energy, flags)
    b_comb = compute_combined_score(numerology_result_b, b_color_res, provider_data.get("moon",{}), v_energy, flags)

    out = {
        "input": {
            "teamA": {"name": a_name, "dob": a_dob, "birth_num": a_bno, "life_path": a_lp, "name_number": a_name_num, "colors": a_colors},
            "teamB": {"name": b_name, "dob": b_dob, "birth_num": b_bno, "life_path": b_lp, "name_number": b_name_num, "colors": b_colors},
            "match_date": match_date,
            "match_time": match_time if match_time else "sunrise(approx)",
            "venue": venue_name,
            "tz_offset": tz_off_hours
        },
        "provider": {"used": provider_used, "data_sample": provider_data},
        "numerology": {
            "teamA": numerology_result_a,
            "teamB": numerology_result_b
        },
        "color_analysis": {"teamA": a_color_res, "teamB": b_color_res, "date_colors": date_colors},
        "moon": provider_data.get("moon"),
        "transit_flags": flags,
        "venue_energy": v_energy,
        "combined": {"teamA": a_comb, "teamB": b_comb}
    }

    # Print summary
    print("\n\n===== SUMMARY =====")
    print(f"Match: {a_name} (Team A) vs {b_name} (Team B) on {match_date} at {venue_name}")
    print("Moon:", provider_data.get("moon"))
    print("\nTeam A:", a_name, "| Prediction:", a_comb["outcome"], "| Score:", a_comb["score"])
    print("Team B:", b_name, "| Prediction:", b_comb["outcome"], "| Score:", b_comb["score"])
    print("\nDetailed JSON written to prediction.json")
    with open("prediction.json","w",encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
