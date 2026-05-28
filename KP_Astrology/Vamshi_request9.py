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
# Coordinates from your RVA Report: 16° 07' N, 80° 55' E
TEST_LAT, TEST_LON = 16.12, 80.93 
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}
SUB_DIVS = [7.0, 20.0, 6.0, 10.0, 7.0, 18.0, 16.0, 19.0, 17.0]

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

class AstroEngineV77:
    def __init__(self, dob, tob):
        self.view_date = datetime.now()
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        # STRICT NATAL DATA: 05/04/1979 at 16:55:00
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
        # Current Transit Julian Day (Moves with arrows)
        t_jd = swe.julday(self.view_date.year, self.view_date.month, self.view_date.day, 
                          self.view_date.hour + self.view_date.minute/60.0 - 5.5)
        self.t_pos = {}
        
        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            n_res, _ = swe.calc_ut(self.njd, pid, flag)
            t_res, _ = swe.calc_ut(t_jd, pid, flag)
            self.n_pos[nm], self.t_pos[nm] = n_res[0], t_res[0]
        
        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360
        
        # Natal Cusps stay fixed as per your Birth Chart
        res_n = swe.houses_ex(self.njd, TEST_LAT, TEST_LON, b'P', flag)
        self.cusps = res_n[0]
        
        self.p_to_h = {p: self.get_house(lon, self.cusps) for p, lon in self.n_pos.items()}
        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            self.own_map[RASHI_OWNERS[int(self.cusps[i]/30)]].append(i+1)

    def get_kp_lords(self, lon):
        sign_l = RASHI_OWNERS[int(lon/30)]
        star_idx = int(lon * 60 / 800) % 9
        star_l = PLANET_LIT[star_idx]
        star_start = (int(lon * 3 / 40)) * (40/3)
        rem = lon - star_start
        sub_sum, sub_l = 0, ""
        for i in range(9):
            idx = (star_idx + i) % 9
            span = (SUB_DIVS[idx] / 120.0) * (40/3)
            if sub_sum <= rem < (sub_sum + span):
                sub_l = PLANET_LIT[idx]
                break
            sub_sum += span
        sub_star_l = PLANET_LIT[int(self.n_pos[sub_l] * 60 / 800) % 9]
        return [sign_l, star_l, sub_l, sub_star_l]

    def get_4_fold_set(self, p_name):
        # Your original logic applied to sub-lords for consolidation
        lon = self.n_pos[p_name]
        st_l = PLANET_LIT[int(lon * 60 / 800) % 9]
        res = {self.p_to_h[st_l], self.p_to_h[p_name]}
        res.update(self.own_map[st_l])
        res.update(self.own_map[p_name])
        return res

    def get_consolidated_strip(self, p_name):
        if p_name == "?": return Text("-")
        lords = self.get_kp_lords(self.n_pos[p_name])
        combined = set()
        for l in lords: combined.update(self.get_4_fold_set(l))
        
        # LIVE TRANSIT IMPACT
        t_lon = self.t_pos[p_name]
        # Current Natal House position of the moving planet
        current_h = self.get_house(t_lon, self.cusps)
        combined.add(current_h)

        # Live Aspect Injection
        for n_p, n_lon in self.n_pos.items():
            diff = abs(t_lon - n_lon) % 360
            if diff > 180: diff = 360 - diff
            for angle, name, col in ALL_ASPECTS:
                if abs(diff - angle) <= 5:
                    combined.add(self.p_to_h[n_p])

        strip = Text()
        sorted_h = sorted(list(combined))
        for i, h in enumerate(sorted_h):
            strip.append(str(h), style=HOUSE_COLORS.get(h, "white"))
            if i < len(sorted_h)-1: strip.append(",", style="white")
        return strip

    def get_colored_ranked_significators(self, p_name):
        if p_name == "?": return "-"
        lon = self.n_pos[p_name]
        st_lord = PLANET_LIT[int(lon * 60 / 800) % 9]
        levels = [("A", [self.p_to_h[st_lord]]), ("B", [self.p_to_h[p_name]]), 
                  ("C", self.own_map[st_lord]), ("D", self.own_map[p_name])]
        ui_text = Text()
        seen = set()
        for label, houses in levels:
            unique = [h for h in houses if h not in seen]
            if unique:
                if len(ui_text) > 0: ui_text.append(" | ", style="white")
                ui_text.append(f"{label}:[", style="cyan")
                for idx, h in enumerate(unique):
                    ui_text.append(str(h), style=HOUSE_COLORS.get(h, "white"))
                    if idx < len(unique) - 1: ui_text.append(",", style="white")
                ui_text.append("]", style="cyan")
                for h in houses: seen.add(h)
        return ui_text

    def get_dasha_6(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        moon_lon = self.n_pos["Mo"] # Moon at 03° 16' 57" [cite: 22]
        one_star = 360/27
        star_idx = int(moon_lon / one_star)
        lord_id = star_idx % 9
        rem_deg = one_star - (moon_lon % one_star)
        # Offset to match Jupiter Dasha end on 28-04-1979 [cite: 128]
        m_start = self.njd - (((DASHA_YEARS[lord_id] - (rem_deg / one_star * DASHA_YEARS[lord_id]))) * 365.2425)
        
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
            
        cycle = 120 * 365.2425
        check_start = m_start
        while t_jd > (check_start + cycle): check_start += cycle
        return recurse(check_start, cycle, lord_id, 0)

engine = AstroEngineV77("05/04/1979", "16:55:00")

def make_layout():
    d_list = engine.get_dasha_6(engine.view_date)
    table = Table(expand=True, title=f"KP LIVE EVENT ENGINE | {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
    table.add_column("Level", style="cyan", width=10)
    table.add_column("Planet", style="bold yellow", width=8)
    table.add_column("Natal Matrix (Fixed)", width=35)
    table.add_column("Live Consolidated (Moving)", width=30)

    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(d_list):
        table.add_row(lvls[i], p, engine.get_colored_ranked_significators(p), engine.get_consolidated_strip(p))
    
    return Layout(Panel(table, subtitle="[Arrows] +/- 15m | [Q] Quit | SYNCED TO RVA PDF [cite: 113]"))

exit_flag = False
def on_press(key):
    global exit_flag
    try:
        if hasattr(key, 'char') and key.char.lower() == 'q': exit_flag = True
        if key == keyboard.Key.right: engine.view_date += timedelta(minutes=15); engine.refresh_data()
        if key == keyboard.Key.left: engine.view_date -= timedelta(minutes=15); engine.refresh_data()
    except: pass

listener = keyboard.Listener(on_press=on_press); listener.start()
try:
    with Live(make_layout(), refresh_per_second=2, screen=True) as live:
        while not exit_flag: live.update(make_layout()); time.sleep(0.5)
finally:
    listener.stop(); os.system('cls' if os.name == 'nt' else 'clear')