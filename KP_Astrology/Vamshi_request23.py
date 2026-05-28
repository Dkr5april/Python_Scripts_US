import swisseph as swe
import os, time
from datetime import datetime, timedelta
from collections import Counter
from pynput import keyboard
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pandas as pd

console = Console()

# ==================== CONSTANTS =======================
YEAR_LEN = 365.2425
EPS = 1e-7  # JD tolerance

swe.set_ephe_path("./ephe")
swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

PLANET_LIT = ["Ke","Ve","Su","Mo","Ma","Ra","Ju","Sa","Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

RASHI_OWNERS = {
    0:"Ma", 1:"Ve", 2:"Me", 3:"Mo", 4:"Su", 5:"Me",
    6:"Ve", 7:"Ma", 8:"Ju", 9:"Sa", 10:"Sa", 11:"Ju"
}

POS_HOUSES = {1, 2, 3, 6, 10, 11}
NEG_HOUSES = {8, 12}

ALL_ASPECTS = [
    (0, "Conj"), (180, "Oppo"), (120, "Trin"), (90, "Squa"), (60, "Sext"), # Major
    (30, "SSxt"), (45, "SSqu"), (150, "Quin"), (72, "Qnt"), (135, "Sesq") # Minor
]

# ==================== CORE ENGINE =====================
class KPEngineV89:
    def __init__(self, dob, tob, lat, lon):
        self.lat, self.lon = lat, lon
        d, m, y = map(int, dob.split("/"))
        hh, mm, ss = map(int, tob.split(":"))

        self.njd = swe.julday(y, m, d, hh + mm/60 + ss/3600 - 5.5)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

        self.birth_moon = swe.calc_ut(self.njd, swe.MOON, flag)[0][0]
        self.view_date = datetime.now()
        self.refresh()

    def refresh(self):
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        self.n_pos, self.t_pos = {}, {}

        t_jd = swe.julday(
            self.view_date.year,
            self.view_date.month,
            self.view_date.day,
            self.view_date.hour + self.view_date.minute/60 - 5.5
        )

        for pid, nm in [(0,"Su"),(1,"Mo"),(2,"Me"),(3,"Ve"),(4,"Ma"),(5,"Ju"),(6,"Sa"),(11,"Ra")]:
            self.n_pos[nm] = swe.calc_ut(self.njd, pid, flag)[0][0]
            self.t_pos[nm] = swe.calc_ut(t_jd, pid, flag)[0][0]

        self.n_pos["Ke"] = (self.n_pos["Ra"] + 180) % 360
        self.t_pos["Ke"] = (self.t_pos["Ra"] + 180) % 360

        self.cusps = swe.houses_ex(self.njd, self.lat, self.lon, b'P', flag)[0]
        self.p_to_h = {p: self.get_h(lon) for p, lon in self.n_pos.items()}

        self.own_map = {p: [] for p in PLANET_LIT}
        for i in range(12):
            owner = RASHI_OWNERS[int(self.cusps[i] / 30)]
            self.own_map[owner].append(i + 1)

    def get_h(self, lon):
        for i in range(12):
            s, e = self.cusps[i], self.cusps[(i+1)%12]
            if (s < e and s <= lon < e) or (s > e and (lon >= s or lon < e)):
                return i + 1
        return 1

    def analyze(self, p):
        if p == "?" or p not in self.n_pos: 
            return "-", "-", "-", "-", [], 0
        
        n_lon = self.n_pos[p]
        t_lon = self.t_pos[p]
        
        # 1. KP Lords Calculation (Natal)
        sign_lord = RASHI_OWNERS[int(n_lon / 30)]
        star_lord = PLANET_LIT[int(n_lon * 3 / 40) % 9]
        sub_lord  = PLANET_LIT[int(n_lon * 27 / 40) % 9] 
        
        # SUBSTAR: Star Lord of the Sub Lord (Natal)
        sub_natal_lon = self.n_pos[sub_lord]
        substar_lord  = PLANET_LIT[int(sub_natal_lon * 3 / 40) % 9]

        # 2. SIGNIFICATOR HITS (Including Sign Lord)
        hits = [
            self.p_to_h[p],              # Planet Occupancy
            self.p_to_h[star_lord],      # Star Lord Occupancy
            self.p_to_h[sign_lord]       # Sign Lord Occupancy
        ] 
        hits += self.own_map[star_lord]  # Star Lord Ownership
        hits += self.own_map[sign_lord]  # Sign Lord Ownership
        hits.append(self.get_h(t_lon))   # Transit House

        # 3. TRANSIT-TO-NATAL ASPECTS (10 Types)
        asp_hits = []
        for n_nm, n_lon_birth in self.n_pos.items():
            diff = abs(t_lon - n_lon_birth) % 360
            if diff > 180: diff = 360 - diff
            
            for ang, name in ALL_ASPECTS:
                orb = 2.5 if ang in [0, 180, 120, 90, 60] else 1.2
                if abs(diff - ang) < orb:
                    color = "green" if ang in [60, 120, 30, 72] else "red" if ang in [90, 180, 45, 135, 150] else "white"
                    asp_hits.append(f"[{color}]{name}->{n_nm}[/]")

        # 4. Final Net Score Calculation
        counts = Counter(hits)
        net = sum(counts[h] for h in counts if h in POS_HOUSES) - \
              sum(counts[h] for h in counts if h in NEG_HOUSES)
        
        return sign_lord, star_lord, sub_lord, substar_lord, asp_hits, net

    def dasha6(self, dt):
        STAR_LEN = 360 / 27
        moon = self.birth_moon
        nak = int(moon // STAR_LEN)
        maha_lord_idx = nak % 9

        rem = STAR_LEN - (moon % STAR_LEN)
        bal_years = (rem / STAR_LEN) * DASHA_YEARS[maha_lord_idx]
        maha_start = self.njd - (DASHA_YEARS[maha_lord_idx] - bal_years) * YEAR_LEN
        t_jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 - 5.5)

        def walk(start_jd, total_years, lord_idx, level):
            if level == 6: return []
            cur = start_jd
            for k in range(9):
                idx = (lord_idx + k) % 9
                dur = (DASHA_YEARS[idx] / 120) * total_years * YEAR_LEN
                if (t_jd + EPS) >= cur and (t_jd - EPS) < (cur + dur):
                    return [PLANET_LIT[idx]] + walk(cur, dur / YEAR_LEN, idx, level + 1)
                cur += dur
            return ["?"]
        return walk(maha_start, 120, maha_lord_idx, 0)

# ==================== UI =====================

dob, tob, lat, lon = "05/04/1979", "16:55:00", 16.12, 80.93
engine = KPEngineV89(dob, tob, lat, lon)
exit_f = False

def on_p(key):
    global exit_f
    try:
        if key == keyboard.Key.right:
            engine.view_date += timedelta(minutes=5)
            engine.refresh()
        if key == keyboard.Key.left:
            engine.view_date -= timedelta(minutes=5)
            engine.refresh()
        if hasattr(key, 'char') and key.char == 'q':
            exit_f = True
    except: pass

def draw():
    table = Table(title=f"KP MASTER ENGINE V89.6 | {engine.view_date.strftime('%Y-%m-%d %H:%M')}")
    table.add_column("Level", style="cyan")
    table.add_column("Planet", style="bold yellow")
    table.add_column("Lords (Sgn/Str/Sub/SStr)", style="white")
    table.add_column("Net", justify="right")
    table.add_column("Transit Aspects (T->N)")

    lvls = ["MAHA","BHUKTI","ANTARA","SOOKSHMA","PRANA","DEHA"]
    dashas = engine.dasha6(engine.view_date)

    for i, p in enumerate(dashas):
        # Corrected unpacking to match the 6 return values from analyze()
        sign, star, sub, substar, asp, net = engine.analyze(p)
        
        color = "green" if net > 0 else "red" if net < 0 else "white"
        table.add_row(
            lvls[i], p, 
            f"{sign}/{star}/{sub}/{substar}", 
            f"[bold {color}]{net}[/]", 
            ", ".join(asp)
        )
    return table

listener = keyboard.Listener(on_press=on_p)
listener.start()

with Live(draw(), refresh_per_second=2, screen=True) as live:
    while not exit_f:
        live.update(draw())
        time.sleep(0.2)
listener.stop()