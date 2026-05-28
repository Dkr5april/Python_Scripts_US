from datetime import datetime
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch 

# Initialize colorama
init(autoreset=True)

# --- Global Definitions ---
# PDF colors changed to strings for safer reportlab rendering.
RISK_MAP = {
    0: (Fore.GREEN, 'green'),    # Console color, PDF color name (string)
    1: (Fore.YELLOW, 'yellow'),  # Low Risk / Neutral (🟡)
    2: (Fore.BLUE, 'blue'),      # Medium Risk / Significant Work (🔵)
    3: (Fore.RED, 'red')         # High Risk / Major Conflict (🔴)
}

PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1,
    'B': 2, 'K': 2, 'T': 2,
    'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4,
    'E': 5, 'N': 5, 'W': 5,
    'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7,
    'H': 8, 'Q': 8, 'Z': 8,
    'I': 9, 'R': 9
}

# --- General Helper Functions ---
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
    # Life Path calculation keeps master numbers until the final reduction
    total = day + month + year
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(d) for d in str(total))
    return total

def get_3x3_chart(day, month, year):
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}

def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]

def calculate_destiny_number(full_name):
    """Calculates the Destiny/Expression Number from the full name using Pythagorean system."""
    name_clean = ''.join(c.upper() for c in full_name if c.isalpha())
    total_sum = 0
    for letter in name_clean:
        total_sum += PYTHAGOREAN_MAP.get(letter, 0)
    
    # Destiny Number calculation keeps master numbers until the final reduction
    return get_life_path(0, 0, total_sum) # Reusing LP logic for master number check

# --- Risk Calculation Functions (DOB-ONLY) ---

# EON Risk (E)
def eon_risk_score(chart, birth_root, life_path, date):
    missing = missing_numbers(chart)
    icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month)
    icc_year = reduce_to_single_digit(date.year)
    score = 0
    # Rule 1: Birth Root conflict with a missing number
    if icc_day == reduce_to_single_digit(birth_root) and icc_day in missing: score += 2
    # Rule 2: Conflicts with Missing Digits (3 chances for day, month, year)
    if icc_month in missing: score += 1
    if icc_year in missing: score += 1
    if icc_day in missing: score += 1
    
    # Simplified score mapping for the 4-level system
    if score == 0: return 0 
    elif score in [1, 2]: return 1 
    elif score in [3, 4]: return 2 
    else: return 3 

# Pythagorean Vibe (P)
def pythagorean_vibe(date):
    DN = reduce_to_single_digit(date.day + date.month + date.year)
    vibe = reduce_to_single_digit(DN)
    if vibe in [1, 3, 5, 9]: return 0 
    elif vibe in [4, 8]: return 3 
    else: return 1 

# Chaldean Vibe (C)
def chaldean_vibe(date):
    DN = reduce_to_single_digit(date.day + date.month + date.year)
    vibe = reduce_to_single_digit(DN)
    if vibe in [1, 3, 5, 6, 9]: return 0
    elif vibe in [2, 4, 8]: return 3
    else: return 1

# Kabbalah Vibe (K)
def kabbalah_vibe(date):
    DN = reduce_to_single_digit(date.day + date.month + date.year)
    vibe = reduce_to_single_digit(DN)
    if vibe in [3, 6, 9]: return 0
    elif vibe in [2, 4, 7, 8]: return 3
    else: return 1


# --- Risk Calculation Functions (DESTINY HYBRID - Name + DOB) ---

def get_day_vibe(date):
    DN = reduce_to_single_digit(date.day + date.month + date.year)
    return reduce_to_single_digit(DN)

# Simple Destiny Alignment (D)
def destiny_alignment(date, destiny_number):
    day_vibe = get_day_vibe(date)
    destiny_num_reduced = reduce_to_single_digit(destiny_number)

    if day_vibe == destiny_num_reduced:
        return 0  # Green: Perfect Alignment
    else:
        return 3  # Red: No Alignment

# Pythagorean Destiny Hybrid (P.D)
def pythagorean_destiny_hybrid(date, destiny_number):
    day_vibe = get_day_vibe(date)
    destiny_num_reduced = reduce_to_single_digit(destiny_number)

    if day_vibe == destiny_num_reduced:
        return 0  # Green: Alignment overrides general risk
    
    # Defaults to general Pythagorean rule
    return pythagorean_vibe(date) 

# Chaldean Destiny Hybrid (C.D)
def chaldean_destiny_hybrid(date, destiny_number):
    day_vibe = get_day_vibe(date)
    destiny_num_reduced = reduce_to_single_digit(destiny_number)
    
    if day_vibe == destiny_num_reduced:
        return 0  # Green: Alignment overrides general risk
    
    # Defaults to general Chaldean rule
    return chaldean_vibe(date)

# Kabbalah Destiny Hybrid (K.D)
def kabbalah_destiny_hybrid(date, destiny_number):
    day_vibe = get_day_vibe(date)
    destiny_num_reduced = reduce_to_single_digit(destiny_number)

    if day_vibe == destiny_num_reduced:
        return 0  # Green: Alignment overrides general risk
    
    # Defaults to general Kabbalah rule
    return kabbalah_vibe(date)


# --- CONSOLE DISPLAY FUNCTION (DAILY LIST FORMAT) ---
def display_month_calendar(chart, birth_root, life_path, month, year, include_destiny, destiny_num=None):
    """Displays a single month as a list for guaranteed alignment."""
    
    print(Style.BRIGHT + Fore.CYAN + f"\n=== {calendar.month_name[month]} {year} (Daily Multi-System Assessment) ===")
    
    # Print Key
    print(Style.BRIGHT + "Risk Key: 🟢 Good, 🟡 Low, 🔵 Medium, 🔴 High")
    
    # Define the Header based on whether destiny is included
    if include_destiny:
        print(Style.BRIGHT + "Systems: E=EON, P=Pythagorean, K=Kabbalah, C=Chaldean")
        print(Style.BRIGHT + "Hybrids: D=Simple Destiny Alignment, P.D/K.D/C.D = Hybrid Vibe")
        print(Style.BRIGHT + "---------------------------------------------------------------------------------------------------")
        # Ensure the header string length is consistent for clean formatting
        header = f"| DATE | DAY | E | P | K | C | D | P.D | K.D | C.D |"
        print(header)
        print("-" * len(header))
    else:
        print(Style.BRIGHT + "Systems: E=EON, P=Pythagorean, K=Kabbalah, C=Chaldean")
        print(Style.BRIGHT + "-------------------------------------------------------------")
        header = f"| DATE | DAY | E | P | K | C |"
        print(header)
        print("-" * len(header))
    
    # Function to get color-coded letter
    def get_colored_letter(letter, score):
        color, _ = RISK_MAP[score]
        # Pad P.D, K.D, C.D for alignment if destiny is included
        if include_destiny and len(letter) > 1:
            return f"{color}{letter}{Style.RESET_ALL}"
        # Pad single letters
        return f"{color}{letter} {Style.RESET_ALL}"

    num_days = calendar.monthrange(year, month)[1] 
    
    for day in range(1, num_days + 1):
        try:
            current_date = datetime(year, month, day)
        except ValueError:
            continue 
            
        day_name = calendar.day_abbr[current_date.weekday()]
        
        # Calculate scores for the four core DOB systems
        e_score = eon_risk_score(chart, birth_root, life_path, current_date)
        p_score = pythagorean_vibe(current_date)
        c_score = chaldean_vibe(current_date)
        k_score = kabbalah_vibe(current_date)
        
        e_code = get_colored_letter('E', e_score)
        p_code = get_colored_letter('P', p_score)
        k_code = get_colored_letter('K', k_score)
        c_code = get_colored_letter('C', c_score)
        
        # Note: Added an extra space pad in the formatting string for single letters
        output_line = f"| {day:4d} | {day_name:3s} | {e_code} | {p_code} | {k_code} | {c_code} |"

        # Add Destiny Hybrid Systems if requested
        if include_destiny and destiny_num is not None:
            d_score = destiny_alignment(current_date, destiny_num)
            pd_score = pythagorean_destiny_hybrid(current_date, destiny_num)
            kd_score = kabbalah_destiny_hybrid(current_date, destiny_num)
            cd_score = chaldean_destiny_hybrid(current_date, destiny_num)
            
            d_code = get_colored_letter('D', d_score)
            pd_code = get_colored_letter('P.D', pd_score)
            kd_code = get_colored_letter('K.D', kd_score)
            cd_code = get_colored_letter('C.D', cd_score)

            output_line += f" {d_code}|{pd_code}|{kd_code}|{cd_code}|"
        
        # Print without the extra space to ensure alignment
        print(output_line.replace(' | ', '|'))

    # Recalculate length for accurate footer line
    print("-" * len(header.replace(' | ', '|')))

# --- PDF GENERATION FUNCTION (EON ONLY) ---
def generate_pdf_calendar(name, dob_str, start_year, num_years, life_path):
    # This remains EON-only as requested for the main planning tool
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    
    # Helper for PDF color
    def eon_risk_pdf(date, chart, birth_root, life_path):
        # We reuse the full EON logic for score calculation
        score = eon_risk_score(chart, birth_root, life_path, date) 
        color_name_str = RISK_MAP[score][1]
        # Safely convert the color string to the reportlab color object
        return getattr(colors, color_name_str, colors.black) 

    filename = f"EON_Calendar_{start_year}_{start_year + num_years - 1}.pdf"
    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.5 * inch
    
    for year_offset in range(num_years):
        current_year = start_year + year_offset
        if year_offset > 0: c.showPage()
        
        # Title and Info
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, height - margin, f"EON Numerology Calendar: {name} ({dob_str}) - {current_year}")
        c.setFont("Helvetica", 10)
        
        # Simplified PDF generation loop
        row_height = 0.25 * inch
        start_y = height - 1.5 * inch
        
        for month_num in range(1, 13):
            month_name = calendar.month_name[month_num]
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, start_y - (month_num-1) * 2 * row_height, month_name)
            
            c.setFont("Helvetica", 8)
            current_y = start_y - (month_num-1) * 2 * row_height - row_height/2
            
            # Print Weekday Headers
            for i, wd in enumerate(calendar.day_abbr):
                c.drawString(margin + i * (0.4 * inch), current_y, wd)

            # Print Days (simplified)
            current_y -= row_height/2
            cal_iter = calendar.Calendar().itermonthdays2(current_year, month_num)
            
            x_pos = 0
            for day, weekday in cal_iter:
                if day != 0:
                    day_date = datetime(current_year, month_num, day)
                    # FIX: Pass life_path to the helper function
                    color = eon_risk_pdf(day_date, chart, birth_root, life_path)
                    
                    # Draw colored box
                    c.setFillColor(color)
                    c.rect(margin + x_pos * (0.4 * inch), current_y, 0.3 * inch, 0.3 * inch, fill=1)
                    
                    # Draw Day number
                    c.setFillColor(colors.black)
                    c.drawCentredString(margin + x_pos * (0.4 * inch) + 0.15 * inch, current_y + 0.1 * inch, str(day))
                    
                    x_pos += 1
                
                if weekday == 6: # Sunday
                    x_pos = 0
                    current_y -= 0.5 * inch
        
    c.save()
    print(f"\nPDF calendar saved as {filename}")

# --- Main Execution ---
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Multi-System Numerology Calendar Generator ---")
    name = input("Enter Full Name: ")
    dob_input = input("Enter DOB (DD/MM/YYYY): ")
    
    # --- Input for Screen Output ---
    while True:
        try:
            screen_date_str = input("Enter Date for Screen Display (DD/MM/YYYY, or leave blank for current month): ")
            if not screen_date_str:
                now = datetime.now()
                # Use current context time (December 2025)
                screen_month, screen_year = 12, 2025 
                print(f"-> Using current month/year: {calendar.month_name[screen_month]} {screen_year}")
            else:
                _, screen_month, screen_year = parse_dob(screen_date_str)
            break
        except ValueError:
            print(Fore.RED + "Invalid date format. Please use DD/MM/YYYY.")

    # --- NEW INPUT: Destiny Alignment (FORCE 'Y' TO BYPASS INTERACTIVE ISSUE) ---
    include_destiny = True
    destiny_num = calculate_destiny_number(name)
    print(Fore.GREEN + f"-> Destiny Number is {destiny_num}. Full 7-System comparison enabled.")
    
    # --- Input for PDF Output ---
    while True:
        try:
            pdf_start_year = int(input("Enter START Year for PDF Calendar (YYYY): "))
            years_to_generate = 0
            valid_choices = ['1', '5', '10', '25', '50']
            while str(years_to_generate) not in valid_choices:
                year_choice = input(f"Generate calendar for {', '.join(valid_choices)} years? (Enter {', '.join(valid_choices)}): ")
                if year_choice in valid_choices:
                    years_to_generate = int(year_choice)
                else:
                    print(Fore.RED + f"Invalid choice. Please enter {', '.join(valid_choices)}.")
            break
        except ValueError:
            print(Fore.RED + "Invalid year format.")
            
    # Calculate natal chart details (Used by both screen and PDF)
    day, m, y = parse_dob(dob_input)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y) # Crucial for EON score
    
    # Generate and Display Screen Calendar
    display_month_calendar(chart, birth_root, life_path, screen_month, screen_year, include_destiny, destiny_num)

    # Generate PDF Calendar (Life path passed to function)
    generate_pdf_calendar(name, dob_input, pdf_start_year, years_to_generate, life_path)