from datetime import datetime

# ---------------------------
# NUMEROLOGY FUNCTIONS
# ---------------------------

def reduce_num(n):
    """Reduce a number to single digit except master numbers."""
    while n > 9:
        n = sum(int(i) for i in str(n))
    return n

def birth_number(dob):
    """Birth number = day reduced."""
    day = int(dob.split("/")[0])
    return reduce_num(day)

def life_path_number(dob):
    """Life path number = total of full DOB."""
    nums = dob.replace("/", "")
    return reduce_num(sum(int(i) for i in nums))

def day_number(date):
    """Match date day number."""
    day = int(date.split("/")[0])
    return reduce_num(day)

def date_life_path(date):
    """Life path of match date."""
    nums = date.replace("/", "")
    return reduce_num(sum(int(i) for i in nums))

# ---------------------------
# COMPATIBILITY LOGIC
# ---------------------------

good_pairs = [
    (1,1),(1,3),(1,5),(1,6),
    (2,2),(2,4),(2,6),
    (3,3),(3,5),(3,6),(3,9),
    (4,1),(4,4),(4,8),
    (5,1),(5,3),(5,5),(5,6),(5,8),
    (6,2),(6,3),(6,6),(6,9),
    (7,1),(7,2),(7,4),(7,7),
    (8,1),(8,2),(8,4),(8,8),
    (9,3),(9,6),(9,9)
]

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

def check_compatibility(bno, lp, dno, dlp):
    """Return Good / Bad result."""
    captain_key = (bno, dno)
    lifepath_key = (lp, dlp)

    if captain_key in good_pairs or lifepath_key in good_pairs:
        return "GOOD DAY"
    else:
        return "BAD DAY"

# ---------------------------
# MAIN FUNCTION
# ---------------------------

def numerology_judge(captain_dob, match_date):
    bno = birth_number(captain_dob)
    lp = life_path_number(captain_dob)
    dno = day_number(match_date)
    dlp = date_life_path(match_date)

    result = check_compatibility(bno, lp, dno, dlp)

    return {
        "Captain DOB": captain_dob,
        "Birth Number": bno,
        "Life Path Number": lp,
        "Match Day Number": dno,
        "Match Date Life Path": dlp,
        "Prediction": result,
        "Lucky Colours": lucky_colors[bno]
    }

# ---------------------------
# EXAMPLE RUN
# ---------------------------

print(numerology_judge("06/10/1989", "20/11/2025"))

"whoever Installing software please maintain standard password which is Welcome12"
