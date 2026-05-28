# --- FULL DEBUG SCRIPT: EON_Differential_Pair_Analysis.py (Use this version) ---
from datetime import datetime, timedelta
import calendar
from colorama import Fore, Style, init
import sys
import math

# --- Setup and Mapping (UNCHANGED) ---
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

init(autoreset=True)

RISK_MAP = {
    0: (Fore.GREEN, 'green'),
    1: (Fore.YELLOW, 'yellow'),
    2: (Fore.BLUE, 'blue'),
    3: (Fore.RED, 'red')
}

PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1, 'B': 2, 'K': 2, 'T': 2, 'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4, 'E': 5, 'N': 5, 'W': 5, 'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7, 'H': 8, 'Q': 8, 'Z': 8, 'I': 9, 'R': 9
}
CHALDEAN_MAP = {
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
    'B': 2, 'K': 2, 'R': 2, 'C': 3, 'G': 3, 'L': 3, 'S': 3,
    'D': 4, 'M': 4, 'T': 4, 'E': 5, 'H': 5, 'N': 5, 'X': 5,
    'U': 6, 'V': 6, 'W': 6, 'O': 7, 'Z': 7, 'F': 8, 'P': 8
}
KABBALAH_MAP = PYTHAGOREAN_MAP # Using Pythagorean map

# --- Utility Functions (UNCHANGED) ---
def reduce_to_single_digit(n):
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    if n in [11, 22, 33]:
        # Handle master numbers by reducing to single digit for final comparison
        n = sum(int(d) for d in str(n)) 
    return n

def parse_dob(dob_str):
    dob_str = dob_str.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(dob_str, fmt)
            return dt.day, dt.month, dt.year
        except:
            pass
    parts = dob_str.replace('-', '/').replace('.', '/').split('/')
    if len(parts) == 3:
        d, m, y = parts
        return int(d), int(m), int(y if len(y) == 4 else int(y) + (1900 if int(y) > 30 else 2000))
    raise ValueError("Invalid date format")

def get_birth_root(day):
    return reduce_to_single_digit(day)

def get_life_path(day, month, year):
    total = reduce_to_single_digit(day) + reduce_to_single_digit(month) + reduce_to_single_digit(year)
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def get_3x3_chart(day, month, year):
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}

def get_day_vibe(date):
    total = date.day + date.month + date.year
    return reduce_to_single_digit(total)

# --- DEBUG CODE ADDED HERE (Name Sums) ---
def calculate_all_destiny_numbers(full_name):
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    
    # PYTHAGOREAN
    total_sum_p = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    dn_p = reduce_to_single_digit(total_sum_p)

    # CHALDEAN
    total_sum_c = sum(CHALDEAN_MAP.get(letter, 0) for letter in name_clean)
    dn_c = reduce_to_single_digit(total_sum_c)

    # KABBALAH
    total_sum_k = sum(KABBALAH_MAP.get(letter, 0) for letter in name_clean)
    dn_k = reduce_to_single_digit(total_sum_k)
    
    # !!! NEW DEBUG PRINT !!!
    #print(Fore.RED + f"  [SUM DEBUG] {full_name}: P={total_sum_p}(->{dn_p}), C={total_sum_c}(->{dn_c}), K={total_sum_k}(->{dn_k})")
    # !!! END DEBUG PRINT !!!

    return dn_p, dn_c, dn_k
# --- END DEBUG CODE ---

# --- Risk Score Functions (UNCHANGED) ---
def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]

def eon_risk_score(chart, birth_root, date):
    missing = missing_numbers(chart)
    icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month)
    icc_year = reduce_to_single_digit(date.year)
    score = 0
    if icc_day == reduce_to_single_digit(birth_root) and icc_day in missing: score += 2
    if icc_day in missing: score += 1
    if icc_month in missing: score += 1
    if icc_year in missing: score += 1
    if score == 0: return 0
    elif score in [1, 2]: return 1
    elif score in [3, 4]: return 2
    else: return 3

def pythagorean_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 9]: return 0
    elif vibe in [2, 6, 7]: return 1
    else: return 3

def chaldean_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [1, 3, 5, 6, 9]: return 0
    elif vibe in [7]: return 1
    else: return 3

def kabbalah_vibe(date):
    vibe = get_day_vibe(date)
    if vibe in [3, 6, 9]: return 0
    elif vibe in [1, 5]: return 1
    else: return 3
    
def destiny_alignment(date, dn_p):
    day_vibe = get_day_vibe(date)
    return 0 if day_vibe == dn_p else 3

def pythagorean_destiny_hybrid(date, dn_p):
    if get_day_vibe(date) == dn_p:
        return 0
    return pythagorean_vibe(date)

def chaldean_destiny_hybrid(date, dn_c):
    if get_day_vibe(date) == dn_c:
        return 0
    return chaldean_vibe(date)

def kabbalah_destiny_hybrid(date, dn_k):
    if get_day_vibe(date) == dn_k:
        return 0
    return kabbalah_vibe(date)

# --- DEBUG CODE ADDED HERE (Score Inputs) ---
def get_all_risk_scores(date, chart, birth_root, destiny_nums, name):
    dn_p, dn_c, dn_k = destiny_nums 
    scores = {}
    
    # DEBUG PRINT: Verify inputs for unique systems
    #print(Fore.BLUE + f"  [DEBUG] Calculating scores for: {name}")
    #print(Fore.BLUE + f"  [DEBUG]   Birth Root: {birth_root}, DNs (P/C/K): {dn_p}/{dn_c}/{dn_k}")
    #print(Fore.BLUE + f"  [DEBUG]   Missing Numbers: {missing_numbers(chart)}")

    scores['E'] = eon_risk_score(chart, birth_root, date)
    scores['P'] = pythagorean_vibe(date)
    scores['K'] = kabbalah_vibe(date)
    scores['C'] = chaldean_vibe(date)
    
    scores['D'] = destiny_alignment(date, dn_p)
    scores['PD'] = pythagorean_destiny_hybrid(date, dn_p)
    scores['KD'] = kabbalah_destiny_hybrid(date, dn_k) 
    scores['CD'] = chaldean_destiny_hybrid(date, dn_c)
    
    # DEBUG PRINT: Print final scores before returning
    #print(Fore.BLUE + f"  [DEBUG]   Scores: {scores}")
    #print(Fore.BLUE + f"  [DEBUG]   Total Sum: {sum(scores.values())}" + Style.RESET_ALL)
    
    return scores
# --- END DEBUG CODE ---

# -------------------------
# NEW: Differential Report Generator
# -------------------------

SYSTEM_KEYS = ['E','P','K','C','D','PD','KD','CD']
SYSTEM_NAMES = {
    'E': 'EON', 'P': 'Pythagorean Vibe', 'K': 'Kabbalah Vibe', 'C': 'Chaldean Vibe',
    'D': 'Destiny Align', 'PD': 'P. Destiny Hybrid', 'KD': 'K. Destiny Hybrid', 'CD': 'C. Destiny Hybrid'
}

def generate_differential_report(person_data_list, target_dates):
    
    print(Style.BRIGHT + Fore.MAGENTA + "\n=== FIXED PAIRWISE DIFFERENTIAL ANALYSIS REPORT ===" + Style.RESET_ALL)
    
    if len(person_data_list) % 2 != 0:
        print(Fore.RED + "\nWarning: Odd number of individuals. The last person will be ignored.")
        person_data_list = person_data_list[:-1]

    num_pairs = len(person_data_list) // 2
    
    for date in target_dates:
        date_str = date.strftime('%d/%m/%Y (%a)')
        # DEBUG PRINT: Universal Vibe
        day_vibe = get_day_vibe(date)
        print(Style.BRIGHT + Fore.CYAN + f"\n════════ TARGET DATE: {date_str} (Day Vibe: {day_vibe}) ════════" + Style.RESET_ALL)
        
        # Print Table Header
        header = f"{'Pair':<10} | {'Pair Members':<30} | {'Overall Advantage':<25} | {'Sum A / Sum B':<15} | {'Key Differential Systems (A/B Score)'}"
        print(Fore.YELLOW + "-"*110 + Style.RESET_ALL)
        print(Fore.YELLOW + header + Style.RESET_ALL)
        print(Fore.YELLOW + "-"*110 + Style.RESET_ALL)

        for i in range(num_pairs):
            A = person_data_list[2*i]
            B = person_data_list[2*i + 1]
            
            # 1. Calculate Scores and Sums (Passing 'name' for debug print)
            # The DN calculation print (SUM DEBUG) happens here:
            scores_A = get_all_risk_scores(date, A['chart'], A['birth_root'], A['destiny_nums'], A['name'])
            scores_B = get_all_risk_scores(date, B['chart'], B['birth_root'], B['destiny_nums'], B['name'])
            sum_A = sum(scores_A.values())
            sum_B = sum(scores_B.values())
            
            # 2. Determine Advantage
            if sum_A < sum_B:
                advantage_name = A['name']
                adv_color = Fore.GREEN
            elif sum_B < sum_A:
                advantage_name = B['name']
                adv_color = Fore.RED
            else:
                advantage_name = "Neutral"
                adv_color = Fore.BLUE
                
            advantage_display = f"{advantage_name} (Lower Sum is Better)"
            
            # 3. Find Differential Systems
            differential_systems = []
            for key in SYSTEM_KEYS:
                score_A = scores_A[key]
                score_B = scores_B[key]
                
                if score_A != score_B:
                    # Format: System Key (A_Score/B_Score)
                    color_A = RISK_MAP[score_A][0]
                    color_B = RISK_MAP[score_B][0]
                    
                    diff_str = f"{key}({color_A}{score_A}{Style.RESET_ALL}/{color_B}{score_B}{Style.RESET_ALL})"
                    differential_systems.append(diff_str)
                    
            # 4. Print Row
            pair_label = f"Pair {i+1}"
            members_label = f"{A['name']} vs {B['name']}"
            sums_label = f"{sum_A:02d} / {sum_B:02d}"
            
            row = (
                f"{pair_label:<10} | {members_label:<30} | "
                f"{adv_color}{advantage_display:<25}{Style.RESET_ALL} | "
                f"{sums_label:<15} | {' '.join(differential_systems)}"
            )
            print(row)
            
        print(Fore.CYAN + "="*110 + Style.RESET_ALL)


# -------------------------
# MAIN CLI LOGIC (UNCHANGED)
# -------------------------
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Fixed Pairwise Differential Numerology Analysis ---")

    person_data_list = []

    # 1. Gather all individuals (Group must be even, preferably 10)
    print(Style.BRIGHT + Fore.YELLOW + "\n--- Enter Individual Data (Group Analysis) ---" + Style.RESET_ALL)
    print("Format: Name,DD/MM/YYYY. Enter data in pairs (A, then B, then C, then D, etc.).")
    print("Enter a blank line when finished.")
    
    i = 1
    while True:
        line = input(f"Individual {i} (Name, DOB): ").strip()
        if not line:
            break

        try:
            name_str, dob_str = line.split(',')
            name = name_str.strip()
            dob_input = dob_str.strip()
            
            day, m, y = parse_dob(dob_input)
            
            chart = get_3x3_chart(day, m, y)
            birth_root = get_birth_root(day)
            
            # The critical function call where DNs are calculated:
            destiny_nums = calculate_all_destiny_numbers(name)
            
            person_data_list.append({
                'name': name,
                'dob': dob_input,
                'chart': chart,
                'birth_root': birth_root,
                'destiny_nums': destiny_nums
            })
            
            print(Fore.GREEN + f"-> Added {name} (P:{destiny_nums[0]}, C:{destiny_nums[1]}, K:{destiny_nums[2]})" + Style.RESET_ALL)
            i += 1

        except ValueError:
            print(Fore.RED + "Invalid format or DOB. Please use 'Name,DD/MM/YYYY'.")
            
    if len(person_data_list) < 2:
        print(Fore.RED + "Must enter at least two individuals for comparison. Exiting.")
        exit()
    if len(person_data_list) % 2 != 0:
        print(Fore.RED + f"Warning: Entered {len(person_data_list)} individuals. Last person will be ignored.")


    # 2. Gather Target Dates
    print(Style.BRIGHT + Fore.YELLOW + "\n--- Enter Target Dates for Analysis ---" + Style.RESET_ALL)
    dates_input = input("Enter one or more target dates separated by commas (DD/MM/YYYY,DD/MM/YYYY,... or blank for today): ")
    
    target_dates = []
    if not dates_input:
        target_dates.append(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        print(f"-> Using current date: {target_dates[0].strftime('%Y-%m-%d')}")
    else:
        for dstr in dates_input.split(","):
            dstr = dstr.strip()
            if not dstr: continue
            try:
                d, mo, yr = parse_dob(dstr)
                target_dates.append(datetime(yr, mo, d))
            except Exception as e:
                print(Fore.RED + f"Skipping invalid date: {dstr}")
                
    if not target_dates:
        print(Fore.RED + "No valid target dates entered. Exiting.")
        exit()

    # 3. Generate Report
    generate_differential_report(person_data_list, target_dates)