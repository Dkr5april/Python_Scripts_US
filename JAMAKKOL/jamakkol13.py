import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. SCIENTIFIC DATA & HOUSE LOGIC
# ==========================================
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

def get_house_details(udh, aru):
    house_num = (aru - udh) % 12 + 1
    meanings = {
        1: "Self/Identity", 2: "Finance/Family", 3: "Efforts", 4: "Property/Mother",
        5: "Intelligence", 6: "Enemies/Debt", 7: "Partners", 8: "Obstacles",
        9: "Fortune", 10: "Action/Job", 11: "Gains", 12: "Losses"
    }
    return house_num, meanings.get(house_num)

# ==========================================
# 2. CALCULATION ENGINE (TIME & DEGREES)
# ==========================================
def get_jama_data(weekday, query_dt, sr, ss):
    fixed_order = ["Jupiter", "Mars", "Mercury", "Sun", "Snake", "Venus", "Saturn", "Moon"]
    day_lords = {"Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", 
                 "Wednesday": "Mercury", "Thursday": "Jupiter", 
                 "Friday": "Venus", "Saturday": "Saturn"}
    
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
    
    # Calculate Degree
    time_into_jamam = elapsed % jamam_len
    float_deg = (time_into_jamam.total_seconds() / jamam_len.total_seconds()) * 30
    deg_str = f"{int(float_deg)}°{int((float_deg % 1) * 60)}'"
    
    return rotated, rotated[active_idx], deg_str, "Day" if is_day else "Night"

# ==========================================
# 3. DRAWING THE SOUTH INDIAN CHART (DIVYACHAKSHU STYLE)
# ==========================================
def draw_south_indian_scientific_chart(rotated_jama, jama_deg, transit_data, points_data, active_p, mode):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(-1, 5); ax.set_ylim(-1, 5); ax.axis("off")

    # Mapping for South Indian Chart
    grid_map = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
                9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}

    # 1. Draw Grid
    skip = [(1,1),(1,2),(2,1),(2,2)]
    for x in range(4):
        for y in range(4):
            if (x,y) not in skip:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, lw=1.5, edgecolor='#333333'))

    ax.text(2, 2, f"JAMAKKOL\n{mode} MODE", ha="center", va="center", fontsize=14, fontweight="bold")

    # 2. Place Outer Jama Planets in Red Strips
    # Top
    ax.add_patch(Rectangle((1, 4), 1.5, 0.4, color="#cc0033"))
    ax.text(1.75, 4.2, f"{rotated_jama[0]} {jama_deg}", color="white", ha="center", fontsize=9)
    ax.add_patch(Rectangle((2.5, 4), 1.5, 0.4, color="#cc0033"))
    ax.text(3.25, 4.2, f"{rotated_jama[1]} {jama_deg}", color="white", ha="center", fontsize=9)
    ax.plot([2.5, 2.5], [4, 4.4], color="white", lw=2)

    # Right
    ax.add_patch(Rectangle((4, 1.5), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 2.25, f"{rotated_jama[2]} {jama_deg}", color="white", rotation=270, fontsize=9)
    ax.add_patch(Rectangle((4, 0), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 0.75, f"{rotated_jama[3]} {jama_deg}", color="white", rotation=270, fontsize=9)
    ax.plot([4, 4.4], [1.5, 1.5], color="white", lw=2)

    # Bottom
    ax.add_patch(Rectangle((1.5, -0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(2.25, -0.2, f"{rotated_jama[4]} {jama_deg}", color="white", ha="center", fontsize=9)
    ax.add_patch(Rectangle((0, -0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(0.75, -0.2, f"{rotated_jama[5]} {jama_deg}", color="white", ha="center", fontsize=9)
    ax.plot([1.5, 1.5], [-0.4, 0], color="white", lw=2)

    # Left
    ax.add_patch(Rectangle((-0.4, 1), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 1.75, f"{rotated_jama[6]} {jama_deg}", color="white", rotation=90, fontsize=9)
    ax.add_patch(Rectangle((-0.4, 2.5), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 3.25, f"{rotated_jama[7]} {jama_deg}", color="white", rotation=90, fontsize=9)
    ax.plot([-0.4, 0], [2.5, 2.5], color="white", lw=2)

    # 3. Inner Data (Transits & Points)
    for i, (gx, gy) in grid_map.items():
        # Metadata (Scientific Evidence)
        ax.text(gx+0.1, gy+0.85, f"{RASHI_META[i]['dir'][0]} R:{RASHI_META[i]['rashmi']}", fontsize=7, alpha=0.6)
        
        if i in transit_data:
            ax.text(gx+0.5, gy+0.6, " ".join(transit_data[i]), ha='center', fontsize=9)
        if i in points_data:
            ax.text(gx+0.5, gy+0.25, " ".join(points_data[i]), ha='center', fontsize=11, fontweight='bold', color='blue')

    plt.show()

# --- EXECUTION ---
# Enter indices (Aries=0...Pisces=11)
udh, aru, cha = 0, 3, 11
transits = {0: ["Jup(12°)"], 7: ["Sun(22°)", "Mer(15°)"], 3: ["Sat(18°)"]}

# Sun Logic
g = geocoder.ip('me')
lat, lng = g.latlng
sun = Sun(lat, lng)
now = datetime.now()
sr = sun.get_local_sunrise_time().replace(tzinfo=None)
ss = sun.get_local_sunset_time().replace(tzinfo=None)

rotated, active_p, j_deg, mode = get_jama_data(now.strftime('%A'), now, sr, ss)
pts = {udh: ["UDH"], aru: ["ARU"], cha: ["CHA"]}

draw_south_indian_scientific_chart(rotated, j_deg, transits, pts, active_p, mode)