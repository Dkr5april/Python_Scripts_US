import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_divyachakshu_style_chart(jama_data, transit_data, points_data):
    fig, ax = plt.subplots(figsize=(10, 10))
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

    # 1. DRAW INNER RASHI GRID (The main 12 houses)
    skip = [(1,1),(1,2),(2,1),(2,2)]
    for x in range(4):
        for y in range(4):
            if (x,y) not in skip:
                ax.add_patch(Rectangle((x,y), 1, 1, fill=False, linewidth=1.5, edgecolor='#333333'))

    ax.text(2, 2, "JAMAKKOL\nPRASANAM", ha="center", va="center", fontsize=16, fontweight="bold")

    # 2. DRAW OUTER JAMA STRIPS WITH SEPARATORS
    drawn_top = drawn_bottom = drawn_left = drawn_right = False

    for sign_idx in range(12):
        gx, gy = grid_map[sign_idx]
        
        # --- TOP ROW: Leaves Pisces (0,3) empty ---
        if gy == 3 and not drawn_top:
            ax.add_patch(Rectangle((1.0, 4.0), 1.5, 0.4, color="#cc0033"))
            ax.add_patch(Rectangle((2.5, 4.0), 1.5, 0.4, color="#cc0033"))
            ax.text(1.75, 4.2, "Top A", color="white", ha="center", va="center")
            ax.text(3.25, 4.2, "Top B", color="white", ha="center", va="center")
            # Vertical separator at X=2.5
            ax.plot([2.5, 2.5], [4.0, 4.4], color="white", linewidth=2)
            drawn_top = True

        # --- BOTTOM ROW: Leaves Virgo (3,0) empty ---
        elif gy == 0 and not drawn_bottom:
            ax.add_patch(Rectangle((0.0, -0.4), 1.5, 0.4, color="#cc0033"))
            ax.add_patch(Rectangle((1.5, -0.4), 1.5, 0.4, color="#cc0033"))
            ax.text(0.75, -0.2, "Bot A", color="white", ha="center", va="center")
            ax.text(2.25, -0.2, "Bot B", color="white", ha="center", va="center")
            # Vertical separator at X=1.5
            ax.plot([1.5, 1.5], [-0.4, 0.0], color="white", linewidth=2)
            drawn_bottom = True

        # --- LEFT COLUMN: Leaves Sagittarius (0,0) empty ---
        elif gx == 0 and not drawn_left:
            ax.add_patch(Rectangle((-0.4, 1.0), 0.4, 1.5, color="#cc0033"))
            ax.add_patch(Rectangle((-0.4, 2.5), 0.4, 1.5, color="#cc0033"))
            ax.text(-0.2, 1.75, "Left A", color="white", ha="center", va="center", rotation=90)
            ax.text(-0.2, 3.25, "Left B", color="white", ha="center", va="center", rotation=90)
            # Horizontal separator at Y=2.5
            ax.plot([-0.4, 0.0], [2.5, 2.5], color="white", linewidth=2)
            drawn_left = True

        # --- RIGHT COLUMN: Leaves Gemini (3,3) empty ---
        elif gx == 3 and not drawn_right:
            ax.add_patch(Rectangle((4.0, 0.0), 0.4, 1.5, color="#cc0033"))
            ax.add_patch(Rectangle((4.0, 1.5), 0.4, 1.5, color="#cc0033"))
            ax.text(4.2, 0.75, "Right A", color="white", ha="center", va="center", rotation=270)
            ax.text(4.2, 2.25, "Right B", color="white", ha="center", va="center", rotation=270)
            # Horizontal separator at Y=1.5
            ax.plot([4.0, 4.4], [1.5, 1.5], color="white", linewidth=2)
            drawn_right = True

    # 3. FILL INNER DATA
    for i in range(12):
        gx, gy = grid_map[i]
        if i in transit_data:
            ax.text(gx+0.5, gy+0.7, " ".join(transit_data[i]), ha='center', fontsize=11)
        if i in points_data:
            ax.text(gx+0.5, gy+0.3, " ".join(points_data[i]), ha='center', fontsize=12, fontweight='bold', color='blue')

    plt.show()

# Example Call
draw_divyachakshu_style_chart({}, {}, {})