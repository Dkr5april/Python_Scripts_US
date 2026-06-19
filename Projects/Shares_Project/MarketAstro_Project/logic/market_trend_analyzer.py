# logic/market_trend_analyzer.py
import plotly.graph_objects as go

def get_dynamic_equal_house(start_lon, target_lon):
    if target_lon >= start_lon:
        distance = target_lon - start_lon
    else:
        distance = (target_lon + 360.0) - start_lon
    return int(distance // 30) + 1, distance

def analyze_market_trends(data):
    """
    Parses snapshot planet data according to the X N Y rules.
    Integrates specialized rules for Sideways (ladder climbs) and Angular (1st half up, 2nd half down).
    """
    if "Mo" not in data:
        return None

    # Classifications including Outer Planets
    BULLISH_PLANETS = ["Ju", "Ra", "Ur"]
    BEARISH_PLANETS = ["Ma", "Sa", "Pl"]
    SIDEWAYS_PLANETS = ["Su", "Mo", "Me", "Ve", "Ke", "Ne"]
    
    BULLISH_HOUSES = [1, 3, 6, 10, 11]
    BEARISH_HOUSES = [5, 8, 12]
    SIDEWAYS_HOUSES = [4, 7]
    ANGULAR_HOUSES = [2, 9]

    X = data["Mo"]["lord"]
    Y = data[X]["lord"] if X in data else "N/A"

    # Identify chains (Excluding Ascendant from the loop as per request)
    x_chain = [p for p, d in data.items() if d["lord"] == X and p not in ["Mo", X, "Asc"]]
    y_chain = [p for p, d in data.items() if d["lord"] == Y and p not in [X, Y, "Asc"]]

    mo_lon = data["Mo"]["lon"]
    analysis_nodes = []

    # Apply frame fallback counting rules
    if not x_chain and not y_chain:
        if X in data:
            h, d = get_dynamic_equal_house(mo_lon, data[X]["lon"])
            analysis_nodes.append({"label": f"Moon ➡️ X ({X})", "planet": X, "house": h, "dist": d})
        if Y in data and Y != "N/A" and Y != X:
            h, d = get_dynamic_equal_house(mo_lon, data[Y]["lon"])
            analysis_nodes.append({"label": f"Moon ➡️ Y ({Y})", "planet": Y, "house": h, "dist": d})
    else:
        for idx, p in enumerate(x_chain):
            if p in data:
                h, d = get_dynamic_equal_house(data[p]["lon"], mo_lon)
                analysis_nodes.append({"label": f"X{idx+1} ({p}) ➡️ Moon", "planet": p, "house": h, "dist": d})
        for idx, p in enumerate(y_chain):
            if p in data:
                h, d = get_dynamic_equal_house(data[p]["lon"], mo_lon)
                analysis_nodes.append({"label": f"Y{idx+1} ({p}) ➡️ Moon", "planet": p, "house": h, "dist": d})

    scored_results = []
    for node in analysis_nodes:
        p = node["planet"]
        h = node["house"]
        is_retro = data[p].get("is_retro", False) if p in data else False

        # 1. Planet Scoring
        if is_retro and p not in ["Ra", "Ke"]:
            p_text = "Bearish (Retro)"
            p_score = -1.0
        elif p in BULLISH_PLANETS:
            p_text = "Bullish"
            p_score = 1.0
        elif p in BEARISH_PLANETS:
            p_text = "Bearish"
            p_score = -1.0
        else:
            p_text = "Sideways (Step Jump)"
            p_score = 0.2  # Dynamic baseline value for step-wise accumulation

        # 2. House Scoring
        if h in BULLISH_HOUSES:
            h_text = "Bullish"
            h_score = 1.0
            graph_type = "bullish"
        elif h in BEARISH_HOUSES:
            h_text = "Bearish"
            h_score = -1.0
            graph_type = "bearish"
        elif h in SIDEWAYS_HOUSES:
            h_text = "Sideways"
            h_score = 0.2
            graph_type = "sideways"
        else:
            h_text = "Angular"
            h_score = 0.0  # Acts as the turning midpoint axis
            graph_type = "angular"

        net_score = p_score + h_score

        # 3. Final Interpretations
        if graph_type == "angular":
            trend_desc = "🔄 1st Half UP / 2nd Half FALL"
            ui_color = "#bd93f9" # Purple
        elif graph_type == "sideways" or (p_score == 0.2 and h_score == 0.2):
            trend_desc = "🪜 Sideways (Slow Step Jumps)"
            ui_color = "#ffb86c" # Orange
        elif net_score > 0.5:
            trend_desc = "📈 Bullish Trend"
            ui_color = "#50fa7b" # Green
        elif net_score < -0.5:
            trend_desc = "📉 Bearish Trend"
            ui_color = "#ff5555" # Red
        else:
            trend_desc = "🪜 Sideways (Slow Step Jumps)"
            ui_color = "#ffb86c"

        scored_results.append({
            **node,
            "p_text": p_text,
            "h_text": h_text,
            "trend": trend_desc,
            "color": ui_color,
            "graph_type": graph_type,
            "score": net_score
        })

    return scored_results

def create_compact_trend_chart(graph_type, color):
    """
    Generates a tiny, clean, sparkline graph depicting the actual wave profile.
    - Bullish: Upward line
    - Bearish: Downward line
    - Sideways: Staircase pattern (slow step-by-step jumps)
    - Angular: Inverted V-shape (first half up, second half down)
    """
    fig = go.Figure()
    
    if graph_type == "bullish":
        x_val = [1, 2, 3, 4]
        y_val = [1, 2, 4, 6]
    elif graph_type == "bearish":
        x_val = [1, 2, 3, 4]
        y_val = [6, 4, 2, 0]
    elif graph_type == "angular":
        x_val = [1, 2, 3, 4]
        y_val = [1, 5, 4, 1]  # Inverted V wave
    else:  # Sideways step-jumps
        x_val = [1, 1.8, 1.8, 2.8, 2.8, 4]
        y_val = [1, 1,   2,   2,   3,   3]  # Staircase path

    fig.add_trace(go.Scatter(
        x=x_val, y=y_val,
        mode="lines+markers" if graph_type != "sideways" else "lines",
        line=dict(color=color, width=3),
        marker=dict(size=4),
        hoverinfo="skip"
    ))
    
    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        height=35,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig