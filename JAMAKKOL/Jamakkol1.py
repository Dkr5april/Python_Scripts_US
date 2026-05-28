import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ---------------------------------
# SIGN GRID (South Indian Style)
# ---------------------------------

SIGN_POS = {
    "Pisces": (0, 3), "Aries": (1, 3), "Taurus": (2, 3), "Gemini": (3, 3),
    "Aquarius": (0, 2),                  "Cancer": (3, 2),
    "Capricorn": (0, 1),                 "Leo": (3, 1),
    "Sagittarius": (0, 0), "Scorpio": (1, 0), "Libra": (2, 0), "Virgo": (3, 0)
}

FIXED_SIGNS = {"Taurus", "Leo", "Scorpio", "Aquarius"}

# ---------------------------------
# JAMAKKOL DATA (FROM YOU)
# ---------------------------------

INNER_PLANETS = {
    "Aries":   "UDY",
    "Pisces":  "ARU",
    "Cancer":  "KAV"
}

OUTER_PLANETS = {
    "Pisces": "J-Su",
    "Capricorn": "J-Ma",
    "Sagittarius": "J-Ju",
    "Libra": "J-Me",
    "Virgo": "J-Ve",
    "Cancer": "J-Sa",
    "Gemini": "J-Mo",
    "Aries": "J-SN"
}

# ---------------------------------
# DRAW FUNCTIONS
# ---------------------------------

def draw_sign(ax, sign, x, y):
    ax.add_patch(Rectangle((x, y), 1, 1, fill=False, linewidth=2))
    ax.text(x + 0.5, y + 0.5, sign, ha="center", va="center",
            fontsize=10, fontweight="bold")

def draw_inner(ax, x, y, text):
    ax.add_patch(Rectangle((x + 0.15, y + 0.15), 0.7, 0.3,
                           facecolor="#ffe082", edgecolor="black"))
    ax.text(x + 0.5, y + 0.3, text,
            ha="center", va="center",
            fontsize=9, fontweight="bold")

def draw_outer(ax, x, y, text):
    ax.add_patch(Rectangle((x, y + 0.72), 1, 0.28,
                           facecolor="#c2185b", edgecolor="black"))
    ax.text(x + 0.5, y + 0.86, text,
            ha="center", va="center",
            fontsize=9, color="white", fontweight="bold")

# ---------------------------------
# MAIN DRAW
# ---------------------------------

def draw_jamakkol_chart():
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    ax.axis("off")

    for sign, (x, y) in SIGN_POS.items():
        draw_sign(ax, sign, x, y)

        # Inner planets
        if sign in INNER_PLANETS:
            draw_inner(ax, x, y, INNER_PLANETS[sign])

        # Outer planets (not for fixed signs)
        if sign in OUTER_PLANETS and sign not in FIXED_SIGNS:
            draw_outer(ax, x, y, OUTER_PLANETS[sign])

    ax.text(2, 2, "JAMAKKOL\n(Rasi Chart)",
            ha="center", va="center",
            fontsize=14, fontweight="bold")

    plt.show()

# ---------------------------------
# RUN
# ---------------------------------

if __name__ == "__main__":
    draw_jamakkol_chart()
