import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel

# ---------------- FIXED CONFIG ----------------
# Hardcoded for Challapalli testing
TEST_LAT = 16.12
TEST_LON = 80.93

# Set this to the path where your ephemeris files are located
swe.set_ephe_path("./ephe") 
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}

# Aspect Definitions (Angle, Name, Orb)
ASPECTS = [(0, "Conjunction", 8), (60, "Sextile", 6), (90, "Square", 8), (120, "Trine", 8), (180, "Opposition", 8)]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- PHASE 1: DATA ENTRY ----------------
clear_screen()
console.print(Panel.fit("[bold cyan]KP V64 - FULL SIGNIFICATOR & ASPECT ENGINE[/bold cyan]\n[white]Location: Challapalli (16.12, 80.93)[/white]"))

u_name = "Koteswararao"
u_dob  = "05/04/1979"
u_tob  = "16:23:00"

# ---------------- PHASE 2: ENGINE ----------------
class AstroEngineV64:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.is_tropical = False
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        self.lat, self.lon = lat, lon
        self.refresh_data()

    def refresh_data(self):
        flag = swe.FLG_SWIEPH if self.is_tropical else swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        if not self.is_tropical: swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        # Natal & Transit Positions
        self.n_pos = {}
        t_jd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, self.view_date.hour - 5.5)
        self.t_pos = {}

        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            n_res, _ = swe.calc_ut(self.njd, pid, flag)
            t_res, _ = swe.calc_ut(t_jd, pid, flag)
            self.n_pos[nm], self.t_pos[nm] = n_res[0], t_res[0]
        
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        
        # House Cusps & Mapping
        res = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)
        self.cusps = res[0]
        self.p_to_h = {p: self.get_house(lon) for p, lon in self.n_pos.items()}
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_house(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): return i + 1
        return 1

    def get_4fold_numbers(self, p_name):
        lon = self.n_pos[p_name]
        st_lord = PLANET_LIT[int(lon * 60 / 800) % 9]
        return f"{self.p_to_h[st_lord]} | {self.p_to_h[p_name]} | {','.join(map(str, self.own_map[st_lord])) or '-'} | {','.join(map(str, self.own_map[p_name])) or '-'}"

    def get_aspects(self, p_name):
        found = []
        t_lon = self.t_pos[p_name]
        for n_p, n_lon in self.n_pos.items():
            diff = abs(t_lon - n_lon) % 360
            if diff > 180: diff = 360 - diff
            for angle, name, orb in ASPECTS:
                if abs(diff - angle) <= orb:
                    found.append(f"{name} Natal {n_p}")
        return ", ".join(found) if found else "-"

    def get_dasha_6(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
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
        return recurse(check_start, cycle, lord_id, 0)

engine = AstroEngineV64(u_dob, u_tob, TEST_LAT, TEST_LON)

# ---------------- PHASE 3: UI ----------------
def make_layout():
    dasha_list = engine.get_dasha_6(engine.view_date)
    table = Table(expand=True, title=f"KP 4-Fold & Aspects | {engine.view_date.strftime('%d-%m-%Y %H:%M')}")
    table.add_column("Level", style="cyan")
    table.add_column("Planet", style="bold yellow")
    table.add_column("4-Fold (A|B|C|D)", style="green")
    table.add_column("Western Aspects (Transit -> Natal)", style="magenta")

    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(dasha_list):
        table.add_row(lvls[i], p, engine.get_4fold_numbers(p), engine.get_aspects(p))
    return Layout(Panel(table))

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1); engine.refresh_data()
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1); engine.refresh_data()
        elif hasattr(key, 'char') and key.char.lower() == 'q': exit_flag = True
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop(); clear_screen()