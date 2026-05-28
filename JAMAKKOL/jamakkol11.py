import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# ==========================================
# 1. CORE DATA & RULES (ALL 9 PLANETS)
# ==========================================
PLANET_KARAKAS = {
    "Sun": "Government, Father, Status, Bones.",
    "Moon": "Mother, Mind, Liquids, Travel.",
    "Mars": "Property, Surgery, Siblings, Debt.",
    "Mercury": "Education, Trade, Logic, Communication.",
    "Jupiter": "Gold, Wealth, Children, Wisdom.",
    "Venus": "Vehicle, Marriage, Luxury, Art.",
    "Saturn": "Labor, Delay, Chronic issues, Longevity.",
    "Snake": "Electronics, Scans, Foreign travel, Confusion."
}

def get_house_details(udh, aru):
    house_num = (aru - udh) % 12 + 1
    meanings = {
        1: "Self/Health", 2: "Family/Finance", 3: "Efforts/Siblings", 4: "Mother/Property",
        5: "Children/Intelligence", 6: "Debt/Disease/Enemies", 7: "Partnership/Spouse",
        8: "Obstacles/Secrets", 9: "Fortune/Long Travel", 10: "Job/Action",
        11: "Gains/Desires", 12: "Losses/Expenditure"
    }
    return house_num, meanings.get(house_num)

# ==========================================
# 2. CALCULATION & DEGREES
# ==========================================
def get_jama_data(weekday, query_dt, sr, ss):
    fixed_order = ["Jupiter", "Mars", "Mercury", "Sun", "Snake", "Venus", "Saturn", "Moon"]
    day_lords = {"Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury", 
                 "Thursday": "Jupiter", "Friday": "Venus", "Saturday": "Saturn"}
    
    is_day = sr <= query_dt <= ss
    start_idx = fixed_order.index(day_lords[weekday])
    
    if is_day:
        rotated = fixed_order[start_idx:] + fixed_order[:start_idx]
        total_dur = ss - sr
        elapsed = query_dt - sr
    else:
        night_idx = (start_idx + 4) % 8
        rotated = fixed_order[night_idx:] + fixed_order[:night_idx]
        elapsed = query_dt - ss if query_dt > ss else (query_dt + timedelta(days=1)) - ss
        total_dur = timedelta(hours=12) 

    jamam_len = total_dur / 8
    active_idx = min(int(elapsed / jamam_len), 7)
    
    # Calculate Degree (0-30)
    time_into_jamam = elapsed % jamam_len
    deg = int((time_into_jamam.total_seconds() / jamam_len.total_seconds()) * 30)
    
    return rotated, rotated[active_idx], f"{deg}°", "Day" if is_day else "Night"

# ==========================================
# 3. PDF REPORT WITH VISUAL CHART
# ==========================================
def generate_pdf_report(filename, report_info, rotated_jama, regular_planets, points):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "JAMAKKOL PRASANAM SCIENTIFIC REPORT")
    c.line(50, 795, 550, 795)

    # Drawing the Rasi Chart in PDF
    c.setLineWidth(1)
    chart_x, chart_y, size = 150, 450, 300
    cell = size / 4
    
    # Draw 4x4 Grid
    grid_coords = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
                   9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}
    
    for sign, (gx, gy) in grid_coords.items():
        rx, ry = chart_x + (gx * cell), chart_y + (gy * cell)
        c.rect(rx, ry, cell, cell)
        
        # Add Inner Regular Planets
        if sign in regular_planets:
            c.setFont("Helvetica", 8)
            c.drawString(rx+5, ry+55, ", ".join(regular_planets[sign]))
            
        # Add UDH, ARU, CHA
        c.setFont("Helvetica-Bold", 10)
        for label, idx in points.items():
            if idx == sign:
                c.drawString(rx+15, ry+15, label)

    # Text Report Below Chart
    c.setFont("Helvetica", 11)
    y_text = 400
    for line in report_info.split('\n'):
        c.drawString(50, y_text, line)
        y_text -= 20
    
    c.save()
    print(f"\n✅ PDF GENERATED: {filename}")

# ==========================================
# 4. EXECUTION
# ==========================================
def run_prasnam(udh, aru, cha, regular_transits):
    g = geocoder.ip('me')
    lat, lng = g.latlng
    sun = Sun(lat, lng)
    
    now = datetime.now()
    sr = sun.get_local_sunrise_time().replace(tzinfo=None)
    ss = sun.get_local_sunset_time().replace(tzinfo=None)
    
    rotated, active_p, deg, mode = get_jama_data(now.strftime('%A'), now, sr, ss)
    h_num, h_msg = get_house_details(udh, aru)
    
    # Blockage Logic
    block_status = "CLEAR (The path is open)"
    if udh == cha: block_status = "BLOCKED: Kavippu is on the Querent (Confusion/Hurdles)"
    elif aru == cha: block_status = "BLOCKED: Kavippu is on the Goal (Obstacles/Failure)"

    report = (
        f"Time: {now.strftime('%Y-%m-%d %H:%M')} | Mode: {mode}\n"
        f"Active Jama Planet: {active_p} at {deg}\n"
        f"Query House: {h_num} ({h_msg})\n"
        f"Blockage Status: {block_status}\n"
        f"Success Probability: {'HIGH' if h_num in [1,4,7,10] and 'CLEAR' in block_status else 'LOW/DELAY'}\n"
        f"Planet Meaning: {PLANET_KARAKAS.get(active_p)}"
    )

    filename = f"Jamakkol_Result_{now.strftime('%H%M')}.pdf"
    generate_pdf_report(filename, report, rotated, regular_transits, {'UDH':udh, 'ARU':aru, 'CHA':cha})
    
    print(report)

# --- RUN IT ---
# Enter indices 0-11 for signs (Aries=0...Pisces=11)
# regular_transits includes ALL 9 planets (Sun, Moon, Mars, Mer, Jup, Ven, Sat, Rah, Ket)
regular_transits = {
    0: ["Jup"], 1: ["Rah"], 3: ["Sat"], 7: ["Sun", "Mer", "Ket"], 9: ["Ven"], 10: ["Mar"]
}
run_prasnam(udh=0, aru=3, cha=11, regular_transits=regular_transits)