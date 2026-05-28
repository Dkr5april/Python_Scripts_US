import swisseph as swe
import os, sys, time
import geocoder
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- CONFIG ----------------
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
# Rashi Lords for Level D Significators
RASHI_LORDS = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- DATA ENTRY ----------------
clear_screen()
console.print(Panel("[bold cyan]KP ASTRO LIVE V55 - 4-FOLD SIGNIFICATOR MODE[/bold cyan]"))

u_name = console.input("[bold yellow]Name:[/] ")
u_dob  = console.input("[bold yellow]DOB (DD/MM/YYYY):[/] ")
u_tob  = console.input("[bold yellow]TOB (HH:MM:SS):[/] ")
u_city = console.input("[bold yellow]City:[/] ")

with console.status("Syncing Ephemeris..."):
    g = geocoder.osm(u_city)
    b_lat, b_lon = g.latlng if g.ok else (16.11, 80.91)

# ---------------- ENGINE ----------------
class AstroEngineV55:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.active_tab = "CHART" # Options: CHART, ANALYTICS, SIGNIFICATORS
        self.lat, self.lon = lat, lon
        
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        # Natal Logic
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            self.n_pos[nm] = {"lon": res[0], "retro": res[3] < 0}
        self.n_pos["Ke"] = {"lon": (self.n_pos["Ra"]["lon"] + 180) % 360, "retro": True}
        
        res = swe.houses_ex(self.njd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = res[0]

    def get_transit(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        transits = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            transits[nm] = {"lon": res[0], "retro": res[3] < 0}
        transits["Ke"] = {"lon": (transits["Ra"]["lon"] + 180) % 360, "retro": True}
        return transits

    def get_star_lord(self, degree):
        stars = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        # Star lord changes every 13°20'
        star_index = int(degree / (360/27)) % 9
        return stars[star_index]

    def get_4fold_significators(self, is_transit=False):
        positions = self.get_transit(self.view_date) if is_transit else self.n_pos
        sig_data = {i: {"A": [], "B": [], "C": [], "D": []} for i in range(1, 13)}
        
        # 1. Map every planet to its Star Lord
        p_star_lords = {p: self.get_star_lord(data['lon']) for p, data in positions.items()}

        for h in range(1, 13):
            # LEVEL D: House Lord (Rashi Lord of the Cusp)
            # RVA calculates this based on the sign where the house starts
            h_lord = RASHI_LORDS[int(self.n_cusps[h-1] / 30)]
            sig_data[h]["D"].append(h_lord)

            # LEVEL B: Occupants
            # Planets physically located within the span of this house
            occupants = []
            for p, d in positions.items():
                # Checking house occupancy (standard 30-deg or cuspal)
                if int(d['lon']/30)+1 == h:
                    occupants.append(p)
            sig_data[h]["B"].extend(occupants)

            # LEVEL A: Planets in the STAR of the Occupants
            # This is the "Reverse Lookup" that RVA performs
            for occ in occupants:
                for planet, s_lord in p_star_lords.items():
                    if s_lord == occ:
                        sig_data[h]["A"].append(planet)

            # LEVEL C: Planets in the STAR of the House Lord
            # This links the House Owner's agents to the house
            for planet, s_lord in p_star_lords.items():
                if s_lord == h_lord:
                    sig_data[h]["C"].append(planet)
                    
        return sig_data

engine = AstroEngineV55(u_dob, u_tob, b_lat, b_lon)

# ---------------- SCREENS ----------------

def get_chart_screen():
    transit = engine.get_transit(engine.view_date)
    grid = {i:{"n":[], "t":[], "c":[]} for i in range(1, 13)}
    
    for p, d in engine.n_pos.items(): grid[int(d["lon"]/30)+1]["n"].append(f"{p}{'(R)' if d['retro'] else ''}")
    for p, d in transit.items(): grid[int(d["lon"]/30)+1]["t"].append(f"{p}{'(R)' if d['retro'] else ''}")
    for i, cl in enumerate(engine.n_cusps): grid[int(cl/30)+1]["c"].append(f"H{i+1}")

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n):
        content = [f"[yellow]{' '.join(grid[n]['c'])}[/]", f"[green]{' '.join(grid[n]['n'])}[/]", f"[red]{' '.join(grid[n]['t'])}[/]"]
        return Panel(Align.center("\n".join(content)), height=7)

    t.add_row(cell(12), cell(1), cell(2), cell(3)); t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), "", "", cell(5)); t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def get_analytics_screen():
    table = Table(expand=True, title="Detailed KP Planetary Dynamics")
    table.add_column("Planet", style="bold")
    table.add_column("Natal Degree", style="green")
    table.add_column("Transit Degree", style="red")
    table.add_column("Status", style="yellow")
    
    trans = engine.get_transit(engine.view_date)
    for p in PLANET_LIT:
        n_deg = f"{engine.n_pos[p]['lon']:.2f}°"
        t_deg = f"{trans[p]['lon']:.2f}°"
        status = "Retrograde" if trans[p]['retro'] else "Direct"
        table.add_row(p, n_deg, t_deg, status)
    return table

def get_significator_screen():
    table = Table(expand=True, title="KP 4-FOLD SIGNIFICATORS (NATAL)")
    table.add_column("House", style="cyan", justify="center")
    table.add_column("A (Star of Occ)", style="green", justify="center")
    table.add_column("B (Occupant)", style="yellow", justify="center")
    table.add_column("C (Star of Owner)", style="magenta", justify="center")
    table.add_column("D (Owner)", style="red", justify="center")

    sig_data = engine.get_4fold_significators(is_transit=False)
    for h in range(1, 13):
        table.add_row(
            f"House {h}",
            ", ".join(set(sig_data[h]["A"])),
            ", ".join(set(sig_data[h]["B"])),
            ", ".join(set(sig_data[h]["C"])),
            ", ".join(set(sig_data[h]["D"]))
        )
    return table

def make_layout():
    layout = Layout()
    header_text = f"USER: {u_name} | SCREEN: [bold]{engine.active_tab}[/] | [TAB] Switch | [Arrows] Time"
    layout.split_column(
        Layout(Panel(header_text, style="white on blue"), size=3),
        Layout(name="main")
    )
    
    if engine.active_tab == "CHART":
        layout["main"].update(get_chart_screen())
    elif engine.active_tab == "ANALYTICS":
        layout["main"].update(get_analytics_screen())
    else:
        layout["main"].update(get_significator_screen())
    return layout

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.tab:
            # Cycle through 3 tabs
            tabs = ["CHART", "ANALYTICS", "SIGNIFICATORS"]
            idx = tabs.index(engine.active_tab)
            engine.active_tab = tabs[(idx + 1) % len(tabs)]
        elif key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char') and key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop(); clear_screen()     