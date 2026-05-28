# EON_BeautifulOutput_final_group_analysis.py
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
# MAPPING LOGIC (UNCHANGED from previous revision)
# -------------------------
RISK_MAP = {
    0: (Fore.GREEN, 'green'),
    1: (Fore.YELLOW, 'yellow'),
    2: (Fore.BLUE, 'blue'),
    3: (Fore.RED, 'red')
}

# Pythagorean Destiny Map (DN_P, D score, PD)
PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1, 'B': 2, 'K': 2, 'T': 2, 'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4, 'E': 5, 'N': 5, 'W': 5, 'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7, 'H': 8, 'Q': 8, 'Z': 8, 'I': 9, 'R': 9
}

# Chaldean Destiny Map (DN_C, CD)
CHALDEAN_MAP = {
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
    'B': 2, 'K': 2, 'R': 2,
    'C': 3, 'G': 3, 'L': 3, 'S': 3,
    'D': 4, 'M': 4, 'T': 4,
    'E': 5, 'H': 5, 'N': 5, 'X': 5,
    'U': 6, 'V': 6, 'W': 6,
    'O': 7, 'Z': 7,
    'F': 8, 'P': 8
}

# Kabbalah Destiny Map (DN_K, KD) - Using Pythagorean map per the original script structure
KABBALAH_MAP = PYTHAGOREAN_MAP 

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

def get_day_vibe(date):
    return reduce_to_single_digit(date.day + date.month + date.year)

def calculate_all_destiny_numbers(full_name):
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    
    total_sum_p = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    dn_p = reduce_to_single_digit(total_sum_p)
    
    total_sum_c = sum(CHALDEAN_MAP.get(letter, 0) for letter in name_clean)
    dn_c = reduce_to_single_digit(total_sum_c)
    
    total_sum_k = sum(KABBALAH_MAP.get(letter, 0) for letter in name_clean)
    dn_k = reduce_to_single_digit(total_sum_k)
    
    return dn_p, dn_c, dn_k

# -------------------------
# Risk Score Functions (UNCHANGED LOGIC)
# -------------------------

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

# ALIGNMENT AND HYBRID FUNCTIONS (Native DN logic retained)
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

def get_all_risk_scores(date, chart, birth_root, life_path, destiny_nums):
    dn_p, dn_c, dn_k = destiny_nums 
    scores = {}
    
    scores['E'] = eon_risk_score(chart, birth_root, date)
    scores['P'] = pythagorean_vibe(date)
    scores['K'] = kabbalah_vibe(date)
    scores['C'] = chaldean_vibe(date)
    
    scores['D'] = destiny_alignment(date, dn_p)
    scores['PD'] = pythagorean_destiny_hybrid(date, dn_p)
    scores['KD'] = kabbalah_destiny_hybrid(date, dn_k) 
    scores['CD'] = chaldean_destiny_hybrid(date, dn_c)
    
    return scores

def get_overall_risk_for_bar(scores):
    total_score = sum(scores.values())
    average_score = total_score / len(scores)
    overall_risk = int(math.ceil(average_score))
    overall_risk = min(3, max(0, overall_risk))
    
    return overall_risk, RISK_MAP[overall_risk][0] 

# -------------------------
# Console output helpers (MODIFIED for flexible input)
# -------------------------

def print_large_block_day_result(day_date, person_data):
    # person_data is a dictionary containing: name, chart, birth_root, life_path, destiny_nums
    name = person_data['name']
    chart = person_data['chart']
    birth_root = person_data['birth_root']
    life_path = person_data['life_path']
    destiny_nums = person_data['destiny_nums']

    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_nums)
    
    overall_risk, overall_color = get_overall_risk_for_bar(scores)
    
    keys = ['E','P','K','C','D','PD','KD','CD']
    risk_colors = [RISK_MAP[scores[k]][0] for k in keys]

    BLOCK_FULL = "█"
    EMPTY_SPACE = " "
    
    # Header Line: Name
    print(Fore.CYAN + f"┌─ {Style.BRIGHT + Fore.WHITE + name.upper() + Style.RESET_ALL} (P:{destiny_nums[0]}/C:{destiny_nums[1]}/K:{destiny_nums[2]})" + "─" * (75 - len(name) - 20) + "┐" + Style.RESET_ALL)
    
    # --- Line 1 (Top Half) ---
    line1 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    overall_box_width = 11
    line1_overall = (
        overall_color + Style.BRIGHT + BLOCK_FULL * overall_box_width
    )
    line1 += f"{line1_overall}{Fore.CYAN} │{Style.RESET_ALL} {Style.BRIGHT + Fore.WHITE}SYSTEM SCORES:{Style.RESET_ALL} "
    
    for i in range(4):
        line1 += f"{risk_colors[i]}{BLOCK_FULL}{Style.RESET_ALL}"
        line1 += f"{Fore.CYAN} {keys[i]} {Style.RESET_ALL}"
    line1 += f"{Fore.CYAN}│{Style.RESET_ALL}"
    
    # --- Line 2 (Bottom Half) ---
    line2 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    date_str = day_date.strftime('%Y-%m-%d %a')
    date_padded = f" {date_str} ".center(overall_box_width)
    line2_overall = overall_color + Style.BRIGHT + date_padded + Style.RESET_ALL
    line2 += f"{line2_overall}{Fore.CYAN} │{Style.RESET_ALL} "
    
    for i in range(4, 8):
        line2 += f"{risk_colors[i]}{BLOCK_FULL}{Style.RESET_ALL}"
        line2 += f"{Fore.CYAN} {keys[i]} {Style.RESET_ALL}"
    line2 += f"{Fore.CYAN}│{Style.RESET_ALL}"

    # --- Line 3 (Score Line) ---
    line3 = f"{Fore.CYAN}│ {Style.RESET_ALL}"
    
    score_display = f" SCORE: {overall_risk} ".center(overall_box_width)
    line3_overall = overall_color + Style.BRIGHT + score_display + Style.RESET_ALL
    line3 += f"{line3_overall}{Fore.CYAN} │{Style.RESET_ALL} "
    
    risk_legend = f" {Fore.GREEN}0 {Fore.YELLOW}1 {Fore.BLUE}2 {Fore.RED}3{Style.RESET_ALL}"
    legend_content_width = 24
    total_space_in_right_box = 45
    padding_space = total_space_in_right_box - legend_content_width
    
    line3 += f"{Fore.CYAN}Risk: {risk_legend}{EMPTY_SPACE*(padding_space)}│{Style.RESET_ALL}"

    print(line1)
    print(line2)
    print(line3)
    print(Fore.CYAN + "└─────────────────────────┴───────────────────────────────────────────┘" + Style.RESET_ALL)


def display_console_output_group(person_data_list, target_dates, view_option):
    print(Style.BRIGHT + Fore.MAGENTA + "\n=== GROUP MULTI-SYSTEM DAILY RISK ASSESSMENT ===" + Style.RESET_ALL)
    
    for date in target_dates:
        print(Style.BRIGHT + Fore.CYAN + f"\n════════ TARGET DATE: {date.strftime('%d/%m/%Y')} ════════" + Style.RESET_ALL)
        
        if view_option == 'day':
            for person_data in person_data_list:
                print_large_block_day_result(date, person_data)
        
        elif view_option == 'week':
            # This handles a full week for each person, starting on the target date.
            for person_data in person_data_list:
                print(Style.BRIGHT + Fore.YELLOW + f"\n--- {person_data['name']}'s Week Starting {date.strftime('%Y-%m-%d')} ---" + Style.RESET_ALL)
                for i in range(7):
                    d = date + timedelta(days=i)
                    print_large_block_day_result(d, person_data)
        
        elif view_option == 'month':
             print(Fore.RED + "Monthly view is not ideal for multiple people on a single screen. Please use Day or Week view.")
             break
        
        print(Fore.CYAN + "="*75 + Style.RESET_ALL)
        
# -------------------------
# PDF generation (UNCHANGED logic, updated arguments)
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

def generate_multi_system_pdf(name, dob_str, start_year, num_years, destiny_nums):
    # This PDF function is designed for a single person/year view, so we only run it if needed.
    dn_p, _, _ = destiny_nums 
    
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)

    end_year = start_year + num_years - 1
    filename = f"MultiSystem_Beautiful_3x4_Aligned_{name.replace(' ', '_')}_{start_year}_{end_year}_{num_years}yrs.pdf" # Updated to include name

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.35 * inch
    
    num_cols = 3
    num_rows = 4
    box_w = (width - 2*margin) / num_cols
    box_h = (height - 2*margin - 0.8*inch) / num_rows

    header_space = 28  
    max_rows_per_month_grid = 6 

    for year_offset in range(num_years):
        current_year = start_year + year_offset

        c.setFillColor(colors.HexColor("#0D47A1"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - margin + 6, f"{name} — Multi-System Calendar ({current_year})")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(margin, height - margin - 8, f"DOB: {dob_str}    Destiny(P): {dn_p} / Destiny(C): {destiny_nums[1]} / Destiny(K): {destiny_nums[2]}")

        cal = calendar.Calendar(firstweekday=6)
        for month_index in range(1, 13):
            mrow = (month_index - 1) // num_cols
            mcol = (month_index - 1) % num_cols
            
            box_x = margin + mcol * box_w
            box_y = height - margin - 0.9*inch - (mrow+1) * box_h

            c.setFillColor(colors.HexColor("#263238"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(box_x + 6, box_y + box_h - 12, calendar.month_name[month_index])

            c.setFont("Helvetica", 6)
            wd_w = box_w / 7.0
            for wi, wd in enumerate(calendar.day_abbr):
                tx = box_x + wi * wd_w + 4
                ty = box_y + box_h - 22
                c.drawString(tx, ty, wd[:1]) 

            weeks = list(cal.monthdayscalendar(current_year, month_index))

            row_height = (box_h - header_space) / max_rows_per_month_grid
            cell_w = wd_w
            cell_h = row_height
            inner_pad_x = 2
            cell_inner_w = cell_w - 2*inner_pad_x
            
            dot_radius = 2.8 
            DOT_LAYOUT_COLS = 2
            dot_v_step = dot_radius * 2.5  
            dot_h_step = dot_radius * 3.5  

            array_width = dot_radius + dot_h_step + dot_radius
            center_offset_x = (cell_inner_w - array_width) / 2.0
            top_dot_center_y_offset = 10 
            
            for r, wk in enumerate(weeks):
                for ccol, d in enumerate(wk):
                    cell_x_base = box_x + ccol * cell_w 
                    cell_y_base = box_y + box_h - header_space - (r+1) * row_height
                    
                    if d == 0:
                        continue
                        
                    c.setStrokeColor(colors.lightgrey)
                    c.rect(cell_x_base + 2, cell_y_base + 2, cell_w - 4, cell_h - 4, fill=0, stroke=1)

                    c.setFont("Helvetica-Bold", 7) 
                    c.setFillColor(colors.black)
                    c.drawString(cell_x_base + 4, cell_y_base + 4, str(d)) 

                    day_date = datetime(current_year, month_index, d)
                    scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_nums)
                    keys = ['E','P','K','C','D','PD','KD','CD']

                    dot_y_start = cell_y_base + cell_h - top_dot_center_y_offset
                    dot_x_start = cell_x_base + center_offset_x + dot_radius
                    
                    for i, key in enumerate(keys):
                        rr = i // DOT_LAYOUT_COLS
                        cc = i % DOT_LAYOUT_COLS
                        
                        dot_x = dot_x_start + (cc * dot_h_step)
                        dot_y = dot_y_start - (rr * dot_v_step) 
                        
                        color_name = RISK_MAP[scores[key]][1]
                        c.setFillColor(_rl_color(color_name))
                        c.circle(dot_x, dot_y, dot_radius, stroke=0, fill=1)

            c.setStrokeColor(colors.black)
            c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)

        legend_x = margin
        legend_y = margin + 6
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        c.drawString(legend_x, legend_y + 20, "Legend (dots, left to right, top to bottom): EON, Pythagorean, Kabbalah, Chaldean, Destiny(P), P.Destiny(P), K.Destiny(K), C.Destiny(C)")
        legend_items = [('Good', 'green'), ('Low', 'yellow'), ('Med', 'blue'), ('High', 'red')]
        lx = legend_x
        for label, cname in legend_items:
            c.setFillColor(_rl_color(cname))
            c.rect(lx, legend_y + 4, 10, 10, fill=1)
            c.setFillColor(colors.black)
            c.drawString(lx + 14, legend_y + 4, label)
            lx += 70

        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.grey)
        c.drawRightString(width - margin, margin - 2, f"Generated by EON — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        c.showPage()

    c.save()
    print(Fore.GREEN + f"\n✅ Beautiful PDF saved as {filename}" + Fore.RESET)

# -------------------------
# MAIN CLI LOGIC (MAJOR RESTRUCTURING)
# -------------------------
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Group Multi-System Numerology Calendar Generator ---")

    person_data_list = []

    # 1. Gather all individuals (Name, DOB)
    print(Style.BRIGHT + Fore.YELLOW + "\n--- Enter Individual Data (Group Analysis) ---" + Style.RESET_ALL)
    print("Format: Name,DD/MM/YYYY (e.g., Jane Doe, 01/01/1980)")
    print("Enter a blank line when finished.")

    while True:
        line = input(f"Individual {len(person_data_list) + 1} (Name, DOB): ").strip()
        if not line:
            break

        try:
            name_str, dob_str = line.split(',')
            name = name_str.strip()
            dob_input = dob_str.strip()
            
            day, m, y = parse_dob(dob_input)
            
            chart = get_3x3_chart(day, m, y)
            birth_root = get_birth_root(day)
            life_path = get_life_path(day, m, y)
            destiny_nums = calculate_all_destiny_numbers(name)
            
            person_data_list.append({
                'name': name,
                'dob': dob_input,
                'chart': chart,
                'birth_root': birth_root,
                'life_path': life_path,
                'destiny_nums': destiny_nums
            })
            
            print(Fore.GREEN + f"-> Added {name} (P:{destiny_nums[0]}, C:{destiny_nums[1]}, K:{destiny_nums[2]})" + Style.RESET_ALL)

        except ValueError:
            print(Fore.RED + "Invalid format or DOB. Please use 'Name,DD/MM/YYYY'.")
            
    if not person_data_list:
        print(Fore.RED + "No valid individuals entered. Exiting.")
        exit()

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

    # 3. Screen Output Granularity
    while True:
        view_option = input("\nView screen output for [D]ay or [W]eek? (M views are too wide for groups): ").lower()
        if view_option in ['d', 'w']:
            view_option = 'day' if view_option == 'd' else 'week'
            break
        print(Fore.RED + "Invalid option. Please enter D or W.")

    # 4. Display Results
    display_console_output_group(person_data_list, target_dates, view_option)

    # 5. PDF Generation Prompt (Single-Person PDF)
    print(Fore.BLUE + "\n--- PDF Generation (Requires Single Person Selection) ---" + Style.RESET_ALL)
    pdf_generate_choice = input(Fore.BLUE + "Do you want to generate a DETAILED Multi-System PDF Calendar for ONE person? (y/n): ").lower()
    
    if pdf_generate_choice == 'y':
        
        print("\nSelect the individual for PDF generation:")
        for i, data in enumerate(person_data_list):
            print(f"{i+1}) {data['name']}")
        
        while True:
            try:
                selection = int(input("Enter number of individual: ")) - 1
                if 0 <= selection < len(person_data_list):
                    selected_person = person_data_list[selection]
                    break
                else:
                    print(Fore.RED + "Invalid selection number.")
            except ValueError:
                print(Fore.RED + "Invalid input. Enter a number.")

        while True:
            try:
                pdf_start_year = int(input(f"Enter START Year for {selected_person['name']}'s PDF (YYYY): "))
                years_to_generate_input = input("Enter number of years to generate (e.g., 1 or 5): ")
                years_to_generate = 1 if not years_to_generate_input else int(years_to_generate_input)
                if years_to_generate <= 0:
                    print(Fore.RED + "Number of years must be positive.")
                    continue
                print(f"-> Generating beautiful calendar for {selected_person['name']} for {years_to_generate} year(s), starting {pdf_start_year}.")
                
                generate_multi_system_pdf(
                    selected_person['name'], 
                    selected_person['dob'], 
                    pdf_start_year, 
                    years_to_generate, 
                    selected_person['destiny_nums']
                )
                break
            except ValueError:
                print(Fore.RED + "Invalid year or number of years format.")
    else:
        print(Fore.YELLOW + "PDF generation skipped. Analysis complete.")