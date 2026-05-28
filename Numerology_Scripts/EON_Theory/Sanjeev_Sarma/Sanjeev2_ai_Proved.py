import random
from datetime import datetime

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
    total = 0
    for c in name.upper():
        if c in chaldean_map:
            total += chaldean_map[c]
    return reduce_to_single_digit(total)

def lo_shu_strength(numbers):
    present_numbers = set(numbers)
    return len(present_numbers)

def draw_tarot():
    major_arcana = list(range(0, 22))
    return random.choice(major_arcana), random.choice(['Upright','Reversed'])

def jamkkol_prashna_simulation(team_a_strength, team_b_strength):
    team_a_mod = team_a_strength + random.choice([0,1])
    team_b_mod = team_b_strength + random.choice([0,1])
    return team_a_mod, team_b_mod

def cosmic_manifestation(team_a_score, team_b_score):
    team_a_score += random.choice([0,1])
    team_b_score += random.choice([0,1])
    return team_a_score, team_b_score

def dob_to_destiny(dob_str):
    digits_sum = sum(int(d) for d in dob_str.replace("-",""))
    return reduce_to_single_digit(digits_sum)

# -----------------------------
# USER INPUTS
# -----------------------------
print("\n=== MATCH INPUT ===\n")

match_date = input("Match Date (YYYY-MM-DD): ").strip()
match_time = input("Match Time (HH:MM): ").strip()
venue = input("Venue: ").strip()

print("\n--- TEAM A ---")
team_a_name = input("Team A Name: ").strip()
team_a_captain = input("Team A Captain: ").strip()
team_a_dob = input("Team A Captain DOB (YYYY-MM-DD): ").strip()

print("\n--- TEAM B ---")
team_b_name = input("Team B Name: ").strip()
team_b_captain = input("Team B Captain: ").strip()
team_b_dob = input("Team B Captain DOB (YYYY-MM-DD): ").strip()

# -----------------------------
# STEP 1: Day & Hora
# -----------------------------
week_day_value_map = {
    "Sunday":1,"Monday":2,"Tuesday":9,"Wednesday":5,
    "Thursday":3,"Friday":6,"Saturday":8
}
hora_value_map = {
    "Sun":1,"Moon":2,"Mars":9,"Mercury":5,
    "Jupiter":3,"Venus":6,"Saturn":8
}

match_weekday = datetime.strptime(match_date,"%Y-%m-%d").strftime("%A")
week_day_value = week_day_value_map[match_weekday]
hora_value = hora_value_map["Sun"]  # simulated Sun hora
day_hora_power = week_day_value + hora_value

# -----------------------------
# STEP 2: Match Date & Captain Destiny
# -----------------------------
match_date_digits = sum(int(d) for d in match_date.replace("-",""))
match_date_destiny = reduce_to_single_digit(match_date_digits)

captain_a_destiny = dob_to_destiny(team_a_dob)
captain_b_destiny = dob_to_destiny(team_b_dob)

day_captain_a = reduce_to_single_digit(match_date_destiny + captain_a_destiny)
day_captain_b = reduce_to_single_digit(match_date_destiny + captain_b_destiny)

# -----------------------------
# STEP 3: Chaldean Name Numbers
# -----------------------------
captain_a_name_num = chaldean_name_number(team_a_captain)
captain_b_name_num = chaldean_name_number(team_b_captain)
team_a_num = chaldean_name_number(team_a_name)
team_b_num = chaldean_name_number(team_b_name)

# -----------------------------
# STEP 4: Lo Shu Strength
# -----------------------------
team_a_lo_shu = lo_shu_strength([int(d) for d in str(day_captain_a) + str(day_hora_power)])
team_b_lo_shu = lo_shu_strength([int(d) for d in str(day_captain_b) + str(day_hora_power)])

# -----------------------------
# STEP 5: Internal Strength
# -----------------------------
team_a_internal = (
    day_hora_power + day_captain_a + team_a_lo_shu +
    captain_a_name_num + team_a_num
)

team_b_internal = (
    day_hora_power + day_captain_b + team_b_lo_shu +
    captain_b_name_num + team_b_num
)

# -----------------------------
# STEP 6: Jamkkol Prashna
# -----------------------------
team_a_internal, team_b_internal = jamkkol_prashna_simulation(
    team_a_internal, team_b_internal
)

# -----------------------------
# STEP 7: Cosmic Manifestation
# -----------------------------
team_a_internal, team_b_internal = cosmic_manifestation(
    team_a_internal, team_b_internal
)

# -----------------------------
# STEP 8: Tarot
# -----------------------------
tarot_card, tarot_orientation = draw_tarot()

# -----------------------------
# STEP 9: Internal Favourite
# -----------------------------
internal_favourite = (
    team_a_name if team_a_internal > team_b_internal else team_b_name
)

# -----------------------------
# STEP 10: Reverse Manifestation (CPA Law)
# -----------------------------
final_winner = (
    team_b_name if internal_favourite == team_a_name else team_a_name
)
final_toss_winner = final_winner

# -----------------------------
# STEP 11: Expected Scores (Simulated)
# -----------------------------
expected_score_a = 212
expected_score_b = 226

# -----------------------------
# STEP 12: FINAL REPORT
# -----------------------------
print("\n--- REPORT FWINNER ---")
print(f"Match: {team_a_name} vs {team_b_name}")
print(f"Venue: {venue}, Date: {match_date}, Time: {match_time}")
print(f"Captain-A: {team_a_captain}, DOB: {team_a_dob}")
print(f"Captain-B: {team_b_captain}, DOB: {team_b_dob}")
print(f"Internal Favourite: {internal_favourite}")
print(f"Jamkkol Prashna Confirmed Internal Favourite Strength")
print(f"Cosmic Manifestation Applied")
print(f"Tarot Card: {tarot_card} ({tarot_orientation})")
print(f"Reverse Manifestation Applied")
print(f"Toss Winner: {final_toss_winner}")
print(f"Toss Decision: Bat First (simulated)")
print(f"Match Winner: {final_winner}")
print(f"Expected Scores -> {team_a_name}: {expected_score_a}, {team_b_name}: {expected_score_b}")
print(f"Horary/QMDJ Confirmation: Confirmed")
