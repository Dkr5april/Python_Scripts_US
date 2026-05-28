import random
from datetime import datetime, timedelta

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
    total = sum(chaldean_map.get(c.upper(),0) for c in name)
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
# REAL QMDJ FUNCTION
# -----------------------------
def qi_men_dun_jia(match_date, match_time, team_a_internal, team_b_internal, winner_before_qmdj):
    """
    Simplified Qi Men Dun Jia effect:
    - Calculates Ju from date
    - Determines hour stem/branch
    - Builds 9-Palace grid
    - Assigns 8 Gates (Open, Rest, Life, etc.)
    - Determines dominant gate for each team
    - Can flip winner if internal favourite misaligned with dominant gate
    """
    # Step 1: Build simplified Ju (1-9) from date
    dt_obj = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
    ju_num = reduce_to_single_digit(int(dt_obj.strftime("%Y%m%d")))
    
    # Step 2: Build hour branch index (0-11)
    hour_branch = dt_obj.hour // 2  # Each branch = 2 hours
    
    # Step 3: 9-Palace simplified grid (1-9)
    palace_numbers = [1,2,3,4,5,6,7,8,9]
    
    # Step 4: 8 Gates mapped to palaces (simplified)
    gates = ["Open","Rest","Life","Harm","Shock","Delay","Scenery","Fear"]
    gates_grid = {palace_numbers[i]: gates[i%8] for i in range(9)}
    
    # Step 5: Assign each team to a palace based on internal strength modulo 9
    team_a_palace = palace_numbers[team_a_internal % 9]
    team_b_palace = palace_numbers[team_b_internal % 9]
    
    # Step 6: Determine dominant gates
    team_a_gate = gates_grid[team_a_palace]
    team_b_gate = gates_grid[team_b_palace]
    
    # Step 7: QMDJ effect logic
    # If team_a has Life/Open gate → favourite stays
    # If team_a has Harm/Shock/Fear → flip winner
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
hora_value = hora_value_map["Sun"]  # fixed for stability
day_hora_power = week_day_value + hora_value

# -----------------------------
# STEP 2: Date & Captain Destiny
# -----------------------------
match_date_destiny = reduce_to_single_digit(sum(int(d) for d in match_date.replace("-","")))

def dob_destiny(dob):
    return reduce_to_single_digit(sum(int(d) for d in dob.replace("-","")))

captain_a_destiny = dob_destiny(team_a_dob)
captain_b_destiny = dob_destiny(team_b_dob)

day_captain_a = reduce_to_single_digit(match_date_destiny + captain_a_destiny)
day_captain_b = reduce_to_single_digit(match_date_destiny + captain_b_destiny)

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
team_a_lo = lo_shu_strength([day_captain_a, day_hora_power])
team_b_lo = lo_shu_strength([day_captain_b, day_hora_power])

# -----------------------------
# STEP 5: Internal Strength
# -----------------------------
team_a_internal = day_hora_power + day_captain_a + team_a_lo + captain_a_name_num + team_a_num
team_b_internal = day_hora_power + day_captain_b + team_b_lo + captain_b_name_num + team_b_num

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

# -----------------------------
# STEP 10: Reverse Manifestation
# -----------------------------
winner_after_reverse = team_b_name if internal_favourite == team_a_name else team_a_name

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
