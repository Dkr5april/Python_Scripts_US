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

# ---------------- INITIALIZATION ----------------
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- DATA ENTRY PHASE (CLEAN) ----------------
clear_screen()
console.print(Panel("[bold cyan]KP ASTRO LIVE ENGINE - DATA ENTRY[/bold cyan]", expand=False))

u_name = console.input("[bold yellow]1. Enter Name:[/] ")
u_dob  = console.input("[bold yellow]2. Enter DOB (DD/MM/YYYY):[/] ")
u_tob  = console.input("[bold yellow]3. Enter TOB (HH:MM:SS):[/] ")
u_city = console.input("[bold yellow]4. Enter Birth City:[/] ")

# Coordination Fetch
with console.status("[bold green]Fetching coordinates and calculating natal chart..."):
    g = geocoder.osm(u_city)
    if g.ok:
        b_lat, b_lon = g.latlng
    else:
        b_lat, b_lon = 16.11, 80.91 # Default fallback

# ---------------- ENGINE ----------------
PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

class AstroEngineV52:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.request_jump = False
        self.lat = lat
        self.lon = lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            self.n_pos[nm] = res[0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        
        res = swe.houses_ex(self.njd, self.lat, self.lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = res[0]

    def get_dasha_6(self, target_dt):
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute/60.0 - 5.5)
        moon_lon = self.n_pos["Mo"]
        one_star = 13.33333333
        star_idx = int(moon_lon / one_star)
        lord_id = star_idx % 9
        rem_deg = one_star - (moon_lon % one_star)
        m_start = self.njd - (((DASHA_YEARS[lord_id] - (rem_deg / one_star * DASHA_YEARS[lord_id]))) * 365.2425)
        
        def recurse(start, total_days, p_idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                idx = (p_idx + i) % 9
                dur = (DASHA_YEARS[idx] / 120.0) * total_days
                if curr <= t_jd < (curr + dur + 1e-7):
                    return [PLANET_LIT[idx]] + recurse(curr, dur, idx, depth + 1)
                curr += dur
            return ["?"]
        
        cycle = 120 * 365.2425
        check_start = m_start
        while t_jd > (check_start + cycle): check_start += cycle
        while t_jd < check_start: check_start -= cycle
        return "-".join(recurse(check_start, cycle, lord_id, 0))

engine = AstroEngineV52(u_dob, u_tob, b_lat, b_lon)

# ---------------- UI DASHBOARD ----------------

def get_chart_widget():
    t_jd = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 
                     engine.view_date.hour + engine.view_date.minute/60.0 - 5.5)
    transit = {}
    for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
        res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        transit[nm] = res[0]
    transit["Ke"] = (transit["Ra"] + 180) % 360

    grid = {i:{"n":[], "t":[], "c":[]} for i in range(1, 13)}
    for p, lon in engine.n_pos.items(): grid[int(lon/30)+1]["n"].append(f"{p}:{lon%30:.0f}")
    for p, lon in transit.items(): grid[int(lon/30)+1]["t"].append(f"{p}:{lon%30:.0f}")
    for i, cl in enumerate(engine.n_cusps): grid[int(cl/30)+1]["c"].append(f"H{i+1}")

    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n):
        content = [f"[yellow]{' '.join(grid[n]['c'])}[/]", f"[green]{' '.join(grid[n]['n'])}[/]", f"[red]{' '.join(grid[n]['t'])}[/]"]
        return Panel(Align.center("\n".join(content)), height=5)

    t.add_row(cell(12), cell(1), cell(2), cell(3))
    t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), "", "", cell(5))
    t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def get_calc_table():
    table = Table(expand=True, border_style="dim")
    table.add_column("Time", width=6)
    table.add_column("Dasha (6-Level)", width=22, style="yellow")
    table.add_column("Significant Hits", style="magenta")
    
    t_jd_base = swe.julday(engine.view_date.year, engine.view_date.month, engine.view_date.day, 
                           engine.view_date.hour + engine.view_date.minute/60.0 - 5.5)
    
    for i in range(25):
        dt = engine.view_date + timedelta(minutes=i*5)
        dasha = engine.get_dasha_6(dt)
        hits = []
        tjd = t_jd_base + (i*5/1440.0)
        
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa")]:
            res, _ = swe.calc_ut(tjd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            t_lon = res[0]
            for n_nm, n_lon in engine.n_pos.items():
                diff = abs(t_lon - n_lon) % 360
                if diff > 180: diff = 360 - diff
                if diff < 1.0: hits.append(f"T-{nm} Conj N-{n_nm}")
                if abs(diff-180) < 1.0: hits.append(f"T-{nm} Opp N-{n_nm}")
        
        if hits:
            table.add_row(dt.strftime("%H:%M"), dasha, " | ".join(hits))
    return table

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"USER: [bold]{u_name}[/] | VIEWING: [bold]{engine.view_date.strftime('%d-%m-%Y %H:%M')}[/] | [J] Jump | [Q] Quit", style="white on blue"), size=3),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart_widget(), title="South Indian Chart (G:Natal, R:Transit)"), ratio=1),
        Layout(Panel(get_calc_table(), title="KP Real-Time Analytics"), ratio=1)
    )
    return layout

# ---------------- CONTROLS ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif key == keyboard.Key.up: engine.view_date += timedelta(hours=1)
        elif key == keyboard.Key.down: engine.view_date -= timedelta(hours=1)
        elif hasattr(key, 'char'):
            if key.char == 'q': exit_flag = True
            if key.char == 'j': engine.request_jump = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

# ---------------- FINAL LAUNCH ----------------
clear_screen() # Final wipe before launching dashboard
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                console.print("\n" * 2)
                target = console.input("[bold yellow]Enter Jump Date/Time (DD/MM/YYYY HH:MM):[/] ")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y %H:%M")
                except: pass
                engine.request_jump = False
                clear_screen() # Clear jump text
                live.start()
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop()
    clear_screen()