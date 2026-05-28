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

# Planet list includes Outer Planets for RVA alignment
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
        self.active_tab = "CHART" 
        self.lat, self.lon = lat, lon
        
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        # KP NEW AYANAMSA OFFSET
        self.ayan_offset = -(6.0 / 60.0) 
        self.n_pos = self.get_positions(self.njd)
        
        res = swe.houses_ex(self.njd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = [(c + self.ayan_offset) % 360 for c in res[0]]

    def get_positions(self, jd):
        pos_dict = {}
        p_ids = [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra"),(7,"Ur"),(8,"Ne"),(9,"Pl")]
        for pid, nm in p_ids:
            # FLG_SPEED is required to detect Retrograde (R) status
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            adj_lon = (res[0] + self.ayan_offset) % 360
            pos_dict[nm] = {"lon": adj_lon, "retro": res[3] < 0}
        
        pos_dict["Ke"] = {"lon": (pos_dict["Ra"]["lon"] + 180) % 360, "retro": pos_dict["Ra"]["retro"]}
        return pos_dict

    def get_transit(self, t_dt):
        """Fix for the AttributeError: Calculates positions for the current view time."""
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        return self.get_positions(t_jd)

    def get_star_lord(self, degree):
        stars = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
        return stars[int(degree / (360/27)) % 9]

    def get_4fold_data(self):
        h_sig = {i: {"A": [], "B": [], "C": [], "D": [], "Cusp": ""} for i in range(1, 13)}
        p_sig = {p: {"A": [], "B": [], "C": [], "D": []} for p in PLANET_LIT}
        p_star_lords = {p: self.get_star_lord(data['lon']) for p, data in self.n_pos.items()}

        for p, data in self.n_pos.items():
            p_lon = data['lon']
            h_found = 12 
            for h in range(12):
                c_s, c_e = self.n_cusps[h], self.n_cusps[(h+1)%12]
                if (c_s < c_e and c_s <= p_lon < c_e) or (c_s > c_e and (p_lon >= c_s or p_lon < c_e)):
                    h_found = h + 1
                    break
            h_sig[h_found]["B"].append(p)
            p_sig[p]["B"].append(str(h_found))

        for h in range(1, 13):
            h_sig[h]["Cusp"] = format_deg(self.n_cusps[h-1])
            h_lord = RASHI_LORDS[int(self.n_cusps[h-1]/30)]
            h_sig[h]["D"].append(h_lord)
            p_sig[h_lord]["D"].append(str(h))

            for occ in h_sig[h]["B"]:
                for p, sl in p_star_lords.items():
                    if sl == occ: 
                        h_sig[h]["A"].append(p)
                        p_sig[p]["A"].append(str(h))
            for p, sl in p_star_lords.items():
                if sl == h_lord: 
                    h_sig[h]["C"].append(p)
                    p_sig[p]["C"].append(str(h))
                    
        return h_sig, p_sig

# ---------------- UI ----------------

def get_dual_significator_screen():
    h_data, p_data = engine.get_4fold_data()
    
    # House View
    h_table = Table(expand=True, title="Significator - House View", border_style="cyan")
    h_table.add_column("H", justify="center"); h_table.add_column("(A)", style="green")
    h_table.add_column("(B)", style="yellow"); h_table.add_column("(C)", style="magenta")
    h_table.add_column("(D)", style="red")
    for h in range(1, 13):
        h_table.add_row(str(h), ", ".join(sorted(set(h_data[h]["A"]))), ", ".join(sorted(set(h_data[h]["B"]))),
                        ", ".join(sorted(set(h_data[h]["C"]))), ", ".join(sorted(set(h_data[h]["D"]))))

    # Planet View
    p_table = Table(expand=True, title="Significators - Planet View", border_style="magenta")
    p_table.add_column("Planet"); p_table.add_column("(A)"); p_table.add_column("(B)")
    p_table.add_column("(C)"); p_table.add_column("(D)")
    for p in PLANET_LIT:
        # Appends (R) if the engine detects retrograde status
        name = f"{p}(R)" if engine.n_pos[p]['retro'] else p
        p_table.add_row(name, ", ".join(sorted(set(p_data[p]["A"]))), ", ".join(sorted(set(p_data[p]["B"]))),
                        ", ".join(sorted(set(p_data[p]["C"]))), ", ".join(sorted(set(p_data[p]["D"]))))

    dual_layout = Layout()
    dual_layout.split_row(Layout(h_table), Layout(p_table))
    return dual_layout

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
        return Panel(Align.center("\n".join(content)), height=7, border_style="blue")
    t.add_row(cell(12), cell(1), cell(2), cell(3)); t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), "", "", cell(5)); t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def make_layout():
    layout = Layout()
    head = f"USER: {u_name} | SCREEN: {engine.active_tab} | [TAB] Switch | [Arrows] Time"
    layout.split_column(Layout(Panel(head, style="white on blue"), size=3), Layout(name="main"))
    if engine.active_tab == "CHART": layout["main"].update(get_chart_screen())
    else: layout["main"].update(get_dual_significator_screen())
    return layout

# ---------------- RUNTIME ----------------
clear_screen()
u_name = "Koteswararao"
u_dob = console.input("[yellow]DOB (DD/MM/YYYY): [/]")
u_tob = console.input("[yellow]TOB (HH:MM:SS): [/]")
u_city = console.input("[yellow]City: [/]")
g = geocoder.osm(u_city)
b_lat, b_lon = g.latlng if g.ok else (16.11, 80.91)
engine = AstroEngineV55(u_dob, u_tob, b_lat, b_lon)

exit_flag = False
def on_press(key):
    global exit_flag
    if key == keyboard.Key.tab:
        tabs = ["CHART", "SIGNIFICATORS"]
        engine.active_tab = tabs[(tabs.index(engine.active_tab) + 1) % 2]
    elif key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
    elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
    elif hasattr(key, 'char') and key.char == 'q': exit_flag = True

listener = keyboard.Listener(on_press=on_press); listener.start()
try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop(); clear_screen()