import random
from datetime import datetime, timedelta

# -----------------------------
# HELPER FUNCTIONS WITH DEBUG
# -----------------------------
def reduce_to_single_digit(number, debug_label=""):
    original = number
    while number > 9:
        number = sum(int(d) for d in str(number))
    print(f"[DEBUG] {debug_label}: reduce_to_single_digit({original}) -> {number}")
    return number

def chaldean_name_number(name):
    chaldean_map = {
        'A':1,'B':2,'C':3,'D':4,'E':5,'F':8,'G':3,'H':5,'I':1,'J':1,'K':2,
        'L':3,'M':4,'N':5,'O':7,'P':8,'Q':1,'R':2,'S':3,'T':4,'U':6,'V':6,
        'W':6,'X':5,'Y':1,'Z':7
    }
    total = sum(chaldean_map.get(c.upper(),0) for c in name)
    print(f"[DEBUG] chaldean_name_number('{name}') -> total before reduce: {total}")
    return reduce_to_single_digit(total, f"Chaldean name number for {name}")

def lo_shu_strength(numbers, label=""):
    strength = len(set(numbers))
    print(f"[DEBUG] lo_shu_strength({numbers}) [{label}] -> {strength}")
    return strength

def draw_tarot():
    random.seed(42)
    major_arcana = list(range(0, 22))
    card = random.choice(major_arcana)
    orientation = random.choice(['Upright','Reversed'])
    print(f"[DEBUG] Tarot draw -> card: {card}, orientation: {orientation}")
    return card, orientation

def jamkkol_prashna_simulation(a, b):
    random.seed(7)
    a_mod = a + random.choice([0,1])
    b_mod = b + random.choice([0,1])
    print(f"[DEBUG] Jamkkol Prashna -> team_a: {a} -> {a_mod}, team_b: {b} -> {b_mod}")
    return a_mod, b_mod

def cosmic_manifestation(a, b):
    random.seed(11)
    a_mod = a + random.choice([0,1])
    b_mod = b + random.choice([0,1])
    print(f"[DEBUG] Cosmic Manifestation -> team_a: {a} -> {a_mod}, team_b: {b} -> {b_mod}")
    return a_mod, b_mod

# -----------------------------
# REAL QMDJ FUNCTION WITH DEBUG
# -----------------------------
def qi_men_dun_jia(match_date, match_time, team_a_internal, team_b_internal, winner_before_qmdj):
    print("\n[DEBUG] ---- Qi Men Dun Jia Layer ----")
    dt_obj = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
    print(f"[DEBUG] Match datetime parsed: {dt_obj}")

    # Step 1: Build simplified Ju (1-9) from date
    ju_num = reduce_to_single_digit(int(dt_obj.strftime("%Y%m%d")), "QMDJ Ju Number")
    print(f"[DEBUG] Ju Number calculated from date: {ju_num}")

    # Step 2: Hour branch index (0-11)
    hour_branch = dt_obj.hour // 2
    print(f"[DEBUG] Hour branch (0-11): {hour_branch}")

    # Step 3: 9-Palace simplified grid (1-9)
    palace_numbers = [1,2,3,4,5,6,7,8,9]
    print(f"[DEBUG] Palace numbers: {palace_numbers}")

    # Step 4: 8 Gates mapped to palaces
    gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
    gates_grid = {palace_numbers[i]: gates[i%8] for i in range(9)}
    print(f"[DEBUG] Gates Grid Mapping: {gates_grid}")

    # Step 5: Assign team palace
    team_a_palace = palace_numbers[team_a_internal % 9]
    team_b_palace = palace_numbers[team_b_internal % 9]
    print(f"[DEBUG] Team A palace: {team_a_palace}, Team B palace: {team_b_palace}")

    # Step 6: Determine dominant gates
    team_a_gate = gates_grid[team_a_palace]
    team_b_gate = gates_grid[team_b_palace]
    print(f"[DEBUG] Team A gate: {team_a_gate}, Team B gate: {team_b_gate}")

    # Step 7: QMDJ effect logic
    harmful_gates = ["Harm","Shock","Fear","Delay"]
    if winner_before_qmdj == "Team-A":
        if team_a_gate in harmful_gates:
            final_winner = "Team-B"
            qmdj_result = f"QMDJ Flip due to {team_a_gate} Gate"
        else:
            final_winner = "Team-A"
            qmdj_result = f"QMDJ Confirmed ({team_a_gate} Gate)"
    else:
        if team_b_gate in harmful_gates:
            final_winner = "Team-A"
            qmdj_result = f"QMDJ Flip due to {team_b_gate} Gate"
        else:
            final_winner = "Team-B"
            qmdj_result = f"QMDJ Confirmed ({team_b_gate} Gate)"

    print(f"[DEBUG] QMDJ decision -> final winner: {final_winner}, reason: {qmdj_result}")
    return final_winner, qmdj_result

# -----------------------------
# USER INPUTS
# -----------------------------
print("\n=== MATCH INPUT ===\n")
match_date = input("Match Date (YYYY-MM-DD): ").strip()
match_time = input("Match Time (HH:MM): ").strip()
venue = input("Venue: ").strip()

team_a_name = input("\nTeam A Name: ").strip()
team_a_captain = input("Team A Captain Name: ").strip()
team_a_dob = input("Team A Captain DOB (YYYY-MM-DD): ").strip()

team_b_name = input("\nTeam B Name: ").strip()
team_b_captain = input("Team B Captain Name: ").strip()
team_b_dob = input("Team B Captain DOB (YYYY-MM-DD): ").strip()

# -----------------------------
# STEP 1: Day & Hora
# -----------------------------
week_day_value_map = {"Sunday":1,"Monday":2,"Tuesday":9,"Wednesday":5,
                      "Thursday":3,"Friday":6,"Saturday":8}
hora_value_map = {"Sun":1,"Moon":2,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":6,"Saturn":8}

match_weekday = datetime.strptime(match_date,"%Y-%m-%d").strftime("%A")
week_day_value = week_day_value_map[match_weekday]
hora_value = hora_value_map["Sun"]
day_hora_power = week_day_value + hora_value
print(f"[DEBUG] Match Weekday: {match_weekday} -> Week Day Value: {week_day_value}")
print(f"[DEBUG] Hora Value: {hora_value} -> Day+Hora Power: {day_hora_power}")

# -----------------------------
# STEP 2: Date & Captain Destiny
# -----------------------------
match_date_destiny = reduce_to_single_digit(sum(int(d) for d in match_date.replace("-","")), "Match Date Destiny")

def dob_destiny(dob):
    return reduce_to_single_digit(sum(int(d) for d in dob.replace("-","")), f"DOB Destiny for {dob}")

captain_a_destiny = dob_destiny(team_a_dob)
captain_b_destiny = dob_destiny(team_b_dob)

day_captain_a = reduce_to_single_digit(match_date_destiny + captain_a_destiny, "Day Captain A")
day_captain_b = reduce_to_single_digit(match_date_destiny + captain_b_destiny, "Day Captain B")

# -----------------------------
# STEP 3: Name Numbers
# -----------------------------
captain_a_name_num = chaldean_name_number(team_a_captain)
captain_b_name_num = chaldean_name_number(team_b_captain)
team_a_num = chaldean_name_number(team_a_name)
team_b_num = chaldean_name_number(team_b_name)

# -----------------------------
# STEP 4: Lo Shu
# -----------------------------
team_a_lo = lo_shu_strength([day_captain_a, day_hora_power], "Team A")
team_b_lo = lo_shu_strength([day_captain_b, day_hora_power], "Team B")

# -----------------------------
# STEP 5: Internal Strength
# -----------------------------
team_a_internal = day_hora_power + day_captain_a + team_a_lo + captain_a_name_num + team_a_num
team_b_internal = day_hora_power + day_captain_b + team_b_lo + captain_b_name_num + team_b_num
print(f"[DEBUG] Internal Strength -> Team A: {team_a_internal}, Team B: {team_b_internal}")

# -----------------------------
# STEP 6: Jamkkol
# -----------------------------
team_a_internal, team_b_internal = jamkkol_prashna_simulation(team_a_internal, team_b_internal)

# -----------------------------
# STEP 7: Cosmic Layer
# -----------------------------
team_a_internal, team_b_internal = cosmic_manifestation(team_a_internal, team_b_internal)

# -----------------------------
# STEP 8: Tarot
# -----------------------------
tarot_card, tarot_orientation = draw_tarot()

# -----------------------------
# STEP 9: Internal Favourite
# -----------------------------
internal_favourite = team_a_name if team_a_internal > team_b_internal else team_b_name
print(f"[DEBUG] Internal Favourite: {internal_favourite}")

# -----------------------------
# STEP 10: Reverse Manifestation
# -----------------------------
winner_after_reverse = team_b_name if internal_favourite == team_a_name else team_a_name
print(f"[DEBUG] Winner after Reverse Manifestation: {winner_after_reverse}")

# -----------------------------
# STEP 11: APPLY REAL QMDJ
# -----------------------------
final_winner, qmdj_result = qi_men_dun_jia(
    match_date, match_time, team_a_internal, team_b_internal, winner_after_reverse
)

# -----------------------------
# OUTPUT
# -----------------------------
print("\n--- REPORT FWINNER ---")
print(f"Match: {team_a_name} vs {team_b_name}")
print(f"Venue: {venue}")
print(f"Internal Favourite: {internal_favourite}")
print(f"Reverse Manifestation Winner: {winner_after_reverse}")
print(f"Tarot: {tarot_card} ({tarot_orientation})")
print(f"QMDJ Result: {qmdj_result}")
print(f"FINAL MATCH WINNER: {final_winner}")
