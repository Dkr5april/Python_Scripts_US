from datetime import datetime
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import sys
import math

# Ensure UTF-8 on Windows consoles for console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

init(autoreset=True)

# -------------------------
# 1. Numerology & Calculation Logic
# -------------------------
RISK_MAP = {
    0: (Fore.GREEN, '#2E7D32', 'green'), # Console Color, Hex Code, Name (Good)
    1: (Fore.YELLOW, '#FBC02D', 'yellow'), # Low
    2: (Fore.BLUE, '#1976D2', 'blue'), # Medium
    3: (Fore.RED, '#D32F2F', 'red') # High
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

def get_birth_root(day): return reduce_to_single_digit(day)
def get_life_path(day, month, year):
    total = reduce_to_single_digit(day) + reduce_to_single_digit(month) + reduce_to_single_digit(year)
    while total > 9 and total not in [11, 22, 33]: total = sum(int(d) for d in str(total))
    return total
def get_3x3_chart(day, month, year):
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}
def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]
def calculate_destiny_number(full_name):
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum = sum(PYTHAGOREAN_MAP.get(letter, 0) for letter in name_clean)
    return reduce_to_single_digit(total_sum)
def get_day_vibe(date):
    return reduce_to_single_digit(date.day + date.month + date.year)
def eon_risk_score(chart, birth_root, life_path, date):
    missing = missing_numbers(chart); icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month); icc_year = reduce_to_single_digit(date.year)
    score = 0
    if icc_day == reduce_to_single_digit(birth_root) and icc_day in missing: score += 2
    if icc_day in missing: score += 1; 
    if icc_month in missing: score += 1;
    if icc_year in missing: score += 1;
    if score == 0: return 0
    elif score in [1, 2]: return 1
    elif score in [3, 4]: return 2
    else: return 3
def pythagorean_vibe(date):
    vibe = get_day_vibe(date); return 0 if vibe in [1, 3, 5, 9] else 1 if vibe in [2, 6, 7] else 3
def chaldean_vibe(date):
    vibe = get_day_vibe(date); return 0 if vibe in [1, 3, 5, 6, 9] else 1 if vibe in [7] else 3
def kabbalah_vibe(date):
    vibe = get_day_vibe(date); return 0 if vibe in [3, 6, 9] else 1 if vibe in [1, 5] else 3
def destiny_alignment(date, destiny_number):
    day_vibe = get_day_vibe(date); destiny_num_reduced = reduce_to_single_digit(destiny_number)
    return 0 if day_vibe == destiny_num_reduced else 3
def pythagorean_destiny_hybrid(date, destiny_number):
    return 0 if get_day_vibe(date) == reduce_to_single_digit(destiny_number) else pythagorean_vibe(date)
def chaldean_destiny_hybrid(date, destiny_number):
    return 0 if get_day_vibe(date) == reduce_to_single_digit(destiny_number) else chaldean_vibe(date)
def kabbalah_destiny_hybrid(date, destiny_number):
    return 0 if get_day_vibe(date) == reduce_to_single_digit(destiny_number) else kabbalah_vibe(date)

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
# 2. PDF Generation (Final: 3x2 Layout + Shifted Dots + Top Legend)
# -------------------------
def _rl_color(hex_code):
    """Converts hex code to reportlab color object."""
    return colors.HexColor(hex_code)

def generate_multi_system_pdf(name, dob_str, start_year, num_years, destiny_num):
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)

    end_year = start_year + num_years - 1
    filename = f"MultiSystem_3x2_DoubleHeight_ShiftedDots_{start_year}_{end_year}_{num_years}yrs.pdf"

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.35 * inch
    
    # --- KEY LAYOUT PARAMETERS (3 Columns x 2 Rows: DOUBLE HEIGHT) ---
    num_cols = 3
    num_rows = 2 
    box_w = (width - 2*margin) / num_cols
    box_h = (height - 2*margin - 0.8*inch) / num_rows

    header_space = 28  
    max_rows_per_month_grid = 6 

    # --- DOT PARAMETERS ---
    dot_radius = 2.0 
    DOT_LAYOUT_COLS = 2
    dot_v_step = dot_radius * 2.3  
    dot_h_step = dot_radius * 3.0 
    array_width = (dot_radius * 2) + dot_h_step
    inner_pad_x = 2 
    top_dot_center_y_offset = 8 
    
    # --- WEEK SHIFT PARAMETER (Fixed downward shift for weeks 2 onward) ---
    WEEK_FIXED_SHIFT = 2 * dot_v_step 

    for year_offset in range(num_years):
        current_year = start_year + year_offset

        # -----------------------------
        # 1. Page Header and Legend (New Placement: Top)
        # -----------------------------
        # 1a. Main Header
        c.setFillColor(colors.HexColor("#0D47A1")); c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - margin + 6, f"{name} — Multi-System Calendar ({current_year})")
        c.setFont("Helvetica", 8); c.setFillColor(colors.black)
        c.drawString(margin, height - margin - 8, f"DOB: {dob_str}    Destiny: {destiny_num}")

        # 1b. Legend Moved to the Top Space
        legend_x = margin
        legend_y_base = height - margin - 35 
        
        c.setFont("Helvetica", 8); c.setFillColor(colors.black)
        
        # Legend text
        c.drawString(legend_x, legend_y_base, "Legend (4 rows x 2 cols): EON, Pythagorean | Kabbalah, Chaldean | Destiny, P.Destiny Hybrid | K.Destiny Hybrid, C.Destiny Hybrid")
        
        # Risk Key (Good, Low, Med, High dots)
        risk_legend_x = legend_x
        risk_legend_y = legend_y_base - 10 
        risk_items = [('Good(0)', '#2E7D32'), ('Low(1)', '#FBC02D'), ('Med(2)', '#1976D2'), ('High(3)', '#D32F2F')]
        
        for label, hex_code in risk_items:
            c.setFillColor(_rl_color(hex_code))
            c.circle(risk_legend_x + 5, risk_legend_y + 4, 3, stroke=0, fill=1)
            c.setFillColor(colors.black)
            c.drawString(risk_legend_x + 10, risk_legend_y + 2, label)
            risk_legend_x += 80

        # Draw a line to separate the Legend from the Calendar Grid
        c.setStrokeColor(colors.grey)
        c.line(margin, legend_y_base - 18, width - margin, legend_y_base - 18)
        
        # -----------------------------
        # 2. Calendar Grid (Starts below the Legend)
        # -----------------------------
        cal = calendar.Calendar(firstweekday=6)  # Sunday first
        
        # Iterate through 6 months per page (0, 6)
        for page_month_offset in range(0, 12, num_cols * num_rows):
            if page_month_offset >= 12: break

            # Iterate through the 6 months for this page
            for month_offset in range(num_cols * num_rows):
                month_index = page_month_offset + month_offset + 1
                if month_index > 12: break

                # Positioning Logic (3 columns x 2 rows)
                mrow = month_offset // num_cols 
                mcol = month_offset % num_cols 
                
                box_x = margin + mcol * box_w
                # box_y calculation remains the same for 2 rows
                box_y = height - margin - 0.9*inch - (mrow+1) * box_h

                # Month Title & Weekday Headings
                c.setFillColor(colors.HexColor("#263238")); c.setFont("Helvetica-Bold", 10) 
                c.drawString(box_x + 6, box_y + box_h - 12, calendar.month_name[month_index])
                c.setFont("Helvetica", 7) 
                wd_w = box_w / 7.0
                for wi, wd in enumerate(calendar.day_abbr):
                    tx = box_x + wi * wd_w + 4; ty = box_y + box_h - 24
                    c.drawString(tx, ty, wd[:1]) 

                weeks = list(cal.monthdayscalendar(current_year, month_index))
                row_height = (box_h - header_space) / max_rows_per_month_grid
                cell_w = wd_w
                cell_h = row_height
                
                # Dot Centering Calculation 
                cell_inner_w = cell_w - 2*inner_pad_x
                center_offset_x = (cell_inner_w - array_width) / 2.0
                
                # Draw Days and Dots
                for r, wk in enumerate(weeks): # 'r' is the calendar week row index (0 to 5)
                    for ccol, d in enumerate(wk):
                        cell_x_base = box_x + ccol * cell_w 
                        cell_y_base = box_y + box_h - header_space - (r+1) * row_height
                        
                        if d == 0: continue
                            
                        # Cell Boundary & Day Number
                        c.setStrokeColor(colors.lightgrey)
                        c.rect(cell_x_base + 2, cell_y_base + 2, cell_w - 4, cell_h - 4, fill=0, stroke=1)
                        c.setFont("Helvetica-Bold", 8); c.setFillColor(colors.black) 
                        c.drawString(cell_x_base + 4, cell_y_base + cell_h - 14, str(d)) 

                        # Determine the required shift for this week
                        current_week_shift = 0.0
                        if r > 0: # Apply WEEK_FIXED_SHIFT to all weeks starting from the second week (r=1)
                            current_week_shift = WEEK_FIXED_SHIFT
                            
                        # Dot Drawing Setup
                        day_date = datetime(current_year, month_index, d)
                        scores = get_all_risk_scores(day_date, chart, birth_root, life_path, destiny_num)
                        keys = ['E','P','K','C','D','PD','KD','CD']
                        
                        # Dot Starting Positions (X: left dot center, Y: top row center)
                        dot_x_start = cell_x_base + inner_pad_x + center_offset_x + dot_radius
                        
                        # Y START ADJUSTMENT: Apply the shift to the base Y coordinate
                        dot_y_start = cell_y_base + cell_h - top_dot_center_y_offset - current_week_shift
                        
                        # Draw 8 Dots
                        for i, key in enumerate(keys):
                            rr = i // DOT_LAYOUT_COLS; cc = i % DOT_LAYOUT_COLS   
                            
                            dot_x = dot_x_start + (cc * dot_h_step)
                            # Y position: Start Y - (Standard Steps for the 4 dot rows)
                            dot_y = dot_y_start - (rr * dot_v_step) 
                            
                            hex_code = RISK_MAP[scores[key]][1]
                            c.setFillColor(_rl_color(hex_code))
                            c.circle(dot_x, dot_y, dot_radius, stroke=0, fill=1)

                # Draw outer border for the month box
                c.setStrokeColor(colors.black)
                c.rect(box_x, box_y, box_w, box_h, fill=0, stroke=1)

            # -----------------------------
            # 3. Footer (Only generation info remains at the bottom)
            # -----------------------------
            c.setFont("Helvetica-Oblique", 7); c.setFillColor(colors.grey)
            c.drawRightString(width - margin, margin - 2, f"Generated by EON — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            c.showPage()
            
    c.save()
    print(Fore.GREEN + f"\n✅ Final PDF saved as {filename}" + Fore.RESET)

# -------------------------
# 4. Main Execution Block
# -------------------------
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Multi-System Numerology Calendar Generator (Final PDF Output) ---")

    # 1. Gather Inputs
    name = input("Enter Full Name: ")
    dob_input = input("Enter DOB (DD/MM/YYYY): ")

    try:
        day, m, y = parse_dob(dob_input)
    except ValueError:
        print(Fore.RED + "Invalid DOB format. Exiting.")
        sys.exit()

    destiny_num = calculate_destiny_number(name)
    print(Fore.GREEN + f"-> Destiny Number is {destiny_num}.")

    # PDF generation prompt
    pdf_generate_choice = input(Fore.BLUE + "\nDo you want to generate the final 3x2 PDF calendar? (y/n): ").lower()
    if pdf_generate_choice == 'y':
        while True:
            try:
                pdf_start_year = int(input("Enter START Year for the Detailed PDF (YYYY): "))
                years_to_generate_input = input("Enter number of years to generate (e.g., 1 or 50): ")
                years_to_generate = 1 if not years_to_generate_input else int(years_to_generate_input)
                if years_to_generate <= 0:
                    print(Fore.RED + "Number of years must be positive.")
                    continue
                print(f"-> Generating final calendar for {years_to_generate} year(s), starting {pdf_start_year}.")
                
                generate_multi_system_pdf(name, dob_input, pdf_start_year, years_to_generate, destiny_num)
                break
            except ValueError:
                print(Fore.RED + "Invalid year or number of years format.")
    else:
        print(Fore.YELLOW + "PDF generation skipped.")