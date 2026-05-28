import random
import re
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo
    
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def clean_date_input(date_str):
    return re.sub(r'\D', '', date_str)

def reduce_to_single_digit(number, label=""):
    original = number
    while number > 9:
        number = sum(int(d) for d in str(number))
    if label:
        print(f"  [DEBUG] Reduction ({label}): {original} -> {number}")
    return number

def chaldean_name_number(name):
    chaldean_map = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':8,'G':3,'H':5,'I':1,'J':1,'K':2,
        'L':3,'M':4,'N':5,'O':7,'P':8,'Q':1,'R':2,'S':3,'T':4,'U':6,'V':6,
        'W':6,'X':5,'Y':1,'Z':7
    }
    total = sum(chaldean_map.get(c.upper(),0) for c in name if c.isalpha())
    reduced = reduce_to_single_digit(total)
    print(f"  [DEBUG] Chaldean Name: {name:15} | Raw Sum: {total} | Reduced: {reduced}")
    return reduced

def lo_shu_strength(numbers, team_label=""):
    unique_elements = set(numbers)
    strength = len(unique_elements)
    print(f"  [DEBUG] Lo Shu ({team_label}): Elements {unique_elements} | Strength Score: {strength}")
    return strength

def draw_tarot():
    random.seed(42)
    major_arcana = list(range(0, 22))
    card = random.choice(major_arcana)
    orientation = random.choice(['Upright','Reversed'])
    print(f"  [DEBUG] Tarot Method: Card {card}, Orientation: {orientation}")
    return card, orientation

def jamkkol_prashna_simulation(a, b):
    random.seed(7)
    shift_a = random.choice([0,1])
    shift_b = random.choice([0,1])
    print(f"  [DEBUG] Jamkkol Method: Team A +{shift_a}, Team B +{shift_b}")
    return a + shift_a, b + shift_b

def cosmic_manifestation(a, b):
    random.seed(11)
    shift_a = random.choice([0,1])
    shift_b = random.choice([0,1])
    print(f"  [DEBUG] Cosmic Method:  Team A +{shift_a}, Team B +{shift_b}")
    return a + shift_a, b + shift_b

# -----------------------------
# GEO + TIMEZONE
# -----------------------------
def get_location_details(venue_name):
    print(f"  [DEBUG] Accessing Geopy for venue: {venue_name}...")
    geolocator = Nominatim(user_agent="match_hora_app_v2")
    location = geolocator.geocode(venue_name)

    if not location:
        raise ValueError("Venue not found. Please check venue name.")

    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
    print(f"  [DEBUG] Coordinates: {location.latitude}, {location.longitude} | TZ Name: {tz_name}")
    return location.latitude, location.longitude, tz_name

# -----------------------------
# HORA CALCULATION
# -----------------------------
def calculate_hora(match_date, match_time, venue_name):
    hora_value_map = {"Sun":1,"Moon":2,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":6,"Saturn":8}
    planetary_sequence = ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"]
    weekday_ruler = {"Sunday":"Sun","Monday":"Moon","Tuesday":"Mars","Wednesday":"Mercury","Thursday":"Jupiter","Friday":"Venus","Saturday":"Saturn"}

    lat, lon, tz_name = get_location_details(venue_name)
    tz_obj = ZoneInfo(tz_name) # Convert string to TZ Object

    date_obj = datetime.strptime(match_date, "%d%m%Y")
    time_obj = datetime.strptime(match_time, "%H:%M").time()
    
    # Make match_dt timezone-aware
    match_dt = datetime.combine(date_obj, time_obj).replace(tzinfo=tz_obj)

    location = LocationInfo(latitude=lat, longitude=lon, timezone=tz_name)
    s = sun(location.observer, date=date_obj, tzinfo=tz_obj)
    sunrise = s["sunrise"]

    print(f"  [DEBUG] Sunrise at Venue: {sunrise.strftime('%H:%M:%S')}")

    if match_dt < sunrise:
        sunrise -= timedelta(days=1)
        print("  [DEBUG] Match is before sunrise. Using previous day's weekday ruler.")

    hours_since_sunrise = int((match_dt - sunrise).total_seconds() // 3600)
    
    # Calculate day lord based on the solar day (if before sunrise, it's the previous day)
    solar_day_dt = date_obj if match_dt >= sunrise else (date_obj - timedelta(days=1))
    day_name = solar_day_dt.strftime("%A")
    day_lord = weekday_ruler[day_name]

    start_index = planetary_sequence.index(day_lord)
    hora_lord = planetary_sequence[(start_index + hours_since_sunrise) % 7]

    print(f"  [DEBUG] Solar Day: {day_name} (Lord: {day_lord}) | Hours Post-Sunrise: {hours_since_sunrise}")
    print(f"  [DEBUG] Final Hora Lord: {hora_lord} (Power Value: {hora_value_map[hora_lord]})")
    return hora_lord, hora_value_map[hora_lord]

# -----------------------------
# QMDJ
# -----------------------------
def qi_men_dun_jia(team_a_internal, team_b_internal, winner_before_qmdj):
    print("\n--- QMDJ DECISION PROCESS ---")
    palace_numbers = [1,2,3,4,5,6,7,8,9]
    gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
    gates_grid = {palace_numbers[i]: gates[i % 8] for i in range(9)}

    a_idx_mod = (team_a_internal % 9)
    b_idx_mod = (team_b_internal % 9)
    
    a_palace = palace_numbers[a_idx_mod - 1]
    b_palace = palace_numbers[b_idx_mod - 1]

    team_a_gate = gates_grid[a_palace]
    team_b_gate = gates_grid[b_palace]

    print(f"  [DEBUG] Team A Internal: {team_a_internal} -> Palace: {a_palace} -> Gate: {team_a_gate}")
    print(f"  [DEBUG] Team B Internal: {team_b_internal} -> Palace: {b_palace} -> Gate: {team_b_gate}")

    harmful = ["Harm","Shock","Fear","Delay"]

    if winner_before_qmdj == "Team-A":
        if team_a_gate in harmful:
            print(f"  [DEBUG] Team-A hit harmful gate '{team_a_gate}'. Result MUST FLIP.")
            return ("Team-B", f"QMDJ Flip due to {team_a_gate} Gate")
        else:
            print(f"  [DEBUG] Team-A gate '{team_a_gate}' is safe. Result CONFIRMED.")
            return ("Team-A", f"QMDJ Confirmed ({team_a_gate} Gate)")
    else:
        if team_b_gate in harmful:
            print(f"  [DEBUG] Team-B hit harmful gate '{team_b_gate}'. Result MUST FLIP.")
            return ("Team-A", f"QMDJ Flip due to {team_b_gate} Gate")
        else:
            print(f"  [DEBUG] Team-B gate '{team_b_gate}' is safe. Result CONFIRMED.")
            return ("Team-B", f"QMDJ Confirmed ({team_b_gate} Gate)")

# -----------------------------
# MAIN EXECUTION
# -----------------------------
try:
    match_date_raw = input("Match Date (DDMMYYYY): ")
    match_date = clean_date_input(match_date_raw)
    
    match_time = input("Match Time (HH:MM): ")
    venue = input("Venue (full name): ")

    team_a_name = input("Team A Name: ")
    team_a_captain = input("Team A Captain: ")
    team_a_dob_raw = input("Team A Captain DOB (DDMMYYYY): ")
    team_a_dob = clean_date_input(team_a_dob_raw)

    team_b_name = input("Team B Name: ")
    team_b_captain = input("Team B Captain: ")
    team_b_dob_raw = input("Team B Captain DOB (DDMMYYYY): ")
    team_b_dob = clean_date_input(team_b_dob_raw)

    print("\n--- STARTING FULL BRAIN ANALYSIS ---")

    week_day_value_map = {"Sunday":1,"Monday":2,"Tuesday":9,"Wednesday":5,"Thursday":3,"Friday":6,"Saturday":8}
    weekday_str = datetime.strptime(match_date, "%d%m%Y").strftime("%A")
    week_day_value = week_day_value_map[weekday_str]

    hora_lord, hora_value = calculate_hora(match_date, match_time, venue)
    day_hora_power = week_day_value + hora_value
    print(f"  [DEBUG] Combined Day/Hora Environmental Power: {day_hora_power}")

    match_date_destiny = reduce_to_single_digit(sum(map(int, match_date)), "Match Date")
    a_dest = reduce_to_single_digit(sum(map(int, team_a_dob)), "Team A Captain DOB")
    b_dest = reduce_to_single_digit(sum(map(int, team_b_dob)), "Team B Captain DOB")

    a_day = reduce_to_single_digit(match_date_destiny + a_dest, "Team A Sync")
    b_day = reduce_to_single_digit(match_date_destiny + b_dest, "Team B Sync")

    print("\n--- CALCULATING TEAM A INTERNAL ---")
    a_name_vibe = chaldean_name_number(team_a_name)
    a_capt_vibe = chaldean_name_number(team_a_captain)
    a_lo_shu = lo_shu_strength([a_day, day_hora_power], "Team A")
    team_a_internal = day_hora_power + a_day + a_lo_shu + a_capt_vibe + a_name_vibe

    print("\n--- CALCULATING TEAM B INTERNAL ---")
    b_name_vibe = chaldean_name_number(team_b_name)
    b_capt_vibe = chaldean_name_number(team_b_captain)
    b_lo_shu = lo_shu_strength([b_day, day_hora_power], "Team B")
    team_b_internal = day_hora_power + b_day + b_lo_shu + b_capt_vibe + b_name_vibe

    print("\n--- TRIGGERING STOCHASTIC SIMULATIONS ---")
    team_a_internal, team_b_internal = jamkkol_prashna_simulation(team_a_internal, team_b_internal)
    team_a_internal, team_b_internal = cosmic_manifestation(team_a_internal, team_b_internal)
    tarot_card, tarot_orient = draw_tarot()

    print(f"\n  [DEBUG] Final Internal Score A: {team_a_internal} | B: {team_b_internal}")

    if team_a_internal > team_b_internal:
        internal_fav = team_a_name
        winner_before_qmdj = "Team-A"
        reverse_winner_label = "Team-B"
    else:
        internal_fav = team_b_name
        winner_before_qmdj = "Team-B"
        reverse_winner_label = "Team-A"

    print(f"  [DEBUG] Internal Leader: {internal_fav}")
    print(f"  [DEBUG] Applying Reverse Manifestation Logic...")

    final_label, qmdj_status = qi_men_dun_jia(team_a_internal, team_b_internal, reverse_winner_label)
    final_winner = team_a_name if final_label == "Team-A" else team_b_name

    print("\n--- FINAL RESULT ---")
    print(f"Venue: {venue}")
    print(f"Hora Lord: {hora_lord}")
    print(f"Tarot Card: {tarot_card} ({tarot_orient})")
    print(f"Internal Favourite: {internal_fav}")
    print(f"QMDJ Status: {qmdj_status}")
    print(f"FINAL MATCH WINNER: {final_winner}")

except Exception as e:
    import traceback
    print(f"\n[ERROR] The brain encountered a problem: {e}")
    traceback.print_exc()