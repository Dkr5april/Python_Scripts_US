import random
from datetime import datetime, timedelta
from astral.sun import sun
from astral import LocationInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def reduce_to_single_digit(number):
    while number > 9:
        number = sum(int(d) for d in str(number))
    return number

def chaldean_name_number(name):
    chaldean_map = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':8,'G':3,'H':5,'I':1,'J':1,'K':2,
        'L':3,'M':4,'N':5,'O':7,'P':8,'Q':1,'R':2,'S':3,'T':4,'U':6,'V':6,
        'W':6,'X':5,'Y':1,'Z':7
    }
    total = sum(chaldean_map.get(c.upper(),0) for c in name if c.isalpha())
    return reduce_to_single_digit(total)

def lo_shu_strength(numbers):
    return len(set(numbers))

def draw_tarot():
    random.seed(42)
    major_arcana = list(range(0, 22))
    return random.choice(major_arcana), random.choice(['Upright','Reversed'])

def jamkkol_prashna_simulation(a, b):
    random.seed(7)
    return a + random.choice([0,1]), b + random.choice([0,1])

def cosmic_manifestation(a, b):
    random.seed(11)
    return a + random.choice([0,1]), b + random.choice([0,1])

# -----------------------------
# GEO + TIMEZONE
# -----------------------------
def get_location_details(venue_name):
    geolocator = Nominatim(user_agent="match_hora_app")
    location = geolocator.geocode(venue_name)

    if not location:
        raise ValueError("Venue not found. Please check venue name.")

    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)

    return location.latitude, location.longitude, timezone

# -----------------------------
# HORA CALCULATION
# -----------------------------
def calculate_hora(match_date, match_time, venue_name):
    hora_value_map = {
        "Sun":1,"Moon":2,"Mars":9,
        "Mercury":5,"Jupiter":3,
        "Venus":6,"Saturn":8
    }

    planetary_sequence = [
        "Saturn","Jupiter","Mars",
        "Sun","Venus","Mercury","Moon"
    ]

    weekday_ruler = {
        "Sunday":"Sun","Monday":"Moon","Tuesday":"Mars",
        "Wednesday":"Mercury","Thursday":"Jupiter",
        "Friday":"Venus","Saturday":"Saturn"
    }

    lat, lon, timezone = get_location_details(venue_name)

    date_obj = datetime.strptime(match_date, "%Y-%m-%d")
    time_obj = datetime.strptime(match_time, "%H:%M").time()
    match_dt = datetime.combine(date_obj, time_obj)

    location = LocationInfo(latitude=lat, longitude=lon, timezone=timezone)
    s = sun(location.observer, date=date_obj, tzinfo=location.timezone)
    sunrise = s["sunrise"]

    if match_dt < sunrise:
        sunrise -= timedelta(days=1)

    hours_since_sunrise = int((match_dt - sunrise).total_seconds() // 3600)
    day_lord = weekday_ruler[match_dt.strftime("%A")]

    start_index = planetary_sequence.index(day_lord)
    hora_lord = planetary_sequence[(start_index + hours_since_sunrise) % 7]

    return hora_lord, hora_value_map[hora_lord]

# -----------------------------
# QMDJ
# -----------------------------
def qi_men_dun_jia(match_date, match_time, team_a_internal, team_b_internal, winner_before_qmdj):

    palace_numbers = [1,2,3,4,5,6,7,8,9]
    gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
    gates_grid = {palace_numbers[i]: gates[i % 8] for i in range(9)}

    team_a_gate = gates_grid[palace_numbers[team_a_internal % 9]]
    team_b_gate = gates_grid[palace_numbers[team_b_internal % 9]]

    harmful = ["Harm","Shock","Fear","Delay"]

    if winner_before_qmdj == "Team-A":
        return ("Team-B","QMDJ Flip") if team_a_gate in harmful else ("Team-A","QMDJ Confirmed")
    else:
        return ("Team-A","QMDJ Flip") if team_b_gate in harmful else ("Team-B","QMDJ Confirmed")

# -----------------------------
# USER INPUT
# -----------------------------
match_date = input("Match Date (YYYY-MM-DD): ")
match_time = input("Match Time (HH:MM): ")
venue = input("Venue (full name): ")

team_a_name = input("Team A Name: ")
team_a_captain = input("Team A Captain: ")
team_a_dob = input("Team A Captain DOB (YYYY-MM-DD): ")

team_b_name = input("Team B Name: ")
team_b_captain = input("Team B Captain: ")
team_b_dob = input("Team B Captain DOB (YYYY-MM-DD): ")

# -----------------------------
# DAY + HORA
# -----------------------------
week_day_value_map = {
    "Sunday":1,"Monday":2,"Tuesday":9,
    "Wednesday":5,"Thursday":3,
    "Friday":6,"Saturday":8
}

weekday = datetime.strptime(match_date,"%Y-%m-%d").strftime("%A")
week_day_value = week_day_value_map[weekday]

hora_lord, hora_value = calculate_hora(match_date, match_time, venue)
day_hora_power = week_day_value + hora_value

# -----------------------------
# DESTINY & INTERNAL POWER
# -----------------------------
match_date_destiny = reduce_to_single_digit(sum(map(int, match_date.replace("-",""))))

def dob_destiny(d):
    return reduce_to_single_digit(sum(map(int, d.replace("-",""))))

a_dest = dob_destiny(team_a_dob)
b_dest = dob_destiny(team_b_dob)

a_day = reduce_to_single_digit(match_date_destiny + a_dest)
b_day = reduce_to_single_digit(match_date_destiny + b_dest)

team_a_internal = (
    day_hora_power + a_day +
    lo_shu_strength([a_day, day_hora_power]) +
    chaldean_name_number(team_a_captain) +
    chaldean_name_number(team_a_name)
)

team_b_internal = (
    day_hora_power + b_day +
    lo_shu_strength([b_day, day_hora_power]) +
    chaldean_name_number(team_b_captain) +
    chaldean_name_number(team_b_name)
)

team_a_internal, team_b_internal = jamkkol_prashna_simulation(team_a_internal, team_b_internal)
team_a_internal, team_b_internal = cosmic_manifestation(team_a_internal, team_b_internal)

# -----------------------------
# FINAL
# -----------------------------
internal_fav = team_a_name if team_a_internal > team_b_internal else team_b_name
reverse = team_b_name if internal_fav == team_a_name else team_a_name

final, qmdj = qi_men_dun_jia(
    match_date, match_time, team_a_internal, team_b_internal,
    "Team-A" if reverse == team_a_name else "Team-B"
)

print("\n--- FINAL RESULT ---")
print(f"Venue Auto-located: {venue}")
print(f"Hora Lord: {hora_lord}")
print(f"Internal Favourite: {internal_fav}")
print(f"FINAL MATCH WINNER: {final}")
