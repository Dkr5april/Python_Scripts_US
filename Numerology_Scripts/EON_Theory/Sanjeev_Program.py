import random
from datetime import datetime

# -----------------------------
# NUMEROLOGY (simple chaldean)
# -----------------------------
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

def name_number(name):
    return sum(CHALDEAN.get(c,0) for c in name.upper() if c.isalpha()) % 9 or 9


# -----------------------------
# TAROT (randomizer)
# -----------------------------
TAROT = [
    "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers",
    "The Chariot", "Strength", "The Hermit"
]

def draw_tarot():
    return random.choice(TAROT)


# -----------------------------
# CPA CORE LOGIC
# -----------------------------
def cpa_prediction(date, team_a, team_b):
    day_num = sum(int(x) for x in date.replace("-", "")) % 9 or 9
    team_a_num = name_number(team_a)
    team_b_num = name_number(team_b)

    internal_winner = team_a if team_a_num + day_num > team_b_num else team_b

    # Reverse manifestation (MANDATORY)
    final_winner = team_b if internal_winner == team_a else team_a

    tarot = draw_tarot()

    return {
        "Date Number": day_num,
        "Team A Number": team_a_num,
        "Team B Number": team_b_num,
        "Tarot Card": tarot,
        "Final Winner": final_winner,
        "Toss Winner": final_winner,
        "Score Range": "150–180",
        "Match Nature": "Chasing advantage"
    }


# -----------------------------
# USER INPUT
# -----------------------------
if __name__ == "__main__":
    print("\n=== CPA Cricket Prediction ===\n")
    date = input("Match Date (YYYY-MM-DD): ")
    team_a = input("Team A: ")
    team_b = input("Team B: ")

    result = cpa_prediction(date, team_a, team_b)

    print("\n--- CPA FINAL PREDICTION ---")
    for k, v in result.items():
        print(f"{k}: {v}")
