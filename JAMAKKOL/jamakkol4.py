import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def draw_jamakkol_chart_with_outer():

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_xlim(-0.6, 4.6)
    ax.set_ylim(-0.6, 4.6)
    ax.axis("off")

    # -----------------------------
    # INNER RASHI GRID (UNCHANGED)
    # -----------------------------
    skip = [(1,1),(1,2),(2,1),(2,2)]

    for x in range(4):
        for y in range(4):
            if (x,y) not in skip:
                ax.add_patch(Rectangle((x,y),1,1,fill=False,linewidth=2))

    # Center label
    ax.text(2,2,"Rashi Chart",ha="center",va="center",
            fontsize=14,fontweight="bold")

    # Example INNER planet text (as in your image)
    ax.text(0.5,3.5,"Sa",ha="center",va="center",fontsize=11)
    ax.text(3.5,3.5,"(Ju)",ha="center",va="center",fontsize=11)
    ax.text(0.5,1.5,"(Ra)",ha="center",va="center",fontsize=11)
    ax.text(3.5,1.5,"(Ke) CHA",ha="center",va="center",fontsize=11)
    ax.text(0.5,0.5,"Mo* Su\nMa*",ha="center",va="center",fontsize=10)
    ax.text(1.5,0.5,"Me Ve*",ha="center",va="center",fontsize=10)
    ax.text(2.5,0.5,"ARU",ha="center",va="center",fontsize=10)
    ax.text(3.5,0.5,"Md",ha="center",va="center",fontsize=10)

    # --------------------------------
    # OUTER JAMAKKOL PLANET STRIPS
    # --------------------------------

    # TOP STRIPS (Pisces, Taurus, Gemini)
    ax.add_patch(Rectangle((0,4),1,0.4,fill=True,color="#cc0033"))
    ax.text(0.5,4.2,"Ve 13°",color="white",ha="center",va="center")

    ax.add_patch(Rectangle((1,4),1,0.4,fill=True,color="#cc0033"))
    ax.text(1.5,4.2,"",ha="center",va="center")  # Aries intentionally blank

    ax.add_patch(Rectangle((2,4),1,0.4,fill=True,color="#cc0033"))
    ax.text(2.5,4.2,"Me 58°",color="white",ha="center",va="center")

    # LEFT STRIPS
    ax.add_patch(Rectangle((-0.4,2),0.4,1,fill=True,color="#cc0033"))
    ax.text(-0.2,2.5,"Sa\n328°",color="white",ha="center",va="center")

    ax.add_patch(Rectangle((-0.4,1),0.4,1,fill=True,color="#cc0033"))
    ax.text(-0.2,1.5,"Mo\n283°",color="white",ha="center",va="center")

    # RIGHT STRIPS
    ax.add_patch(Rectangle((4,2),0.4,1,fill=True,color="#cc0033"))
    ax.text(4.2,2.5,"Ju\n103°",color="white",ha="center",va="center")

    ax.add_patch(Rectangle((4,1),0.4,1,fill=True,color="#cc0033"))
    ax.text(4.2,1.5,"Ma\n148°",color="white",ha="center",va="center")

    # BOTTOM STRIPS
    ax.add_patch(Rectangle((0,-0.4),1,0.4,fill=True,color="#cc0033"))
    ax.text(0.5,-0.2,"SN 238°",color="white",ha="center",va="center")

    ax.add_patch(Rectangle((1,-0.4),1,0.4,fill=True,color="#cc0033"))
    ax.text(1.5,-0.2,"Su 193°",color="white",ha="center",va="center")

    plt.show()

# RUN
draw_jamakkol_chart_with_outer()
