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
# Hardcoded for Challapalli testing to bypass geocoding errors
TEST_LAT = 16.12
TEST_LON = 80.93

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# Traditional KP Rashi Lordships for Level D
RASHI_OWNERS = {
    0: "Ma", 1: "Ve", 2: "Me", 3: "Mo", 4: "Su", 
    5: "Me", 6: "Ve", 7: "Ma", 8: "Ju", 9: "Sa", 
    10: "Sa", 11: "Ju"
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------- PHASE 1: DATA ENTRY ----------------
clear_screen()
console.print(Panel.fit("[bold cyan]KP V63 - HOUSE NUMBER SIGNIFICATOR ENGINE[/bold cyan]\n[white]Location: Challapalli (16.12, 80.93)[/white]"))

u_name = console.input("[bold yellow]1. Name:[/] ")
u_dob  = console.input("[bold yellow]2. DOB (DD/MM/YYYY):[/] ")
u_tob  = console.input("[bold yellow]3. TOB (HH:MM:SS):[/] ")

# ---------------- PHASE 2: ENGINE ----------------
class AstroEngineV63:
    def __init__(self, dob, tob, lat, lon):
        self.view_date = datetime.now()
        self.is_tropical = False
        self.request_jump = False
        
        # Parse Birth Time
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        # Adjust for IST (GMT+5.5)
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        self.lat, self.lon = lat, lon
        self.refresh_data()

    def refresh_data(self):
        flag = swe.FLG_SWIEPH if self.is_tropical else swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        if not self.is_tropical: swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        # Natal Positions
        self.n_pos = {}
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            res, _ = swe.calc_ut(self.njd, pid, flag)
            self.n_pos[nm] = res[0]
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        
        # House Cusps
        res = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)
        self.cusps = res[0]
        
        # Map Planet -> House Occupancy
        self.p_to_h = {}
        for p, lon in self.n_pos.items():
            self.p_to_h[p] = self.get_house(lon)
            
        # Map Planet -> Houses Owned
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            rashi = int(self.cusps[i] / 30)
            lord = RASHI_OWNERS[rashi]
            self.own_map[lord].append(i + 1)

    def get_house(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): return i + 1
        return 1

    def get_4fold_numbers(self, p_name):
        lon = self.n_pos[p_name]
        # Calculate Star Lord (Standard KP 13°20' increments)
        st_lord = PLANET_LIT[int(lon * 60 / 800) % 9]
        
        # A: House occupied by Star Lord
        lev_a = self.p_to_h[st_lord]
        # B: House occupied by Planet
        lev_b = self.p_to_h[p_name]
        # C: Houses owned by Star Lord
        lev_c = ",".join(map(str, self.own_map[st_lord])) or "-"
        # D: Houses owned by Planet
        lev_d = ",".join(map(str, self.own_map[p_name])) or "-"
        
        return f"{lev_a} | {lev_b} | {lev_c} | {lev_d}"

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
        return recurse(check_start, cycle, lord_id, 0)

engine = AstroEngineV63(u_dob, u_tob, TEST_LAT, TEST_LON)

# ---------------- PHASE 3: UI ----------------
def make_layout():
    dasha_list = engine.get_dasha_6(engine.view_date)
    z_mode = "TROPICAL" if engine.is_tropical else "SIDEREAL (KP)"
    
    table = Table(expand=True, border_style="cyan")
    table.add_column("Dasha Level", style="white")
    table.add_column("Planet", style="bold yellow")
    table.add_column("4-Fold (A:StOcc | B:Occ | C:StOwn | D:Own)", style="green")
    
    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(dasha_list):
        table.add_row(lvls[i], p, engine.get_4fold_numbers(p))

    footer = f"[Z] Zodiac Toggle | [Arrows] Change Time | [Q] Quit"
    return Layout(Panel(table, title=f"{u_name} | {z_mode} | {engine.view_date.strftime('%d-%m-%Y %H:%M')}", subtitle=footer))

# ---------------- RUNTIME ----------------
exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if key == keyboard.Key.right: engine.view_date += timedelta(days=1)
        elif key == keyboard.Key.left: engine.view_date -= timedelta(days=1)
        elif hasattr(key, 'char'):
            c = key.char.lower()
            if c == 'q': exit_flag = True
            elif c == 'z': 
                engine.is_tropical = not engine.is_tropical
                engine.refresh_data()
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()

try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag:
            live.update(make_layout())
            time.sleep(0.5)
finally:
    listener.stop(); clear_screen()