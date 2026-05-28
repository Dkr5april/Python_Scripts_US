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

# Includes Outer Planets for RVA alignment
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ur", "Ne", "Pl"]
RASHI_NAMES = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
RASHI_LORDS = ["Ma", "Ve", "Me", "Mo", "Su", "Me", "Ve", "Ma", "Ju", "Sa", "Sa", "Ju"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_deg(deg):
    r_idx = int(deg / 30) % 12
    rem = deg % 30
    m = int((rem - int(rem)) * 60)
    return f"{RASHI_NAMES[r_idx]} {int(rem):02d}°{m:02d}'"

# ---------------- ENGINE ----------------
class AstroEngineV55:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.active_tab = "SIGNIFICATORS" 
        self.lat, self.lon = lat, lon
        
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        # KP NEW AYANAMSA OFFSET (~6 mins)
        self.ayan_offset = -(6.0 / 60.0) 

        self.n_pos = {}
        p_ids = [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra"),(7,"Ur"),(8,"Ne"),(9,"Pl")]
        
        for pid, nm in p_ids:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            adj_lon = (res[0] + self.ayan_offset) % 360
            self.n_pos[nm] = {"lon": adj_lon, "retro": res[3] < 0 if len(res)>3 else False}
            
        self.n_pos["Ke"] = {"lon": (self.n_pos["Ra"]["lon"] + 180) % 360, "retro": True}
        
        # Adjusted House Cusps
        res = swe.houses_ex(self.njd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = [(c + self.ayan_offset) % 360 for c in res[0]]

    def get_star_lord(self, degree):
        stars = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        return stars[int(degree / (360/27)) % 9]

    def get_4fold_significators(self):
        sig_data = {i: {"A": [], "B": [], "C": [], "D": [], "Cusp": ""} for i in range(1, 13)}
        p_star_lords = {p: self.get_star_lord(data['lon']) for p, data in self.n_pos.items()}

        for p, data in self.n_pos.items():
            p_lon = data['lon']
            house_found = 12 
            for h in range(12):
                c_start = self.n_cusps[h]
                c_end = self.n_cusps[(h + 1) % 12]
                if (c_start < c_end and c_start <= p_lon < c_end) or \
                   (c_start > c_end and (p_lon >= c_start or p_lon < c_end)):
                    house_found = h + 1
                    break
            sig_data[house_found]["B"].append(p)

        for h in range(1, 13):
            sig_data[h]["Cusp"] = format_deg(self.n_cusps[h-1])
            h_lord = RASHI_LORDS[int(self.n_cusps[h-1] / 30)]
            sig_data[h]["D"].append(h_lord)
            for occ in sig_data[h]["B"]:
                for planet, s_lord in p_star_lords.items():
                    if s_lord == occ: sig_data[h]["A"].append(planet)
            for planet, s_lord in p_star_lords.items():
                if s_lord == h_lord: sig_data[h]["C"].append(planet)
        return sig_data

# ---------------- SCREENS ----------------

def get_chart_screen():
    grid = {i:{"n":[], "c":[]} for i in range(1, 13)}
    # Use Sign-based grid for visual chart
    for p, d in engine.n_pos.items(): grid[int(d["lon"]/30)+1]["n"].append(f"{p}{'(R)' if d.get('retro') else ''}")
    for i, cl in enumerate(engine.n_cusps): grid[int(cl/30)+1]["c"].append(f"H{i+1}")

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n):
        content = [f"[yellow]{' '.join(grid[n]['c'])}[/]", f"[green]{' '.join(grid[n]['n'])}[/]"]
        return Panel(Align.center("\n".join(content)), height=7, border_style="blue")

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def get_analytics_screen():
    table = Table(expand=True, title="Planetary Degrees & Star Lords")
    table.add_column("Planet", style="bold cyan")
    table.add_column("Position (Rashi)", style="green")
    table.add_column("Star Lord", style="yellow")
    for p in PLANET_LIT:
        table.add_row(p, format_deg(engine.n_pos[p]['lon']), engine.get_star_lord(engine.n_pos[p]['lon']))
    return table

def get_significator_screen():
    table = Table(expand=True, title="KP 4-FOLD SIGNIFICATORS (ALIGNED)")
    table.add_column("House", style="cyan", justify="center")
    table.add_column("Cusp Start", style="dim")
    table.add_column("A", style="green", justify="center")
    table.add_column("B", style="yellow", justify="center")
    table.add_column("C", style="magenta", justify="center")
    table.add_column("D", style="red", justify="center")

    sig_data = engine.get_4fold_significators()
    for h in range(1, 13):
        table.add_row(
            str(h), sig_data[h]["Cusp"],
            ", ".join(sorted(set(sig_data[h]["A"]))),
            ", ".join(sorted(set(sig_data[h]["B"]))),
            ", ".join(sorted(set(sig_data[h]["C"]))),
            ", ".join(sorted(set(sig_data[h]["D"])))
        )
    return table

# ---------------- UI & RUNTIME ----------------

clear_screen()
u_name = "Koteswararao"
u_dob = console.input("[yellow]DOB (DD/MM/YYYY): [/]")
u_tob = console.input("[yellow]TOB (HH:MM:SS): [/]")
u_city = console.input("[yellow]City: [/]")

g = geocoder.osm(u_city)
b_lat, b_lon = g.latlng if g.ok else (16.11, 80.91)
engine = AstroEngineV55(u_dob, u_tob, b_lat, b_lon)

def make_layout():
    layout = Layout()
    header = f"KP LIVE V55 | {u_name} | TAB: {engine.active_tab} | [TAB] Cycle | [Q] Quit"
    layout.split_column(Layout(Panel(header, style="white on blue"), size=3), Layout(name="main"))
    
    if engine.active_tab == "CHART": layout["main"].update(get_chart_screen())
    elif engine.active_tab == "ANALYTICS": layout["main"].update(get_analytics_screen())
    else: layout["main"].update(get_significator_screen())
    return layout

exit_flag = False
def on_press(key):
    global exit_flag
    if key == keyboard.Key.tab:
        tabs = ["CHART", "ANALYTICS", "SIGNIFICATORS"]
        engine.active_tab = tabs[(tabs.index(engine.active_tab) + 1) % 3]
    if hasattr(key, 'char') and key.char == 'q': exit_flag = True

listener = keyboard.Listener(on_press=on_press); listener.start()
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop(); clear_screen()