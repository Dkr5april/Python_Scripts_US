# ======================================================
# EPM : Exact Prediction Method
# Author : Sanjeev Sarma
# ======================================================

import datetime

# -------------------------------
# BASIC NUMEROLOGY UTILITIES
# -------------------------------

def reduce_number(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def destiny_from_dob(dob):
    return reduce_number(sum(int(d) for d in dob if d.isdigit()))

def day_destiny(match_date):
    return reduce_number(sum(int(d) for d in match_date.strftime("%Y%m%d")))

# -------------------------------
# DAY & HORA LORD
# -------------------------------

DAY_LORD = {
    0: "Moon", 1: "Mars", 2: "Mercury",
    3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"
}

HORA_SEQUENCE = ["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"]

def get_day_lord(date):
    return DAY_LORD[date.weekday()]

def get_hora_lord(time):
    return HORA_SEQUENCE[time.hour % 7]

# -------------------------------
# LO SHU GRID
# -------------------------------

def lo_shu_grid(dob, name):
    digits = [int(d) for d in dob if d.isdigit()]
    for c in name.upper():
        if c.isalpha():
            digits.append((ord(c) - 64) % 9 or 9)
    return {i: digits.count(i) for i in range(1,10)}

# -------------------------------
# EPM ENGINE
# -------------------------------

def apply_epm():
    print("\n🔮 EPM – Exact Prediction Method 🔮\n")

    # USER INPUTS (DD/MM/YYYY)
    match_date = datetime.datetime.strptime(
        input("Match Date (DD/MM/YYYY): "), "%d/%m/%Y"
    ).date()

    match_time = datetime.datetime.strptime(
        input("Match Time (HH:MM, 24hr): "), "%H:%M"
    ).time()

    venue = input("Venue: ")

    team1 = input("Team 1 Name: ")
    captain1 = input("Team 1 Captain Name: ")
    captain1_dob = input("Captain 1 DOB (DD/MM/YYYY): ")

    team2 = input("\nTeam 2 Name: ")
    captain2 = input("Team 2 Captain Name: ")
    captain2_dob = input("Captain 2 DOB (DD/MM/YYYY): ")

    # CALCULATIONS
    day_lord = get_day_lord(match_date)
    hora_lord = get_hora_lord(match_time)
    day_num = day_destiny(match_date)

    cap1_dest = destiny_from_dob(captain1_dob)
    cap2_dest = destiny_from_dob(captain2_dob)

    total1 = reduce_number(cap1_dest + day_num)
    total2 = reduce_number(cap2_dest + day_num)

    raw_winner = team1 if total1 > total2 else team2
    final_winner = team2 if raw_winner == team1 else team1  # CPA Reverse

    # OUTPUT
    print("\n📊 EPM RESULT")
    print("────────────────────────")
    print(f"Venue           : {venue}")
    print(f"Day Lord        : {day_lord}")
    print(f"Hora Lord       : {hora_lord}")
    print(f"Day Destiny     : {day_num}")
    print(f"{captain1} Total : {total1}")
    print(f"{captain2} Total : {total2}")
    print("────────────────────────")
    print(f"RAW WINNER      : {raw_winner}")
    print(f"FINAL WINNER 🧿 : {final_winner}")
    print("────────────────────────")

# -------------------------------
# RUN PROGRAM
# -------------------------------

if __name__ == "__main__":
    apply_epm()
