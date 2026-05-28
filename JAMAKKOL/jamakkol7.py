import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta

def get_jama_planets_for_time(weekday, sunrise, sunset, query_datetime):
    # Fixed Order from Book: Ju, Ma, Me, Su, Snake, Ve, Sa, Mo
    fixed_order = ["Jupiter", "Mars", "Mercury", "Sun", "Snake", "Venus", "Saturn", "Moon"]
    day_lords = {"Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", 
                 "Wednesday": "Mercury", "Thursday": "Jupiter", 
                 "Friday": "Venus", "Saturday": "Saturn"}
    
    # Check if query is during day or night
    query_time = query_datetime.time()
    is_day = sunrise <= query_time <= sunset
    
    # Calculate Day Start
    day_start_p = day_lords[weekday]
    day_start_idx = fixed_order.index(day_start_p)
    
    if is_day:
        # Day Rotation
        rotated_order = fixed_order[day_start_idx:] + fixed_order[:day_start_idx]
        total_duration = datetime.combine(datetime.today(), sunset) - datetime.combine(datetime.today(), sunrise)
        elapsed = datetime.combine(datetime.today(), query_time) - datetime.combine(datetime.today(), sunrise)
    else:
        # Night Logic: Starts with the 5th planet from the day lord
        night_start_idx = (day_start_idx + 4) % 8
        rotated_order = fixed_order[night_start_idx:] + fixed_order[:night_start_idx]
        
        # Calculate elapsed time since sunset
        if query_time > sunset:
            elapsed = datetime.combine(datetime.today(), query_time) - datetime.combine(datetime.today(), sunset)
        else: # Post-midnight
            elapsed = (datetime.combine(datetime.today(), query_time) + timedelta(days=1)) - datetime.combine(datetime.today(), sunset)
        
        # Approximate night duration (Sunset to next Sunrise)
        total_duration = timedelta(hours=12) 

    jamam_len = total_duration / 8
    active_idx = min(int(elapsed / jamam_len), 7)
    return rotated_order, rotated_order[active_idx], "Day" if is_day else "Night"

def draw_final_jamakkol_system(weekday, sunrise_str, sunset_str, query_str, transit_data, points_data):
    sunrise = datetime.strptime(sunrise_str, "%H:%M").time()
    sunset = datetime.strptime(sunset_str, "%H:%M").time()
    query_dt = datetime.strptime(query_str, "%H:%M")
    
    # 1. SCIENTIFIC CALCULATIONS
    jama_sequence, active_p, period = get_jama_planets_for_time(weekday, sunrise, sunset, query_dt)
    
    # 2. ANALYSIS
    udh, aru, cha = points_data['UDH'], points_data['ARU'], points_data['CHA']
    house_pos = (aru - udh) % 12 + 1
    
    # 3. VISUALIZATION
    fig, (ax, ax_text) = plt.subplots(1, 2, figsize=(22, 12), gridspec_kw={'width_ratios': [1.2, 1]})
    ax.set_xlim(-1, 5); ax.set_ylim(-1, 5); ax.axis("off")
    ax_text.axis("off")

    # [Drawing Logic for Rashi Grid and Outer Strips]
    grid_map = {11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3), 10:(0,2), 3:(3,2), 
                9:(0,1), 4:(3,1), 8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)}
    
    for x in range(4):
        for y in range(4):
            if (x,y) not in [(1,1),(1,2),(2,1),(2,2)]:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, linewidth=2, edgecolor='#333333'))

    # Draw Outer Strips (Top, Right, Bottom, Left)
    # ... (Refer to previous code for detailed Rectangle/ax.plot logic) ...
    
    # Label Points (Blue Bold)
    for lbl, s_idx in points_data.items():
        gx, gy = grid_map[s_idx]
        ax.text(gx+0.5, gy+0.2, lbl, ha='center', fontweight='bold', color='blue', fontsize=16)

    # 4. REPORT
    report = (
        f"JAMAKKOL SCIENTIFIC REPORT\n"
        f"==========================\n"
        f"Period: {period} Jamam\n"
        f"Active Planet: {active_p.upper()}\n\n"
        f"PREDICTION LOGIC:\n"
        f"-----------------\n"
        f"House Focus: {house_pos}\n"
    )
    if udh == cha: report += "⚠️ BLOCK: Chathiram is on Udhayam.\n"
    if aru == cha: report += "⚠️ BLOCK: Chathiram is on Aarudam.\n"
    
    ax_text.text(0, 0.5, report, fontsize=16, va='center', family='monospace', 
                 bbox=dict(facecolor='white', edgecolor='black', pad=10))
    
    plt.show()

# --- RUNNING THE PRASANAM ---
# Example: Sunday Night query at 9:00 PM (21:00)
draw_final_jamakkol_system(
    weekday="Sunday",
    sunrise_str="06:00",
    sunset_str="18:00",
    query_str="21:00",
    transit_data={},
    points_data={'UDH': 0, 'ARU': 6, 'CHA': 11}
)