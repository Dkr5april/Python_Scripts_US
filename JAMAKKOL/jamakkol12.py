import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# ==========================================
# 1. CORE DATA & KARAKATWAS (Chapter 6)
# ==========================================
PLANET_KARAKAS = {
    "Sun": "Govt, Father, Status, Soul, Power, Heart, Bones.",
    "Moon": "Mother, Mind, Travel, Liquids, Emotions, Changes.",
    "Mars": "Property, Land, Surgery, Debt, Siblings, Courage.",
    "Mercury": "Education, Trade, Logic, Uncle, Communication, Writing.",
    "Jupiter": "Gold, Wealth, Children, Wisdom, Justice, Liver.",
    "Venus": "Vehicle, Marriage, Luxury, Art, Wife, Comfort.",
    "Saturn": "Labor, Delay, Chronic issues, Longevity, Iron, Hard work.",
    "Snake": "Electronics, MRI/Scans, Foreign travel, Confusion, Photography."
}

# SCIENTIFIC DATA: Rashmi, Directions, Veedhi
RASHI_META = {
    0: {"name": "Aries", "dir": "Triyagmukha", "rashmi": 7, "veedhi": "Gaja"},
    1: {"name": "Taurus", "dir": "Triyagmukha", "rashmi": 8, "veedhi": "Gaja"},
    2: {"name": "Gemini", "dir": "Triyagmukha", "rashmi": 5, "veedhi": "Vrshabha"},
    3: {"name": "Cancer", "dir": "Urdvamukha", "rashmi": 3, "veedhi": "Vrshabha"},
    4: {"name": "Leo", "dir": "Urdvamukha", "rashmi": 7, "veedhi": "Vrshabha"},
    5: {"name": "Virgo", "dir": "Triyagmukha", "rashmi": 11, "veedhi": "Airavatha"},
    6: {"name": "Libra", "dir": "Triyagmukha", "rashmi": 2, "veedhi": "Airavatha"},
    7: {"name": "Scorpio", "dir": "Adomukha", "rashmi": 4, "veedhi": "Airavatha"},
    8: {"name": "Sagittarius", "dir": "Urdvamukha", "rashmi": 9, "veedhi": "Mrga"},
    9: {"name": "Capricorn", "dir": "Adomukha", "rashmi": 8, "veedhi": "Mrga"},
    10: {"name": "Aquarius", "dir": "Triyagmukha", "rashmi": 8, "veedhi": "Mrga"},
    11: {"name": "Pisces", "dir": "Urdvamukha", "rashmi": 27, "veedhi": "Gaja"}
}

def get_house_details(udhayam, aarudam):
    """The 12 Houses of Results logic."""
    house_num = (aarudam - udhayam) % 12 + 1
    meanings = {
        1: "Self, health, or personal identity.",
        2: "Family, finance, or speech.",
        3: "Siblings, courage, or short travels.",
        4: "Mother, house, land, or vehicles.",
        5: "Children, creativity, or past merit.",
        6: "Debts, disease, or enemies.",
        7: "Spouse, partnership, or public image.",
        8: "Obstacles, longevity, or secrets.",
        9: "Father, fortune, or long distance travel.",
        10: "Job, career, or status.",
        11: "Gains, desires, or elder siblings.",
        12: "Losses, expenditure, or foreign stay."
    }
    return house_num, meanings[house_num]

# ==========================================
# 2. CALCULATION ENGINE (JAMA MATH & DEGREES)
# ==========================================
def get_jama_logic(weekday, query_dt, sr, ss):
    fixed_order = ["Jupiter", "Mars", "Mercury", "Sun", "Snake", "Venus", "Saturn", "Moon"]
    day_lords = {"Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", 
                 "Wednesday": "Mercury", "Thursday": "Jupiter", 
                 "Friday": "Venus", "Saturday": "Saturn"}
    
    is_day = sr <= query_dt <= ss
    start_p = day_lords[weekday]
    start_idx = fixed_order.index(start_p)

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
    float_deg = (time_into_jamam.total_seconds() / jamam_len.total_seconds()) * 30
    deg = int(float_deg)
    minutes = int((float_deg - deg) * 60)
    
    return rotated, rotated[active_idx], f"{deg}°{minutes}'", "Day" if is_day else "Night"

# ==========================================
# 3. THE PDF GENERATION (WITH VISUAL CHART)
# ==========================================
def generate_pdf_report(filename, report_info, rotated_jama, jama_deg, reg_transits, points):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 810, "JAMAKKOL PRASANAM SCIENTIFIC REPORT")
    c.line(50, 805, 550, 805)

    # Drawing the Rasi Chart
    chart_x, chart_y, size = 150, 480, 300
    cell = size / 4
    grid = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
            9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}
    
    for sign, (gx, gy) in grid.items():
        rx, ry = chart_x + (gx * cell), chart_y + (gy * cell)
        c.rect(rx, ry, cell, cell)
        
        # Add Rashi Scientific Metadata
        c.setFont("Helvetica-Oblique", 6)
        c.drawString(rx+2, ry+65, f"{RASHI_META[sign]['dir']}")
        c.drawString(rx+2, ry+58, f"R:{RASHI_META[sign]['rashmi']} V:{RASHI_META[sign]['veedhi']}")

        # Inner Regular Planets with Degrees
        if sign in reg_transits:
            c.setFont("Helvetica-Bold", 7)
            y_off = 48
            for p_name, p_deg in reg_transits[sign].items():
                c.drawString(rx+5, ry+y_off, f"{p_name} ({p_deg})")
                y_off -= 8
            
        # UDH, ARU, CHA
        c.setFont("Helvetica-Bold", 10)
        for label, idx in points.items():
            if idx == sign:
                c.drawString(rx+15, ry+12, label)

    # Draw JAMA PLANETS (OUTSIDE THE CHART)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0.7, 0, 0)
    jama_pos = [
        (chart_x+50, chart_y+310), (chart_x+180, chart_y+310), # Top
        (chart_x+310, chart_y+180), (chart_x+310, chart_y+50), # Right
        (chart_x+180, chart_y-20), (chart_x+50, chart_y-20),   # Bottom
        (chart_x-60, chart_y+50), (chart_x-60, chart_y+180)    # Left
    ]
    for i, (jx, jy) in enumerate(jama_pos):
        c.drawString(jx, jy, f"{rotated_jama[i]} ({jama_deg})")

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    y_text = 440
    for line in report_info.split('\n'):
        c.drawString(50, y_text, line)
        y_text -= 18
    
    c.save()
    print(f"\n✅ REPORT READY: {filename}")

# ==========================================
# 4. EXECUTION
# ==========================================
def run_jamakkol_engine(udh, aru, cha, regular_transits):
    g = geocoder.ip('me')
    lat, lng = g.latlng
    sun = Sun(lat, lng)
    
    now = datetime.now()
    sr = sun.get_local_sunrise_time().replace(tzinfo=None)
    ss = sun.get_local_sunset_time().replace(tzinfo=None)
    
    rotated, active_p, j_deg, mode = get_jama_logic(now.strftime('%A'), now, sr, ss)
    h_num, h_msg = get_house_details(udh, aru)
    
    # SCIENTIFIC ANALYSIS LOGIC
    u_meta = RASHI_META[udh]
    a_meta = RASHI_META[aru]
    
    block_status = "CLEAR"
    if udh == cha: block_status = "BLOCKED: Kavippu on Udhayam"
    elif aru == cha: block_status = "BLOCKED: Kavippu on Aarudam"

    # Probability Calculation based on Scientific Concepts
    score = 0
    if a_meta['dir'] == "Urdvamukha": score += 20
    score += a_meta['rashmi']
    if h_num in [1,4,7,10]: score += 30
    if block_status == "CLEAR": score += 40

    report = (
        f"Time: {now.strftime('%Y-%m-%d %H:%M')} | Mode: {mode}\n"
        f"Active Jama Planet: {active_p} ({j_deg})\n"
        f"Query House: {h_num} ({h_msg})\n"
        f"Blockage: {block_status}\n"
        f"Rashi Strength: {a_meta['rashmi']} Rashmi\n"
        f"Veedhi: {a_meta['veedhi']} | Direction: {a_meta['dir']}\n"
        f"Scientific Probability: {min(score, 100)}%\n"
        f"Karaka: {PLANET_KARAKAS.get(active_p)}"
    )

    filename = f"Jamakkol_Scientific_{now.strftime('%H%M')}.pdf"
    generate_pdf_report(filename, report, rotated, j_deg, regular_transits, {'UDH':udh, 'ARU':aru, 'CHA':cha})
    print(report)

# --- RUN THE ENGINE ---
# regular_transits: {SignIndex: {PlanetName: Degree}}
inner_planets_with_degrees = {
    0: {"Jup": "12°14'"},
    1: {"Rah": "05°30'"},
    3: {"Sat": "18°45'"},
    7: {"Sun": "22°10'", "Mer": "15°05'"},
    11: {"Ket": "05°30'"}
}

run_jamakkol_engine(udh=0, aru=3, cha=11, regular_transits=inner_planets_with_degrees)