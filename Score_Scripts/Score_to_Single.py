# ----------------------------------------
# Cricket Score Numerology Transformation (Exact Multi-Step)
# ----------------------------------------

def reduce_digit(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def derive_final_two_digit(score_input):
    # Step 0: parse input
    abc, x = score_input.split('/')
    A = int(abc[0])
    B = int(abc[1])
    C = int(abc[2])
    X = int(x)

    # Step 1: A+B+C -> Y
    Y = reduce_digit(A + B + C)

    # Step 2: 11 - Y -> Z
    Z = reduce_digit(11 - Y)

    # Step 3: X + Z -> D
    D = reduce_digit(X + Z)

    # Step 4: ABCD
    ABCD = [A,B,C,D]

    # Step 5: Convert ABCD to numerology style
    A_new = 9 + ABCD[0]  # 9 + A
    B_new = 9 + ABCD[1]  # 9 + B
    C_new = 9 + ABCD[2]  # 9 + C
    D_new = 9 + ABCD[3]  # 9 + D
    ABCD_new = [A_new, B_new, C_new, D_new]

    # Step 6: Derive 3-digit number
    first = (ABCD_new[0] - ABCD_new[1]) % 9 or 9
    second = (ABCD_new[1] - ABCD_new[2]) % 9 or 9
    third = (ABCD_new[2] - ABCD_new[3]) % 9 or 9
    three_digit = [first, second, third]

    # Step 7: Convert 3-digit -> final 2-digit
    final_first = reduce_digit(first + second)
    final_second = reduce_digit(second + third)
    final_two_digit = int(f"{final_first}{final_second}")

    # Return full info
    return {
        "Y (A+B+C reduced)": Y,
        "Z (11-Y reduced)": Z,
        "D (X+Z reduced)": D,
        "ABCD": ABCD,
        "ABCD_new (9+ each)": ABCD_new,
        "3-digit": three_digit,
        "Final 2-digit": final_two_digit
    }

# ------------------------ MAIN ------------------------
if __name__ == "__main__":
    score_input = input("Enter score in ABC/X format (e.g. 145/7): ").strip()
    result = derive_final_two_digit(score_input)

    print("\n--- Numerology Transformation ---")
    for k,v in result.items():
        print(f"{k}: {v}")
