from datetime import datetime
import calendar
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch 

init(autoreset=True)

# --- Helper Functions (No Change) ---
def reduce_to_single_digit(n):
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

def parse_dob(dob_str):
    day, month, year = map(int, dob_str.split('/'))
    return day, month, year

def get_birth_root(day):
    return reduce_to_single_digit(day)

def get_life_path(day, month, year):
    return reduce_to_single_digit(day + month + year)

def get_3x3_chart(day, month, year):
    digits = [int(d) for d in f"{day:02d}{month:02d}{year}"]
    return {i: digits.count(i) for i in range(1, 10)}

def missing_numbers(chart):
    return [num for num, count in chart.items() if count == 0]

# --- FIXED RISK LOGIC (No Change) ---
def risk_score_for_day(chart, birth_root, life_path, date):
    missing = missing_numbers(chart)

    icc_day = reduce_to_single_digit(date.day)
    icc_month = reduce_to_single_digit(date.month)
    icc_year = reduce_to_single_digit(date.year)

    ecc_day = icc_day 
    ecc_month = icc_month
    ecc_year = icc_year

    score = 0
    if icc_day == birth_root and icc_day in missing:
        score += 2
    if icc_month in missing:
        score += 1
    if icc_year in missing:
        score += 1
    if ecc_day in missing:
        score += 1
    if ecc_month in missing:
        score += 1
    if ecc_year in missing:
        score += 1

    if score == 0:
        return Fore.GREEN, colors.green
    elif score in [1, 2]:
        return Fore.YELLOW, colors.yellow
    elif score in [3, 4]:
        return Fore.BLUE, colors.blue
    else:
        return Fore.RED, colors.red

# --- 🚀 ENHANCED PDF Calendar (Final Alignment Fix) ---
def generate_pdf_calendar(name, dob_str, year, filename="EON_Calendar.pdf"):
    day, m, y = parse_dob(dob_str)
    chart = get_3x3_chart(day, m, y)
    birth_root = get_birth_root(day)
    life_path = get_life_path(day, m, y)
    missing = missing_numbers(chart)

    c = canvas.Canvas(filename, pagesize=landscape(A4))
    width, height = landscape(A4)
    margin = 0.5 * inch
    
    calendar_area_width = width - 2 * margin
    
    # ===== HEADER & KEY NUMEROLOGY INFO (No Change) =====
    header_y = height - 0.5 * inch
    
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, header_y, "Numerology Calendar Analysis")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, header_y - 25, f"{name}")
    
    c.setFont("Helvetica", 12)
    c.drawString(margin, header_y - 50, f"DOB: {dob_str}")
    c.drawString(margin + 1.5 * inch, header_y - 50, f"Year of Focus: {year}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 4 * inch, header_y - 50, f"Life Path: {life_path}")
    c.drawString(margin + 6 * inch, header_y - 50, f"Birth Root: {birth_root}")
    
    # --- DRAW LOSHU GRID (3x3 Chart) ---
    grid_size = 1.0 * inch
    grid_x = width - margin - grid_size
    grid_y = height - 1.5 * inch 
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(grid_x + grid_size / 2, grid_y + 0.1 * inch, "3x3 Chart")
    
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    
    loshu_map = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]

    for row_idx, row_nums in enumerate(loshu_map):
        for col_idx, num in enumerate(row_nums):
            cell_val = " " if chart[num] == 0 else f"{num}" * chart[num]
            
            x = grid_x + col_idx * (grid_size / 3)
            y = grid_y - (row_idx + 1) * (grid_size / 3) 

            c.rect(x, y, grid_size / 3, grid_size / 3)
            
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            c.drawCentredString(x + (grid_size / 6), y + (grid_size / 10), cell_val)
            
    # --- Missing Digits (Placed on the left of the Loshu Chart) ---
    c.drawString(margin + 8 * inch, header_y - 50, f"Missing Digits: {', '.join(map(str, sorted(missing))) or 'None'}")
            
    # ===== LEGEND (Top Left Position) =====
    
    legend_start_x = margin
    legend_start_y = grid_y - grid_size - 0 * inch 

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(legend_start_x, legend_start_y + 0.2 * inch, "Risk Level Legend:")

    legend_items = [
        ("Good Day (Score 0)", colors.green),
        ("Low Risk (Score 1-2)", colors.yellow),
        ("Medium Risk (Score 3-4)", colors.blue),
        ("High Risk (Score 5+)", colors.red)
    ]

    lx = legend_start_x
    box_size = 0.15 * inch
    spacing = 1.8 * inch

    for label, col in legend_items:
        c.setFillColor(col)
        c.rect(lx, legend_start_y, box_size, box_size, fill=1)
        
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(lx + box_size + 0.05 * inch, legend_start_y + 2, label)
        
        lx += spacing
        
    # --- MAIN CALENDAR GRID SETUP (Calendar Raised) ---
    
    # 🌟 FIX: Raise the calendar grid to better center it on the page.
    # We move it from 3.5 inches to 2.5 inches from the top.
    calendar_start_y = height - 2.5 * inch 
    
    # Define the height allocated for the 3 rows of months
    # We must reduce this height to ensure the calendar grid finishes before the bottom margin.
    # Total space available for 3 rows: height - 2.5*inch (top) - 0.5*inch (bottom margin) = height - 3.0*inch.
    # Landscape A4 height is approx 8.27 inches. 8.27 - 3.0 = 5.27 inches available.
    # Let's set the height a little lower than max to avoid any cutting.
    total_calendar_height = 4.8 * inch 
    calendar_height = total_calendar_height 
    
    months_per_row = 4
    months_per_col = 3
    
    month_width = calendar_area_width / months_per_row
    month_height = calendar_height / months_per_col
    cell_width = month_width / 7
    cell_height = month_height / 8

    for month in range(1, 13):
        row = (month - 1) // months_per_row
        col = (month - 1) % months_per_row
        
        x_start = margin + col * month_width
        
        y_start = calendar_start_y - (row + 1) * month_height

        # Draw box for the entire month
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.gray)
        c.rect(x_start, y_start, month_width, month_height)

        # --- Month Title ---
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        
        title_y = y_start + month_height - 0.2 * inch
        
        c.drawCentredString(x_start + month_width / 2, title_y, 
                            f"{calendar.month_name[month]} {year}")

        # --- Weekdays ---
        c.setFont("Helvetica-Bold", 7)
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        wd_y = title_y - 0.25 * inch
        
        for i, wd in enumerate(weekdays):
            c.drawCentredString(
                x_start + (i + 0.5) * cell_width,
                wd_y,
                wd
            )

        # Draw line separating weekdays from dates
        c.line(x_start, wd_y - 0.05 * inch, x_start + month_width, wd_y - 0.05 * inch)


        # --- Dates (The core of the calendar) ---
        num_days = calendar.monthrange(year, month)[1]
        start_weekday = datetime(year, month, 1).weekday()
        week_row = 0
        day_col = start_weekday

        date_y_start = wd_y - 0.1 * inch

        for d in range(1, num_days + 1):
            current_date = datetime(year, month, d)
            _, color = risk_score_for_day(chart, birth_root, life_path, current_date)

            date_x_center = x_start + (day_col + 0.5) * cell_width
            date_y = date_y_start - (week_row + 0.5) * cell_height 
            
            box_w = cell_width * 0.9
            box_h = cell_height * 0.9
            c.setFillColor(color)
            c.rect(date_x_center - box_w / 2, date_y - box_h / 2, box_w, box_h, fill=1)
            
            c.setFont("Helvetica-Bold", 9)
            if color in [colors.blue, colors.red]:
                c.setFillColor(colors.white)
            else:
                c.setFillColor(colors.black)
                
            c.drawCentredString(date_x_center, date_y - 4, f"{d}") 

            day_col += 1
            if day_col > 6:
                day_col = 0
                week_row += 1

    c.save()
    print(f"\nPDF calendar saved as {filename}")

# --- Main ---
if __name__ == "__main__":
    print(Style.BRIGHT + Fore.CYAN + "--- Numerology Calendar Generator ---")
    name = input("Enter Full Name: ")
    dob_input = input("Enter DOB (DD/MM/YYYY): ")
    year_input = int(input("Enter Year (YYYY): "))

    generate_pdf_calendar(name, dob_input, year_input)