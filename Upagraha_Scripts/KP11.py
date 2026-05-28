import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align

# ---------------- ENGINE CORE ----------------
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI) # KP SYSTEM

# Using your birth data from previous turns
DOB_N, TOB_N = "05/04/1979", "16:55:00"
B_LAT, B_LON = 16.11, 80.91

class AstroEngineV49:
    def __init__(self):
        self.view_date = datetime.now()
        self.mode = "SIDEREAL"
        d, m, y = map(int, DOB_N.split("/"))
        hh, mm, ss = map(int, TOB_N.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        # Calculate Natal
        self.n_pos = self.calc_planets(self.njd)
        res = swe.houses_ex(self.njd, B_LAT, B_LON, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = res[0]

    def calc_planets(self, jd):
        data = {}
        # KP Planets
        plist = [(0,"Su"), (1,"Mo"), (2,"Me"), (3,"Ve"), (4,"Ma"), (5,"Ju"), (6,"Sa"), (11,"Ra")]
        for pid, pnm in plist:
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            data[pnm] = res[0]
        data["Ke"] = (data["Ra"] + 180) % 360
        return data

engine = AstroEngineV49()

# ---------------- UI COMPONENTS ----------------

def get_chart():
    # Transit Calculation
    tjd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 
                     engine.view_date.hour + engine.view_date.minute/60.0 - 5.5)
    transit = engine.calc_planets(tjd)
    
    # 12-Sign Grid (1=Aries, 12=Pisces)
    grid = {i:{"n":[], "t":[], "c":[]} for i in range(1, 13)}
    
    # Map Natal Planets
    for p, lon in engine.n_pos.items():
        grid[int(lon/30)+1]["n"].append(f"{p}:{lon%30:.1f}")
    
    # Map Transit Planets
    for p, lon in transit.items():
        grid[int(lon/30)+1]["t"].append(f"{p}:{lon%30:.1f}")
        
    # Map House Cusps
    for i, clon in enumerate(engine.n_cusps):
        grid[int(clon/30)+1]["c"].append(f"H{i+1}:{clon%30:.1f}")

    # Build the Visual Table (South Indian Style)
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    
    def cell(n):
        sign_names = ["ARI","TAU","GEM","CAN","LEO","VIR","LIB","SCO","SAG","CAP","AQU","PIS"]
        content = []
        # House Cusps (Yellow)
        if grid[n]['c']: content.append(f"[yellow]{' '.join(grid[n]['c'])}[/]")
        # Natal (Green)
        if grid[n]['n']: content.append(f"[green]{' '.join(grid[n]['n'])}[/]")
        # Transit (Red)
        if grid[n]['t']: content.append(f"[bold red]{' '.join(grid[n]['t'])}[/]")
        
        return Panel(Align.center("\n".join(content)), title=f"[dim]{sign_names[n-1]}[/]", height=6)

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), Align.center(f"[bold white]KP V49[/]\n[cyan]{engine.view_date:%d-%b-%y}[/]\n[cyan]{engine.view_date:%H:%M}[/]"), "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"KP VISUAL ENGINE | [J] Jump | [Arrows] Time Travel | [Q] Quit", style="white on blue"), size=3),
        Layout(get_chart())
    )
    return layout

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char'):
            if key.char == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=4, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.1)
finally:
    listener.stop()