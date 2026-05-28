import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_true_jamakkol_chart():

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    ax.axis("off")

    # Coordinates to SKIP (center 2x2)
    skip_cells = [(1,1), (1,2), (2,1), (2,2)]

    # Draw only the 12 rasi boxes
    for x in range(4):
        for y in range(4):
            if (x, y) not in skip_cells:
                ax.add_patch(Rectangle((x, y), 1, 1,
                                       fill=False, linewidth=2))

    # -------------------------
    # CENTER TEXT (Jamakkol Info)
    # -------------------------
    ax.text(2, 2.2,
            "JAMAKKOL HORARY\n"
            "Thursday Jamam #3\n"
            "18-Dec-2025 05:59 PM (UTC-7)\n"
            "Herriman, UT, USA\n\n"
            "UD   003°55'\n"
            "MO   233°50'\n"
            "VE   238°54'\n"
            "SU   243°19'\n"
            "MA   248°44'\n"
            "RA   318°38'\n"
            "SA   331°21'\n"
            "AR   355°06'",
            ha="center", va="center",
            fontsize=10, fontweight="bold")

    # -------------------------
    # Example planet placements
    # -------------------------
    ax.text(0.5, 3.5, "SA\nAR", ha="center", va="center", color="green", fontweight="bold")
    ax.text(3.5, 3.5, "(JU)", ha="center", va="center", color="green", fontweight="bold")
    ax.text(0.5, 1.5, "(RA)", ha="center", va="center", color="green", fontweight="bold")
    ax.text(3.5, 1.5, "(KE)", ha="center", va="center", color="green", fontweight="bold")
    ax.text(0.5, 0.5, "SU  MA", ha="center", va="center", color="green", fontweight="bold")
    ax.text(1.5, 0.5, "ME  MO  VE", ha="center", va="center", color="green", fontweight="bold")

    plt.show()

# RUN
draw_true_jamakkol_chart()
