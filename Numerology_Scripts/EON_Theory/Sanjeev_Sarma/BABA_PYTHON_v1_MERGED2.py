# ============================================================
# BABA PYTHON v1.0 (MERGED - FIXED)
# EPM MODI + NEWSANJEEVI Unified Prediction Engine
# ============================================================
from pathlib import Path
import sys

# ------------------ HELPER FUNCTIONS ------------------

def digit_reduce(suma, sumb):
    """Custom reduction logic: adds two numbers and reduces to single digit if needed."""
    tmpA = suma + sumb
    if tmpA > 9:
        sumtemp = 0
        for i in list(str(tmpA)):
            sumtemp += int(i)
        return sumtemp
    else:
        return int(tmpA)

def sum4(suma, sumb, sumc, sumd):
    """Reduces 4 numbers down to a single digit."""
    tmpA = suma + sumb + sumc + sumd
    while tmpA > 9:
        tmpA = sum(int(i) for i in str(tmpA))
    return tmpA

def convert2int(ilist):
    s = [str(i) for i in ilist]
    res = "".join(s)
    return int(res)

def convert2list(string):
    return list(string)

def subtract_logic(suma, sumb):
    tmpA = suma - sumb
    if tmpA <= 0:
        return 9 + tmpA
    return int(tmpA)

def get_wl_table(a, b):
    winA = 9 if (a - 1) == 0 else (a - 1)
    lossA = 1 if (a + 1) == 10 else (a + 1)
    winB = 9 if (b - 1) == 0 else (b - 1)
    lossB = 1 if (b + 1) == 10 else (b + 1)
    return winA, winB, lossA, lossB

def subtract90(a):
    if a > 90:
        b = 9 - abs(90 - a)
        c = str(b).zfill(2) if b != 0 else "09"
    else:
        b = 90 - a
        c = str(b).zfill(2) if b != 0 else "09"
    
    clist = list(c)
    return digit_reduce(int(clist[0]), int(clist[1]))

# ------------------ DATA TABLES ------------------

def get_battlefield_value(A, B):
    db = {11:5129, 22:8343, 33:8638, 12:4784, 23:6856, 34:7255, 13:4967, 24:3593, 35:2536,
          14:8383, 25:2976, 36:3599, 15:6542, 26:2259, 37:1165, 16:2734, 27:1824, 38:3981,
          17:2465, 28:5229, 39:2165, 18:4611, 29:7187, 19:9335, 44:6969, 55:2254, 66:3239,
          45:1487, 56:5316, 67:8769, 46:7377, 57:5612, 68:1598, 47:7313, 58:4518, 69:4874,
          48:4888, 59:2384, 88:6479, 49:2999, 77:3655, 99:9635, 78:7161, 89:4293, 79:6354}
    return db.get(A*10+B) or db.get(B*10+A)

def get_win_max_value(A, B):
    win_max = {19:5662, 11:5382, 12:2172, 28:737, 29:3324, 39:4701, 37:4882, 38:7421, 48:2077,
               46:7670, 47:3108, 57:1254, 55:3703, 56:5105, 66:3636, 13:7353, 14:8482, 15:6687,
               22:3077, 23:1828, 24:636, 49:321, 59:5481, 33:4501, 58:7712, 68:6276, 69:8355,
               67:3551, 77:4120, 78:5168, 16:6850, 17:2673, 18:5882, 25:6612, 26:2888, 27:8678,
               34:1438, 35:2517, 36:6093, 79:2330, 44:7178, 45:8115, 88:2214, 89:845, 99:9867}
    return win_max.get(A*10+B) or win_max.get(B*10+A)

# ------------------ MAIN ENGINE ------------------

def run_newsanjeevi_full():
    try:
        log_file = Path(__file__).parent / (Path(__file__).stem + '.log')
        with open(log_file, 'w') as f:
            p1 = input('Enter Player A Date of Birth (DD-MM-YYYY): ')
            p2 = input('Enter Player B Date of Birth (DD-MM-YYYY): ')
            p3 = input('Enter Game of Day (DD-MM-YYYY): ')

            # Parse Dates
            A_list = p1.split("-")
            B_list = p2.split("-")
            C_list = p3.split("-")

            # Calculation for Player A
            ares = list(A_list[0])
            atotal = sum(int(i) for i in ares) + sum(int(i) for i in A_list[1]) + sum(int(i) for i in A_list[2])
            intTotalA = int(A_list[0]) + atotal
            TotalA = list(str(intTotalA).zfill(2))
            
            PlayerA_Count = digit_reduce(int(TotalA[0]), int(TotalA[1]))
            print(f"Player A Count: {PlayerA_Count}", file=f)

            # Calculation for Player B
            b1res = list(B_list[0])
            btotal = sum(int(i) for i in b1res) + sum(int(i) for i in B_list[1]) + sum(int(i) for i in B_list[2])
            intTotalB = int(B_list[0]) + btotal
            TotalB = list(str(intTotalB).zfill(2))

            PlayerB_Count = digit_reduce(int(TotalB[0]), int(TotalB[1]))
            print(f"Player B Count: {PlayerB_Count}", file=f)

            # Logic for Combined Matrix
            wA, wB, lA, lB = get_wl_table(PlayerA_Count, PlayerB_Count)
            rA = digit_reduce(wA, lA)
            rB = digit_reduce(wB, lB)
            
            print("======== Combined Matrix =========", file=f)
            print("{:<8} {:<15} {:<10}".format(PlayerA_Count, wA, lA), file=f)
            print("{:<8} {:<15} {:<10}".format(PlayerB_Count, wB, lB), file=f)

            # Table Lookups
            bf_val = get_battlefield_value(PlayerA_Count, PlayerB_Count)
            wm_val = get_win_max_value(PlayerA_Count, PlayerB_Count)

            print(f"Battlefield Value: {bf_val}", file=f)
            print(f"Win Max Value: {wm_val}", file=f)
            
            print("\nProcessing complete. Check the log file for full details.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_newsanjeevi_full()