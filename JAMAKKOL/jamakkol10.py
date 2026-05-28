import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta
import geocoder
from suntime import Sun

def get_jama_degree(elapsed_in_jamam, jamam_len):
    """Calculates the degree of the Jama planet (0-30°) based on time elapsed."""
    # (Elapsed time / Total Jamam time) * 30 degrees
    ratio = elapsed_in_jamam.total_seconds() / jamam_len.total_seconds()
    total_degrees = ratio * 30
    deg = int(total_degrees)
    min_dec = (total_degrees - deg) * 60
    return f"{deg}°{int(min_dec)}'"

def get_jama_logic_with_degrees(weekday, query_dt, sr, ss):
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
    
    # Calculate degree for ALL 8 Jama planets (all move together in this system)
    time_into_current_jamam = elapsed % jamam_len
    current_degree = get_jama_degree(time_into_current_jamam, jamam_len)
    
    return rotated, rotated[active_idx], current_degree

def draw_final_scientific_chart(rotated_jama, jama_degree, regular_planets, points):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(-1, 5); ax.set_ylim(-1, 5); ax.axis("off")

    grid = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
            9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}

    # Draw Rashi Grid
    for sign_idx, (gx, gy) in grid.items():
        ax.add_patch(Rectangle((gx, gy), 1, 1, fill=False, lw=2))
        
        # 1. Place ALL Regular Inner Planets (Gocharam)
        if sign_idx in regular_planets:
            planets = regular_planets[sign_idx]
            # Split into two lines if many planets
            mid = len(planets)//2 + 1
            ax.text(gx+0.5, gy+0.8, ", ".join(planets[:mid]), ha='center', fontsize=9)
            if len(planets) > mid:
                ax.text(gx+0.5, gy+0.65, ", ".join(planets[mid:]), ha='center', fontsize=9)
        
        # 2. Place Special Points
        for label, p_idx in points.items():
            if p_idx == sign_idx:
                ax.text(gx+0.5, gy+0.2, label, ha='center', color='blue', fontweight='bold', fontsize=12)

    # 3. Draw Outer Jama Planets with Degrees
    # Positions: Top(Ar,Ta,Ge,Cn), Right(Le,Vi,Li,Sc), Bottom(Sa,Cp,Aq,Pi) is rotated based on time
    outer_pos = [(1.75, 4.2), (3.25, 4.2), (4.2, 2.25), (4.2, 0.75), 
                 (2.25, -0.2), (0.75, -0.2), (-0.2, 1.75), (-0.2, 3.25)]
    
    for i, (ox, oy) in enumerate(outer_pos):
        color = "#cc0033" if rotated_jama[i] == active_p else "#666666"
        ax.add_patch(Rectangle((ox-0.5, oy-0.15), 1.0, 0.4, color=color))
        # Display Planet Name + Calculated Degree
        ax.text(ox, oy+0.05, f"{rotated_jama[i]}", color='white', ha='center', fontweight='bold', fontsize=8)
        ax.text(ox, oy-0.1, f"{jama_degree}", color='yellow', ha='center', fontsize=7)

    plt.title(f"Jamakkol Chart - Active Degree: {jama_degree}", fontsize=15)
    plt.show()

# ==========================================
# INPUT ALL 9 REGULAR PLANETS HERE
# ==========================================
# 0=Aries, 1=Taurus, 2=Gemini, 3=Cancer, 4=Leo, 5=Virgo, 
# 6=Libra, 7=Scorpio, 8=Sagittarius, 9=Capricorn, 10=Aquarius, 11=Pisces
regular_astrology = {
    0: ["Jupiter"],
    2: ["Mars"],
    3: ["Moon"],
    7: ["Sun", "Mercury", "Ketu"],
    1: ["Rahu"],
    9: ["Venus"],
    10: ["Saturn"]
}

# Run Engine
# (Assume sunrise/sunset logic from previous steps)
# pts = {'UDH': 0, 'ARU': 3, 'CHA': 11}
# draw_final_scientific_chart(rotated, active_deg, regular_astrology, pts)