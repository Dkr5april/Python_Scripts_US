import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

# ==========================================
# 1. THE KARAKATWA ENGINE (EXPANDED)
# ==========================================
def get_planet_karakas(planet):
    """Based on S. Gopalakrishnan's book - Chapter 6 & Appendix."""
    data = {
        "Sun": "Govt, Father, Status, Administration, Heart, Power.",
        "Moon": "Mother, Mind, Travel, Liquids, Emotions, Changes.",
        "Mars": "Property, Land, Surgery, Debt, Siblings, Fire.",
        "Mercury": "Education, Trade, Logic, Uncle, Writing, Communication.",
        "Jupiter": "Gold, Wealth, Children, Wisdom, Justice, Liver.",
        "Venus": "Vehicle, Marriage, Luxury, Art, Wife, Comfort.",
        "Saturn": "Labor, Delay, Chronic issues, Longevity, Iron, Hard work.",
        "Snake": "Electronics, MRI/Scans, Foreign travel, Confusion, Photography, X-ray."
    }
    return data.get(planet, "")

def get_house_details(udhayam, aarudam):
    """The 12 Houses of Results logic."""
    house_num = (aarudam - udhayam) % 12 + 1
    meanings = {
        1: "Self/Health", 2: "Family/Finance", 3: "Siblings/Travel", 
        4: "Mother/Property", 5: "Children/Intelligence", 6: "Enemies/Debt/Disease", 
        7: "Spouse/Partners", 8: "Obstacles/Secrets", 9: "Fortune/Father", 
        10: "Job/Status", 11: "Gains/Desires", 12: "Losses/Foreign"
    }
    return house_num, meanings[house_num]

# ==========================================
# 2. THE CALCULATION ENGINE (JAMA MATH)
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
    return rotated, rotated[active_idx], "Day" if is_day else "Night"

# ==========================================
# 3. THE VISUALIZATION ENGINE (MATPLOTLIB)
# ==========================================
def draw_chart(rotated_jama, transit_planets, points, title_info):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 5)
    ax.axis("off")

    grid = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
            9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}

    # Draw Rashi Grid
    for x in range(4):
        for y in range(4):
            if (x,y) not in [(1,1),(1,2),(2,1),(2,2)]:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, lw=2, edgecolor='black'))

    # Draw Outer Jama Planets (Outside the chart)
    # Positions are mapped clockwise: Aries(0), Tau/Gem(1/2), Can/Leo(3/4)...
    ax.add_patch(Rectangle((1,4), 1.5, 0.4, color="#cc0033"))
    ax.text(1.75, 4.2, rotated_jama[0], color='white', ha='center', fontweight='bold')
    ax.add_patch(Rectangle((2.5,4), 1.5, 0.4, color="#cc0033"))
    ax.text(3.25, 4.2, rotated_jama[1], color='white', ha='center', fontweight='bold')
    
    ax.add_patch(Rectangle((4, 1.5), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 2.25, rotated_jama[2], color='white', rotation=270, fontweight='bold')
    ax.add_patch(Rectangle((4, 0), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 0.75, rotated_jama[3], color='white', rotation=270, fontweight='bold')

    ax.add_patch(Rectangle((1.5,-0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(2.25, -0.2, rotated_jama[4], color='white', ha='center', fontweight='bold')
    ax.add_patch(Rectangle((0,-0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(0.75, -0.2, rotated_jama[5], color='white', ha='center', fontweight='bold')

    ax.add_patch(Rectangle((-0.4, 1), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 1.75, rotated_jama[6], color='white', rotation=90, fontweight='bold')
    ax.add_patch(Rectangle((-0.4, 2.5), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 3.25, rotated_jama[7], color='white', rotation=90, fontweight='bold')

    # Plot Interior Data (Transit Planets & Special Points)
    for sign_idx, (gx, gy) in grid.items():
        # Regular Astrology Planets (Transit)
        if sign_idx in transit_planets:
            ax.text(gx+0.5, gy+0.8, ", ".join(transit_planets[sign_idx]), 
                    ha='center', fontsize=9, color='black')
        
        # UDH, ARU, CHA
        for label, p_idx in points.items():
            if p_idx == sign_idx:
                ax.text(gx+0.5, gy+0.2, label, ha='center', color='blue', fontweight='bold')

    plt.title(title_info, fontsize=16, pad=30)
    plt.show()

# ==========================================
# 4. MASTER EXECUTION & PDF GENERATION
# ==========================================
def save_pdf_report(summary_text):
    filename = f"Jamakkol_Prasna_{datetime.now().strftime('%H%M')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 800, "JAMAKKOL PRASANAM SCIENTIFIC REPORT")
    c.setFont("Helvetica", 11)
    y = 770
    for line in summary_text.split('\n'):
        c.drawString(100, y, line)
        y -= 20
    c.save()
    print(f"PDF saved as: {filename}")

def run_jamakkol_engine(udh, aru, cha, transit_data, manual_time=None):
    g = geocoder.ip('me')
    lat, lng = g.latlng
    sun = Sun(lat, lng)
    
    query_dt = datetime.now() if not manual_time else datetime.strptime(manual_time, "%H:%M")
    weekday = query_dt.strftime('%A')
    sr = sun.get_local_sunrise_time().replace(tzinfo=None)
    ss = sun.get_local_sunset_time().replace(tzinfo=None)
    
    rotated, active_p, period = get_jama_logic(weekday, query_dt, sr, ss)
    h_num, h_msg = get_house_details(udh, aru)
    
    block = "CLEAR"
    if udh == cha: block = "CRITICAL: CHATHIRAM BLOCKS UDHAYAM"
    if aru == cha: block = "WARNING: CHATHIRAM BLOCKS AARUDAM"

    summary = (f"Location: {lat}, {lng}\nMode: {period} Jamam\nActive Planet: {active_p}\n"
               f"Question Subject: {h_msg} (House {h_num})\n"
               f"Blockage Status: {block}\n"
               f"Planet Meaning: {get_planet_karakas(active_p)}")

    # Draw Visualization
    pts = {'UDH': udh, 'ARU': aru, 'CHA': cha}
    draw_chart(rotated, transit_data, pts, f"Jamakkol - {weekday} {query_dt.strftime('%H:%M')}")
    
    # Save PDF & Print Report
    save_pdf_report(summary)
    print("\n--- POSSIBILITIES REPORT ---")
    print(summary)

# ==========================================
# INPUT TRANSITS & RUN (Aries=0, Taurus=1 ... Pisces=11)
# ==========================================
transits = {0: ["Jup"], 3: ["Sat"], 7: ["Sun", "Mer"]} # Regular astrology planets
run_jamakkol_engine(udh=0, aru=3, cha=11, transit_data=transits)