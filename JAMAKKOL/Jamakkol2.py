import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_jamakkol_chart():

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(-1.2, 5.2)
    ax.set_ylim(-1.2, 5.2)
    ax.axis("off")

    # -------------------------
    # RASI GRID (4 x 4)
    # -------------------------
    for x in range(4):
        for y in range(4):
            ax.add_patch(Rectangle((x, y), 1, 1,
                                   fill=False, linewidth=2))

    ax.text(2, 2, "Rashi Chart",
            ha="center", va="center",
            fontsize=16, fontweight="bold")

    # -------------------------
    # JAMAKKOL BANDS
    # -------------------------

    # TOP BAND
    ax.add_patch(Rectangle((0, 4.05), 4, 0.6,
                           facecolor="#c2185b", edgecolor="black"))
    ax.text(2, 4.35,
            "Ve 13°   ♂ ♀ ☿     Me 58°   ♀ ♂ ♄",
            ha="center", va="center",
            fontsize=12, color="white", fontweight="bold")

    # BOTTOM BAND
    ax.add_patch(Rectangle((0, -0.65), 4, 0.6,
                           facecolor="#c2185b", edgecolor="black"))
    ax.text(2, -0.35,
            "SN 238°   ☋ ♄     Su 193°   ♀ ☊ ☿",
            ha="center", va="center",
            fontsize=12, color="white", fontweight="bold")

    # LEFT BAND
    ax.add_patch(Rectangle((-0.65, 0), 0.6, 4,
                           facecolor="#c2185b", edgecolor="black"))
    ax.text(-0.35, 2,
            "Sa 328°\n\nMo 283°",
            ha="center", va="center",
            fontsize=12, color="white", fontweight="bold")

    # RIGHT BAND
    ax.add_patch(Rectangle((4.05, 0), 0.6, 4,
                           facecolor="#c2185b", edgecolor="black"))
    ax.text(4.35, 2,
            "Ju 103°\n\nMa 148°",
            ha="center", va="center",
            fontsize=12, color="white", fontweight="bold")

    plt.show()

# RUN
draw_jamakkol_chart()
