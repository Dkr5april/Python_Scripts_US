from rich.table import Table
from engine import format_deg  # Assuming format_deg is in engine.py

def get_analytics_screen(engine):
    """
    Renders the Detailed KP Planetary Dynamics table.
    Compares Natal status vs current Transit status side-by-side.
    """
    transit_pos = engine.get_transit(engine.view_date)
    
    table = Table(title="Detailed KP Planetary Dynamics (Natal vs Transit)", expand=True, border_style="dim")
    table.add_column("Planet", style="cyan", header_style="bold cyan")
    table.add_column("Natal Degree", style="green")
    table.add_column("Natal Status", justify="center")
    table.add_column("Transit Degree", style="red")
    table.add_column("Transit Status", justify="center")
    table.add_column("Transit Star", style="yellow")

    PLANETS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ur", "Ne", "Pl"]
    
    for p in PLANETS:
        n_pos = engine.n_pos[p]
        t_pos = transit_pos[p]
        
        # Natal Status formatting
        n_status = "[bold yellow]RETRO[/]" if n_pos['retro'] else "[white]Direct[/]"
        
        # Transit Status formatting (Dynamic based on arrow key time)
        t_status = "[bold magenta]RETRO[/]" if t_pos['retro'] else "[white]Direct[/]"
        
        # Star Lord of the Transit position
        t_s_lord = engine.get_star_lord(t_pos['lon'])
        
        table.add_row(
            p, 
            format_deg(n_pos['lon']), 
            n_status,
            format_deg(t_pos['lon']), 
            t_status,
            t_s_lord
        )
        
    return table