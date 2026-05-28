import random
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

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
# HORA AUTO CALCULATION
# -----------------------------
def calculate_hora(match_date, match_time, latitude, longitude, timezone):
    """
    Calculates planetary hora based on:
    - Location (lat/long)
    - Local sunrise
    - Weekday ruler
    """

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

    date_obj = datetime.strptime(match_date, "%Y-%m-%d")
    time_obj = datetime.strptime(match_time, "%H:%M").time()
    match_dt = datetime.combine(date_obj, time_obj)

    location = LocationInfo(latitude=latitude, longitude=longitude, timezone=timezone)
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
# QMDJ FUNCTION
# -----------------------------
def qi_men_dun_jia(match_date, match_time, team_a_internal, team_b_internal, winner_before_qmdj):

    dt_obj = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
    ju_num = reduce_to_single_digit(int(dt_obj.strftime("%Y%m%d")))

    palace_numbers = [1,2,3,4,5,6,7,8,9]
    gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
    gates_grid = {palace_numbers[i]: gates[i % 8] for i in range(9)}

    team_a_palace = palace_numbers[team_a_internal % 9]
    team_b_palace = palace_numbers[team_b_internal % 9]

    team_a_gate = gates_grid[team_a_palace]
    team_b_gate = gates_grid[team_b_palace]

    harmful_gates = ["Harm","Shock","Fear","Delay"]

    if winner_before_qmdj == "Team-A":
        if team_a_gate in harmful_gates:
            return "Team-B", f"QMDJ Flip due to {team_a_gate} Gate"
        else:
            return "Team-A", f"QMDJ Confirmed ({team_a_gate} Gate)"
    else:
        if team_b_gate in harmful_gates:
            return "Team-A", f"QMDJ Flip due to {team_b_gate} Gate"
        else:
            return "Team-B", f"QMDJ Confirmed ({team_b_gate} Gate)"

# -----------------------------
# USER INPUT
# -----------------------------
match_date = input("Match Date (YYYY-MM-DD): ").strip()
match_time = input("Match Time (HH:MM): ").strip()
venue = input("Venue: ").strip()

latitude = float(input("Venue Latitude: "))
longitude = float(input("Venue Longitude: "))
timezone = input("Timezone (e.g. Australia/Melbourne): ")

team_a_name = input("\nTeam A Name: ").strip()
team_a_captain = input("Team A Captain Name: ").strip()
team_a_dob = input("Team A Captain DOB (YYYY-MM-DD): ").strip()

team_b_name = input("\nTeam B Name: ").strip()
team_b_captain = input("Team B Captain Name: ").strip()
team_b_dob = input("Team B Captain DOB (YYYY-MM-DD): ").strip()

# -----------------------------
# STEP 1: DAY + HORA
# -----------------------------
week_day_value_map = {
    "Sunday":1,"Monday":2,"Tuesday":9,
    "Wednesday":5,"Thursday":3,
    "Friday":6,"Saturday":8
}

weekday = datetime.strptime(match_date,"%Y-%m-%d").strftime("%A")
week_day_value = week_day_value_map[weekday]

hora_lord, hora_value = calculate_hora(
    match_date, match_time, latitude, longitude, timezone
)

day_hora_power = week_day_value + hora_value

# -----------------------------
# STEP 2: DESTINY
# -----------------------------
match_date_destiny = reduce_to_single_digit(
    sum(int(d) for d in match_date.replace("-",""))
)

def dob_destiny(dob):
    return reduce_to_single_digit(sum(int(d) for d in dob.replace("-","")))

captain_a_destiny = dob_destiny(team_a_dob)
captain_b_destiny = dob_destiny(team_b_dob)

day_captain_a = reduce_to_single_digit(match_date_destiny + captain_a_destiny)
day_captain_b = reduce_to_single_digit(match_date_destiny + captain_b_destiny)

# -----------------------------
# STEP 3–7: INTERNAL POWER
# -----------------------------
team_a_internal = (
    day_hora_power +
    day_captain_a +
    lo_shu_strength([day_captain_a, day_hora_power]) +
    chaldean_name_number(team_a_captain) +
    chaldean_name_number(team_a_name)
)

team_b_internal = (
    day_hora_power +
    day_captain_b +
    lo_shu_strength([day_captain_b, day_hora_power]) +
    chaldean_name_number(team_b_captain) +
    chaldean_name_number(team_b_name)
)

team_a_internal, team_b_internal = jamkkol_prashna_simulation(team_a_internal, team_b_internal)
team_a_internal, team_b_internal = cosmic_manifestation(team_a_internal, team_b_internal)

# -----------------------------
# STEP 8–11
# -----------------------------
tarot_card, tarot_orientation = draw_tarot()

internal_favourite = team_a_name if team_a_internal > team_b_internal else team_b_name
winner_after_reverse = team_b_name if internal_favourite == team_a_name else team_a_name

final_winner, qmdj_result = qi_men_dun_jia(
    match_date, match_time, team_a_internal, team_b_internal,
    "Team-A" if winner_after_reverse == team_a_name else "Team-B"
)

# -----------------------------
# OUTPUT
# -----------------------------
print("\n--- FINAL QMDJ REPORT ---")
print(f"Match: {team_a_name} vs {team_b_name}")
print(f"Venue: {venue}")
print(f"Hora Lord: {hora_lord}")
print(f"Internal Favourite: {internal_favourite}")
print(f"Tarot: {tarot_card} ({tarot_orientation})")
print(f"QMDJ Result: {qmdj_result}")
print(f"FINAL MATCH WINNER: {final_winner}")
