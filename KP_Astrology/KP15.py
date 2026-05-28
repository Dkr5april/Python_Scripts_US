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
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- DATA ENTRY ----------------
clear_screen()
console.print(Panel("[bold cyan]KP ASTRO LIVE V55 - TABBED TOGGLE MODE[/bold cyan]"))

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
        self.active_tab = "CHART" # Options: CHART, ANALYTICS
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

def make_layout():
    layout = Layout()
    header_text = f"USER: {u_name} | SCREEN: [bold]{engine.active_tab}[/] | [TAB] Switch | [Arrows] Time"
    layout.split_column(
        Layout(Panel(header_text, style="white on blue"), size=3),
        Layout(name="main")
    )
    
    if engine.active_tab == "CHART":
        layout["main"].update(get_chart_screen())
    else:
        layout["main"].update(get_analytics_screen())
    return layout

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.tab:
            engine.active_tab = "ANALYTICS" if engine.active_tab == "CHART" else "CHART"
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