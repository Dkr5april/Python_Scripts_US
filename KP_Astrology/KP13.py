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
console.print(Panel("[bold cyan]KP ASTRO LIVE ENGINE V54 - FULL TOGGLE RESTORATION[/bold cyan]", expand=False))

u_name = console.input("[bold yellow]1. Enter Name:[/] ")
u_dob  = console.input("[bold yellow]2. Enter DOB (DD/MM/YYYY):[/] ")
u_tob  = console.input("[bold yellow]3. Enter TOB (HH:MM:SS):[/] ")
u_city = console.input("[bold yellow]4. Enter Birth City:[/] ")

with console.status("[bold green]Calculating Full Data Toggles..."):
    g = geocoder.osm(u_city)
    b_lat, b_lon = g.latlng if g.ok else (16.11, 80.91)

# ---------------- ENGINE ----------------
class AstroEngineV54:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.request_jump = False
        self.lat, self.lon = lat, lon
        
        # UI TOGGLES
        self.show_dasha = True
        self.show_aspects = True
        self.show_houses = True
        
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        
        # Natal Data
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            self.n_pos[nm] = {"lon": res[0], "retro": res[3] < 0}
        self.n_pos["Ke"] = {"lon": (self.n_pos["Ra"]["lon"] + 180) % 360, "retro": True}
        
        res = swe.houses_ex(self.njd, lat, lon, b'P', swe.FLG_SIDEREAL)
        self.n_cusps = res[0]

    def get_house_of_lon(self, lon):
        for i in range(12):
            s, e = self.n_cusps[i], self.n_cusps[(i+1)%12]
            if s < e:
                if s <= lon < e: return i + 1
            elif lon >= s or lon < e: return i + 1
        return 0

    def get_transit_data(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        transits = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(t_jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            transits[nm] = {"lon": res[0], "retro": res[3] < 0, "star": PLANET_LIT[int(res[0] * 60 / 800) % 9]}
        transits["Ke"] = {"lon": (transits["Ra"]["lon"] + 180) % 360, "retro": True, "star": PLANET_LIT[(int(transits["Ra"]["lon"] * 60 / 800) + 4) % 9]}
        return transits

    def get_dasha_6(self, target_dt):
        t_jd = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute/60.0 - 5.5)
        moon_lon = self.n_pos["Mo"]["lon"]
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

engine = AstroEngineV54(u_dob, u_tob, b_lat, b_lon)

# ---------------- UI DASHBOARD ----------------

def get_calc_table():
    table = Table(expand=True, border_style="dim")
    table.add_column("Time", width=6)
    if engine.show_dasha: table.add_column("Dasha (6-L)", style="yellow", width=18)
    if engine.show_houses: table.add_column("KP Transit House", style="cyan")
    if engine.show_aspects: table.add_column("Transit Hits", style="magenta")
    
    for i in range(25):
        dt = engine.view_date + timedelta(minutes=i*5)
        transit = engine.get_transit_data(dt)
        hits, house_info = [], []
        
        for p_t, d_t in transit.items():
            t_h = engine.get_house_of_lon(d_t["lon"])
            house_info.append(f"{p_t}:H{t_h}")
            for p_n, d_n in engine.n_pos.items():
                diff = abs(d_t["lon"] - d_n["lon"]) % 360
                if diff > 180: diff = 360 - diff
                if diff < 1.0: hits.append(f"T-{p_t} Conj N-{p_n}")
                if abs(diff-180) < 1.0: hits.append(f"T-{p_t} Opp N-{p_n}")
        
        if hits or engine.show_houses:
            row = [dt.strftime("%H:%M")]
            if engine.show_dasha: row.append(engine.get_dasha_6(dt))
            if engine.show_houses: row.append(" ".join(house_info[:4] + ["..."])) # Show first 4 for space
            if engine.show_aspects: row.append(" | ".join(hits[:2]))
            table.add_row(*row)
    return table

def get_chart_widget():
    # ... (Same South Indian Chart code as V53) ...
    transit = engine.get_transit_data(engine.view_date)
    grid = {i:{"n":[], "t":[], "c":[]} for i in range(1, 13)}
    for p, data in engine.n_pos.items():
        r = "(R)" if data["retro"] else ""
        grid[int(data["lon"]/30)+1]["n"].append(f"{p}{r}:{data['lon']%30:.0f}")
    for p, data in transit.items():
        r = "(R)" if data["retro"] else ""
        grid[int(data["lon"]/30)+1]["t"].append(f"{p}{r}:{data['lon']%30:.0f}")
    for i, cl in enumerate(engine.n_cusps): grid[int(cl/30)+1]["c"].append(f"H{i+1}")
    t = Table.grid(expand=True)
    for _ in range(4): t.add_column()
    def cell(n):
        content = [f"[yellow]{' '.join(grid[n]['c'])}[/]", f"[green]{' '.join(grid[n]['n'])}[/]", f"[red]{' '.join(grid[n]['t'])}[/]"]
        return Panel(Align.center("\n".join(content)), height=5)
    t.add_row(cell(12), cell(1), cell(2), cell(3)); t.add_row(cell(11), "", "", cell(4))
    t.add_row(cell(10), "", "", cell(5)); t.add_row(cell(9), cell(8), cell(7), cell(6))
    return t

def make_layout():
    # Dynamic status bar for toggles
    d_st = "[green]ON[/]" if engine.show_dasha else "[red]OFF[/]"
    a_st = "[green]ON[/]" if engine.show_aspects else "[red]OFF[/]"
    h_st = "[green]ON[/]" if engine.show_houses else "[red]OFF[/]"

    layout = Layout()
    layout.split_column(
        Layout(Panel(f"USER: {u_name} | VIEW: {engine.view_date.strftime('%d-%m %H:%M')}\n"
                     f"TOGGLES: [D] Dasha:{d_st} | [A] Aspect:{a_st} | [H] House:{h_st} | [J] Jump | [Q] Quit", 
                     style="white on blue"), size=4),
        Layout(name="body")
    )
    layout["body"].split_row(
        Layout(Panel(get_chart_widget(), title="South Indian Chart"), ratio=1),
        Layout(Panel(get_calc_table(), title="KP Analytics Monitor"), ratio=1)
    )
    return layout

# ---------------- KEYBOARD ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15)
        elif hasattr(key, 'char'):
            c = key.char.lower()
            if c == 'q': exit_flag = True
            if c == 'j': engine.request_jump = True
            if c == 'd': engine.show_dasha = not engine.show_dasha
            if c == 'a': engine.show_aspects = not engine.show_aspects
            if c == 'h': engine.show_houses = not engine.show_houses
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

clear_screen()
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            if engine.request_jump:
                live.stop()
                target = console.input("\nJump (DD/MM/YYYY HH:MM): ")
                try: engine.view_date = datetime.strptime(target, "%d/%m/%Y %H:%M")
                except: pass
                engine.request_jump = False
                clear_screen(); live.start()
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop(); clear_screen()