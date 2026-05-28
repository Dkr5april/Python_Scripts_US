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
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI) # Base KP
console = Console()

# Added Outer Planets to match RVA
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
        
        # KP NEW AYANAMSA OFFSET
        # We calculate the difference between standard KP and New KP
        # Usually New = Old - (0° 06' 00") approximately
        self.ayan_offset = -(6.0 / 60.0) 

        self.n_pos = {}
        # 0:Su, 1:Mo, 2:Me, 3:Ve, 4:Ma, 5:Ju, 6:Sa, 11:Ra, 7:Ur, 8:Ne, 9:Pl
        p_ids = [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra"),(7,"Ur"),(8,"Ne"),(9,"Pl")]
        
        for pid, nm in p_ids:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            # Apply the "New" Ayanamsa shift
            adj_lon = (res[0] + self.ayan_offset) % 360
            self.n_pos[nm] = {"lon": adj_lon}
            
        self.n_pos["Ke"] = {"lon": (self.n_pos["Ra"]["lon"] + 180) % 360}
        
        # Adjust House Cusps for New Ayanamsa
        res = swe.houses_ex(self.njd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = [(c + self.ayan_offset) % 360 for c in res[0]]

    def get_star_lord(self, degree):
        stars = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        star_index = int(degree / (360/27)) % 9
        return stars[star_index]

    def get_4fold_significators(self):
        sig_data = {i: {"A": [], "B": [], "C": [], "D": [], "Cusp": ""} for i in range(1, 13)}
        p_star_lords = {p: self.get_star_lord(data['lon']) for p, data in self.n_pos.items()}

        # 1. House Occupancy
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

        # 2. Level Mapping
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

# ---------------- UI ----------------

clear_screen()
console.print(Panel("[bold cyan]KP NEW AYANAMSA ALIGNMENT (RVA STYLE)[/bold cyan]"))
u_name = "Koteswararao"
u_dob = console.input("[yellow]DOB (DD/MM/YYYY): [/]")
u_tob = console.input("[yellow]TOB (HH:MM:SS): [/]")
u_city = console.input("[yellow]City: [/]")

g = geocoder.osm(u_city)
b_lat, b_lon = g.latlng if g.ok else (16.11, 80.91)
engine = AstroEngineV55(u_dob, u_tob, b_lat, b_lon)

def get_significator_screen():
    table = Table(expand=True, title="[bold white]SIGNIFICATOR - HOUSE VIEW (NEW KP AYANAMSA)[/]")
    table.add_column("House", style="cyan", justify="center")
    table.add_column("Cusp Start", style="dim")
    table.add_column("(A)", style="green", justify="center")
    table.add_column("(B)", style="yellow", justify="center")
    table.add_column("(C)", style="magenta", justify="center")
    table.add_column("(D)", style="red", justify="center")

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

def make_layout():
    layout = Layout()
    layout.split_column(Layout(name="main"), Layout(name="footer", size=5))
    layout["main"].update(get_significator_screen())
    
    p_info = " | ".join([f"{p}: {format_deg(engine.n_pos[p]['lon'])}" for p in ["Su", "Mo", "Ju", "Sa", "Ra", "Ke"]])
    layout["footer"].update(Panel(p_info, title="Key Planet Degrees"))
    return layout

exit_flag = False
def on_press(key):
    global exit_flag
    if hasattr(key, 'char') and key.char == 'q': exit_flag = True

listener = keyboard.Listener(on_press=on_press); listener.start()
try:
    with Live(make_layout(), refresh_per_second=1, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop(); clear_screen()