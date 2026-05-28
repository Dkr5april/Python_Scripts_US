import swisseph as swe
import os, sys, time
from datetime import datetime, timedelta
from pynput import keyboard
from collections import Counter
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

# ---------------- CONFIG ----------------
YEAR_LEN = 365.2425
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}
SUB_DIVS = [7.0, 20.0, 6.0, 10.0, 7.0, 18.0, 16.0, 19.0, 17.0]

# KP House Significance Colors
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

class AstroEngineV84:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        self.view_date = datetime.now()
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        # Base birth time in GMT (adjusting for IST 5.5)
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

    def get_4_lords(self, lon):
        sign_l = RASHI_OWNERS[int(lon/30)]
        star_idx = int(lon * 60 / 800) % 9
        star_l = PLANET_LIT[star_idx]
        star_start = (int(lon * 3 / 40)) * (40/3)
        rem = lon - star_start
        sub_sum, sub_l = 0, ""
        for i in range(9):
            idx = (star_idx + i) % 9
            span = (SUB_DIVS[idx] / 120.0) * (40/3)
            if sub_sum <= rem < (sub_sum + span + 1e-9):
                sub_l = PLANET_LIT[idx]
                break
            sub_sum += span
        ss_lon = self.n_pos[sub_l]
        sub_star_l = PLANET_LIT[int(ss_lon * 60 / 800) % 9]
        return [sign_l, star_l, sub_l, sub_star_l]

    def get_4_fold_houses(self, p_name):
        lon = self.n_pos[p_name]
        st_l = PLANET_LIT[int(lon * 60 / 800) % 9]
        res = [self.p_to_h[st_l], self.p_to_h[p_name]]
        res.extend(self.own_map[st_l])
        res.extend(self.own_map[p_name])
        return res

    def get_consolidated_strip(self, p_name):
        if p_name == "?": return Text("-")
        hits = []
        
        # 1. Natal Lords (Weighted)
        lords = self.get_4_lords(self.n_pos[p_name])
        for l in lords:
            hits.extend(self.get_4_fold_houses(l))
            
        # 2. Live Transit
        t_lon = self.t_pos[p_name]
        hits.append(self.get_house(t_lon, self.cusps))
        
        # 3. Western Aspects
        aspect_notes = []
        for n_p, n_lon in self.n_pos.items():
            diff = abs(t_lon - n_lon) % 360
            if diff > 180: diff = 360 - diff
            for angle, name, col in ALL_ASPECTS:
                if abs(diff - angle) <= 2.5: # 2.5 degree orb
                    h = self.p_to_h[n_p]
                    hits.append(h)
                    aspect_notes.append(f"{name}(H{h})")

        counts = Counter(hits)
        strip = Text()
        for h in sorted(counts.keys()):
            count = counts[h]
            color = HOUSE_COLORS.get(h, "white")
            # Intensity Symbols: 1=Normal, 2=+, 3+=★
            sym = "" if count == 1 else ("⁺" if count == 2 else "★")
            style = f"bold {color}" if count > 1 else color
            strip.append(f"{h}{sym} ", style=style)
            
        if aspect_notes:
            strip.append("| ", style="white")
            strip.append(" ".join(set(aspect_notes)), style="yellow italic")
        return strip

    def get_dasha_6(self, t_dt):
        t_jd = swe.julday(t_dt.year, t_dt.month, t_dt.day, t_dt.hour + t_dt.minute/60.0 - 5.5)
        moon_lon = self.n_pos["Mo"]
        one_star = 360.0 / 27.0
        star_idx = int(moon_lon // one_star)
        lord_id = star_idx % 9
        passed = moon_lon % one_star
        rem = one_star - passed
        balance_years = (rem / one_star) * DASHA_YEARS[lord_id]
        maha_start = self.njd - (DASHA_YEARS[lord_id] - balance_years) * YEAR_LEN
        cycle_days = 120.0 * YEAR_LEN
        offset = (t_jd - maha_start) % cycle_days
        t_norm = maha_start + offset

        def recurse(start, total_days, idx, depth):
            if depth == 6: return []
            curr = start
            for i in range(9):
                p = (idx + i) % 9
                dur = (DASHA_YEARS[p] / 120.0) * total_days
                if curr <= t_norm < (curr + dur + 1e-9):
                    return [PLANET_LIT[p]] + recurse(curr, dur, p, depth + 1)
                curr += dur
            return ["?"]
        return recurse(maha_start, cycle_days, lord_id, 0)

# ---------------- INITIALIZATION ----------------
engine = AstroEngineV84(dob="05/04/1979", tob="16:55:00", lat=16.12, lon=80.93)

def make_layout():
    d_list = engine.get_dasha_6(engine.view_date)
    table = Table(expand=True, title=f"KP INTENSITY ENGINE V84 | {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
    table.add_column("Level", style="cyan", width=10)
    table.add_column("Planet", style="bold yellow", width=8)
    table.add_column("Consolidated Intensity (⁺=2x, ★=3x+ Hits)", width=65)

    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(d_list):
        table.add_row(lvls[i], p, engine.get_consolidated_strip(p))
    
    return Layout(Panel(table, subtitle="[Arrows] Move Time | [Q] Quit | Red=Malefic, Green=Benefic"))

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