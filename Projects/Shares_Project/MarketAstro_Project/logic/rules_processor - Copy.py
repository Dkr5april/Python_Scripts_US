# logic/rules_processor.py

def evaluate_market_rules(data, dt):
    # Core Logic
    X = data["Mo"]["lord"]
    Y = data[X]["lord"] if X in data else "N/A"
    
    # Stellar Chains (Including Outer Planets if they sit in X/Y's stars)
    x_chain = [p for p, d in data.items() if d["lord"] == X and p not in ["Mo", X]]
    y_chain = [p for p, d in data.items() if d["lord"] == Y and p not in [X, Y]]
    
    day_lord_list = ["Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Su"]
    day_lord = day_lord_list[dt.weekday()]
    
    results = [
        f"R1 Day Lord: {'[green]PASS[/]' if day_lord in [X, Y] and not (x_chain or y_chain) else '[red]FAIL/BLOCKED[/]' if day_lord in [X, Y] else 'FAIL'}",
        f"R2 Moon Day: {'[green]PASS[/]' if X == 'Mo' or Y == 'Mo' else 'FAIL'}",
        f"R3 Mo-X Exchange: {'[green]PASS[/]' if X in data and data[X]['lord'] == 'Mo' else 'FAIL'}",
        f"R4 Stellar Chain: {'[yellow]ACTIVE[/]' if x_chain or y_chain else 'INACTIVE'} ({len(x_chain)+len(y_chain)} Subs)",
        f"R5 Key Planet: {'[green]PASS[/]' if X in data and data[X]['lord'] == X else 'FAIL'}"
    ]
    
    return {
        "X": X, "Y": Y, "XC": x_chain, "YC": y_chain, 
        "Rule_Results": results, "Day_Lord": day_lord
    }