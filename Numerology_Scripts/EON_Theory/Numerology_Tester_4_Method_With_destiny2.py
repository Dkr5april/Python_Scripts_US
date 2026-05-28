from datetime import datetime, timedelta
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch 
import math

# Initialize colorama for colored console output
init(autoreset=True)

# --- Global Definitions ---
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

# --- General & Risk Calculation Functions (Unchanged) ---
def reduce_to_single_digit(n):
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    if n in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    return n

def parse_dob(dob_str):
    day, month, year = map(int, dob_str.split('/'))
    return day, month, year

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

def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]

def calculate_destiny_number(full_name):
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum = 0
    for letter in name_clean:
        total_sum += PYTHAGOREAN_MAP.get(letter, 0)
    return reduce_to_single_digit(total_sum)

def get_day_vibe(date):
    return reduce_to_single_digit(date.day + date.month + date.year)

def eon_risk_score(chart, birth_root, life_path, date):
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

def destiny_alignment(date, destiny_number):
    day_vibe = get_day_vibe(date)
    destiny_num_reduced = reduce_to_single_digit(destiny_number)
    if day_vibe == destiny_num_reduced:
        return 0
    else:
        return 3

def pythagorean_destiny_hybrid(date, destiny_number):
    if get_day_vibe(date) == reduce_to_single_digit(destiny_number):
        return 0
    return pythagorean_vibe(date)

def chaldean_destiny_hybrid(date, destiny_number):
    if get_day_vibe(date) == reduce_to_single_digit(destiny_number):
        return 0
    return chaldean_vibe(date)

def kabbalah_destiny_hybrid(date, destiny_number):
    if get_day_vibe(date) == reduce_to_single_digit(destiny_number):
        return 0
    return kabbalah_vibe(date)

def get_all_risk_scores(date, chart, birth_root, life_path, destiny_num):
    scores = {}
    scores['E'] = eon_risk_score(chart, birth_root, life_path, date)
    scores['P'] = pythagorean_vibe(date)
    scores['K'] = kabbalah_vibe(date)
    scores['C'] = chaldean_vibe(date)
    scores['D'] = destiny_alignment(date, destiny_num)
    scores['PD'] = pythagorean_destiny_hybrid(date, destiny_num)
    scores['KD'] = kabbalah_destiny_hybrid(date, destiny_num)
    scores['CD'] = chaldean_destiny_hybrid(date, destiny_num)
    return scores

# --- CONSOLE DISPLAY FUNCTION (Separated Vertical Blocks) ---
def print_detailed_day_result(day_date, chart, birth_root, life_path, destiny_num):
    """Prints the detailed, separated scores for a single day."""
    
    day = day_date.day
    day_name = calendar.day_abbr[day_date.weekday()]
    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
    
    def get_colored_letter(letter, score):
        color, _ = RISK_MAP[score]
        return f"{color}{letter}{Style.RESET_ALL}"
    
    # 1. DAILY SUMMARY
    print(Style.BRIGHT + Fore.YELLOW + f"| DATE: {day:2d} | DAY: {day_name:3s} |")
    print("-" * 20)

    # 2. NATAL CHART (EON)
    e_code = get_colored_letter('EON', scores['E'])
    print(f"| NATAL CHART: {e_code:3s} (Row 1, Col 1) | Score: {scores['E']}")
    print("-" * 40)

    # 3. UNIVERSAL VIBE (P, K, C)
    p_code = get_colored_letter('P', scores['P'])
    k_code = get_colored_letter('K', scores['K'])
    c_code = get_colored_letter('C', scores['C'])
    print(f"| UNIVERSAL VIBE | Pyt: {p_code} (Row 1, Col 2) | Score: {scores['P']}")
    print(f"|                | Kab: {k_code} (Row 2, Col 1) | Score: {scores['K']}")
    print(f"|                | Cha: {c_code} (Row 2, Col 2) | Score: {scores['C']}")
    print("-" * 40)
    
    # 4. DESTINY ALIGNMENT (D, P.D, K.D, C.D)
    d_code = get_colored_letter('D', scores['D'])
    pd_code = get_colored_letter('PD', scores['PD'])
    kd_code = get_colored_letter('KD', scores['KD'])
    cd_code = get_colored_letter('CD', scores['CD'])
    print(f"| DESTINY ALIGN. | Sim: {d_code} (Row 3, Col 1) | Score: {scores['D']}")
    print(f"|                | P.D: {pd_code} (Row 3, Col 2) | Score: {scores['PD']}")
    print(f"|                | K.D: {kd_code} (Row 4, Col 1) | Score: {scores['KD']}")
    print(f"|                | C.D: {cd_code} (Row 4, Col 2) | Score: {scores['CD']}")
    print(Fore.RESET + "=" * 40 + "\n")


def display_console_output(chart, birth_root, life_path, start_date, view_option, destiny_num):
    """Controls the loop for displaying Day, Week, or Month results using the separated blocks."""
    
    print(Style.BRIGHT + Fore.CYAN + "\n--- Detailed Daily Verification Output ---")
    print(Style.BRIGHT + "Risk Key: 🟢 Good (0), 🟡 Low (1), 🔵 Medium (2), 🔴 High (3)")
    
    # DOT GRID LEGEND (For reference to the PDF output)
    print(Style.BRIGHT + Fore.MAGENTA + "\nDOT GRID LEGEND (PDF 4 Rows, 2 Columns):")
    print("| R1: EON (E) | Pythagorean (P) | R2: Kabbalah (K) | Chaldean (C) |")
    print("| R3: Destiny (D) | Pythagorean Hybrid (P.D) | R4: Kabbalah Hybrid (K.D) | Chaldean Hybrid (C.D) |")
    print(Fore.RESET + "=" * 80)
    
    if view_option == 'day':
        # Single Day
        print_detailed_day_result(start_date, chart, birth_root, life_path, destiny_num)
        
    elif view_option == 'week':
        # Single Week (7 days starting from the selected date)
        print(Style.BRIGHT + Fore.BLUE + f"--- Displaying Week starting {start_date.strftime('%Y-%m-%d')} ---")
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            print_detailed_day_result(current_date, chart, birth_root, life_path, destiny_num)
            
    elif view_option == 'month':
        # Full Month (Using the separated blocks for maximum clarity)
        print(Style.BRIGHT + Fore.BLUE + f"--- Displaying Full Month of {calendar.month_name[start_date.month]} {start_date.year} ---")
        num_days = calendar.monthrange(start_date.year, start_date.month)[1]
        for day in range(1, num_days + 1):
            try:
                current_date = datetime(start_date.year, start_date.month, day)
                print_detailed_day_result(current_date, chart, birth_root, life_path, destiny_num)
            except ValueError:
                continue
    else:
        print(Fore.RED + "Internal Error: Invalid view option.")


# --- PDF GENERATION FUNCTION (Detailed Multi-System Grid - Flexible Years) ---
def generate_multi_system_pdf(name, dob_str, start_year, num_years, destiny_num):
    """Generates the detailed calendar with 8 colored dots per day for flexible number of years."""
    
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)

    end_year = start_year + num_years - 1
    filename = f"MultiSystem_Calendar_{start_year}_{end_year}_{num_years}yrs_DETAILED.pdf"
    
    # PDF setup logic (identical to previous version)
    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.5 * inch
    day_cell_size = 0.4 * inch
    dot_size = 0.05 * inch
    
    # Title and Key
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - margin, f"Detailed {num_years}-Year Multi-System Numerology Calendar: {name} ({dob_str})")
    c.setFont("Helvetica", 8)
    legend_y = height - 1.2 * inch
    c.drawString(margin, legend_y, "KEY: E=EON, P=Pythagorean, K=Kabbalah, C=Chaldean, D=Destiny, P.D/K.D/C.D=Hybrids. | Colors: G=0, Y=1, B=2, R=3")
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, legend_y - 0.2 * inch, "DOT GRID: R1: (E, P) | R2: (K, C) | R3: (D, P.D) | R4: (K.D, C.D)")
    
    current_page_year_count = 0
    
    for year_offset in range(num_years):
        current_year = start_year + year_offset
        
        if current_page_year_count >= 4:
            c.showPage()
            current_page_year_count = 0
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width / 2, height - margin, f"Detailed {num_years}-Year Multi-System Numerology Calendar: {name} ({dob_str}) (Cont.)")
        
        year_x_start = margin + current_page_year_count * (width - 2 * margin) / 4
        year_width = (width - 2 * margin) / 4
        month_col_width = year_width / 12
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(year_x_start, height - 1.7 * inch, str(current_year))
        
        month_row_y = height - 1.9 * inch
        
        for month_num in range(1, 13):
            month_name = calendar.month_abbr[month_num]
            month_x_start = year_x_start + (month_num - 1) * month_col_width
            
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(month_x_start + day_cell_size / 2, month_row_y, month_name)
            
            for i, wd in enumerate(calendar.day_abbr):
                c.setFont("Helvetica", 5)
                c.drawString(month_x_start + i * day_cell_size + 0.01*inch, month_row_y - 0.1 * inch, wd[0])

            current_day_y = month_row_y - 0.25 * inch
            cal_iter = calendar.Calendar(firstweekday=calendar.MONDAY).itermonthdays2(current_year, month_num)
            
            for day, weekday in cal_iter:
                if day != 0:
                    day_date = datetime(current_year, month_num, day)
                    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
                    
                    cell_x = month_x_start + weekday * day_cell_size
                    
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica-Bold", 6)
                    c.drawCentredString(cell_x + day_cell_size / 2, current_day_y + day_cell_size * 0.7, str(day))

                    color_names = [RISK_MAP[scores['E']][1], RISK_MAP[scores['P']][1],
                                   RISK_MAP[scores['K']][1], RISK_MAP[scores['C']][1],
                                   RISK_MAP[scores['D']][1], RISK_MAP[scores['PD']][1],
                                   RISK_MAP[scores['KD']][1], RISK_MAP[scores['CD']][1]]
                    
                    for i, color_name in enumerate(color_names):
                        row = i // 2 
                        col = i % 2  
                        
                        color = getattr(colors, color_name, colors.black)
                        
                        dot_x = cell_x + col * (dot_size * 2) + 0.1 * inch
                        dot_y = current_day_y + day_cell_size * 0.45 - row * (dot_size * 2)
                        
                        c.setFillColor(color)
                        c.rect(dot_x, dot_y, dot_size, dot_size, fill=1)

                if weekday == 6:
                    current_day_y -= day_cell_size
            
            month_row_y = current_day_y - day_cell_size
            
        current_page_year_count += 1

    c.save()
    print(f"\n✅ Detailed Multi-System PDF saved as {filename}")


# --- Main Execution ---
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Multi-System Numerology Calendar Generator ---")
    
    # 1. Gather Inputs
    name = input("Enter Full Name: ")
    dob_input = input("Enter DOB (DD/MM/YYYY): ")
    
    try:
        day, m, y = parse_dob(dob_input)
    except ValueError:
        print(Fore.RED + "Invalid DOB format. Exiting.")
        exit()
        
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)
    destiny_num = calculate_destiny_number(name)
    print(Fore.GREEN + f"-> Destiny Number is {destiny_num}. All 7 Systems are calculated.")
    
    # --- Screen Output Granularity Input ---
    while True:
        view_option = input("View screen output for [D]ay, [W]eek, or [M]onth? (D/W/M - All use separated vertical blocks): ").lower()
        if view_option in ['d', 'w', 'm']:
            if view_option == 'd': view_option = 'day'
            elif view_option == 'w': view_option = 'week'
            elif view_option == 'm': view_option = 'month'
            break
        print(Fore.RED + "Invalid option. Please enter D, W, or M.")

    # --- Screen Date Input ---
    while True:
        try:
            screen_date_str = input("Enter START Date for Screen Display (DD/MM/YYYY, or leave blank for today): ")

            if not screen_date_str:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"-> Using current date: {start_date.strftime('%Y-%m-%d')}")
            else:
                d, mo, yr = parse_dob(screen_date_str)
                start_date = datetime(yr, mo, d)
            break
        except ValueError:
            print(Fore.RED + "Invalid date format. Please use DD/MM/YYYY.")

    # 2. Display Detailed Console Output
    display_console_output(chart, birth_root, life_path, start_date, view_option, destiny_num)

    # 3. PDF Generation Control
    pdf_generate_choice = input(Fore.BLUE + "Do you want to generate the DETAILED Multi-System PDF? (y/n): ").lower()
    
    if pdf_generate_choice == 'y':
        while True:
            try:
                pdf_start_year = int(input("Enter START Year for the Detailed PDF (YYYY): "))
                years_to_generate_input = input(f"Enter number of years to generate (e.g., 50): ")
                
                if not years_to_generate_input:
                     years_to_generate = 50
                else:
                    years_to_generate = int(years_to_generate_input)
                
                if years_to_generate <= 0:
                    print(Fore.RED + "Number of years must be positive.")
                    continue
                
                print(f"-> Generating detailed calendar for {years_to_generate} years, starting {pdf_start_year}.")
                generate_multi_system_pdf(name, dob_input, pdf_start_year, years_to_generate, destiny_num)
                break
            except ValueError:
                print(Fore.RED + "Invalid year or number of years format.")
    else:
        print(Fore.YELLOW + "PDF generation skipped. Displayed data is for screen verification only.")