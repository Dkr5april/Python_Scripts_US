# EON_BeautifulOutput_final_3_months_per_row.py
from datetime import datetime, timedelta
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import sys
import os
import math

# Ensure UTF-8 on Windows consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

init(autoreset=True)

# -------------------------
# Calculation logic (unchanged)
# -------------------------
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

def reduce_to_single_digit(n):
    while n > 9 and n not in [11, 22, 33]:
        n = sum(int(d) for d in str(n))
    if n in [11, 22, 33]:
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

def get_overall_risk_for_bar(scores):
    # Calculate the average score across all 8 systems (E, P, K, C, D, PD, KD, CD)
    total_score = sum(scores.values())
    average_score = total_score / len(scores)
    # Map the average to the closest integer risk level (0, 1, 2, 3).
    overall_risk = int(math.ceil(average_score))
    # Ensure it's within the 0-3 range
    overall_risk = min(3, max(0, overall_risk))
    
    return overall_risk, RISK_MAP[overall_risk][0] # Returns score (0-3) and colorama color

# -------------------------
# Console output helpers (using large block art - left as is)
# -------------------------

def print_large_block_day_result(day_date, chart, birth_root, life_path, destiny_num):
    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
    
    # 1. Get Overall Risk for the big bar
    overall_risk, overall_color = get_overall_risk_for_bar(scores)
    
    # 2. Map system scores to colors/blocks
    keys = ['E','P','K','C','D','PD','KD','CD']
    risk_colors = [RISK_MAP[scores[k]][0] for k in keys]

    # Block art characters
    BLOCK_FULL = "█"
    EMPTY_SPACE = " "
    
    # --- Line 1 (Top Half) ---
    line1 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    # Overall Score (Large box with number inside)
    overall_box_width = 11
    line1_overall = (
        overall_color + Style.BRIGHT + BLOCK_FULL * overall_box_width
    )
    line1 += f"{line1_overall}{Fore.CYAN} │{Style.RESET_ALL} {Style.BRIGHT + Fore.WHITE}SYSTEM SCORES:{Style.RESET_ALL} "
    
    # System 1 to 4 (EON, PYT, KAB, CHL) - Using full block for visual consistency
    for i in range(4):
        line1 += f"{risk_colors[i]}{BLOCK_FULL}{Style.RESET_ALL}"
        line1 += f"{Fore.CYAN} {keys[i]} {Style.RESET_ALL}"
    line1 += f"{Fore.CYAN}│{Style.RESET_ALL}"
    
    # --- Line 2 (Bottom Half) ---
    line2 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    # Overall Score - Date and Day
    date_str = day_date.strftime('%Y-%m-%d %a')
    date_padded = f" {date_str} ".center(overall_box_width)
    line2_overall = overall_color + Style.BRIGHT + date_padded + Style.RESET_ALL
    line2 += f"{line2_overall}{Fore.CYAN} │{Style.RESET_ALL} "
    
    # System 5 to 8 (DEST, P.D, K.D, C.D)
    for i in range(4, 8):
        line2 += f"{risk_colors[i]}{BLOCK_FULL}{Style.RESET_ALL}"
        line2 += f"{Fore.CYAN} {keys[i]} {Style.RESET_ALL}"
    line2 += f"{Fore.CYAN}│{Style.RESET_ALL}"

    # --- Line 3 (Score Line) ---
    line3 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    # Overall Score - Actual Score
    score_display = f" SCORE: {overall_risk} ".center(overall_box_width)
    line3_overall = overall_color + Style.BRIGHT + score_display + Style.RESET_ALL
    line3 += f"{line3_overall}{Fore.CYAN} │{Style.RESET_ALL} "
    
    # Risk Legend (Aligned to systems)
    risk_legend = f" {Fore.GREEN}0 {Fore.YELLOW}1 {Fore.BLUE}2 {Fore.RED}3{Style.RESET_ALL}"
    # Calculate required padding
    legend_content_width = 24 # Approximate width of "Risk: 0 1 2 3" and labels
    total_space_in_right_box = 45 # Based on the header
    padding_space = total_space_in_right_box - legend_content_width
    
    line3 += f"{Fore.CYAN}Risk: {risk_legend}{EMPTY_SPACE*(padding_space)}│{Style.RESET_ALL}"


    # --- Print Box Structure ---
    print(Fore.CYAN + "┌─────────────────────────┬───────────────────────────────────────────┐" + Style.RESET_ALL)
    print(line1)
    print(line2)
    print(line3)
    print(Fore.CYAN + "└─────────────────────────┴───────────────────────────────────────────┘" + Style.RESET_ALL)


def display_console_output(chart, birth_root, life_path, start_date, view_option, destiny_num):
    print(Style.BRIGHT + Fore.MAGENTA + "\n=== EON Multi-System Daily Risk Assessment (Large Blocks) ===" + Style.RESET_ALL)
    print(Fore.CYAN + "-"*75 + Style.RESET_ALL)
    
    if view_option == 'day':
        print_large_block_day_result(start_date, chart, birth_root, life_path, destiny_num)
        print()
    
    elif view_option == 'week':
        print(Fore.CYAN + f"--- Week starting {start_date.strftime('%Y-%m-%d')} ---" + Style.RESET_ALL)
        for i in range(7):
            d = start_date + timedelta(days=i)
            print_large_block_day_result(d, chart, birth_root, life_path, destiny_num)
        print()
        
    elif view_option == 'month':
        # Retained the previous month view for compactness, as a large block calendar would be too wide.
        year = start_date.year
        month = start_date.month
        cal = calendar.Calendar(firstweekday=6)  # Sunday-first
        month_name = calendar.month_name[month]
        print(Style.BRIGHT + Fore.CYAN + f"\n==== {month_name} {year} (Overall Risk Bar) ====")
        print(Style.DIM + "Legend: " + Fore.GREEN + "Good(0) " + Fore.YELLOW + "Low(1) " + Fore.BLUE + "Med(2) " + Fore.RED + "High(3)")
        weekdays = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
        header = " ".join(d.center(12) for d in weekdays)
        print(Style.BRIGHT + header)
        print("-"*len(header))
        weeks = list(cal.monthdayscalendar(year, month))
        
        BLOCK_CHAR = "█"
        BLOCK_WIDTH = 12
        
        for wk in weeks:
            line_dates = ""
            for d in wk:
                if d == 0:
                    line_dates += " ".center(BLOCK_WIDTH)
                else:
                    line_dates += f"{str(d).center(BLOCK_WIDTH)}"
            print(line_dates)
            
            line_blocks = ""
            for d in wk:
                if d == 0:
                    line_blocks += " ".center(BLOCK_WIDTH)
                else:
                    day_dt = datetime(year, month, d)
                    scores = get_all_risk_scores(day_dt, chart, birth_root, life_path, destiny_num)
                    
                    overall_risk, ansi_color = get_overall_risk_for_bar(scores)
                    
                    bar = ansi_color + Style.BRIGHT + (BLOCK_CHAR * BLOCK_WIDTH) + Style.RESET_ALL
                    line_blocks += bar 
                    
            print(line_blocks)
            print()
    else:
        print(Fore.RED + "Invalid view option.")

# -------------------------
# PDF generation (MODIFIED FOR 3 MONTHS PER ROW)
# -------------------------
def _rl_color(name):
    mapping = {
        'green': colors.HexColor("#2E7D32"),
        'yellow': colors.HexColor("#FBC02D"),
        'blue': colors.HexColor("#1976D2"),
        'red': colors.HexColor("#D32F2F"),
        'black': colors.black
    }
    return mapping.get(name, colors.black)

def generate_multi_system_pdf(name, dob_str, start_year, num_years, destiny_num):
    # parse DOB (reuse robust parser)
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)

    end_year = start_year + num_years - 1
    # Updated filename to reflect 3-month layout
    filename = f"MultiSystem_Beautiful_3x4_Aligned_{start_year}_{end_year}_{num_years}yrs.pdf"

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.35 * inch
    
    # --- KEY LAYOUT CHANGE: 3 columns (months) x 4 rows (months) ---
    num_cols = 3
    num_rows = 4
    box_w = (width - 2*margin) / num_cols
    box_h = (height - 2*margin - 0.8*inch) / num_rows

    header_space = 28  
    max_rows_per_month_grid = 6 

    for year_offset in range(num_years):
        current_year = start_year + year_offset

        # Header for page
        c.setFillColor(colors.HexColor("#0D47A1"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - margin + 6, f"{name} — Multi-System Calendar ({current_year})")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(margin, height - margin - 8, f"DOB: {dob_str}    Destiny: {destiny_num}")

        # Build all months in order 1..12 using calendar.monthdayscalendar (which is ordered)
        cal = calendar.Calendar(firstweekday=6)  # Sunday first
        for month_index in range(1, 13):
            # --- UPDATED POSITIONING LOGIC ---
            mrow = (month_index - 1) // num_cols # 0, 1, 2, 3
            mcol = (month_index - 1) % num_cols  # 0, 1, 2
            
            box_x = margin + mcol * box_w
            box_y = height - margin - 0.9*inch - (mrow+1) * box_h
            # --------------------------------

            # month title
            c.setFillColor(colors.HexColor("#263238"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(box_x + 6, box_y + box_h - 12, calendar.month_name[month_index])

            # weekday small headings
            c.setFont("Helvetica", 6)
            wd_w = box_w / 7.0
            for wi, wd in enumerate(calendar.day_abbr):
                tx = box_x + wi * wd_w + 4
                ty = box_y + box_h - 22
                c.drawString(tx, ty, wd[:1]) 

            # get week matrix for this month in correct order
            weeks = list(cal.monthdayscalendar(current_year, month_index))

            # compute cell size and inner padding 
            row_height = (box_h - header_space) / max_rows_per_month_grid
            cell_w = wd_w
            cell_h = row_height
            # inner drawing area
            inner_pad_x = 2
            inner_pad_y = 2
            cell_inner_w = cell_w - 2*inner_pad_x
            cell_inner_h = cell_h - 2*inner_pad_y

            # --- Dot parameters (Fixed Size for visibility) ---
            dot_radius = 2.8 
            DOT_LAYOUT_COLS = 2
            dot_v_step = dot_radius * 2.5  
            dot_h_step = dot_radius * 3.5  

            # Calculate total array dimensions
            array_width = dot_radius + dot_h_step + dot_radius
            
            # Calculate offsets to center the array within the cell's inner drawing area
            center_offset_x = (cell_inner_w - array_width) / 2.0
            top_dot_center_y_offset = 10 
            
            # draw days by row (weeks) and column (weekday) - preserves proper sequence
            for r, wk in enumerate(weeks):
                for ccol, d in enumerate(wk):
                    cell_x_base = box_x + ccol * cell_w 
                    cell_x = cell_x_base + inner_pad_x
                    cell_y_base = box_y + box_h - header_space - (r+1) * row_height
                    cell_y = cell_y_base + inner_pad_y
                    
                    if d == 0:
                        continue
                        
                    # draw the cell rectangle lightly
                    c.setStrokeColor(colors.lightgrey)
                    c.rect(cell_x_base + 2, cell_y_base + 2, cell_w - 4, cell_h - 4, fill=0, stroke=1)

                    # day number (small) - placed at the bottom of the cell
                    c.setFont("Helvetica-Bold", 7) 
                    c.setFillColor(colors.black)
                    c.drawString(cell_x + 2, cell_y + 2, str(d)) 

                    # compute scores
                    day_date = datetime(current_year, month_index, d)
                    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
                    keys = ['E','P','K','C','D','PD','KD','CD']

                    # Base Y for the top-most dot center
                    dot_y_start = cell_y_base + cell_h - top_dot_center_y_offset
                    
                    # Base X for the left-most dot center
                    dot_x_start = cell_x_base + center_offset_x + dot_radius
                    
                    # draw 4x2 dots:
                    for i, key in enumerate(keys):
                        rr = i // DOT_LAYOUT_COLS  # 0..3 (Row index)
                        cc = i % DOT_LAYOUT_COLS   # 0 or 1 (Column index)
                        
                        # Calculate center point of the dot
                        dot_x = dot_x_start + (cc * dot_h_step)
                        dot_y = dot_y_start - (rr * dot_v_step) # Subtract step to move down the rows
                        
                        color_name = RISK_MAP[scores[key]][1]
                        c.setFillColor(_rl_color(color_name))
                        c.circle(dot_x, dot_y, dot_radius, stroke=0, fill=1)

            # Draw outer border for the month box
            c.setStrokeColor(colors.black)
            c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)


        # legend bottom-left
        legend_x = margin
        legend_y = margin + 6
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(legend_x, legend_y + 20, "Legend (dots, left to right, top to bottom): EON, Pythagorean, Kabbalah, Chaldean, Destiny, P.Destiny, K.Destiny, C.Destiny")
        legend_items = [('Good', 'green'), ('Low', 'yellow'), ('Med', 'blue'), ('High', 'red')]
        lx = legend_x
        for label, cname in legend_items:
            c.setFillColor(_rl_color(cname))
            c.rect(lx, legend_y + 4, 10, 10, fill=1)
            c.setFillColor(colors.black)
            c.drawString(lx + 14, legend_y + 4, label)
            lx += 70

        # footer (timestamp)
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.grey)
        c.drawRightString(width - margin, margin - 2, f"Generated by EON — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        c.showPage()

    c.save()
    print(Fore.GREEN + f"\n✅ Beautiful PDF saved as {filename}" + Fore.RESET)

# -------------------------
# MAIN CLI (keeps your old flow + PDF call)
# -------------------------
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Multi-System Numerology Calendar Generator (Beautiful Output) ---")

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

    # Screen output granularity
    while True:
        view_option = input("View screen output for [D]ay, [W]eek, or [M]onth? (D/W/M - Day/Week use LARGE BLOCKS): ").lower()
        if view_option in ['d', 'w', 'm']:
            if view_option == 'd': view_option = 'day'
            elif view_option == 'w': view_option = 'week'
            elif view_option == 'm': view_option = 'month'
            break
        print(Fore.RED + "Invalid option. Please enter D, W, or M.")

    # Date input mode (single / multiple)
    date_mode = input(
        "\nChoose date input mode:\n"
        "1) Single Date\n"
        "2) Multiple Dates\n"
        "Enter choice (1/2): "
    ).strip()

    dates_to_display = []
    if date_mode == '2':
        multi_dates = input("Enter multiple dates separated by commas (DD/MM/YYYY,DD/MM/YYYY,...): ")
        for dstr in multi_dates.split(","):
            dstr = dstr.strip()
            try:
                d, mo, yr = parse_dob(dstr)
                dates_to_display.append(datetime(yr, mo, d))
            except Exception as e:
                print(Fore.RED + f"Skipping invalid date: {dstr}")
        if not dates_to_display:
            print(Fore.RED + "No valid dates entered. Exiting.")
            exit()
        # Print for each selected date
        for dt in dates_to_display:
            print(Fore.CYAN + f"\n------ DATE: {dt.strftime('%d/%m/%Y')} ------\n")
            display_console_output(chart, birth_root, life_path, dt, view_option, destiny_num)

    else:
        while True:
            try:
                screen_date_str = input("Enter START Date for Display (DD/MM/YYYY, blank for today): ")
                if not screen_date_str:
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    dates_to_display.append(start_date)
                    print(f"-> Using current date: {start_date.strftime('%Y-%m-%d')}")
                else:
                    d, mo, yr = parse_dob(screen_date_str)
                    start_date = datetime(yr, mo, d)
                    dates_to_display.append(start_date)
                break
            except ValueError:
                print(Fore.RED + "Invalid date format. Use DD/MM/YYYY.")
        display_console_output(chart, birth_root, life_path, start_date, view_option, destiny_num)

    # PDF generation prompt
    pdf_generate_choice = input(Fore.BLUE + "Do you want to generate the BEAUTIFUL Multi-System PDF with 3 MONTHS PER ROW? (y/n): ").lower()
    if pdf_generate_choice == 'y':
        while True:
            try:
                pdf_start_year = int(input("Enter START Year for the Detailed PDF (YYYY): "))
                years_to_generate_input = input("Enter number of years to generate (e.g., 1 for single year, 50): ")
                years_to_generate = 1 if not years_to_generate_input else int(years_to_generate_input)
                if years_to_generate <= 0:
                    print(Fore.RED + "Number of years must be positive.")
                    continue
                print(f"-> Generating beautiful calendar for {years_to_generate} year(s), starting {pdf_start_year}.")
                generate_multi_system_pdf(name, dob_input, pdf_start_year, years_to_generate, destiny_num)
                break
            except ValueError:
                print(Fore.RED + "Invalid year or number of years format.")
    else:
        print(Fore.YELLOW + "PDF generation skipped. Displayed data is for screen verification only.")