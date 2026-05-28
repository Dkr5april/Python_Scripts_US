from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

def create_dashboard_layout(engine_data, logic_results, dasa_levels, view_dt, market_str):
    # 1. Main Table for Planets & Ascendant
    table = Table(expand=True, border_style="cyan", header_style="bold magenta")
    table.add_column("Entity")
    table.add_column("Star (Lord)")
    table.add_column("Pada")
    table.add_column("Deg")
    table.add_column("Status")

    # Add Entities to Table
    for name, d in engine_data.items():
        # Distinguish Ascendant and Outer Planets visually
        color = "yellow" if name == "Asc" else "white"
        if name in ["Ur", "Ne", "Pl"]: color = "blue"
        
        st = "[red]RETRO[/]" if d.get("is_retro") else "[green]DIR[/]"
        table.add_row(
            f"[{color}]{name}[/]", 
            f"{d['star']} ({d['lord']})", 
            str(d["pada"]), 
            f"{d['deg']}°", 
            st
        )

    # 2. Layout Setup
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"TARGET: [bold]{view_dt}[/] | [bold yellow]MARKET:[/] {market_str}"), size=3),
        Layout(name="main")
    )
    
    layout["main"].split_row(
        Layout(Panel(table, title="Sidereal Celestial Metrics (Lahiri)")),
        Layout(name="right")
    )

    # Dasa String
    dasa_str = " > ".join(dasa_levels)

    layout["right"].split_column(
        Layout(Panel(f"Maha > Antar > Pratyantar:\n[bold cyan]{dasa_str}[/]", title="6-Hour Market Dasa")),
        Layout(Panel(f"X: [bold yellow]{logic_results['X']}[/] | Y: [bold yellow]{logic_results['Y']}[/]\n\n" + 
                     "\n".join(logic_results["Rule_Results"]), title="KP Trading Rules")),
        Layout(Panel(f"X-Chain: {', '.join(logic_results['XC'])}\nY-Chain: {', '.join(logic_results['YC'])}", title="Stellar Chain Depth"))
    )
    
    return layout