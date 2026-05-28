import swisseph as swe

# 1. FULL PLANETARY CATEGORIZATION
# Bullish: Jupiter, Rahu, and Neptune (Jupiter's Octave)
BULLISH_PLANETS = ["Ju", "Ra", "Ne"]
# Bearish: Mars, Saturn, Uranus (Mars Octave), Pluto (Sani Octave)
BEARISH_PLANETS = ["Ma", "Sa", "Ur", "Pl"]
# Sideways: Sun, Moon, Mercury, Venus, Ketu
SIDEWAYS_PLANETS = ["Su", "Mo", "Me", "Ve", "Ke"]

# 2. FULL HOUSE TREND MAPPING
BULLISH_HOUSES = [1, 3, 6, 10, 11]  # Upachaya
BEARISH_HOUSES = [5, 8, 12]         # Dusthana
SIDEWAYS_HOUSES = [4, 7]
ANGLE_HOUSES = [2, 9]

# Color Mapping for UI
LORD_COLORS = {
    "Ke": "bright_black", "Ve": "magenta", "Su": "bright_yellow", 
    "Mo": "white", "Ma": "red", "Ra": "blue", 
    "Ju": "yellow", "Sa": "cyan", "Me": "green"
}

def get_precise_house(source_lon, target_lon, direction="to_moon"):
    """
    Directional Degree Logic:
    'to_moon': Planet -> Moon (Xn/Yn Rule)
    'from_moon': Moon -> Planet (Primary X/Y Rule)
    """
    if direction == "to_moon":
        diff = (target_lon - source_lon) % 360
    else:
        diff = (source_lon - target_lon) % 360
        
    return int(diff / 30) + 1

def evaluate_market(data, day_lord):
    verdicts = []
    mo = data["Mo"]
    mo_lon = mo['lon']
    
    x_lord = mo['lord']
    y_lord = data[x_lord]['lord']
    
    # Identify dynamic list of influencers (X1, X2... Y1, Y2...)
    xn_list = [p for p, d in data.items() if d['lord'] == x_lord and p != x_lord]
    yn_list = [p for p, d in data.items() if d['lord'] == y_lord and p != y_lord]
    all_influence = xn_list + yn_list

    # --- STELLAR RULE (Xn, Yn Active) ---
    if all_influence:
        verdicts.append("[bold yellow]STELLAR RULE: Count Planet -> Moon[/]")
        for p in all_influence:
            h_dist = get_precise_house(data[p]['lon'], mo_lon, direction="to_moon")
            
            # Determine Trend
            if h_dist in BULLISH_HOUSES: trend = "BULLISH"
            elif h_dist in BEARISH_HOUSES: trend = "BEARISH"
            elif h_dist in SIDEWAYS_HOUSES: trend = "SIDEWAYS"
            else: trend = "ANGLE (Key)"
            
            # Retrograde Rule
            is_retro = data[p].get('retro', False) and p not in ["Ra", "Ke"]
            final_sentiment = "BEARISH (Retro)" if is_retro else trend
            color = "red" if "BEARISH" in final_sentiment else "green" if "BULLISH" in final_sentiment else "white"
            
            verdicts.append(f"[{color}]- {p} (Inf) -> Moon: H{h_dist} ({final_sentiment})[/]")
            
    # --- PRIMARY RULES (X, Y Active) ---
    else:
        verdicts.append("[bold cyan]PRIMARY RULE: Count Moon -> Planet[/]")
        for label, p_name in [("X", x_lord), ("Y", y_lord)]:
            h_dist = get_precise_house(data[p_name]['lon'], mo_lon, direction="from_moon")
            
            # Rule 1 & 2
            is_bullish_rule = (day_lord == p_name) or (p_name == "Mo")
            style = "bold green" if is_bullish_rule else "white"
            
            verdicts.append(f"[{style}]- {label} ({p_name}) Moon -> {p_name}: H{h_dist}[/]")

    # --- RULE 5: OWN STAR ---
    for p_name in [x_lord, y_lord]:
        if data[p_name]['lord'] == p_name:
            h_dist = get_precise_house(data[p_name]['lon'], mo_lon, direction="to_moon")
            verdicts.append(f"[magenta]RULE 5: {p_name} Own Star (Key) H{h_dist}[/]")

    return verdicts