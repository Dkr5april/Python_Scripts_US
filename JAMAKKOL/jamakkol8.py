import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. THE KARAKATWA ENGINE (SIGNIFICATIONS)
# ==========================================
def get_planet_karakas(planet):
    """Based on Chapter 6 of S. Gopalakrishnan's book."""
    data = {
        "Sun": "Govt, Father, Status, Soul, Power, Heart, Bones.",
        "Moon": "Mother, Mind, Travel, Liquids, Emotions, Changes.",
        "Mars": "Property, Land, Surgery, Debt, Siblings, Courage.",
        "Mercury": "Education, Trade, Logic, Uncle, Communication, Writing.",
        "Jupiter": "Gold, Wealth, Children, Wisdom, Justice, Liver.",
        "Venus": "Vehicle, Marriage, Luxury, Art, Wife, Comfort.",
        "Saturn": "Labor, Delay, Chronic issues, Longevity, Iron, Hard work.",
        "Snake": "Electronics, MRI/Scans, Foreign travel, Confusion, Photography."
    }
    return data.get(planet, "")

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
        # Night starts with 5th planet from Day Lord
        night_idx = (start_idx + 4) % 8
        rotated = fixed_order[night_idx:] + fixed_order[:night_idx]
        # Sunrise of next day for night duration calc
        elapsed = query_dt - ss if query_dt > ss else (query_dt + timedelta(days=1)) - ss
        total_dur = timedelta(hours=12) # Approximation

    jamam_len = total_dur / 8
    active_idx = min(int(elapsed / jamam_len), 7)
    return rotated, rotated[active_idx], "Day" if is_day else "Night"

# ==========================================
# 3. THE VISUALIZATION ENGINE (MATPLOTLIB)
# ==========================================
def draw_chart(rotated_jama, points, title_info):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 5)
    ax.axis("off")

    # Mapping Sign Index to Grid Coordinates
    grid = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
            9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}

    # Draw Rashi Grid
    for x in range(4):
        for y in range(4):
            if (x,y) not in [(1,1),(1,2),(2,1),(2,2)]:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, linewidth=2, edgecolor='black'))

    # Draw Outer Red Strips
    # Top
    ax.add_patch(Rectangle((1,4), 1.5, 0.4, color="#cc0033"))
    ax.add_patch(Rectangle((2.5,4), 1.5, 0.4, color="#cc0033"))
    ax.text(1.75, 4.2, rotated_jama[0], color='white', ha='center', fontweight='bold')
    ax.text(3.25, 4.2, rotated_jama[1], color='white', ha='center', fontweight='bold')
    ax.plot([2.5, 2.5], [4, 4.4], color='white', lw=2)
    
    # Right
    ax.add_patch(Rectangle((4, 1.5), 0.4, 1.5, color="#cc0033"))
    ax.add_patch(Rectangle((4, 0), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 2.25, rotated_jama[2], color='white', rotation=270, fontweight='bold')
    ax.text(4.2, 0.75, rotated_jama[3], color='white', rotation=270, fontweight='bold')
    ax.plot([4, 4.4], [1.5, 1.5], color='white', lw=2)

    # Bottom
    ax.add_patch(Rectangle((1.5,-0.4), 1.5, 0.4, color="#cc0033"))
    ax.add_patch(Rectangle((0,-0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(2.25, -0.2, rotated_jama[4], color='white', ha='center', fontweight='bold')
    ax.text(0.75, -0.2, rotated_jama[5], color='white', ha='center', fontweight='bold')
    ax.plot([1.5, 1.5], [-0.4, 0], color='white', lw=2)

    # Left
    ax.add_patch(Rectangle((-0.4, 1), 0.4, 1.5, color="#cc0033"))
    ax.add_patch(Rectangle((-0.4, 2.5), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 1.75, rotated_jama[6], color='white', rotation=90, fontweight='bold')
    ax.text(-0.2, 3.25, rotated_jama[7], color='white', rotation=90, fontweight='bold')
    ax.plot([-0.4, 0], [2.5, 2.5], color='white', lw=2)

    # Plot Points
    for label, idx in points.items():
        gx, gy = grid[idx]
        ax.text(gx+0.5, gy+0.3, label, ha='center', color='blue', fontweight='bold', fontsize=14)

    plt.title(title_info, fontsize=16, pad=30)
    plt.show()

# ==========================================
# 4. THE MASTER EXECUTION FUNCTION
# ==========================================
def run_jamakkol_engine(udh, aru, cha, manual_time=None):
    # GPS & Sun Logic
    g = geocoder.ip('me')
    lat, lng = g.latlng
    sun = Sun(lat, lng)
    
    query_dt = datetime.now() if not manual_time else datetime.strptime(manual_time, "%H:%M")
    weekday = query_dt.strftime('%A')
    
    sr = sun.get_local_sunrise_time().replace(tzinfo=None)
    ss = sun.get_local_sunset_time().replace(tzinfo=None)
    
    rotated, active_p, period = get_jama_logic(weekday, query_dt, sr, ss)
    h_num, h_msg = get_house_details(udh, aru)
    
    # Analysis Rules
    block = "CLEAR"
    if udh == cha: block = "CRITICAL: CHATHIRAM BLOCKS UDHAYAM"
    if aru == cha: block = "WARNING: CHATHIRAM BLOCKS AARUDAM"

    summary = (f"Mode: {period} | Active: {active_p}\n"
               f"Question: {h_msg}\n"
               f"Status: {block}\n"
               f"Karaka: {get_planet_karakas(active_p)}")

    # Visualize
    pts = {'UDH': udh, 'ARU': aru, 'CHA': cha}
    draw_chart(rotated, pts, f"Jamakkol - {weekday} {query_dt.strftime('%H:%M')}")
    
    print("\n--- REPORT ---")
    print(summary)

# ==========================================
# USE: Enter Sign Indices (0-11)
# Aries=0, Taurus=1 ... Pisces=11
# ==========================================
run_jamakkol_engine(udh=0, aru=3, cha=11)