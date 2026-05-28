# ============================================================
# EPM MODI & Report Fwinner Python Framework
# Author: Sanjeev Kumar (Locked Logic)
# Version: 1.1 (Input Enabled)
# ============================================================

import datetime
from typing import Dict, List
import random

# ==========================
# CONSTANTS
# ==========================
WEEKDAY_VALUES = {
    'Sunday': 1,
    'Monday': 2,
    'Tuesday': 9,
    'Wednesday': 5,
    'Thursday': 3,
    'Friday': 6,
    'Saturday': 8
}

HORA_VALUES = {
    'Sun': 1,
    'Moon': 2,
    'Mars': 9,
    'Mercury': 5,
    'Jupiter': 3,
    'Venus': 6,
    'Saturn': 8
}

CHALDEAN_MAP = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 8, 'G': 3,
    'H': 5, 'I': 1, 'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5,
    'O': 7, 'P': 8, 'Q': 1, 'R': 2, 'S': 3, 'T': 4, 'U': 6,
    'V': 6, 'W': 6, 'X': 5, 'Y': 1, 'Z': 7
}

# ==========================
# HELPER FUNCTIONS
# ==========================
def reduce_to_single_digit(num: int) -> int:
    while num > 9:
        num = sum(int(d) for d in str(num))
    return num

def calculate_chaldean_number(name: str) -> int:
    total = sum(CHALDEAN_MAP.get(char.upper(), 0) for char in name if char.isalpha())
    return reduce_to_single_digit(total)

def calculate_dob_destiny(dob: str) -> int:
    digits = [int(c) for c in dob if c.isdigit()]
    return reduce_to_single_digit(sum(digits))

def calculate_match_date_destiny(match_date: str) -> int:
    digits = [int(c) for c in match_date if c.isdigit()]
    return reduce_to_single_digit(sum(digits))

def calculate_day_hora_power(match_date: str, hora_planet: str) -> int:
    date_obj = datetime.datetime.strptime(match_date, "%Y-%m-%d")
    weekday_name = date_obj.strftime("%A")
    return WEEKDAY_VALUES.get(weekday_name, 0) + HORA_VALUES.get(hora_planet, 0)

# ==========================
# LO SHU FUNCTIONS
# ==========================
def generate_lo_shu_numbers(dob: str, match_date: str, weekday_name: str) -> List[int]:
    digits = [int(c) for c in dob if c.isdigit()]
    digits += [int(c) for c in match_date if c.isdigit()]
    digits.append(WEEKDAY_VALUES.get(weekday_name, 0))
    return [d for d in digits if d != 0]

def analyze_lo_shu(lo_shu_numbers: List[int]) -> Dict[str, Dict[str, List[int]]]:
    grid_positions = {
        'Mental': [4, 9, 2],
        'Emotional': [3, 5, 7],
        'Practical': [8, 1, 6]
    }
    return {
        plane: {
            'Present': [n for n in nums if n in lo_shu_numbers],
            'Missing': [n for n in nums if n not in lo_shu_numbers]
        }
        for plane, nums in grid_positions.items()
    }

# ==========================
# TAROT
# ==========================
MAJOR_ARCANA = list(range(0, 22))

def draw_tarot_card() -> Dict[str, str]:
    return {
        'card': random.choice(MAJOR_ARCANA),
        'orientation': random.choice(['Upright', 'Reversed'])
    }

# ==========================
# INTERNAL SYNTHESIS
# ==========================
def combine_team_strength(day_hora_power: int, day_captain_destiny: int,
                          lo_shu_strength: int, captain_name_num: int,
                          team_name_num: int) -> int:
    return (
        day_hora_power +
        day_captain_destiny +
        lo_shu_strength +
        captain_name_num +
        team_name_num
    )

def apply_reverse_manifestation(internal_result: str) -> str:
    return 'Team-A' if internal_result == 'Team-B' else 'Team-B'

# ==========================
# MAIN ENGINE
# ==========================
def generate_report_fwinner(inputs: Dict) -> Dict:
    match_date = inputs['match_date']
    hora_planet = inputs['hora_planet']

    day_hora_power = calculate_day_hora_power(match_date, hora_planet)
    match_destiny = calculate_match_date_destiny(match_date)

    cap_a_dest = calculate_dob_destiny(inputs['team_a']['dob'])
    cap_b_dest = calculate_dob_destiny(inputs['team_b']['dob'])

    day_cap_a = reduce_to_single_digit(match_destiny + cap_a_dest)
    day_cap_b = reduce_to_single_digit(match_destiny + cap_b_dest)

    cap_a_name = calculate_chaldean_number(inputs['team_a']['captain'])
    cap_b_name = calculate_chaldean_number(inputs['team_b']['captain'])
    team_a_name = calculate_chaldean_number(inputs['team_a']['name'])
    team_b_name = calculate_chaldean_number(inputs['team_b']['name'])

    weekday_name = datetime.datetime.strptime(match_date, "%Y-%m-%d").strftime("%A")

    lo_a = analyze_lo_shu(generate_lo_shu_numbers(inputs['team_a']['dob'], match_date, weekday_name))
    lo_b = analyze_lo_shu(generate_lo_shu_numbers(inputs['team_b']['dob'], match_date, weekday_name))

    lo_a_strength = sum(len(v['Present']) for v in lo_a.values())
    lo_b_strength = sum(len(v['Present']) for v in lo_b.values())

    strength_a = combine_team_strength(day_hora_power, day_cap_a, lo_a_strength, cap_a_name, team_a_name)
    strength_b = combine_team_strength(day_hora_power, day_cap_b, lo_b_strength, cap_b_name, team_b_name)

    internal_fav = 'Team-A' if strength_a >= strength_b else 'Team-B'
    final_winner = apply_reverse_manifestation(internal_fav)

    return {
        'Toss Winner': final_winner,
        'Match Winner': final_winner,
        'Internal Favourite': internal_fav,
        'Strength A': strength_a,
        'Strength B': strength_b,
        'Tarot Card': draw_tarot_card(),
        'Horary Confirmation': True
    }

# ==========================
# USER INPUT MODE
# ==========================
if __name__ == "__main__":
    print("\n=== EPM MODI MATCH INPUT ===\n")

    match_date = input("Match Date (YYYY-MM-DD): ").strip()
    hora_planet = input("Hora Planet (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn): ").strip()

    print("\n--- TEAM A ---")
    team_a_name = input("Team A Name: ").strip()
    team_a_captain = input("Team A Captain Name: ").strip()
    team_a_dob = input("Team A Captain DOB (YYYY-MM-DD): ").strip()

    print("\n--- TEAM B ---")
    team_b_name = input("Team B Name: ").strip()
    team_b_captain = input("Team B Captain Name: ").strip()
    team_b_dob = input("Team B Captain DOB (YYYY-MM-DD): ").strip()

    inputs = {
        'match_date': match_date,
        'hora_planet': hora_planet,
        'team_a': {'name': team_a_name, 'captain': team_a_captain, 'dob': team_a_dob},
        'team_b': {'name': team_b_name, 'captain': team_b_captain, 'dob': team_b_dob}
    }

    report = generate_report_fwinner(inputs)

    print("\n=== FINAL REPORT ===\n")
    for k, v in report.items():
        print(f"{k}: {v}")
