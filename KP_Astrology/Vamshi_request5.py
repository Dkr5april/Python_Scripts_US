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
TEST_LAT, TEST_LON = 16.12, 80.93
swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
console = Console()

PLANET_LIT = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
RASHI_OWNERS = {0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me", 6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"}
ASPECTS = [(0, "Conj"), (60, "Sext"), (90, "Squa"), (120, "Trin"), (180, "Oppo")]

# House Quality Map
HOUSE_COLORS = {
    1: "green", 2: "green", 3: "green", 11: "green", 10: "green", 6: "green",
    8: "red", 12: "red",
    4: "orange3", 5: "orange3", 7: "orange3", 9: "orange3"
}

class AstroEngineV66:
    def __init__(self, dob, tob):
        self.view_date = datetime.now()
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))
        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        self.refresh_data()

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
        res = swe.houses_ex(self.njd, TEST_LAT, TEST_LON, b'P', flag)
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

    def colorize_houses(self, houses):
        # Returns a Rich Text object with colored house numbers
        txt = Text()
        for i, h in enumerate(houses):
            color = HOUSE_COLORS.get(h, "white")
            txt.append(str(h), style=color)
            if i < len(houses) - 1: txt.append(",", style="white")
        return txt

    def get_ranked_significators_ui(self, p_name):
        lon = self.n_pos[p_name]
        st_lord = PLANET_LIT[int(lon * 60 / 800) % 9]
        levels = [("A", [self.p_to_h[st_lord]]), ("B", [self.p_to_h[p_name]]), 
                  ("C", self.own_map[st_lord]), ("D", self.own_map[p_name])]
        
        final_ui = Text()
        seen = set()
        for label, houses in levels:
            unique = [h for h in houses if h not in seen]
            if unique:
                if len(final_ui) > 0: final_ui.append(" | ", style="white")
                final_ui.append(f"{label}:[", style="cyan")
                final_ui.append(self.colorize_houses(unique))
                final_ui.append("]", style="cyan")
                for h in houses: seen.add(h)
        return final_ui

    def get_aspects(self, p_name):
        found = []
        for n_p, n_lon in self.n_pos.items():
            diff = abs(self.t_pos[p_name] - n_lon) % 360
            if diff > 180: diff = 360 - diff
            for angle, name in ASPECTS:
                if abs(diff - angle) <= 8: found.append(f"{name} {n_p}")
        return ", ".join(found[:2]) or "-"

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

engine = AstroEngineV66("05/04/1979", "16:23:00")

def make_layout():
    dasha = engine.get_dasha_6(engine.view_date)
    table = Table(expand=True, title=f"KP COLOR-CODED RANKED MATRIX | {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
    table.add_column("Level", style="white")
    table.add_column("Planet", style="bold yellow")
    table.add_column("Ranked Houses (Green:Good | Red:Bad | Org:Mixed)", width=50)
    table.add_column("Transit Aspects", style="magenta")

    lvls = ["MAHA", "BHUKTI", "ANTARA", "SOOKSHMA", "PRANA", "DEHA"]
    for i, p in enumerate(dasha):
        table.add_row(lvls[i], p, engine.get_ranked_significators_ui(p), engine.get_aspects(p))
    return Layout(Panel(table, subtitle="[Green]=Gain [Red]=Loss [Org]=Mixed | [Arrows]=Time | [Q]=Quit"))

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