import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

# ---------------- CONFIG ----------------
# Use 365.2425 for Solar Year (RVA Standard) or 360 for Savana Year
YEAR_DAYS = 365.2425 
swe.set_ephe_path("./ephe")

# Setting Sidereal Mode to Krishnamurti
# If the dasha is still off by a few days, it's usually due to Ayanamsa.
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}

HOUSE_COLORS = {
    1: "green", 2: "green", 3: "green", 6: "green", 10: "green", 11: "green",
    8: "red", 12: "red",
    4: "orange3", 5: "orange3", 7: "orange3", 9: "orange3"
}

ALL_ASPECTS = [
    (0, "Conj", "orange3"), (60, "Sext", "green"), (90, "Squa", "red"),
    (120, "Trin", "green"), (180, "Oppo", "red"), (30, "SSxt", "green"),
    (45, "SSqu", "red"), (150, "Quin", "orange3"), (72, "Qnt", "green"),
    (135, "Sesq", "red")
]

class AstroEngineV79:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        self.view_date = datetime.now()
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        # Indian Standard Time (IST) Offset 5.5
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        self.refresh_data()

    def get_house(self, lon, cusps):
        for i in range(12):
            s, e = cusps[i], cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)): return i + 1
        return 1

    def refresh_data(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.n_pos = {}
        t_jd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 
                          self.view_date.hour + self.view_date.minute/60.0 - 5.5)
        self.t_pos = {}
        
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            n_res, _ = swe.calc_ut(self.njd, pid, flag)
            t_res, _ = swe.calc_ut(t_jd, pid, flag)
            self.n_pos[nm], self.t_pos[nm] = n_res[0], t_res[0]
        
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        
        res_n = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)
        self.cusps = res_n[0]
        
        self.p_to_h = {p: self.get_house(lon, self.cusps) for p, lon in self.n_pos.items()}
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_dasha_6(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        
        # Dynamic calculation based on Moon Longitude
        moon_lon = self.n_pos["Mo"]
        one_star = 360/27
        star_idx = int(moon_lon / one_star)
        lord_id = star_idx % 9
        
        # Calculate Balance at birth
        passed_deg = moon_lon % one_star
        rem_deg = one_star - passed_deg
        
        # Initial dasha end date calculation
        # Uses YEAR_DAYS to ensure no drift over decades
        first_dasha_rem_years = (rem_deg / one_star) * DASHA_YEARS[lord_id]
        m_end = self.njd + (first_dasha_rem_years * YEAR_DAYS)
        
        def recurse(start, total_days, p_idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                idx = (p_idx + i) % 9
                dur = (DASHA_YEARS[idx] / 120.0) * total_days
                if curr <= t_jd < (curr + dur + 1e-8):
                    return [PLANET_LIT[idx]] + recurse(curr, dur, idx, depth + 1)
                curr += dur
            return ["?"]

        # Find the start of the current 120-year cycle
        cycle_days = 120 * YEAR_DAYS
        check_start = m_end - (DASHA_YEARS[lord_id] * YEAR_DAYS)
        while t_jd > (check_start + cycle_days): check_start += cycle_days
        
        return recurse(check_start, cycle_days, lord_id, 0)

    def get_consolidated_strip(self, p_name):
        if p_name == "?": return Text("-")
        # Merges Natal Potential + Transit House + Aspects
        combined = {self.p_to_h[p_name]}
        combined.update(self.own_map[p_name])
        
        # Add current house position in natal chart
        t_lon = self.t_pos[p_name]
        combined.add(self.get_house(t_lon, self.cusps))
        
        strip = Text()
        sorted_h = sorted(list(combined))
        for i, h in enumerate(sorted_h):
            strip.append(str(h), style=HOUSE_COLORS.get(h, "white"))
            if i < len(sorted_h)-1: strip.append(",", style="white")
        return strip

# DYNAMIC INPUT SECTION
# Change these values for different people
engine = AstroEngineV79(
    dob="05/04/1979", 
    tob="16:55:00", 
    lat=16.12, 
    lon=80.93
)

def make_layout():
    d_list = engine.get_dasha_6(engine.view_date)
    table = Table(expand=True, title=f"KP DYNAMIC ENGINE V79 | {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
    table.add_column("Level", style="cyan", width=10)
    table.add_column("Planet", style="bold yellow", width=8)
    table.add_column("Live Consolidated", width=40)

    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(d_list):
        table.add_row(lvls[i], p, engine.get_consolidated_strip(p))
    
    return Layout(Panel(table, subtitle="[Arrows] Move Time | Synced to Solar Year (365.24)"))

exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if hasattr(key, 'char') and key.char.lower() == 'q': exit_flag = True
        if key == keyboard.Key.right: engine.view_date += timedelta(hours=1); engine.refresh_data()
        if key == keyboard.Key.left: engine.view_date -= timedelta(hours=1); engine.refresh_data()
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag: live.update(make_layout()); time.sleep(0.5)
finally:
    listener.stop(); os.system('cls' if os.name == 'nt' else 'clear')