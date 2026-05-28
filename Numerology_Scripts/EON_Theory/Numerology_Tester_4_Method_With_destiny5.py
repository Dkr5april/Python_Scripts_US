# EON_BeautifulOutput_fixed_pdf.py
from datetime import datetime, timedelta
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import sys
import os

# Ensure UTF-8 on Windows consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

init(autoreset=True)

# -------------------------
# Original calculation logic (unchanged)
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

# More flexible date parser (accepts single-digit month/day too)
def parse_dob(dob_str):
    dob_str = dob_str.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(dob_str, fmt)
            return dt.day, dt.month, dt.year
        except:
            pass
    # fallback: try manual split with / (accept d/m/yyyy)
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

# -------------------------
# Console output helpers (unchanged)
# -------------------------
def _col(letter, score):
    color, _ = RISK_MAP[score]
    return f"{color}{letter}{Style.RESET_ALL}"

def print_detailed_day_result(day_date, chart, birth_root, life_path, destiny_num):
    day = day_date.day
    day_name = calendar.day_name[day_date.weekday()][:3]
    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
    header = f"┌{'─'*36}┐"
    print(Style.BRIGHT + Fore.CYAN + header)
    print(Style.BRIGHT + Fore.YELLOW + f"│ DATE: {day:2d}  {day_name:^10s}  |  Destiny: {destiny_num:^2d} │")
    print(Style.BRIGHT + Fore.CYAN + f"├{'─'*36}┤")
    e_code = _col('EON', scores['E'])
    print(f"│ NATAL CHART: {e_code:<6s}    | Score: {scores['E']:<1d}           │")
    print(f"│ {'-'*34} │")
    p_code = _col('P', scores['P'])
    k_code = _col('K', scores['K'])
    c_code = _col('C', scores['C'])
    print(f"│ UNIVERSAL VIBE: Pyt:{p_code} ({scores['P']})  Kab:{k_code} ({scores['K']})  Cha:{c_code} ({scores['C']}) │")
    print(f"│ {'-'*34} │")
    d_code = _col('D', scores['D'])
    pd_code = _col('PD', scores['PD'])
    kd_code = _col('KD', scores['KD'])
    cd_code = _col('CD', scores['CD'])
    print(f"│ DESTINY ALIGN: {d_code}({scores['D']})  P.D:{pd_code}({scores['PD']})  K.D:{kd_code}({scores['KD']})  C.D:{cd_code}({scores['CD']}) │")
    footer = f"└{'─'*36}┘"
    print(Style.BRIGHT + Fore.CYAN + footer)
    print()

def display_console_output(chart, birth_root, life_path, start_date, view_option, destiny_num):
    print(Style.BRIGHT + Fore.MAGENTA + "\n=== EON Detailed View ===")
    print(Style.DIM + "Legend: " + Fore.GREEN + "Good(0) " + Fore.YELLOW + "Low(1) " + Fore.BLUE + "Med(2) " + Fore.RED + "High(3)\n")
    if view_option == 'day':
        print_detailed_day_result(start_date, chart, birth_root, life_path, destiny_num)
    elif view_option == 'week':
        print(Style.BRIGHT + Fore.BLUE + f"--- Week starting {start_date.strftime('%Y-%m-%d')} ---")
        for i in range(7):
            d = start_date + timedelta(days=i)
            print_detailed_day_result(d, chart, birth_root, life_path, destiny_num)
    elif view_option == 'month':
        year = start_date.year
        month = start_date.month
        cal = calendar.Calendar(firstweekday=6)  # Sunday-first
        month_name = calendar.month_name[month]
        print(Style.BRIGHT + Fore.CYAN + f"\n==== {month_name} {year} ====")
        weekdays = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
        header = " ".join(d.center(12) for d in weekdays)
        print(Style.BRIGHT + header)
        print("-"*len(header))
        weeks = list(cal.monthdayscalendar(year, month))
        for wk in weeks:
            line_dates = ""
            for d in wk:
                if d == 0:
                    line_dates += " ".center(12)
                else:
                    line_dates += f"{str(d).center(12)}"
            print(line_dates)
            line_blocks = ""
            for d in wk:
                if d == 0:
                    line_blocks += " ".center(12)
                else:
                    day_dt = datetime(year, month, d)
                    scores = get_all_risk_scores(day_dt, chart, birth_root, life_path, destiny_num)
                    keys = ['E','P','K','C','D','PD','KD','CD']
                    parts = []
                    for k in keys:
                        cname = RISK_MAP[scores[k]][1]
                        ansi = RISK_MAP[scores[k]][0]
                        parts.append(ansi + "█" + Style.RESET_ALL)
                    cell = "".join(parts)
                    cell = cell[:12].center(12)
                    line_blocks += cell
            print(line_blocks)
            print()
    else:
        print(Fore.RED + "Invalid view option.")

# -------------------------
# PDF generation (fixed ordering + spacing)
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
    filename = f"MultiSystem_Beautiful_{start_year}_{end_year}_{num_years}yrs.pdf"

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.35 * inch

    # Layout: 4 columns x 3 rows of months per page -> 12 months
    box_w = (width - 2*margin) / 4.0
    box_h = (height - 2*margin - 0.8*inch) / 3.0

    header_space = 28  # space used by month title and weekday headings inside a box
    max_rows_per_month_grid = 6  # calendar may need up to 6 rows

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
            # position on page (4 per row, 3 rows)
            mrow = (month_index - 1) // 4
            mcol = (month_index - 1) % 4
            box_x = margin + mcol * box_w
            box_y = height - margin - 0.9*inch - (mrow+1) * box_h

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
                c.drawString(tx, ty, wd[0])

            # get week matrix for this month in correct order
            weeks = cal.monthdayscalendar(current_year, month_index)

            # compute cell size and inner padding (adaptative)
            row_height = (box_h - header_space) / max_rows_per_month_grid
            cell_w = wd_w
            cell_h = row_height
            # inner drawing area
            inner_pad_x = 4
            inner_pad_y = 4
            cell_inner_w = cell_w - 2*inner_pad_x
            cell_inner_h = cell_h - 2*inner_pad_y

            # determine dot radius & spacing that avoids overlap
            # we need to draw 8 dots arranged 4 rows x 2 cols inside cell_inner_w x cell_inner_h
            dot_radius = min(cell_inner_w / 6.0, cell_inner_h / 8.0)
            dot_radius = max(1.2, dot_radius)  # avoid too small; keep minimum visible size

            # spacing between dot columns and rows
            dot_col_spacing = (cell_inner_w - 2*dot_radius) / 1.5 if cell_inner_w > 0 else dot_radius*3
            dot_row_spacing = (cell_inner_h - 2*dot_radius) / 3.5 if cell_inner_h > 0 else dot_radius*2

            # draw days by row (weeks) and column (weekday) - preserves proper sequence
            for r, wk in enumerate(weeks):
                for ccol, d in enumerate(wk):
                    cell_x = box_x + ccol * cell_w + inner_pad_x
                    # y position: top of box minus header minus r*row_height - cell height
                    cell_y = box_y + box_h - header_space - (r+1) * row_height + inner_pad_y
                    if d == 0:
                        # empty cell (outside month)
                        continue
                    # draw the cell rectangle lightly
                    c.setStrokeColor(colors.lightgrey)
                    c.rect(cell_x - inner_pad_x + 2, cell_y - inner_pad_y + 2, cell_w - 4, cell_h - 4, fill=0, stroke=1)

                    # day number (small)
                    c.setFont("Helvetica-Bold", 6)
                    c.setFillColor(colors.black)
                    c.drawString(cell_x + 2, cell_y + cell_inner_h - 8, str(d))

                    # compute scores
                    day_date = datetime(current_year, month_index, d)
                    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
                    keys = ['E','P','K','C','D','PD','KD','CD']

                    # draw 4x2 dots: layout column positions
                    # left column x, right column x
                    left_x = cell_x + dot_radius + 2
                    right_x = cell_x + cell_inner_w - dot_radius - 2
                    # top row y (start)
                    top_y = cell_y + cell_inner_h - dot_radius - 8

                    # positions for 4 rows
                    for i, key in enumerate(keys):
                        rr = i // 2  # 0..3
                        cc = i % 2   # 0 or 1
                        dot_x = left_x if cc == 0 else right_x
                        dot_y = top_y - rr * dot_row_spacing
                        color_name = RISK_MAP[scores[key]][1]
                        c.setFillColor(_rl_color(color_name))
                        c.circle(dot_x, dot_y, dot_radius, stroke=0, fill=1)

        # legend bottom-left
        legend_x = margin
        legend_y = margin + 6
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(legend_x, legend_y + 20, "Legend (dots): E,P,K,C,D,PD,KD,CD  — Colors: Green Good (0), Yellow Low (1), Blue Med (2), Red High (3)")
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
        view_option = input("View screen output for [D]ay, [W]eek, or [M]onth? (D/W/M - All use separated blocks): ").lower()
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
    pdf_generate_choice = input(Fore.BLUE + "Do you want to generate the BEAUTIFUL Multi-System PDF? (y/n): ").lower()
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
