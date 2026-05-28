# -----------------------------------------------------------
# MLSS (fixed): Multiset intersection for matching counts
# Prompts user for Matrix A, Matrix B, and a 4-digit result
# -----------------------------------------------------------

from itertools import combinations
from collections import Counter

def reduce_digit(n):
    """Reduce any nonnegative integer to a single digit using numerology."""
    n = abs(int(n))
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def flatten_matrix(mat):
    """Flatten a 2x2 matrix into a list of 4 digits."""
    return [mat[0][0], mat[0][1], mat[1][0], mat[1][1]]

def all_pair_sums_reduced(digits):
    """Return a list of reduced pair-sums for all 2-combinations (orderless)."""
    return [reduce_digit(a + b) for a, b in combinations(digits, 2)]

def compute_signature(digits):
    """Return signature dict for raw digits, reduced digits, reduced pairs, total, and counts."""
    raw = list(digits)
    reduced = [reduce_digit(d) for d in raw]
    pairs = all_pair_sums_reduced(raw)
    total = reduce_digit(sum(raw))
    repeat_counts = Counter(raw)
    return {
        "raw": raw,
        "reduced": reduced,
        "pairs": pairs,
        "total": total,
        "repeat": repeat_counts
    }

def multiset_intersection_count(list_a, list_b):
    """Return the count of matching elements between two lists as multiset intersection."""
    ca, cb = Counter(list_a), Counter(list_b)
    # sum of min counts for each element
    return sum(min(ca[k], cb[k]) for k in (ca.keys() & cb.keys()))

def score_match(matrix_sig, result_sig):
    """Compute score using multiset intersections and proportional repetition credit."""
    score = 0

    # Weights (tweakable)
    W_RAW = 2
    W_REDUCED = 3
    W_PAIRS = 4
    W_TOTAL = 5
    W_REPEAT = 2  # per matching repeated digit (proportional)

    # 1. Raw digit multiset intersection
    raw_matches = multiset_intersection_count(matrix_sig["raw"], result_sig["raw"])
    score += raw_matches * W_RAW

    # 2. Reduced digit multiset intersection
    reduced_matches = multiset_intersection_count(matrix_sig["reduced"], result_sig["reduced"])
    score += reduced_matches * W_REDUCED

    # 3. Pair-sum (reduced) multiset intersection
    pair_matches = multiset_intersection_count(matrix_sig["pairs"], result_sig["pairs"])
    score += pair_matches * W_PAIRS

    # 4. Total numerology match (exact)
    total_match = 1 if matrix_sig["total"] == result_sig["total"] else 0
    if total_match:
        score += W_TOTAL

    # 5. Repetition structure credit (proportional)
    # For each digit, give credit proportional to min(count_matrix, count_result)
    repeat_credit = 0
    for d in (matrix_sig["repeat"].keys() & result_sig["repeat"].keys()):
        repeat_credit += min(matrix_sig["repeat"][d], result_sig["repeat"][d])
    score += repeat_credit * W_REPEAT

    # Return detailed breakdown also
    breakdown = {
        "raw_matches": raw_matches,
        "reduced_matches": reduced_matches,
        "pair_matches": pair_matches,
        "total_match": bool(total_match),
        "repeat_credit_units": repeat_credit,
        "score": score
    }
    return score, breakdown

def read_matrix(prompt_name="Matrix"):
    print(f"Enter {prompt_name} (2×2):")
    a11 = int(input(f"{prompt_name}[0][0] = "))
    a12 = int(input(f"{prompt_name}[0][1] = "))
    a21 = int(input(f"{prompt_name}[1][0] = "))
    a22 = int(input(f"{prompt_name}[1][1] = "))
    return [[a11, a12], [a21, a22]]

def read_result_code():
    while True:
        s = input("Enter the final 4-digit result to match: ").strip()
        if len(s) == 4 and all(ch.isdigit() for ch in s):
            return [int(ch) for ch in s]
        else:
            print("Please enter exactly 4 digits (e.g. 2451).")

def print_breakdown(name, sig, breakdown):
    print(f"\n--- {name} breakdown ---")
    print("raw digits:", sig["raw"])
    print("reduced digits:", sig["reduced"])
    print("reduced pair sums:", sig["pairs"])
    print("total numerology:", sig["total"])
    print("repeat counts:", dict(sig["repeat"]))
    print("raw matches (units):", breakdown["raw_matches"])
    print("reduced matches (units):", breakdown["reduced_matches"])
    print("pair matches (units):", breakdown["pair_matches"])
    print("total numerology equal?:", breakdown["total_match"])
    print("repeat-credit units:", breakdown["repeat_credit_units"])
    print("score:", breakdown["score"])

# -------------------- MAIN --------------------
if __name__ == "__main__":
    matrixA = read_matrix("Matrix A")
    matrixB = read_matrix("Matrix B")
    result_digits = read_result_code()

    sigA = compute_signature(flatten_matrix(matrixA))
    sigB = compute_signature(flatten_matrix(matrixB))
    sigR = compute_signature(result_digits)

    scoreA, breakdownA = score_match(sigA, sigR)
    scoreB, breakdownB = score_match(sigB, sigR)

    print("\n----- MATCH RESULTS -----")
    print("Score for Matrix A:", scoreA)
    print("Score for Matrix B:", scoreB)

    if scoreA > scoreB:
        print("\n👉 BEST MATCH = MATRIX A")
    elif scoreB > scoreA:
        print("\n👉 BEST MATCH = MATRIX B")
    else:
        print("\n👉 BOTH MATCH EQUALLY")

    # show detailed breakdowns so you can verify why it chose
    print_breakdown("Matrix A", sigA, breakdownA)
    print_breakdown("Matrix B", sigB, breakdownB)
    print_breakdown("Result", sigR, {"raw_matches": "-", "reduced_matches": "-", "pair_matches": "-", "total_match": "-", "repeat_credit_units": "-", "score": "-"})
