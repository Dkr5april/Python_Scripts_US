# logic/rules_processor.py

def evaluate_market_rules(data, dt):
    """
    Evaluates your 5 Trading Rules using pre-calculated engine data.
    """
    # 1. Identify X and Y from the Engine's output
    X = data["Mo"]["lord"]
    Y = data[X]["lord"] if X in data else "N/A"
    
    # 2. Identify Stellar Chains (X-Subs and Y-Subs)
    # This now automatically includes Ur, Ne, Pl and the Ascendant if they match
    x_chain = [p for p, d in data.items() if d["lord"] == X and p not in ["Mo", X]]
    y_chain = [p for p, d in data.items() if d["lord"] == Y and p not in [X, Y]]
    
    # 3. Identify Day Lord
    day_lords = ["Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Su"]
    current_day_lord = day_lords[dt.weekday()]
    
    results = []
    
    # Rule 1: Day Lord Check (Added Rich color tags for your Dashboard)
    r1_pass = current_day_lord in [X, Y]
    if r1_pass and (x_chain or y_chain):
        results.append(f"R1 Day Lord ({current_day_lord}): [red]BLOCKED[/] by {', '.join(x_chain + y_chain)}")
    elif r1_pass:
        results.append(f"R1 Day Lord ({current_day_lord}): [green]PASS[/]")
    else:
        results.append(f"R1 Day Lord ({current_day_lord}): [red]FAIL[/]")

    # Rule 2: Moon Day
    r2_pass = (X == "Mo" or Y == "Mo")
    results.append(f"R2 Moon Day: {'[green]PASS[/]' if r2_pass else '[red]FAIL[/]'}")

    # Rule 3: Star Exchange (Mo <-> X)
    r3_pass = (X in data and data[X]["lord"] == "Mo")
    results.append(f"R3 Star Exchange (Mo <-> {X}): {'[green]PASS[/]' if r3_pass else '[red]FAIL[/]'}")

    # Rule 4: Stellar Chain Strength
    results.append(f"R4 Chains: {len(x_chain)} X-Subs, {len(y_chain)} Y-Subs")

    # Rule 5: Key Planet (X in its own star)
    r5_pass = (X in data and data[X]["lord"] == X)
    results.append(f"R5 Key Planet ({X} in own star): {'[green]PASS[/]' if r5_pass else '[red]FAIL[/]'}")

    return {
        "X": X, 
        "Y": Y, 
        "XC": x_chain, 
        "YC": y_chain, 
        "Rule_Results": results, 
        "Day_Lord": current_day_lord
    }