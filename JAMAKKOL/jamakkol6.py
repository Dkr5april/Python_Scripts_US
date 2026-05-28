import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_complete_jamakkol_prasanam(jama_outer, transit_data, jama_inner, points_data):
    fig, ax = plt.subplots(figsize=(14, 14))
    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 5)
    ax.axis("off")

    # Mapping 0-11 (Aries-Pisces) to the 4x4 Grid
    grid_map = {
        11:(0,3), 0:(1,3), 1:(2,3), 2:(3,3),
        10:(0,2),             3:(3,2),
        9:(0,1),              4:(3,1),
        8:(0,0), 7:(1,0), 6:(2,0), 5:(3,0)
    }

    # 1. DRAW INNER RASHI GRID
    skip = [(1,1),(1,2),(2,1),(2,2)]
    for x in range(4):
        for y in range(4):
            if (x,y) not in skip:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, linewidth=2, edgecolor='#333333'))

    # Title in the middle of the chart
    ax.text(2, 2.2, "JAMAKKOL", ha="center", va="center", fontsize=22, fontweight="bold", color="#1a1a1a")
    ax.text(2, 1.8, "PRASANAM", ha="center", va="center", fontsize=18, fontweight="bold", color="#cc0033")

    # 2. DRAW OUTER JAMA STRIPS (8 fixed slots)
    # Top Row: Pisces empty
    ax.add_patch(Rectangle((1.0, 4.0), 1.5, 0.4, color="#cc0033"))
    ax.add_patch(Rectangle((2.5, 4.0), 1.5, 0.4, color="#cc0033"))
    ax.text(1.75, 4.2, jama_outer[0], color="white", ha="center", va="center", fontweight="bold")
    ax.text(3.25, 4.2, jama_outer[1], color="white", ha="center", va="center", fontweight="bold")
    ax.plot([2.5, 2.5], [4.0, 4.4], color="white", linewidth=2)

    # Right Column: Gemini empty
    ax.add_patch(Rectangle((4.0, 1.5), 0.4, 1.5, color="#cc0033"))
    ax.add_patch(Rectangle((4.0, 0.0), 0.4, 1.5, color="#cc0033"))
    ax.text(4.2, 2.25, jama_outer[2], color="white", ha="center", va="center", rotation=270, fontweight="bold")
    ax.text(4.2, 0.75, jama_outer[3], color="white", ha="center", va="center", rotation=270, fontweight="bold")
    ax.plot([4.0, 4.4], [1.5, 1.5], color="white", linewidth=2)

    # Bottom Row: Virgo empty
    ax.add_patch(Rectangle((1.5, -0.4), 1.5, 0.4, color="#cc0033"))
    ax.add_patch(Rectangle((0.0, -0.4), 1.5, 0.4, color="#cc0033"))
    ax.text(2.25, -0.2, jama_outer[4], color="white", ha="center", va="center", fontweight="bold")
    ax.text(0.75, -0.2, jama_outer[5], color="white", ha="center", va="center", fontweight="bold")
    ax.plot([1.5, 1.5], [-0.4, 0.0], color="white", linewidth=2)

    # Left Column: Sagittarius empty
    ax.add_patch(Rectangle((-0.4, 1.0), 0.4, 1.5, color="#cc0033"))
    ax.add_patch(Rectangle((-0.4, 2.5), 0.4, 1.5, color="#cc0033"))
    ax.text(-0.2, 1.75, jama_outer[6], color="white", ha="center", va="center", rotation=90, fontweight="bold")
    ax.text(-0.2, 3.25, jama_outer[7], color="white", ha="center", va="center", rotation=90, fontweight="bold")
    ax.plot([-0.4, 0.0], [2.5, 2.5], color="white", linewidth=2)

    # 3. FILL INNER DATA (Transit, Jama Inner, Special Points)
    for i in range(12):
        gx, gy = grid_map[i]
        
        # Transit Planets (Regular + Mandi) - Top Section
        if i in transit_data:
            t_txt = " ".join(transit_data[i])
            ax.text(gx+0.5, gy+0.8, t_txt, ha='center', fontsize=9, color="black")
            
        # Jama Inner Planets (Calculated) - Middle Section
        if i in jama_inner:
            j_txt = " ".join(jama_inner[i])
            ax.text(gx+0.5, gy+0.5, j_txt, ha='center', fontsize=10, color="#cc0033", fontweight="bold")
            
        # Special Points (UDH, ARU, CHA) - Bottom Section
        if i in points_data:
            p_txt = " ".join(points_data[i])
            ax.text(gx+0.5, gy+0.2, p_txt, ha='center', fontsize=11, fontweight='bold', color='blue')

    plt.show()

# --- EXAMPLE DATA WITH MANDI & CHATHIRAM ---

# Outer Fixed Jama Slots
jama_fixed_outer = [
    "Sun 12°", "Moon 08°", "Mars 04°", "Merc 21°", 
    "Jup 15°", "Ven 19°", "Sat 02°", "Snake 25°"
]

# Transit Data including Mandi (MD)
transit_planets = {
    0:  ["Sun 12°", "MD 05°"], # Aries has Sun and Mandi
    11: ["Sa 18°", "Snake 20°"],
    4:  ["Ma 25°", "Ket 25°"]
}

# Calculated Jama Planets for this specific time cycle
jama_calculated_inner = {
    0: ["(Sun)"],
    11: ["(Snake)"]
}

# Points using "CHA" for Chathiram (Kavippu)
prasanam_points = {
    0: ["UDH 10°"], # Udhayam
    6: ["ARU 22°"], # Aarudam
    11: ["CHA 15°"] # Chathiram (Kavippu)
}

draw_complete_jamakkol_prasanam(jama_fixed_outer, transit_planets, jama_calculated_inner, prasanam_points)